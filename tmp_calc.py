import sys
sys.path.append('c:/Users/Administrator/Documents/kasonaops/invest_analysis/08_quarterly-earnings-analyst/tools')
from earnings_calculator import EarningsCalculator

calc = EarningsCalculator()
impact = calc.earnings_impact_score(
    eps_surprise_pct=24.9,
    revenue_surprise_pct=0.2,
    guidance_signal="raised",
    revision_direction="positive",
    sentiment_score=0.75
)

print(f"Total Score: {impact.total_score}")
print(f"Interpretation: {impact.interpretation}")
print(f"EPS Score: {impact.eps_surprise_score}")
print(f"Revenue Score: {impact.revenue_surprise_score}")
print(f"Guidance Score: {impact.guidance_score}")
print(f"Revision Score: {impact.revision_score}")
print(f"Sentiment Score: {impact.sentiment_score}")
