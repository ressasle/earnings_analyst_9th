#!/usr/bin/env python3
"""
enrich_earnings_dates.py — Populate next_earnings_date & last_earnings_date
in kasona_portfolio_assets using EODHD Fundamentals → Earnings.History.

Usage:
    # All stock assets across all portfolios
    python3 enrich_earnings_dates.py

    # Specific portfolio only
    python3 enrich_earnings_dates.py --portfolio 261001-A

    # Dry-run (no writes)
    python3 enrich_earnings_dates.py --dry-run

    # Verbose output
    python3 enrich_earnings_dates.py --verbose

Env vars required:
    EODHD_API_TOKEN   — EODHD API key
    SUPABASE_URL      — Supabase project URL
    SUPABASE_SERVICE_KEY — Supabase service role key
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any

import aiohttp
from dotenv import load_dotenv

load_dotenv()


# ── Configuration ────────────────────────────────────────────────────────────

EODHD_BASE = "https://eodhd.com/api/fundamentals"
RATE_LIMIT_PER_MIN = 25  # Stay under EODHD's 30/min limit
RATE_DELAY = 60.0 / RATE_LIMIT_PER_MIN  # ~2.4 seconds between calls


# ── EODHD: Fetch Earnings History ────────────────────────────────────────────

async def fetch_earnings_history(
    session: aiohttp.ClientSession,
    ticker_eod: str,
    api_token: str,
) -> dict[str, Any]:
    """
    Fetch Earnings.History from EODHD Fundamentals for a single ticker.
    Returns {"next_earnings_date": str|None, "last_earnings_date": str|None}.
    """
    url = (
        f"{EODHD_BASE}/{ticker_eod}"
        f"?filter=Earnings::History"
        f"&fmt=json&api_token={api_token}"
    )
    try:
        async with session.get(url) as resp:
            if resp.status != 200:
                return {"error": f"HTTP {resp.status}"}
            data = await resp.json(content_type=None)
    except Exception as e:
        return {"error": str(e)}

    if not isinstance(data, dict):
        return {"error": "Unexpected response format"}

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    last_date: str | None = None
    next_date: str | None = None

    for _period_end, entry in data.items():
        if not isinstance(entry, dict):
            continue
        report_date = entry.get("reportDate") or ""
        if not report_date:
            continue
        eps_actual = entry.get("epsActual")

        if report_date > today_str:
            # Future report date → candidate for next_earnings_date
            # (EODHD pre-fills future entries with epsActual=0, so we
            #  cannot rely on epsActual being None for future quarters)
            if next_date is None or report_date < next_date:
                next_date = report_date
        elif eps_actual is not None:
            # Past/today report date with actual EPS → last_earnings_date
            if last_date is None or report_date > last_date:
                last_date = report_date

    return {
        "next_earnings_date": next_date,
        "last_earnings_date": last_date,
    }


# ── Supabase: Read & Write ───────────────────────────────────────────────────

def get_supabase_client():
    """Lazy-init Supabase client."""
    from supabase import create_client
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_KEY"]
    return create_client(url, key)


def fetch_stock_assets(sb, portfolio_id: str | None = None) -> list[dict]:
    """Fetch all stock assets with ticker_eod from kasona_portfolio_assets."""
    query = (
        sb.table("kasona_portfolio_assets")
        .select("id, portfolio_id, ticker_eod, stock_name, asset_class, next_earnings_date, last_earnings_date")
    )
    if portfolio_id:
        query = query.eq("portfolio_id", portfolio_id)

    # Only stocks with a ticker_eod
    query = query.not_.is_("ticker_eod", "null")

    resp = query.execute()
    assets = resp.data or []

    # Filter to Stocks/ETF only (skip Crypto/Other)
    return [a for a in assets if a.get("asset_class") in ("Stocks", "ETF", None)]


def update_earnings_dates(
    sb, asset_id: str, next_date: str | None, last_date: str | None
) -> None:
    """Update next/last earnings dates for a single asset."""
    update_data: dict[str, Any] = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    # Always set both fields (even if None → clears stale data)
    update_data["next_earnings_date"] = next_date
    update_data["last_earnings_date"] = last_date

    sb.table("kasona_portfolio_assets").update(update_data).eq("id", asset_id).execute()


# ── Main Logic ───────────────────────────────────────────────────────────────

async def enrich_all(
    portfolio_id: str | None = None,
    dry_run: bool = False,
    verbose: bool = False,
) -> dict[str, Any]:
    """
    Main enrichment loop:
    1. Fetch all stock assets from Supabase
    2. For each, call EODHD Fundamentals → Earnings.History
    3. Update kasona_portfolio_assets with next/last earnings dates
    """
    api_token = os.environ.get("EODHD_API_TOKEN", "")
    if not api_token:
        print("[ERROR] EODHD_API_TOKEN not set")
        sys.exit(1)

    sb = get_supabase_client()
    assets = fetch_stock_assets(sb, portfolio_id)

    # Deduplicate by ticker_eod (many assets share the same ticker across portfolios)
    ticker_to_assets: dict[str, list[dict]] = {}
    for asset in assets:
        ticker = asset["ticker_eod"]
        ticker_to_assets.setdefault(ticker, []).append(asset)

    unique_tickers = list(ticker_to_assets.keys())
    print(f"[enrich] Found {len(assets)} assets, {len(unique_tickers)} unique tickers")

    stats = {"updated": 0, "skipped": 0, "errors": 0, "unchanged": 0}

    async with aiohttp.ClientSession() as session:
        for i, ticker in enumerate(unique_tickers, 1):
            if verbose:
                print(f"  [{i}/{len(unique_tickers)}] {ticker} ...", end=" ", flush=True)

            result = await fetch_earnings_history(session, ticker, api_token)

            if "error" in result:
                if verbose:
                    print(f"[WARNING] {result['error']}")
                stats["errors"] += 1
                # Rate limit even on errors
                await asyncio.sleep(RATE_DELAY)
                continue

            next_date = result["next_earnings_date"]
            last_date = result["last_earnings_date"]

            # Update all assets sharing this ticker
            for asset in ticker_to_assets[ticker]:
                old_next = asset.get("next_earnings_date")
                old_last = asset.get("last_earnings_date")

                if old_next == next_date and old_last == last_date:
                    stats["unchanged"] += 1
                    if verbose:
                        print(f"= (unchanged: next={next_date}, last={last_date})")
                    continue

                if dry_run:
                    print(
                        f"  [DRY-RUN] {ticker} ({asset['stock_name']}): "
                        f"next={old_next} -> {next_date}, "
                        f"last={old_last} -> {last_date}"
                    )
                    stats["updated"] += 1
                else:
                    update_earnings_dates(sb, asset["id"], next_date, last_date)
                    stats["updated"] += 1
                    if verbose:
                        print(
                            f"[OK] next={next_date}, last={last_date}"
                        )

            # Rate limiting
            await asyncio.sleep(RATE_DELAY)

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Enrich kasona_portfolio_assets with earnings dates from EODHD"
    )
    parser.add_argument(
        "--portfolio", type=str, default=None,
        help="Only enrich assets for this portfolio_id (e.g., '261001-A')"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview changes without writing to Supabase"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Show per-ticker progress"
    )
    args = parser.parse_args()

    print(f"[enrich] Starting earnings date enrichment")
    if args.portfolio:
        print(f"[enrich] Portfolio filter: {args.portfolio}")
    if args.dry_run:
        print(f"[enrich] DRY-RUN mode — no writes will be made")

    start = time.time()
    stats = asyncio.run(enrich_all(
        portfolio_id=args.portfolio,
        dry_run=args.dry_run,
        verbose=args.verbose,
    ))
    elapsed = time.time() - start

    print(f"\n[enrich] Done in {elapsed:.1f}s")
    print(f"  Updated:   {stats['updated']}")
    print(f"  Unchanged: {stats['unchanged']}")
    print(f"  Errors:    {stats['errors']}")
    print(f"  Skipped:   {stats['skipped']}")


if __name__ == "__main__":
    main()
