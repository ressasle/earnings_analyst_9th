# Earnings Report Template

> This template defines the complete output structure for the Quarterly Earnings Analyst.
> Language: English ONLY.
> Style: Precise, analytical, data-driven with absolute numerical values ($2.4B instead of "strong growth").
> Adapted and expanded from the ME_CIO_BOT Family Office Format.

---

## Filename Convention

```
analysed_assets/{TICKER}/earnings/Q{X}_{YYYY}_earnings_briefing.md
```

Example: `analysed_assets/AAPL/earnings/Q1_2026_earnings_briefing.md`

---

## Full Report Template

````markdown
# EARNINGS BRIEFING: {COMPANY_NAME} ({TICKER})
> Quarter: Q{X} FY{YYYY} | Report Date: {DATE} | Earnings Date: {EARNINGS_DATE} ({AMC/BMO})

---

## 1. Executive Summary

{One compact paragraph — maximum 5 sentences:}
- Did the results meet, exceed, or miss expectations?
- What is the "Big Picture" for this quarter?
- Has the strategic direction changed?
- Relevance to the existing investment thesis.

**Earnings Impact Score: {XX}/100** ({Interpretation: Excellent/Solid/Mixed/Weak/Alarm})

---

## 2. The Hard Numbers

### Key Financial Metrics

| Metric | Actual | Expectation (Consensus) | Surprise | YoY Change |
|--------|---------|-------------------------|----------|------------|
| **EPS** | ${X.XX} | ${X.XX} | {+/-X.X%} | {+/-X.X%} |
| **Revenue** | ${XX.X}B | ${XX.X}B | {+/-X.X%} | {+/-X.X%} |
| **Gross Margin** | {XX.X%} | — | — | {+/-X.X pp} |
| **Operating Margin** | {XX.X%} | — | — | {+/-X.X pp} |
| **Operating Cash Flow** | ${XX.X}B | — | — | {+/-X.X%} |
| **Free Cash Flow** | ${XX.X}B | — | — | {+/-X.X%} |

### Earnings Surprise Score

```
EPS Surprise:     {Calculation: (Actual - Expected) / |Expected| × 100 = +/-X.X%}
Revenue Surprise: {Calculation: (Actual - Expected) / |Expected| × 100 = +/-X.X%}
```

### Guidance

| Metric | Previous Guidance | New Guidance | Change |
|--------|-------------------|--------------|--------|
| **Revenue Q{X+1}** | ${XX}B - ${XX}B | ${XX}B - ${XX}B | {Raised/Reiterated/Lowered} |
| **EPS FY{YYYY}** | ${X.XX} | ${X.XX} | {Raised/Reiterated/Lowered} |
| **Margin** | {XX%} | {XX%} | {+/-X pp} |

**Guidance Signal:** {🟢 Raised / 🟡 Reiterated / 🔴 Lowered}

### Dividend

| Metric | Current | Previous Quarter | Change |
|--------|---------|------------------|--------|
| **Dividend/Share** | ${X.XX} | ${X.XX} | {+/-X%} |
| **Payout Ratio** | {XX%} | {XX%} | {+/-X pp} |
| **Ex-Dividend Date** | {DATE} | — | — |

---

## 3. Analyst Expectations & Revision Momentum

### EPS Trend Development (90 days prior to earnings)

```
T-90 Days: ${X.XX} (epsTrend90daysAgo)
T-60 Days: ${X.XX} (epsTrend60daysAgo)
T-30 Days: ${X.XX} (epsTrend30daysAgo)
T-7 Days:  ${X.XX} (epsTrend7daysAgo)
Current:   ${X.XX} (epsTrendCurrent)

Drift: {+/-X.X%} in 90 days → {Upward Drift / Neutral / Downward Drift}
```

### Revision Balance (last 30 days)

| Period | Upward Revisions | Downward Revisions | Net |
|--------|-------------------|--------------------|-----|
| Last 7 Days | {X} | {X} | {+/-X} |
| Last 30 Days | {X} | {X} | {+/-X} |

**Revision Signal:** {🟢 Strongly Bullish / 🟢 Bullish / 🟡 Neutral / 🔴 Bearish / 🔴 Strongly Bearish}

### Analyst Rating Distribution

| Rating | Count | Share |
|--------|-------|-------|
| Strong Buy | {X} | {XX%} |
| Buy | {X} | {XX%} |
| Hold | {X} | {XX%} |
| Sell | {X} | {XX%} |
| Strong Sell | {X} | {XX%} |

**Consensus Price Target:** ${XXX.XX} ({+/-XX%} from current price)

---

## 4. Pre-Earnings Setup

### Price Performance (30 days prior to earnings)

```
Price T-30: ${XXX.XX}
Price T-1:  ${XXX.XX}
30-Day Performance: {+/-XX.X%}
30-Day Volume Trend: {Rising / Falling / Normal}
```

**Pre-Earnings Drift:** {Price drifted into earnings — expectations were {high/low/neutral}}

### Sentiment Trend (14 days prior to earnings)

| Date | Score | Articles | Interpretation |
|------|-------|----------|----------------|
| T-14 | {0.XX} | {X} | {Bullish/Neutral/Bearish} |
| T-7 | {0.XX} | {X} | {Bullish/Neutral/Bearish} |
| T-1 | {0.XX} | {X} | {Bullish/Neutral/Bearish} |

**Sentiment Trend:** {Rising → high expectations / Falling → nervousness / Stable}

### Insider Activity (90 days prior to earnings)

| Date | Name | Position | Action | Price | Signal |
|------|------|----------|--------|-------|--------|
| {DATE} | {Name} | {CEO/CFO/Congress} | {Buy/Sell} | ${XXX} | {🟢/🔴/🟡} |

**Insider Signal:** {Cluster Buys = Bullish / Insider Selling = Warning / Neutral}

---

## 5. Market Reaction

### Stock Performance

```
Earnings Day:
  Previous Close: ${XXX.XX}
  Opening:        ${XXX.XX} (Gap: {+/-XX.X%})
  Closing:        ${XXX.XX} (Open-to-Close: {+/-XX.X%})
  Close-to-Close: {+/-XX.X%}

5-Day Follow-Through:
  T+1: {+/-X.X%}
  T+2: {+/-X.X%}
  T+3: {+/-X.X%}
  T+4: {+/-X.X%}
  T+5: {+/-X.X%}
  Cumulative: {+/-XX.X%}
```

**Post-Earnings Drift:** {Continuation of move → PEAD confirmed / Reversal → Overreaction}

### Reaction Pattern Classification

```
Numbers: {Beat/Miss}
Guidance: {Raised/Reiterated/Lowered}
Price Reaction: {+/-XX%}
→ Pattern: {Example: "Beat + Guidance Raised + strong price reaction = Strong Quarter"}
```

### Top 3 Post-Earnings Headlines

1. **{Headline}** — Source: {Source} — Sentiment: {Polarity}
2. **{Headline}** — Source: {Source} — Sentiment: {Polarity}
3. **{Headline}** — Source: {Source} — Sentiment: {Polarity}

**Dominant Narrative:** {What is the central theme of the media coverage?}

### Post-Earnings Sentiment Shift

```
Pre-Earnings Sentiment (Avg 7 days):  {0.XX}
Post-Earnings Sentiment (Avg 3 days): {0.XX}
Shift: {+/-0.XX} → {Positive Swing / Negative Swing / No Shift}
```

---

## 6. Ownership Structure & Institutional Changes

### Top Institutions (with changes)

| Institution | Stake (%) | Change (%) | Direction |
|-------------|-----------|------------|-----------|
| {Name} | {X.XX%} | {+/-X.XX%} | {🟢 Accumulating / 🔴 Reducing} |
| {Name} | {X.XX%} | {+/-X.XX%} | {🟢 Accumulating / 🔴 Reducing} |
| {Name} | {X.XX%} | {+/-X.XX%} | {🟢 Accumulating / 🔴 Reducing} |

**Notable Details:** {e.g., "Berkshire Hathaway reduced position by 14.9% — Buffett scaling back"}

---

## 7. Transcript Highlights

> Source: Earnings Call Transcript via WebSearch

### Management Tone
{Confident / Defensive / Cautious / Euphoric — with concrete quotes}

### Strategic Initiatives
- {Initiative 1}: {Description and implication}
- {Initiative 2}: {Description and implication}
- {Initiative 3}: {Description and implication}

### Key Statements

| Speaker | Statement | Interpretation |
|---------|-----------|----------------|
| CEO | "{Quote}" | {What does this mean?} |
| CFO | "{Quote}" | {What does this mean?} |

### Capital Allocation
- **CapEx:** ${XX}B planned ({Increase/Decrease})
- **Share Buybacks:** ${XX}B authorized
- **M&A Pipeline:** {Any hints of acquisitions?}

---

## 8. Strategic CIO Assessment

> **The Professional Opinion of the Chief Investment Officer**

### Moat Status
{Is the competitive advantage (Moat) still intact? Has it strengthened or eroded?}
{Specific evidence from the quarterly results for the Moat assessment}

### Valuation Check
```
Current Price:    ${XXX.XX}
Consensus Target: ${XXX.XX} ({+/-XX%} Upside/Downside)
Forward P/E:      {XX.X} (vs. Sector Median: {XX.X})
EV/EBITDA:        {XX.X} (vs. 5-Year Average: {XX.X})

Assessment: {Undervalued / Fairly Valued / Overvalued}
```

### Action Recommendation (Internal)

{One of five options:}
- 🟢 **Buy on weakness** — Numbers confirm the thesis, price offers an entry
- 🟢 **Hold and overweight** — Thesis intact, expand position
- 🟡 **Hold** — No change to the position
- 🟡 **Watchlist** — Some warning signs, wait for next quarter
- 🔴 **Reduce position** — Fundamental case showing cracks

### Rationale
{2-3 sentences: Why exactly this recommendation? What was the deciding factor?}

---

## 9. Risks & Monitoring Points

### Short-Term Risks (0-6 months)
1. {Risk 1}: {Description and potential impact}
2. {Risk 2}: {Description and potential impact}
3. {Risk 3}: {Description and potential impact}

### Long-Term Risks (6-24 months)
1. {Risk 1}: {Description}
2. {Risk 2}: {Description}

### Next Catalysts
| Date | Event | Expected Impact |
|------|-------|-----------------|
| {DATE} | {Event e.g., "Next Earnings Q{X+1}"} | {Description} |
| {DATE} | {Event e.g., "Product Launch"} | {Description} |
| {DATE} | {Event e.g., "Fed Decision"} | {Description} |

---

## 10. Data Source Appendix

| Source | EODHD Endpoint | Query Time | Status |
|--------|----------------|------------|--------|
| Earnings Calendar | `get_upcoming_earnings` | {Timestamp} | ✅ |
| Earnings Trends | `get_earnings_trends` | {Timestamp} | ✅ |
| Fundamentals | `get_fundamentals_data` | {Timestamp} | ✅ |
| Sentiment | `get_sentiment_data` | {Timestamp} | ✅ |
| Insider Trades | `get_insider_transactions` | {Timestamp} | ✅ |
| Price Data | `get_historical_stock_prices` | {Timestamp} | ✅ |
| News | `get_company_news` | {Timestamp} | ✅ |
| Dividends | `get_upcoming_dividends` | {Timestamp} | ✅ |
| Transcript | WebSearch | {Timestamp} | {✅/⚠️} |

---

## 11. References

### Data Sources (Institutional APIs)
- **Fundamentals & Valuation:** [Data Source — {Ticker}](https://eodhistoricaldata.com/api/fundamentals/{Ticker})
- **EPS Revisions & Analyst Expectations:** [Analyst Trends — {Ticker}](https://eodhistoricaldata.com/api/calendar/trends?symbols={Ticker})
- **Historical Price Data:** [Price History — {Ticker}](https://eodhistoricaldata.com/api/eod/{Ticker})
- **News Sentiment:** [Sentiment Analysis — {Ticker}](https://eodhistoricaldata.com/api/sentiments?symbols={Ticker})
- **Company News:** [Company News — {Ticker}](https://eodhistoricaldata.com/api/news?s={Ticker})
- **Dividend History:** [Dividend History — {Ticker}](https://eodhistoricaldata.com/api/div/{Ticker})
- **Insider Transactions:** [Insider Transactions](https://eodhistoricaldata.com/api/insider-transactions)

### Earnings Call & Investor Relations
- **Original Transcript & Presentation:** [IR Portal / Call Transcript]({TranscriptLink})
- **Earnings Summary:** [Market Analysis / Analyst Coverage]({AnalysisLink})

### Valuation & Analyst Ratings
- [Simply Wall St — {COMPANY_NAME}](https://simplywall.st/stocks/{COUNTRY_PATH}/{SYMBOL})
- [Yahoo Finance — {SYMBOL} Analyst Ratings](https://finance.yahoo.com/quote/{YAHOO_TICKER}/)

---

> *This report was automatically generated using Artificial Intelligence by the KASONA Quarterly Earnings Analyst. Despite integration with institutionally used data providers and original sources, all information should be independently verified before making any trading decisions.*
> *Confidential — KASONA Investment Intelligence*
````

---

## Calculation Note

> **All numerical calculations** (EPS Surprise, Revenue Surprise, Earnings Impact Score, revision ratios) must be performed via the `earnings_calculator.py` tool — NOT through LLM inference. The skill controls the calculation directly via the tool and uses raw data from the EODHD APIs.
