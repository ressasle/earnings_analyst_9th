# Earnings Reaction Patterns

> Reference Document: Historically observed patterns in quarterly results and their typical market reactions.

## 1. Beat/Miss Matrix

### Revenue × EPS Surprise Combinations

| | EPS Beat | EPS Inline | EPS Miss |
|---|----------|------------|----------|
| **Revenue Beat** | 🟢🟢 Strong Signal (+5-15%) | 🟢 Moderately positive (+2-5%) | 🟡 Mixed (-2% to +2%) |
| **Revenue Inline** | 🟢 Moderately positive (+1-5%) | 🟡 Neutral (-1% to +1%) | 🔴 Negative (-3% to -8%) |
| **Revenue Miss** | 🟡 Mixed — Quality question | 🔴 Negative (-5% to -10%) | 🔴🔴 Strong Warning Signal (-10-25%) |

### Critical Addition: Guidance Trumps Everything

> **Rule:** An EPS beat with lowered guidance is valued WORSE than an EPS miss with raised guidance.

## 2. Earnings Surprise Magnitude

The size of the surprise determines the sustainability of the reaction:

| Surprise Magnitude | Typical Reaction | Post-Earnings Drift |
|---------------------|------------------|----------------------|
| > +15% Beat | +8-20% on Earnings Day | +5-10% follow-up drift over 30 days |
| +5-15% Beat | +3-8% | +2-5% drift |
| +1-5% Beat | +1-3% | Minimal to no drift |
| -1% to -5% Miss | -3-8% | -2-5% drift |
| > -5% Miss | -8-20% | -5-15% drift |

## 3. Post-Earnings Announcement Drift (PEAD)

One of the most robust anomalies in financial research:

- **Positive Surprise → Price drifts FURTHER up** (30-60 days)
- **Negative Surprise → Price drifts FURTHER down** (30-60 days)
- **Strongest Drift** in small/mid-cap companies (information asymmetry)
- **Weaker Drift** in mega-caps (faster information processing)

**Practical Implication:** Don't catch falling knives after a genuine miss. The first sell-off is rarely the last.

## 4. Revenue vs. EPS — What Matters More?

| Metric | Weighting | Reasoning |
|--------|-----------|-----------|
| **Revenue Growth** | 🥇 Higher (for Growth stocks) | Harder to manipulate than EPS |
| **EPS Beat** | 🥇 Higher (for Value stocks) | Shows operational efficiency and margin control |
| **Operating Cash Flow** | 🥇 Highest quality | "Cash is king" — profits without cash flow are just accounting entries |

### Warning Signs of Low Earnings Quality:
- EPS rising while operating cash flow falls → Creative accounting / one-offs
- Revenue rising while gross margin falls → Growth at the cost of profitability
- EPS rising due to share buybacks, not profit growth → Artificial boost

## 5. Guidance Patterns

| Guidance Signal | Typical Market Reaction | Interpretation |
|-----------------|-------------------------|----------------|
| Guidance significantly raised (>5%) | +5-10% above beat reaction | Management sees acceleration |
| Guidance slightly raised (1-5%) | +1-3% above beat reaction | Conservative management, bullish signal |
| Guidance reiterated | Neutral reaction | "Business as usual" |
| Guidance slightly lowered (1-5%) | -3-8% below miss reaction | First warning signs |
| Guidance significantly lowered (>5%) | -10-20% | Fundamental shift — review investment case |
| Guidance withdrawn | -15-30% | Maximum uncertainty — often during crises |

## 6. Sector-Specific Patterns

### Technology / SaaS
- **Key Metrics:** Revenue Growth Rate, Net Revenue Retention (NRR), Rule of 40
- **Typical Overreaction to:** Deceleration in growth (even if still high in absolute terms)
- **Note:** Recurring revenue is valued more highly than one-time revenue

### Financial Sector / Banks
- **Key Metrics:** Net Interest Margin (NIM), Loan Loss Provisions, Book Value
- **Typical Overreaction to:** Increase in risk provisions
- **Note:** Quarterly results highly dependent on macro environment

### Consumer Goods / Retail
- **Key Metrics:** Same-Store Sales, Inventory Days, Customer Acquisition Cost
- **Typical Overreaction to:** Inventory build-up without revenue increase
- **Note:** Seasonal effects (Q4 = Holiday Season) are crucial

### Pharma / Biotech
- **Key Metrics:** Pipeline updates, FDA decisions, patent expirations
- **Typical Overreaction to:** Clinical trial results (Phase 2/3)
- **Note:** Quarterly numbers often less relevant than pipeline progress

## 7. Insider Trading Signals Around Earnings

| Pattern | Signal Strength | Interpretation |
|---------|-----------------|----------------|
| CEO buys before earnings (Open Market) | 🟢🟢 Strong Bullish | Knows the numbers, betting own money |
| CFO buys before earnings | 🟢🟢 Strong Bullish | The "numbers guy" is buying |
| Multiple insiders buy simultaneously | 🟢🟢🟢 Cluster Signal | Strongest insider indicator |
| CEO sells before earnings | 🔴 Warning Signal | Context-dependent (could be tax planning) |
| Scheduled sales (10b5-1 Plan) | ⚪ Neutral | Automated, little signal value |
| Congress member buys | 🟡 Interesting | Potential information edge, but not a defined signal |

## 8. Revision Momentum as a Lead Indicator

```
EPS Revision Signal Strength:

Strongly Bullish: epsRevisionsUp30d >= 8 AND epsRevisionsDown30d <= 1
Bullish:          epsRevisionsUp30d > epsRevisionsDown30d × 2
Neutral:          epsRevisionsUp30d ≈ epsRevisionsDown30d
Bearish:          epsRevisionsDown30d > epsRevisionsUp30d × 2
Strongly Bearish: epsRevisionsDown30d >= 8 AND epsRevisionsUp30d <= 1
```

**Critical Insight:** If EPS estimates have risen steadily over the last 90 days (`epsTrendCurrent > epsTrend90daysAgo`), expectations are high. A beat must be SIGNIFICANT to move the price. The "Whisper Number" is above consensus.
