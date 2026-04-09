#!/usr/bin/env python3
"""
earnings_calculator.py — Deterministic Calculation Tool for Earnings Analysis

All numerical calculations (EPS Surprise, Revenue Surprise, Revision Ratios,
Earnings Impact Score) MUST be computed by this tool — NOT by LLM inference.

Usage (CLI):
    python3 earnings_calculator.py --eps-actual 4.32 --eps-estimate 4.50
    python3 earnings_calculator.py --revision-data '{"up": 1, "down": 3}'
    python3 earnings_calculator.py --full-analysis '{"eps_actual": 4.32, ...}'

Usage (import):
    from earnings_calculator import EarningsCalculator
    calc = EarningsCalculator()
    result = calc.eps_surprise(actual=4.32, estimate=4.50)
"""

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class SurpriseResult:
    actual: float
    estimate: float
    surprise_absolute: float
    surprise_percent: float
    direction: str  # "beat", "miss", "in-line"


@dataclass
class RevisionResult:
    up_revisions: int
    down_revisions: int
    total_revisions: int
    ratio_str: str        # e.g. "3:1 Down-to-Up"
    direction: str        # "positive", "negative", "neutral"
    net_revision_pct: Optional[float] = None  # % change over period


@dataclass
class ImpactScore:
    total_score: int      # 0-10
    eps_surprise_score: int
    revenue_surprise_score: int
    guidance_score: int
    revision_score: int
    sentiment_score: int
    interpretation: str   # "Stark Negativ" / "Negativ" / "Neutral" / "Positiv" / "Stark Positiv"


class EarningsCalculator:
    """Deterministic earnings calculation engine."""

    @staticmethod
    def eps_surprise(actual: float, estimate: float) -> SurpriseResult:
        """Calculate EPS surprise (beat/miss)."""
        surprise_abs = actual - estimate
        surprise_pct = ((actual - estimate) / abs(estimate)) * 100 if estimate != 0 else 0.0

        if surprise_pct > 1.0:
            direction = "beat"
        elif surprise_pct < -1.0:
            direction = "miss"
        else:
            direction = "in-line"

        return SurpriseResult(
            actual=actual,
            estimate=estimate,
            surprise_absolute=round(surprise_abs, 4),
            surprise_percent=round(surprise_pct, 2),
            direction=direction,
        )

    @staticmethod
    def revenue_surprise(actual: float, estimate: float) -> SurpriseResult:
        """Calculate Revenue surprise (beat/miss)."""
        surprise_abs = actual - estimate
        surprise_pct = ((actual - estimate) / abs(estimate)) * 100 if estimate != 0 else 0.0

        if surprise_pct > 0.5:
            direction = "beat"
        elif surprise_pct < -0.5:
            direction = "miss"
        else:
            direction = "in-line"

        return SurpriseResult(
            actual=actual,
            estimate=estimate,
            surprise_absolute=round(surprise_abs, 2),
            surprise_percent=round(surprise_pct, 2),
            direction=direction,
        )

    @staticmethod
    def revision_ratio(up: int, down: int,
                       current_estimate: Optional[float] = None,
                       previous_estimate: Optional[float] = None) -> RevisionResult:
        """Calculate revision ratio (up:down or down:up)."""
        total = up + down

        if up > down:
            ratio_str = f"{up}:{down} Up-to-Down"
            direction = "positive"
        elif down > up:
            ratio_str = f"{down}:{up} Down-to-Up"
            direction = "negative"
        else:
            ratio_str = f"{up}:{down} Even"
            direction = "neutral"

        net_pct = None
        if current_estimate and previous_estimate and previous_estimate != 0:
            net_pct = round(((current_estimate - previous_estimate) / abs(previous_estimate)) * 100, 2)

        return RevisionResult(
            up_revisions=up,
            down_revisions=down,
            total_revisions=total,
            ratio_str=ratio_str,
            direction=direction,
            net_revision_pct=net_pct,
        )

    @staticmethod
    def earnings_impact_score(
        eps_surprise_pct: float,
        revenue_surprise_pct: float,
        guidance_signal: str,        # "raised", "confirmed", "lowered"
        revision_direction: str,     # "positive", "negative", "neutral"
        sentiment_score: float,      # -1.0 to 1.0
    ) -> ImpactScore:
        """Calculate the Earnings Impact Score (0-10 scale)."""

        # EPS Surprise Score (0-2)
        if eps_surprise_pct > 5:
            eps_score = 2
        elif eps_surprise_pct > 0:
            eps_score = 1
        elif eps_surprise_pct > -5:
            eps_score = 0
        else:
            eps_score = -1

        # Revenue Surprise Score (0-2)
        if revenue_surprise_pct > 3:
            rev_score = 2
        elif revenue_surprise_pct > 0:
            rev_score = 1
        elif revenue_surprise_pct > -3:
            rev_score = 0
        else:
            rev_score = -1

        # Guidance Score (0-2)
        guidance_map = {"raised": 2, "confirmed": 1, "lowered": 0}
        guide_score = guidance_map.get(guidance_signal, 1)

        # Revision Score (0-2)
        revision_map = {"positive": 2, "neutral": 1, "negative": 0}
        rev_dir_score = revision_map.get(revision_direction, 1)

        # Sentiment Score (0-2)
        if sentiment_score > 0.3:
            sent_score = 2
        elif sentiment_score > -0.3:
            sent_score = 1
        else:
            sent_score = 0

        # Total: sum of component scores, normalized to 0-10
        raw_total = eps_score + rev_score + guide_score + rev_dir_score + sent_score
        # Raw range: -2 to 10, normalize to 0-10
        total = max(0, min(10, raw_total))

        if total >= 8:
            interpretation = "Stark Positiv"
        elif total >= 6:
            interpretation = "Positiv"
        elif total >= 4:
            interpretation = "Neutral"
        elif total >= 2:
            interpretation = "Negativ"
        else:
            interpretation = "Stark Negativ"

        return ImpactScore(
            total_score=total,
            eps_surprise_score=eps_score,
            revenue_surprise_score=rev_score,
            guidance_score=guide_score,
            revision_score=rev_dir_score,
            sentiment_score=sent_score,
            interpretation=interpretation,
        )

    @staticmethod
    def price_change_pct(price_before: float, price_after: float) -> float:
        """Calculate percentage price change."""
        if price_before == 0:
            return 0.0
        return round(((price_after - price_before) / price_before) * 100, 2)

    @staticmethod
    def upside_to_target(current_price: float, target_price: float) -> float:
        """Calculate upside/downside to analyst price target."""
        if current_price == 0:
            return 0.0
        return round(((target_price - current_price) / current_price) * 100, 2)

    @staticmethod
    def pe_ratio(price: float, eps: float) -> Optional[float]:
        """Calculate P/E ratio."""
        if eps == 0:
            return None
        return round(price / eps, 2)

    @staticmethod
    def dividend_yield(annual_dividend: float, price: float) -> float:
        """Calculate dividend yield percentage."""
        if price == 0:
            return 0.0
        return round((annual_dividend / price) * 100, 2)


def main():
    parser = argparse.ArgumentParser(
        description="Earnings Calculator — Deterministic computation tool"
    )
    parser.add_argument("--eps-actual", type=float, help="Actual EPS")
    parser.add_argument("--eps-estimate", type=float, help="Estimated EPS")
    parser.add_argument("--rev-actual", type=float, help="Actual Revenue (billions)")
    parser.add_argument("--rev-estimate", type=float, help="Estimated Revenue (billions)")
    parser.add_argument("--revision-up", type=int, help="Number of upward revisions")
    parser.add_argument("--revision-down", type=int, help="Number of downward revisions")
    parser.add_argument("--current-estimate", type=float, help="Current consensus estimate")
    parser.add_argument("--previous-estimate", type=float, help="Previous consensus estimate")
    parser.add_argument("--price-before", type=float, help="Price before event")
    parser.add_argument("--price-after", type=float, help="Price after event")
    parser.add_argument("--current-price", type=float, help="Current stock price")
    parser.add_argument("--target-price", type=float, help="Analyst target price")
    parser.add_argument("--full-analysis", type=str, help="Full JSON payload for impact score")
    parser.add_argument("--output-format", default="text", choices=["text", "json"],
                        help="Output format")

    args = parser.parse_args()
    calc = EarningsCalculator()
    results = {}

    # EPS Surprise
    if args.eps_actual is not None and args.eps_estimate is not None:
        r = calc.eps_surprise(args.eps_actual, args.eps_estimate)
        results["eps_surprise"] = asdict(r)
        if args.output_format == "text":
            print(f"EPS Surprise: {r.surprise_percent:+.2f}% ({r.direction})")
            print(f"  Actual: {r.actual} | Estimate: {r.estimate} | Delta: {r.surprise_absolute:+.4f}")

    # Revenue Surprise
    if args.rev_actual is not None and args.rev_estimate is not None:
        r = calc.revenue_surprise(args.rev_actual, args.rev_estimate)
        results["revenue_surprise"] = asdict(r)
        if args.output_format == "text":
            print(f"Revenue Surprise: {r.surprise_percent:+.2f}% ({r.direction})")
            print(f"  Actual: {r.actual} | Estimate: {r.estimate} | Delta: {r.surprise_absolute:+.2f}")

    # Revision Ratio
    if args.revision_up is not None and args.revision_down is not None:
        r = calc.revision_ratio(
            args.revision_up, args.revision_down,
            args.current_estimate, args.previous_estimate
        )
        results["revision_ratio"] = asdict(r)
        if args.output_format == "text":
            print(f"Revision Ratio: {r.ratio_str} ({r.direction})")
            if r.net_revision_pct is not None:
                print(f"  Net Revision: {r.net_revision_pct:+.2f}%")

    # Price Change
    if args.price_before is not None and args.price_after is not None:
        pct = calc.price_change_pct(args.price_before, args.price_after)
        results["price_change_pct"] = pct
        if args.output_format == "text":
            print(f"Price Change: {pct:+.2f}%")

    # Upside to Target
    if args.current_price is not None and args.target_price is not None:
        upside = calc.upside_to_target(args.current_price, args.target_price)
        results["upside_to_target"] = upside
        if args.output_format == "text":
            print(f"Upside to Target: {upside:+.2f}%")

    # Full Analysis (JSON payload)
    if args.full_analysis:
        try:
            data = json.loads(args.full_analysis)
            impact = calc.earnings_impact_score(
                eps_surprise_pct=data.get("eps_surprise_pct", 0),
                revenue_surprise_pct=data.get("revenue_surprise_pct", 0),
                guidance_signal=data.get("guidance_signal", "confirmed"),
                revision_direction=data.get("revision_direction", "neutral"),
                sentiment_score=data.get("sentiment_score", 0),
            )
            results["impact_score"] = asdict(impact)
            if args.output_format == "text":
                print(f"\nEarnings Impact Score: {impact.total_score}/10 — {impact.interpretation}")
                print(f"  EPS Surprise:  {impact.eps_surprise_score}")
                print(f"  Revenue:       {impact.revenue_surprise_score}")
                print(f"  Guidance:      {impact.guidance_score}")
                print(f"  Revisions:     {impact.revision_score}")
                print(f"  Sentiment:     {impact.sentiment_score}")
        except json.JSONDecodeError as e:
            print(f"[ERR] Invalid JSON: {e}", file=sys.stderr)
            sys.exit(1)

    if args.output_format == "json":
        print(json.dumps(results, indent=2))

    if not results:
        parser.print_help()


if __name__ == "__main__":
    main()
