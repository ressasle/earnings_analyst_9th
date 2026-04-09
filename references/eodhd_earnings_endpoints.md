# EODHD MCP Endpoints für Earnings-Analyse

> Referenzdokument: Welche EODHD MCP-Tools werden in welchem Schritt benötigt und mit welchen Parametern aufgerufen.

## Endpoint-Übersicht

| Tool | API-Kosten | Schritt | Hauptzweck |
|------|-----------|---------|------------|
| `get_upcoming_earnings` | 1 Call | 1, 3 | Earnings-Kalender + Actual vs. Estimate |
| `get_earnings_trends` | 10 Calls | 1 | EPS/Revenue-Schätzungen + Revisions |
| `get_historical_stock_prices` | 1 Call | 2, 4 | Kursreaktion vor/nach Earnings |
| `get_sentiment_data` | 1 Call | 2, 4 | Tägliche Stimmungsanalyse |
| `get_insider_transactions` | 10 Calls | 2 | Insider-Aktivität (inkl. Congress) |
| `get_fundamentals_data` | 1 Call | 3 | Financials, Valuation, Holders, Ratings |
| `get_upcoming_dividends` | 1 Call | 3 | Dividenden-Veränderung |
| `get_company_news` | 1 Call | 4 | News mit Tags + Sentiment |
| `get_technical_indicators` | 5 Calls | 2 (opt.) | Technische Setup-Analyse |

**Gesamt-API-Kosten pro Analyse:** ~32 Calls (ohne optionale Technical Indicators)

---

## Detaillierte Endpoint-Dokumentation

### 1. `get_upcoming_earnings`

```
Parameter:
  symbols: "AAPL.US"           # Pflicht, Komma-separiert möglich
  start_date: "2025-01-01"     # Optional, Default: heute
  end_date: "2025-03-31"       # Optional, Default: heute+7d

Rückgabe-Felder:
  code              → Ticker
  company_name      → Firmenname
  date              → Earnings-Datum
  time              → "AMC" (After Market Close) / "BMO" (Before Market Open)
  eps_estimate      → Konsens-EPS-Schätzung
  eps_actual        → Tatsächliches EPS (nach Veröffentlichung)
  revenue_estimate  → Konsens-Umsatz-Schätzung
  revenue_actual    → Tatsächlicher Umsatz

Besonderheit: Wenn symbols übergeben wird, werden from/to ignoriert.
```

### 2. `get_earnings_trends`

```
Parameter:
  symbols: "AAPL.US"     # Pflicht, Komma-separiert möglich

Rückgabe pro Periode (0q, +1q, 0y, +1y):
  earningsEstimateAvg/Low/High    → EPS-Schätzungen
  earningsEstimateNumberOfAnalysts → Anzahl Analysten
  earningsEstimateGrowth          → Erwartetes Wachstum
  revenueEstimateAvg/Low/High     → Umsatz-Schätzungen
  revenueEstimateGrowth           → Erwartetes Umsatzwachstum
  
  epsTrendCurrent                 → Aktuelle Schätzung
  epsTrend7daysAgo/30d/60d/90d    → Historische Schätzungen
  epsRevisionsUpLast7days         → Heraufstufungen letzte 7 Tage
  epsRevisionsUpLast30days        → Heraufstufungen letzte 30 Tage
  epsRevisionsDownLast30days      → Herabstufungen letzte 30 Tage

Besonderheit:
  - Enthält ~3 Jahre historische Trend-Daten
  - Mehrere Perioden pro Datumseintrag (0q, +1q, 0y, +1y)
  - Kostet 10 API-Calls pro Aufruf
```

### 3. `get_fundamentals_data`

```
Parameter:
  ticker: "AAPL.US"           # Pflicht
  from_date: "2024-10-01"     # Optional, filtert Financials
  to_date: "2025-03-10"       # Optional
  include_financials: true     # Default: true

Rückgabe-Sektionen:
  General         → Firmenname, Exchange, Sektor, Industrie, Officers, Mitarbeiter
  Highlights      → MarketCap, EBITDA, P/E, PEG, EPS, DividendYield
                  → ProfitMargin, OperatingMarginTTM, ROE, RevenueTTM
                  → QuarterlyRevenueGrowthYOY, QuarterlyEarningsGrowthYOY
                  → EPSEstimateCurrentYear/NextYear/CurrentQuarter/NextQuarter
  Valuation       → TrailingPE, ForwardPE, PriceSalesTTM, PriceBookMRQ, EV/EBITDA
  SharesStats     → SharesOutstanding, PercentInsiders, PercentInstitutions
  Technicals      → Beta, 52WeekHigh/Low, 50DayMA, 200DayMA, ShortRatio
  SplitsDividends → ForwardDividendRate/Yield, PayoutRatio, ExDividendDate
  AnalystRatings  → StrongBuy/Buy/Hold/Sell/StrongSell + TargetPrice
  Holders         → Top 20 Institutions + Top 20 Funds mit %-Veränderung
  Financials      → Balance Sheet, Income Statement, Cash Flow (wenn include_financials=true)

Besonderheit: Die "One-Stop-Shop"-Abfrage für alle Fundamentaldaten.
```

### 4. `get_sentiment_data`

```
Parameter:
  symbols: "AAPL.US"           # Pflicht, Komma-separiert
  start_date: "2025-01-25"     # Optional
  end_date: "2025-02-10"       # Optional

Rückgabe pro Tag:
  date        → Datum
  count       → Anzahl analysierter Artikel
  normalized  → Sentiment-Score (0.0 = extrem negativ, 1.0 = extrem positiv)

Interpretation:
  > 0.7 = Bullisch
  0.4 - 0.7 = Neutral/Gemischt
  < 0.4 = Bärisch
  
  Hoher Count + niedriger Score = Negative Aufmerksamkeit
  Niedriger Count + hoher Score = Ruhige, positive Phase
```

### 5. `get_insider_transactions`

```
Parameter:
  symbol: "AAPL"          # Optional (ohne Exchange-Suffix)
  start_date: "2025-01-01" # Optional
  end_date: "2025-12-31"   # Optional
  limit: 20                # Default: 100, Max: 1000

Rückgabe:
  code/exchange           → Ticker + Börse
  ownerName               → Name des Insiders
  ownerTitle              → CEO, CFO, Director, "U.S. Congress Member"
  transactionDate         → Datum der Transaktion
  transactionCode         → "P" (Purchase/Kauf), "S" (Sale/Verkauf)
  transactionPrice        → Preis pro Aktie
  transactionAcquiredDisposed → "A" (Acquired/Erworben), "D" (Disposed/Veräußert)

Besonderheit:
  - Enthält Congress-Member-Trades (Pelosi, Tuberville, etc.)
  - Kostet 10 API-Calls pro Aufruf
```

### 6. `get_company_news`

```
Parameter:
  ticker: "AAPL.US"    # Optional (SYMBOL.EXCHANGE)
  tag: "earnings"       # Optional, z.B. "technology", "earnings"
  start_date: "2025-01-25"  # Optional
  end_date: "2025-02-10"    # Optional
  limit: 15                  # Default: 50, Max: 1000

Rückgabe pro Artikel:
  date      → Zeitstempel (ISO 8601)
  title     → Headline
  content   → Vollständiger Artikeltext
  link      → URL zur Quelle
  symbols   → Array aller erwähnten Ticker
  tags      → Array: "EARNINGS", "QUARTERLY RESULTS", "PRICE TARGET", etc.
  sentiment → { polarity, neg, neu, pos }

Besonderheit:
  - Tags ermöglichen präzises Filtern nach Earnings-spezifischen News
  - Sentiment hat sowohl Polarität (Gesamtscore) als auch neg/neu/pos Aufschlüsselung
```

### 7. `get_historical_stock_prices`

```
Parameter:
  ticker: "AAPL.US"          # Pflicht
  start_date: "2025-01-25"   # Optional
  end_date: "2025-02-10"     # Optional
  period: "d"                 # "d" (daily), "w" (weekly), "m" (monthly)
  order: "a"                  # "a" (ascending), "d" (descending)

Rückgabe pro Tag:
  date, open, high, low, close, adjusted_close, volume
```

### 8. `get_upcoming_dividends`

```
Parameter:
  symbol: "AAPL.US"          # Optional
  date_from: "2025-01-01"    # Optional
  date_to: "2025-12-31"      # Optional

Rückgabe:
  declarationDate, exDividendDate, paymentDate, cashAmount, currency
```

### 9. `get_technical_indicators` (Optional)

```
Parameter:
  ticker: "AAPL.US"     # Pflicht
  function: "rsi"        # Pflicht: sma, ema, rsi, macd, bbands, etc.
  period: 14             # Optional, je nach Indikator
  start_date/end_date    # Optional

Nützliche Funktionen für Pre-Earnings-Setup:
  - rsi (period=14)     → Überkauft (>70) / Überverkauft (<30)
  - sma (period=50/200) → Trend-Bestätigung
  - bbands              → Volatilitäts-Kontraktion vor Earnings?
  - macd                → Momentum-Richtung
```
