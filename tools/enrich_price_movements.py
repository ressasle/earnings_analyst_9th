#!/usr/bin/env python3
"""
enrich_price_movements.py — Populate price movement and benchmark comparison
columns for quarterly_earnings rows that have a valid report_date.

Columns populated:
  price_movement_7d_prior       - % change 7 trading days leading into earnings
  price_movement_post_earnings  - % change close on report_date to next trading day
  benchmark_ticker              - QQQ for tech/software, SPY for all others
  benchmark_move_post           - benchmark % change over same post-earnings window
  relative_performance          - stock_post - benchmark_post (pp outperformance)
  movement_reasoning            - factual narrative with market-participant rationale

Usage:
    python tools/enrich_price_movements.py
    python tools/enrich_price_movements.py --dry-run
    python tools/enrich_price_movements.py --ticker STVN.US --verbose
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

import requests
from dotenv import load_dotenv
from utils.supabase_client import get_supabase_client

load_dotenv()

EODHD_EOD_BASE = "https://eodhd.com/api/eod"
RATE_DELAY = 2.5

TECH_SECTOR_KEYWORDS = {
    "technology", "software", "semiconductor", "internet", "electronic",
    "hardware", "cloud", "saas", "artificial intelligence", "cybersecurity",
    "telecom", "telecommunication", "it services", "data", "computing",
}

SKIP_PREFIXES = ("PRIVATE.", "MARKET_OVERVIEW_")
SKIP_TICKERS  = {
    "ANTHROPIC", "OPENAI", "CANVA", "CEREBRAS", "STRIPE", "REVOLUT",
    "SPACEX", "DATABRICKS", "KRAKEN", "DEEL", "DISCORD", "ANDURIL",
    "BTC-USD.CC", "ETH-USD.CC", "SOL-USD.CC",
}


def determine_benchmark(sector: str | None, industry: str | None) -> tuple[str, str]:
    """Returns (benchmark_ticker, benchmark_label) based on sector/industry."""
    combined = f"{(sector or '')} {(industry or '')}".lower()
    for kw in TECH_SECTOR_KEYWORDS:
        if kw in combined:
            return "QQQ.US", "Nasdaq-100"
    return "SPY.US", "S&P 500"


def fetch_eod_prices(ticker: str, from_date: str, to_date: str, api_token: str) -> list[dict]:
    url = (
        f"{EODHD_EOD_BASE}/{ticker}"
        f"?from={from_date}&to={to_date}&period=d&order=a&fmt=json&api_token={api_token}"
    )
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            return []
        data = resp.json()
        if not isinstance(data, list):
            return []
        return [{"date": d["date"], "close": float(d["adjusted_close"])} for d in data if "adjusted_close" in d]
    except Exception:
        return []


def pct_change(before: float, after: float) -> float:
    if before == 0:
        return 0.0
    return round((after - before) / before * 100, 2)


def compute_movements(
    ticker: str, report_date_str: str, api_token: str,
    sector: str | None = None, industry: str | None = None,
) -> dict[str, Any] | None:
    """Compute all price movement and benchmark metrics."""
    report_date = date.fromisoformat(report_date_str)
    from_date = (report_date - timedelta(days=20)).isoformat()
    to_date   = (report_date + timedelta(days=7)).isoformat()

    prices = fetch_eod_prices(ticker, from_date, to_date, api_token)
    time.sleep(RATE_DELAY)

    if len(prices) < 3:
        return None

    price_map = {p["date"]: p["close"] for p in prices}
    dates_sorted = sorted(price_map.keys())
    before_report = [d for d in dates_sorted if d < report_date_str]
    from_report   = [d for d in dates_sorted if d >= report_date_str]

    if len(before_report) < 2 or len(from_report) < 1:
        return None

    # 7-day prior drift
    start_prior = before_report[-8] if len(before_report) >= 8 else before_report[0]
    end_prior = before_report[-1]
    move_7d = pct_change(price_map[start_prior], price_map[end_prior])

    # price_movement_post_earnings:
    #   Preferred: close on report_date → close next trading day
    #   Fallback:  if next trading day not yet published, use prior-day close → report-day close
    #              (captures the earnings-day market reaction when fresh data isn't available)
    report_day_close = price_map.get(report_date_str)
    if report_day_close is None and before_report:
        report_day_close = price_map[before_report[-1]]

    all_after = [d for d in dates_sorted if d > report_date_str]
    if len(from_report) >= 2:
        # Next trading day exists inside our window
        next_day_close = price_map[from_report[1]]
    elif all_after:
        # Next trading day exists beyond our window
        next_day_close = price_map[all_after[0]]
    elif report_day_close and before_report:
        # No next-day data yet (very recent report); use prior-day → report-day as proxy
        prior_close = price_map[before_report[-1]]
        next_day_close = report_day_close
        report_day_close = prior_close
    else:
        return None

    move_post = pct_change(report_day_close, next_day_close)

    # Benchmark comparison
    bm_ticker, bm_label = determine_benchmark(sector, industry)
    bm_prices = fetch_eod_prices(bm_ticker, from_date, to_date, api_token)
    time.sleep(RATE_DELAY)

    benchmark_move_post = None
    relative_perf = None

    if len(bm_prices) >= 2:
        bm_map = {p["date"]: p["close"] for p in bm_prices}
        bm_dates = sorted(bm_map.keys())
        bm_before = [d for d in bm_dates if d < report_date_str]
        bm_from   = [d for d in bm_dates if d >= report_date_str]
        bm_rc = bm_map.get(report_date_str)
        if bm_rc is None and bm_before:
            bm_rc = bm_map[bm_before[-1]]
        if bm_rc:
            if len(bm_from) >= 2:
                bm_nc = bm_map[bm_from[1]]
                benchmark_move_post = pct_change(bm_rc, bm_nc)
            else:
                bm_after = [d for d in bm_dates if d > report_date_str]
                if bm_after:
                    benchmark_move_post = pct_change(bm_rc, bm_map[bm_after[0]])
                elif bm_before:
                    # No next-day data yet — use prior-day → report-day as proxy (same as stock)
                    bm_prior_rc = bm_map[bm_before[-1]]
                    benchmark_move_post = pct_change(bm_prior_rc, bm_rc)
        if benchmark_move_post is not None:
            relative_perf = round(move_post - benchmark_move_post, 2)

    return {
        "price_movement_7d_prior": move_7d,
        "price_movement_post_earnings": move_post,
        "benchmark_ticker": bm_ticker.split(".")[0],
        "benchmark_label": bm_label,
        "benchmark_move_post": benchmark_move_post,
        "relative_performance": relative_perf,
    }


def build_reasoning(
    company_name: str, ticker: str, quarter: str | None, fiscal_year: int | None,
    eps_actual: float | None, eps_estimate: float | None,
    move_7d: float, move_post: float,
    benchmark_label: str = "S&P 500",
    benchmark_move_post: float | None = None,
    relative_perf: float | None = None,
) -> str:
    """Multi-paragraph movement reasoning with benchmark context and market-participant rationale."""
    period = f"{quarter} {fiscal_year}" if quarter and fiscal_year else "the reported quarter"

    # EPS context
    if eps_actual is not None and eps_estimate is not None:
        eps_a, eps_e = float(eps_actual), float(eps_estimate)
        pct = (eps_a - eps_e) / abs(eps_e) * 100 if eps_e != 0 else 0.0
        if abs(pct) < 2:
            eps_text = f"EPS of {eps_a:.2f} was in line with the estimate of {eps_e:.2f}"
            eps_ctx = "an in-line print typically resolves pre-earnings uncertainty without a strong directional catalyst"
        elif pct > 0:
            eps_text = f"EPS of {eps_a:.2f} beat the estimate of {eps_e:.2f} by {abs(pct):.1f}%"
            eps_ctx = "a beat of that magnitude draws incremental demand from momentum participants while prompting some profit-taking from those positioned ahead of the release"
        else:
            eps_text = f"EPS of {eps_a:.2f} missed the estimate of {eps_e:.2f} by {abs(pct):.1f}%"
            eps_ctx = "a miss of that scale often triggers repositioning by event-driven participants and systematic de-risking by algorithms monitoring earnings deviation thresholds"
    else:
        eps_text = "EPS data was not available"
        eps_ctx = "the absence of consensus data makes it difficult to attribute price action directly to a beat or miss"

    # Pre-earnings drift
    if move_7d > 3.0:
        drift = f"the stock gained {move_7d:.1f}% in the seven trading days leading into earnings"
        drift_why = "This appreciation typically reflects informed positioning or sector momentum ahead of an expected material beat."
    elif move_7d > 1.5:
        drift = f"the stock gained {move_7d:.1f}% in the seven trading days leading into earnings"
        drift_why = "The moderate pre-earnings gain suggests measured bullish positioning—investors expecting results at or slightly above consensus."
    elif move_7d < -3.0:
        drift = f"the stock declined {abs(move_7d):.1f}% in the seven trading days leading into earnings"
        drift_why = "A decline of this magnitude indicates defensive repositioning or active short selling by participants anticipating a miss or cautious guidance."
    elif move_7d < -1.5:
        drift = f"the stock declined {abs(move_7d):.1f}% in the seven trading days leading into earnings"
        drift_why = "The modest pre-earnings decline reflects cautious positioning—possibly driven by sector weakness or reduced conviction ahead of the release."
    else:
        drift = f"the stock was largely flat ({move_7d:+.1f}%) in the seven trading days prior to the report"
        drift_why = "The flat pre-earnings drift indicates balanced positioning—the market entered the event without a strong directional lean."

    # Post-earnings reaction
    if move_post > 5.0:
        react = f"shares surged {move_post:.1f}% on the day following the release"
        react_why = "A move of this scale typically signals results exceeded not just consensus but likely the more optimistic whisper numbers, prompting short covering and fresh momentum buying."
    elif move_post > 2.0:
        react = f"shares rose {move_post:.1f}% following the announcement"
        react_why = "A positive measured reaction suggests results were ahead of consensus without dramatically exceeding expectations—reflecting incremental conviction rather than a broad short-covering event."
    elif move_post > 0.5:
        react = f"shares rose modestly by {move_post:.1f}% following the announcement"
        react_why = "The muted positive reaction may indicate results met expectations after pre-announcement appreciation had already absorbed some upside."
    elif move_post < -5.0:
        react = f"shares fell sharply by {abs(move_post):.1f}% on the day following the release"
        react_why = "A decline of this magnitude typically signals a significant negative surprise—EPS miss, guidance cut, or margin deterioration undermining the prevailing growth narrative."
    elif move_post < -2.0:
        react = f"shares declined {abs(move_post):.1f}% following the announcement"
        react_why = "This decline suggests results disappointed relative to consensus or forward guidance introduced uncertainty, with event-driven participants likely driving the initial leg lower."
    elif move_post < -0.5:
        react = f"shares declined modestly by {abs(move_post):.1f}% following the announcement"
        react_why = "The modest negative reaction may reflect a slight miss on one or more metrics or a cautious management tone on guidance—neither severe enough to trigger sustained selling."
    else:
        react = f"shares were relatively unchanged ({move_post:+.1f}%) after the release"
        react_why = "A flat post-earnings reaction suggests results broadly matched expectations, leaving neither bulls nor bears with a strong new signal to act on."

    # Benchmark comparison
    if benchmark_move_post is not None and relative_perf is not None:
        direction = "outperformed" if relative_perf > 0 else "underperformed"
        abs_rel = abs(relative_perf)
        if abs_rel > 3.0:
            rel_note = "a divergence of that magnitude over a single session reflects strong company-specific catalysts rather than broad market momentum"
        elif abs_rel > 1.0:
            rel_note = f"a divergence of {abs_rel:.1f} percentage points indicates a meaningful company-specific move relative to the prevailing market environment"
        else:
            rel_note = "the near-benchmark performance suggests broader market conditions contributed materially to the price action"
        bm_para = (
            f" For context, the {benchmark_label} moved {benchmark_move_post:+.2f}% over the same "
            f"post-earnings window. {company_name} {direction} its benchmark by {abs_rel:.1f} "
            f"percentage points—{rel_note}."
        )
    else:
        bm_para = ""

    return (
        f"For {period}, {company_name} ({ticker}) reported results where {eps_text}; {eps_ctx}. "
        f"In the lead-up to the release, {drift}. {drift_why} "
        f"Following the announcement, {react}. {react_why}{bm_para}"
    )


def fetch_missing_rows(sb, ticker: str | None = None) -> list[dict]:
    base_select = (
        "id, ticker_eod, company_name, report_date, quarter, "
        "fiscal_year, eps_actual, eps_estimate"
    )

    def query(null_field):
        q = (
            sb.table("quarterly_earnings")
            .select(base_select)
            .not_.is_("report_date", "null")
            .is_(null_field, "null")
        )
        if ticker:
            q = q.eq("ticker_eod", ticker)
        return q.execute()

    rows  = query("price_movement_7d_prior").data or []
    rows2 = query("price_movement_post_earnings").data or []
    seen, combined = set(), []
    for r in rows + rows2:
        if r["id"] not in seen:
            seen.add(r["id"])
            combined.append(r)
    return combined


def fetch_sector_for_ticker(ticker: str) -> tuple[str, str]:
    api_token = os.environ.get("EODHD_API_TOKEN", "")
    if not api_token:
        return "", ""
    try:
        url = f"https://eodhd.com/api/fundamentals/{ticker}?api_token={api_token}&fmt=json&filter=General"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("Sector", ""), data.get("Industry", "")
    except Exception:
        pass
    return "", ""


def update_row(sb, row_id: str, move_7d: float, move_post: float, reasoning: str,
               benchmark_ticker: str | None, benchmark_move_post: float | None,
               relative_performance: float | None) -> None:
    sb.table("quarterly_earnings").update({
        "price_movement_7d_prior": move_7d,
        "price_movement_post_earnings": move_post,
        "movement_reasoning": reasoning,
        "benchmark_ticker": benchmark_ticker,
        "benchmark_move_post": benchmark_move_post,
        "relative_performance": relative_performance,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", row_id).execute()


def main():
    parser = argparse.ArgumentParser(
        description="Enrich quarterly_earnings with price movement and benchmark data"
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--ticker", help="Process a single ticker (e.g. STVN.US)")
    args = parser.parse_args()

    api_token = os.environ.get("EODHD_API_TOKEN", "")
    if not api_token:
        print("[ERROR] EODHD_API_TOKEN not set")
        sys.exit(1)

    sb = get_supabase_client()
    rows = fetch_missing_rows(sb, ticker=args.ticker)

    actionable = [
        r for r in rows
        if not any(r.get("ticker_eod", "").startswith(p) for p in SKIP_PREFIXES)
        and r.get("ticker_eod") not in SKIP_TICKERS
        and r.get("report_date")
    ]

    print(f"[enrich_price] Found {len(rows)} total rows missing data")
    print(f"[enrich_price] {len(actionable)} actionable rows")
    if args.dry_run:
        print("[enrich_price] DRY-RUN — no writes")

    stats = {"updated": 0, "skipped": 0, "errors": 0}

    for i, row in enumerate(actionable, 1):
        ticker      = row["ticker_eod"]
        company     = row.get("company_name") or ticker
        report_date = row["report_date"]
        row_id      = row["id"]

        if args.verbose:
            print(f"  [{i}/{len(actionable)}] {ticker} ({report_date}) ... ", end="", flush=True)

        sector, industry = fetch_sector_for_ticker(ticker)
        time.sleep(0.5)

        movements = compute_movements(ticker, report_date, api_token, sector=sector, industry=industry)
        if movements is None:
            if args.verbose:
                print("[SKIP] insufficient price data")
            stats["skipped"] += 1
            continue

        move_7d       = movements["price_movement_7d_prior"]
        move_post     = movements["price_movement_post_earnings"]
        bm_ticker     = movements.get("benchmark_ticker")
        bm_label      = movements.get("benchmark_label", "S&P 500")
        bm_move_post  = movements.get("benchmark_move_post")
        relative_perf = movements.get("relative_performance")

        reasoning = build_reasoning(
            company_name=company, ticker=ticker,
            quarter=row.get("quarter"), fiscal_year=row.get("fiscal_year"),
            eps_actual=row.get("eps_actual"), eps_estimate=row.get("eps_estimate"),
            move_7d=move_7d, move_post=move_post,
            benchmark_label=bm_label,
            benchmark_move_post=bm_move_post,
            relative_perf=relative_perf,
        )

        if args.dry_run:
            bm_str = f"  bm={bm_ticker} {bm_move_post:+.2f}%  rel={relative_perf:+.2f}pp" if bm_move_post is not None else ""
            print(f"\n    7d={move_7d:+.2f}%  post={move_post:+.2f}%{bm_str}")
            print(f"    reasoning: {reasoning[:160]}...")
            stats["updated"] += 1
        else:
            try:
                update_row(sb, row_id, move_7d, move_post, reasoning,
                           bm_ticker, bm_move_post, relative_perf)
                stats["updated"] += 1
                if args.verbose:
                    bm_str = f"  bm={bm_ticker} {bm_move_post:+.2f}%  rel={relative_perf:+.2f}pp" if bm_move_post is not None else ""
                    print(f"[OK] 7d={move_7d:+.2f}%  post={move_post:+.2f}%{bm_str}")
            except Exception as e:
                print(f"[ERROR] {ticker}: {e}")
                stats["errors"] += 1

    print(f"\n[enrich_price] Done. Updated={stats['updated']}  Skipped={stats['skipped']}  Errors={stats['errors']}")


if __name__ == "__main__":
    main()
