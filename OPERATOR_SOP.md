# Kasona Institutional Earnings Operator SOP

## 1. Objective and Cadence
**Cadence**: Weekly (e.g., Every Monday Morning)
**Objective**: Detect net-new earnings releases from the past week across the institutional portfolio, generate branded institutional reports, perform quality assurance, and publish the artifacts securely.

---

## 2. Startup Guide (The Weekly Run)

### Step 1: Detect New Earnings
We need to find out which companies have released their quarterly earnings over the last 7 days.
1. Run the date enrichment script to update dates from the EODHD API:
   ```bash
   python tools/enrich_earnings_dates.py
   ```
2. Open the Supabase Dashboard and view the `kasona_portfolio_assets` table.
3. Compare `last_earnings_date` against `last_earnings_period`. 
   - **Target**: Any row where `last_earnings_date` is recently updated (e.g., past 7 days) AND we haven't yet produced the analysis for that new period.
   - Note the `ticker_eod` (e.g., `AAPL.US`) for these target companies.

### Step 2: Extract & Construct Narrative
For every target `ticker_eod` identified:
1. Ingest the new data from EODHD:
   ```bash
   python tools/sync_earnings_data.py --ticker <TICKER_EOD> --period <PERIOD> --year <YEAR> 
   ```
2. Generate the deep-dive institutional narrative:
   ```bash
   python tools/Giga_Expansion_1515.py --ticker <TICKER_EOD>
   ```

---

## 3. Human Operator Quality Checks (The Guardrail)

Before we produce expensive auditory and visual artifacts, the data must be verified by a human analyst inside the Supabase Dashboard. 

1. **Navigate to `quarterly_earnings` table.**
2. **Find the records** currently holding `review_status = 'to_review'` or `pending`.
3. **Perform the following Quality Checks**:
   - [ ] **Sanity Check Numbers**: Do the `eps_actual` and `revenue_actual` match broader market reality? (Watch out for stock splits or abnormal API ingestion errors).
   - [ ] **Density Check**: Is the `markdown_content` robust? (Must look visibly dense, typically ~1,500 words).
   - [ ] **Format Check**: Are there clear, distinct markdown headers (e.g., `##`) and no broken tables?
   - [ ] **Identity Check**: Ensure the narrative does not mention "AI" or "EODHD".

4. **Flip the Switch**:
   - If the checks pass, change the `review_status` to **`approved`** (or `pending_production` if using the updated queue format).

---

## 4. Produce & Publish
Run the atomic orchestrator to take all `approved` records, generate the PDFs, clone the neural audio, and sync them to public buckets.

```bash
python tools/pipeline_editor.py --batch-approved --type earnings
```

---

## 5. Definition of Done (DoD)

The weekly run is officially **DONE** when the following conditions are met for every target company:

1. [ ] **Artifacts Live**: Both a PDF (`{ticker_eod}_earnings.pdf`) and an MP3 (`{ticker_eod}_audio.mp3`) exist in the correct portfolio folder in Supabase Storage.
2. [ ] **URLs Synced**: The `quarterly_earnings` table has functional, live public links in `pdf_report_url` and `audio_report_url`.
3. [ ] **Portfolio State Updated**: In `kasona_portfolio_assets`, the column `earnings_produced` is `TRUE`, and `last_earnings_period` reflects the newly analyzed quarter.
4. [ ] **Compliance Preserved**: The final PDF possesses the mandatory Kasona branded cover and the legal disclaimer / link on the back page.
5. [ ] **Double Production Avoided**: Because we enforce the `ticker_eod` matching, we verify no duplicates were generated for the same company and fiscal quarter.
