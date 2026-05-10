---
name: quarterly-earnings-analyst
description: >
  Generates institutional-grade earnings reports (PDF/Audio) and company presentations for Kasona.
  Modularized into Data Population (Supabase SSOT) and Institutional Editing (Artifact Production).
---

## 1. Modular Architecture

| Module | Role | Responsible Tools |
| --- | --- | --- |
| **Data Populator** | Ingests data and populates Supabase SSOT. | `sync_earnings_data.py`, `sync_presentation_data.py`, `data_completion_v1.py`, `enrich_price_movements.py` |
| **Institutional Editor** | Generates high-fidelity narratives and PDF/Audio artifacts. | `Giga_Expansion_1515.py` (Main PDF Tool), `pipeline_editor.py`, `generate_audio.py` |
| **Storage & Sync** | Manages artifact uploads and URL persistence. | `supabase_storage_manager.py`, `pipeline_editor.py`, `purge_and_sync_institutional.py` |
| **Batch Orchestrator**| Processes all approved/un-uploaded records. | `pipeline_editor.py --batch-approved` |

---

## 2. Standard Operating Procedure (SOP)

### Stage 1: Data Ingestion & Population
**Objective**: Populate all mandatory fields in `public.quarterly_earnings`.
1. **Execution**: `python tools/sync_earnings_data.py --ticker [TICKER]`
2. **Validation**: Verify `company_outlook`, `executive_summary`, and `impact_score` are NOT NULL in Supabase.
3. **Status**: Record set to `data_populated`.
4. **Safeguard**: `sync_earnings_data.py` will skip any record with `review_status` set to `reviewed` or `approved` to avoid overwriting finalized content.

### Stage 2: Narrative Construction
**Objective**: Generate a high-fidelity research narrative adhering strictly to institutional length and structural constraints.
1. **The Bergman Baseline**: Use [BERG-B.ST_earnings.pdf](file:///c:/Users/Administrator/Documents/kasonaops/invest_analysis/08_quarterly-earnings-analyst/output/BERG-B.ST_earnings.pdf) as the strict baseline for all production.
2. **Strict 10-Section Structure**: All narratives MUST be exactly 10 sections. Over-reporting or fragmentation is prohibited.
    - **Section 10**: Must exclusively contain the **Metrics Table** and final summary.
3. **Narrative Density**: Target a strict baseline of **1,500 - 1,700 words**.
4. **Client Integrity**: The narrative must contain **zero** process disclosures or data provider mentions (e.g., EODHD).

### Stage 3: Narrative Translation (Bilingual Only)
**Objective**: Localize the research narrative for German-speaking clients.
1. **Execution**: Generate `markdown_content_de` and `executive_summary_de`.
2. **Naming**: Filenames must follow `[TICKER]_earnings_de.md`.

### Stage 4: Review & Approval
**Objective**: Manual quality check and sign-off.
1. **Review**: Team member checks both English and German narratives.
2. **Approval**: Update `review_status` from `pending` to `approved` in Supabase.

### Stage 5: Final Batch Production
**Objective**: Atomic generation and upload of all approved artifacts.
1. **Execution**: `python tools/pipeline_editor.py --batch-approved --type [earnings|presentation]`
2. **Fetch Logic**: The system queries `SELECT * FROM quarterly_earnings WHERE review_status = 'approved' AND uploaded = false`.
3. **Atomic Sync**: Automatically uploads artifacts, updates URLs, and sets `uploaded = true`.
3. **Validation**: Check Supabase Storage and `pdf_report_url_de` / `audio_report_url_de`.

---

## 3. Client-Facing Standards

### 3.1 Audio Branding & Narration Style

All audio briefings **must** use the following Kasona Branding:

**Intro**:
> "This quarterly earnings review of [Company Name] shows the latest fundamental developments, future outlook, and market reactions. We provide this analysis to give you a clear sense of the company's current state and what to expect in the coming periods."

**Outro**:
> "That was a Kasona production. Check out our full offering and additional research at Kasona.ai. We distill the most relevant market insights using our AI-driven analysis specifically for your portfolio. This does not constitute financial advice, buy or sell recommendations, and you are in the driver's seat with your money decisions. Feel free to read our disclaimer. Until next time!"

**3.2 Metadata-Aware Audio Generation (Dual-Script Path)**
To ensure both **100% data integrity** in audits and **high-fidelity narration** for listeners, the audio engine (`generate_audio.py`) executes a dual-path scripting logic:

1. **The Audit Path (Database/Transcript)**:
   - Generates a rich text block containing the `[INSTITUTIONAL METADATA]` header.
   - Fields included: **Ticker**, **Fiscal Period**, **Impact Score**, **Recommendation**, **PDF URL**, and **Audio URL**.
   - This script is archived in the Supabase `audio_script` column for long-term traceability.

2. **The Speech Path (Neural Narration)**:
   - Strips all technical noise (URLs, slashes, markdown) from the body.
   - Intelligently omits technical metadata (Impact Score: N/A, etc.) from the spoken intro to maintain a clean listening experience.
   - Ensures zero leakage of http/https/www or SSML tags.

**SSML & Pause Standards**:
To ensure a professional, broadcast-quality experience, the- **Hard Sanitizer (V2 - High Fidelity)**:
    - **Zero URLs**: Strip all `http/https/www` links.
    - **Zero Slashes**: Replace `/` and `\` with spaces to prevent "slash" narration.
    - **Tag-Free Pauses**: Disable all SSML tags (`<voice>`, `<p>`, `<break>`) as they may be narrated by some engines. Use qualitative punctuation (`... `) for natural pacing.
    - **Branding Sandwich**: Strictly enforce the standard Intro and Outro at the start and end of every file.
- **Auditability**:
    - **Metadata Richness**: Every audio script archived in Supabase must contain the `[INSTITUTIONAL METADATA]` header with resolved ticker info and artifact URLs.
    - **Audio Script Sync**: Every audio generation must synchronize the exact **Audit Script** to the `audio_script` column in Supabase for audit transparency.
- **Emphasis**: Use [pause] after names or critical stock price movements.
- **Style**: Narration should shift between [newscaster], [professional], [serious], and [analytical] based on the section context (e.g., [serious] for risks, [confident] for growth).

**Hard Sanitizer**: `generate_audio.py` filters out any line that contains the following keywords before it reaches TTS — these must **never** be spoken:
- `rule of 3` / `rule of three`
- `word count`
- `generated by kasona` / `kasona institutional analytics`
- `disclaimer:`
- `tts script` / `audio script`
- `eodhd` / `python`

### 3.2 PDF Content Policy
The PDF is a **clean intelligence document**. Every report **must** include a professional last page for institutional branding. Any of the following are a **hard quality failure**:
- Disclaimers mentioning how the report was generated (except for the mandatory last page disclaimer)
- Data provider names (e.g., EODHD)
- Word counts or methodology footnotes
- References to internal tools or scripting

### 3.3 Logo & Branding Fallback
1. **Official Logo**: System attempts to pull branding from EODHD (`generate_earnings_pdf.py`).
2. **Fallback Strategy**: If EODHD fails, or for **Private/IPO** tickers (`PRIVATE.*`), the system **must** use the Kasona Logo (`tools/kasona_logo.jpg`) on the cover page centered as the primary visual. 
3. **Audit Rule**: Reports with "Empty" or "Broken" logo boxes are non-compliant and must be regenerated.

### 3.4 Mandatory Last-Page Branding
The final page of every PDF report must contain:
1. **Disclaimer**: "Disclaimer: This report is AI-generated and does not constitute investment advice."
2. **Kasona Branding**: "A Kasona Production" with the official Kasona logo.
3. **Institutional Access**: Link to [kasona.ai](https://www.kasona.ai/) and tagline "**The solution for independent investors**".

### 3.3 Anonymity Policy
**Every artifact delivered to a client must pass this single test:** If a client reads it, they should perceive a professional analyst, not an automated system.

---

## 4. Folder Structure

```
08_quarterly-earnings-analyst/
├── SKILL.md                    ← The SOP (this file)
├── tools/
│   ├── sync_earnings_data.py       ← **Data Populator** (Initial Ingestion & Duplicate Guard)
│   ├── pipeline_editor.py          ← **Atomic Orchestrator** (Gen + Sync + Status Management)
│   ├── Giga_Expansion_1515.py      ← **Main Tool for PDF Generation** (High-Fidelity Mega-Narratives)
│   ├── generate_earnings_pdf.py    ← PDF Generator Engine (Underlying conversion)
│   ├── generate_audio.py           ← Branded Audio Engine (TTS & Script Archiving)
│   ├── supabase_storage_manager.py ← **Storage Master** (Manual/Utility Upload & URL Sync)
│   ├── data_completion_v1.py       ← **Data Enricher** (Backfills missing metrics & translations)
│   ├── enrich_price_movements.py   ← **Price Movement Enricher** (7d drift + post-earnings reaction)
│   ├── enrich_earnings_dates.py    ← Earnings Date Enricher (next/last date sync)
│   ├── final_audit_99.py           ← Institutional Audit Script
│   ├── purge_and_sync_institutional.py ← Recovery Tool (Hard Clean & Storage Resync)
│   └── upload_artifacts.py         ← Legacy/Manual Sync Utility
├── output/                         ← Staging area for artifacts
└── resources/                      ← Brand Assets (Logos, CSS)
```

---

---

## 6. Data Integrity & Synchronization

**Objective**: Ensure 100% column population across all Supabase tables, including legacy and archive records.

### 6.1 Required Column Matrix (quarterly_earnings)
For a report to be considered "Client-Ready," the following columns **must** be populated:
- `pdf_report_url`: Valid Supabase Storage link to the English PDF.
- `audio_report_url`: Valid Supabase Storage link to the English MP3.
- `pdf_report_url_de`: Valid Supabase Storage link to the German PDF.
- `audio_report_url_de`: Valid Supabase Storage link to the German MP3.
- `impact_score`: Deterministic calculation from `sync_earnings_data.py`.
- `price_movement_7d_prior`: % price change in the 7 trading days before the report. Populated by `enrich_price_movements.py`.
- `price_movement_post_earnings`: % price change from report-date close to next-day close. Populated by `enrich_price_movements.py`.
- `movement_reasoning`: Fact-based text summarizing the EPS beat/miss and price reaction. Populated by `enrich_price_movements.py`.
- `review_status`: Must be `approved`.
- `uploaded`: Set to `true` after successful processing.
- `status`: Set to `published` once artifacts are synced.
- `manual_ingestion`: Free-text field. Contains high-fidelity analyst notes, strategic observations, and primary source data entered directly by the user. This field is a **protected, user-controlled column**. It is used as **read-only input** for the Giga Expansion engine and is **never modified or overwritten** by any script.

---

### 6.7 Analyst Insight Pathway (Manual Ingestion)

The `manual_ingestion` column (`TEXT`, nullable) is a persistent, analyst-controlled field. It is used to store qualitative insights, proprietary observations, and specific data points retrieved from primary sources (IR PDFs, transcripts, etc.) that the automated API cannot capture.

**Rules for Manual Ingestion:**
1. **Persistent Input**: Once entered by the user, this field is **immutable for automated scripts**. Tools such as `sync_earnings_data.py` and `Giga_Expansion_1515.py` are strictly prohibited from writing to or modifying this column.
2. **Analytical Multiplier**: The Giga Expansion tool uses this field to enrich the 1,500-word narrative.
3. **Zero Process Disclosure**: Content from this field must be integrated into the narrative without referencing the field name, the fact that it was "manually ingested," or the specific data source (e.g., "Analyst Note: ..."). It must read as part of the core institutional analysis.
4. **Approval Required**: Once notes are added, `review_status` should be set to `approved` to trigger the production pipeline.

**Guard behavior in `sync_earnings_data.py`:** The script checks for existing content in `manual_ingestion`. If populated, it treats the record as "analyst-protected" and will not perform API-driven updates to core narrative fields to prevent conflict with custom observations.

### 6.8 The Giga Expansion Workflow (Analytical Multiplier)

The **Giga Expansion** workflow (powered by `tools/Giga_Expansion_1515.py`) is designed for high-conviction assets where standard API data is insufficient. This workflow uses the `manual_ingestion` column as an analytical multiplier.

**Steps to execute a Giga Expansion:**
1. **Curate Ingestion Data**: Populate the `manual_ingestion` column in Supabase with structured markdown (Key Points, Strategic Positioning, Demand, Profits, etc.).
2. **Execute Giga Tool**:
   ```powershell
   python tools/Giga_Expansion_1515.py --ticker [TICKER] --period "[PERIOD]"
   ```
   *Note: This script automatically pulls the `manual_ingestion` content and injects it into Section 6C of the generated narrative.*
3. **Orchestrate Artifacts**:
   ```powershell
   python tools/atomic_orchestrator.py --ticker [TICKER]
   ```
   *This generates the HTML, PDF, and Audio using the expanded 1,500-word narrative and syncs them to Supabase Storage.*

**Why use Giga Expansion?**
- **Depth**: Scales the report to 1,500+ words, meeting institutional density standards.
- **Precision**: Merges live EODHD valuation metrics with manual analyst insights.
- **Efficiency**: Automates the "Institutional Metadata" and "Dual-Script" audio paths while preserving custom strategic notes.

### 6.2 Bilingual Production (German)
**Objective**: Generate localized artifacts for high-net-worth German-speaking clients.
1. **Translation/Localization**: Generate a German institutional narrative and summary.
2. **Audio Style**: Use neural voices (e.g., `de-DE-KillianNeural` for male, `de-DE-KatjaNeural` for female).
   - **Intro (DE)**: "Diese Quartalsergebnis-Analyse von [Company Name] zeigt die neuesten fundamentalen Entwicklungen, den Zukunftsausblick und die Marktreaktionen..."
   - **Outro (DE)**: "Das war eine Kasona-Produktion. Besuchen Sie Kasona.ai, um unser vollständiges Angebot an Analysen für Ihr Portfolio zu entdecken..."
3. **Storage**: Artifacts must be saved with the `_de` suffix (e.g., `[TICKER]_audio_de.mp3`) and uploaded to the same buckets.
4. **Database Sync**: Populate `pdf_report_url_de`, `audio_report_url_de`, `executive_summary_de`, `markdown_content_de`, `review_status`, and `uploaded`.

| Column | Type | Description |
| --- | --- | --- |
| `pdf_report_url_de` | text | Public URL to German PDF report |
| `audio_report_url_de` | text | Public URL to German Audio briefing |
| `executive_summary_de` | text | German executive summary |
| `markdown_content_de` | text | German narrative content |
| `review_status` | enum | `pending`, `reviewed`, `approved` |
| `uploaded` | boolean | `true` (finished), `false` (pending) |

## Review & Approval Workflow
To ensure institutional quality, all produced artifacts must go through a manual review cycle before final delivery/upload.

### Workflow States
1. **`pending`**: Initial state after data ingestion. Artifacts are NOT yet finalized.
2. **`reviewed`**: Analysis and narrative have been checked by a team member.
3. **`approved`**: Final sign-off. The record is now eligible for automated pipeline processing.

### Pipeline Execution (Approved Only)
The production pipeline (`pipeline_editor.py`) is configured to only process records in the `approved` state that have not yet been marked as `uploaded`.

```bash
# Process all approved reports that are ready for upload
python tools/pipeline_editor.py --batch-approved --type earnings
```

Upon successful artifact synchronization, the system automatically sets `uploaded = true`.

### 6.3 Maintenance & Repair
If a legacy record is missing a score or URL, the **Data Populator** (`sync_earnings_data.py`) or **Uploader** (`batch_upload_artifacts.py`) must be re-run for that specific ticker to "repair" the record.

### 6.3 Portfolio Status Tracking (kasona_portfolio_assets)
To track client delivery progress across the entire institutional portfolio, columns are separated by lifecycle to allow for per-user exposing:

**Updated by normal weekly podcast production / API data sourcing:**
- `next_earnings_date`: Date tracking the upcoming earnings release.
- `last_earnings_date`: Date tracking the most recently occurred earnings release.

**Updated exclusively by this Quarterly Earnings Analyst Skill:**
- `earnings_produced`: Boolean (True if status='published' in quarterly_earnings).
- `last_earnings_period`: Text (e.g., "Q4 2025" or "FY 2025").
- `presentation_produced`: Boolean (True if status='published' in company_presentation).
- `last_presentation_period`: Text (e.g., "2026-03-31").
- `production_updated_at`: Timestamp of the latest artifact synchronization.

### 6.4 The `ticker_eod` Unique ID System & Duplicate Prevention
To ensure we **never produce artifacts for the same company twice**, the entire system relies on `ticker_eod` as the universal unique identifier and a strict idempotency logic.
- **Uniqueness Constraint:** The `quarterly_earnings` table enforces a **Composite Unique Key** on `(ticker_eod, fiscal_period)`. This ensures no duplicate records can exist for the same company in the same quarter.
- **Idempotent Population:** `sync_earnings_data.py` utilizes the `UPSERT` operation with the `on_conflict` directive targeting the composite key. This allows the script to update existing records without creating duplicates.
- **Relational Integrity:** Across layers (from `kasona_portfolio_assets` down to the `analysis_queue` and storage buckets), `ticker_eod` (e.g., `AAPL.US`, `BERG-B.ST`) is the singular anchor ID ensuring matching logic works deterministically and prevents duplication. The system checks for existing artifacts before generation to ensure idempotency.
### 6.5 Required Column Matrix (Bilingual Support)
For "DACH-Region" ready reports:
- `pdf_report_url_de`: German PDF link.
- `audio_report_url_de`: German branded MP3 link.
- `executive_summary_de`: Concise German summary of the earnings event.

---

## 5. QA Checklist (Before Delivery)

- [ ] **Branding Compliance**: Does the PDF contain the mandatory final page with the disclaimer and Kasona website link?
- [ ] **Ticker Branding**: Does the cover page feature the official company logo (acquired from Brandfetch/local if EODHD fails)?
- [ ] **Data Integrity**: Are **all** columns (Score, Recommendation, URLs) populated in the table?
- [ ] **Price Movements**: Are `price_movement_7d_prior`, `price_movement_post_earnings`, and `movement_reasoning` filled for all tickers with a `report_date`? Run `enrich_price_movements.py` if not.
- [ ] **Portfolio Sync**: Are the `earnings_produced` and `last_period` columns updated in `kasona_portfolio_assets`?
- [ ] **Legacy Review**: Have old records been synchronized with fresh sanitized artifacts?
- [ ] **SSOT Verification**: Is Supabase fully populated before generation?
- [ ] **Narrative Depth**: Does the markdown exceed 1,515 words?
- [ ] **PDF First**: Was the PDF generated before the audio file?
- [ ] **Audio Branding**: Does the audio contain only the Kasona brand intro and outro?
- [ ] **Client Integrity**: Does the PDF contain zero internal process disclosures?
- [ ] **Storage Sync**: Are the Supabase URLs live and functional?

---

### 3.3 Advanced Content Parsing (Markdown Header & Table Support)
To ensure institutional continuity, the audio generator now preserves the structure of the `markdown_content` column:
- **Headers**: Section titles (e.g., `## EXECUTIVE SUMMARY`) are preserved and spoken as clean text.
- **Tables**: Financial data tables (e.g., Metric Summary Tables) are automatically converted into a comma-separated spoken list format (e.g., "Metric, Value.") to provide auditory clarity for data-heavy sections.

> [!IMPORTANT]
> When uploading artifacts to Supabase, always specify the `content-type` (e.g., `application/pdf`) to prevent browser rendering issues.

---

## 7. Supabase Data Flow (Per-Step Reference)

This section documents **every** Supabase interaction (reads, writes, storage operations) across the full pipeline, per stage and per tool.

### 7.1 Stage 1 — Data Ingestion (`sync_earnings_data.py`)

| Operation | Table / Bucket | Type | Description |
| :--- | :--- | :--- | :--- |
| **Guard Read** | `quarterly_earnings` | `SELECT review_status` | Checks if the record for `(ticker_eod, fiscal_period)` is already `reviewed` or `approved`. If so, the script **skips** the ticker to prevent overwriting finalized content. |
| **Upsert** | `quarterly_earnings` | `UPSERT (on_conflict: ticker_eod, fiscal_period)` | Writes ~13 columns: `ticker_eod`, `company_name`, `fiscal_period`, `eps_actual`, `eps_estimate`, `eps_surprise_percent`, `revenue_actual`, `revenue_estimate`, `impact_score`, `sentiment_score`, `executive_summary`, `company_outlook`, `company_developments`. Sets `status = 'to_review'`. |

### 7.2 Stage 2 — Narrative Construction (`Giga_Expansion_1515.py`, `populate_sa_de_narratives_v4.py`, `populate_private_narratives_v3.py`)

| Operation | Table / Bucket | Type | Description |
| :--- | :--- | :--- | :--- |
| **Artifact Creation** | `quarterly_earnings` | `UPDATE` | Sets `markdown_content`, `review_status = 'approved'`, `uploaded = false`. This is the **main tool for PDF/Audio initiation** for the expansion portfolio. |
| **Existence check** | `quarterly_earnings` | `SELECT id` | Confirms the record exists before attempting the UPDATE (prevents silent no-ops). |

### 7.3 Stage 3 — Review & Approval (Manual / Dashboard)

| Operation | Table / Bucket | Type | Description |
| :--- | :--- | :--- | :--- |
| **Status flip** | `quarterly_earnings` | `UPDATE review_status` | Transitions from `pending` → `reviewed` → `approved`. Only `approved` records are eligible for the production pipeline. |

### 7.4 Stage 4 — Artifact Production & Upload (`pipeline_editor.py`, `run_priority_99.py`, `run_pep_production.py`)

| Operation | Table / Bucket | Type | Description |
| :--- | :--- | :--- | :--- |
| **Queue fetch** | `quarterly_earnings` | `SELECT *` | Fetches all records matching `review_status = 'approved' AND uploaded = false`. Optionally filtered by `investor_profile`. |
| **Content read** | `quarterly_earnings` | `SELECT *` | Reads `markdown_content`, `company_name`, `fiscal_period`, `impact_score`, `recommendation` for local artifact generation. |
| **Folder lookup** | `quarterly_earnings` | `SELECT investor_profile` | Determines the storage subfolder (e.g., `991001-SA`, `991001-PEP`) for the upload path. |
| **Portfolio mapping** | `kasona_portfolio_assets` | `SELECT ticker, portfolio_id` | Maps tickers to portfolio IDs for correct storage folder routing. |
| **PDF upload** | Storage: `earnings-reports-pdf` | `upload()` | Uploads `{TICKER}_earnings.pdf` to `{portfolio_id}/{TICKER}_earnings.pdf` with `content-type: application/pdf`, `upsert: true`. |
| **Audio upload** | Storage: `earnings-reports-audio` | `upload()` | Uploads `{TICKER}_audio.mp3` to `{portfolio_id}/{TICKER}_audio.mp3` with `content-type: audio/mpeg`, `upsert: true`. |
| **URL sync** | `quarterly_earnings` | `UPDATE` | Writes `pdf_report_url`, `audio_report_url`, `generated_at = now()`. |
| **Audit script** | `quarterly_earnings` | `UPDATE audio_script` | Archives the full TTS text script for compliance traceability. |
| **Tracking update** | `kasona_portfolio_assets` | `UPDATE` | Sets `earnings_produced = true`, `last_earnings_period = '{period}'`, `production_updated_at = now()`. Tries `ticker_eod` first, falls back to `ticker`. |
| **Finalize** | `quarterly_earnings` | `UPDATE` | Sets `uploaded = true`, `status = 'uploaded'`. |

### 7.5 Utility: Storage Manager (`supabase_storage_manager.py`)

| Operation | Table / Bucket | Type | Description |
| :--- | :--- | :--- | :--- |
| **Upload** | Storage: `earnings-reports-pdf` / `earnings-reports-audio` / `earnings-reports-html` | `upload()` | Manual single-file upload with custom naming: `{ticker}/{quarter}_{year}_{filename}`. |
| **DB update** | `quarterly_earnings` | `UPDATE` | Writes the generated public URL to `pdf_report_url`, `audio_report_url`, or `html_report_url`. |
| **Queue update** | `analysis_queue` | `UPDATE status` | Marks the corresponding queue entry as `completed` (searches by both full ticker and root ticker). |

### 7.6 Utility: Purge & Resync (`purge_and_sync_institutional.py`)

| Operation | Table / Bucket | Type | Description |
| :--- | :--- | :--- | :--- |
| **List files** | Storage: `earnings-reports-pdf` / `earnings-reports-audio` | `list()` | Enumerates all files in target folders (`991001-SA`, `991001-PEP`, `991001-IPO`). |
| **Purge files** | Storage (same buckets) | `remove()` | Deletes all files in target folders (hard clean). |
| **Ticker map** | `kasona_portfolio_assets` | `SELECT ticker_eod, portfolio_id` | Rebuilds the ticker → folder mapping for re-upload. |
| **Re-upload** | Storage (same buckets) | `upload()` | Re-uploads local artifacts from `output/` to correct folders. |
| **URL resync** | `quarterly_earnings` | `UPDATE` | Writes fresh `pdf_report_url`, `audio_report_url`, `investor_profile`, `generated_at`. |

### 7.7 Utility: Earnings Date Enrichment (`enrich_earnings_dates.py`)

| Operation | Table / Bucket | Type | Description |
| :--- | :--- | :--- | :--- |
| **Asset fetch** | `kasona_portfolio_assets` | `SELECT id, portfolio_id, ticker_eod, stock_name, asset_class, next_earnings_date, last_earnings_date` | Fetches all Stock/ETF assets with a `ticker_eod`. Optionally filtered by `portfolio_id`. |
| **Date update** | `kasona_portfolio_assets` | `UPDATE` | Writes `next_earnings_date`, `last_earnings_date`, `updated_at` for each asset ID. Uses EODHD `Earnings::History` as the data source. |

### 7.8 Utility: Portfolio Audit (`final_portfolio_audit.py`)

| Operation | Table / Bucket | Type | Description |
| :--- | :--- | :--- | :--- |
| **Full scan** | `quarterly_earnings` | `SELECT ticker_eod, updated_at, uploaded, markdown_content` | Reads all records for compliance checks: freshness, upload status, and narrative word-count density. |

### 7.9 Utility: Price Movement Enrichment (`enrich_price_movements.py`)

Populates three missing financial performance metrics for all rows in `quarterly_earnings` that have a valid `report_date` but are missing price movement data. Fetches adjusted close prices from EODHD and computes drift and reaction percentages.

| Operation | Table / Bucket | Type | Description |
| :--- | :--- | :--- | :--- |
| **Missing row fetch** | `quarterly_earnings` | `SELECT id, ticker_eod, company_name, report_date, quarter, fiscal_year, eps_actual, eps_estimate` | Fetches all rows where `report_date IS NOT NULL` and either `price_movement_7d_prior` or `price_movement_post_earnings` is NULL. Deduplicates by `id`. |
| **Filter** | _(in-memory)_ | — | Skips rows with `PRIVATE.*`, `MARKET_OVERVIEW_*` prefixes and known non-market tickers (private companies, crypto). |
| **EOD price fetch** | EODHD API | `GET /api/eod/{ticker}` | Fetches adjusted close prices over a ±20-calendar-day window around the `report_date`. Rate-limited to 2.5-second delay per call. |
| **Calculation** | _(in-memory)_ | — | `price_movement_7d_prior`: % change from 8 trading days before to 1 trading day before the report. `price_movement_post_earnings`: % change from report-date close to next-day close. |
| **Reasoning generation** | _(in-memory)_ | — | Builds `movement_reasoning` using EPS beat/miss threshold (±2%), pre-drift threshold (±1.5%), and post-reaction threshold (±0.5% / ±3%). |
| **DB write** | `quarterly_earnings` | `UPDATE` | Writes `price_movement_7d_prior`, `price_movement_post_earnings`, `movement_reasoning`, and `updated_at` for each processed row. |

**CLI Flags:**
```bash
python tools/enrich_price_movements.py            # Live run (writes to DB)
python tools/enrich_price_movements.py --dry-run  # Preview only, no writes
python tools/enrich_price_movements.py --verbose  # Verbose per-ticker output
```

**Last Run Results (2026-04-30):**
- **66** actionable tickers processed
- **58** rows updated successfully
- **8** skipped (insufficient EODHD price history — primarily small-cap Nordic stocks)
- **0** errors

---

## 8. Earnings Trigger Detection

### How does the skill know when a new earnings report has dropped?

The detection mechanism is **portfolio-driven** via `kasona_portfolio_assets`:

1. **`enrich_earnings_dates.py`** runs periodically (manually or scheduled) and calls the EODHD Fundamentals API (`Earnings::History` filter) for every stock asset in the portfolio.
2. It writes two columns per asset:
   - **`next_earnings_date`** — The earliest future `reportDate` found in the EODHD history.
   - **`last_earnings_date`** — The most recent past `reportDate` with an `epsActual` value (i.e., earnings have actually been released).
3. **Detection logic**: When `next_earnings_date` transitions from a future date to the past (or when `last_earnings_date` updates to a newer date), that signals a new earnings event has occurred.

### Current Limitation: No Automated Trigger

> [!WARNING]
> There is currently **no automated event-driven trigger** that fires when earnings drop. The system relies on:
> - Manual runs of `enrich_earnings_dates.py` to refresh the dates.
> - A human operator comparing `last_earnings_date` against `last_earnings_period` in the same table to identify which tickers have new, un-produced earnings.
> - Manual invocation of `sync_earnings_data.py` for the specific ticker.

### Analysis Queue (Partial Integration)

The `supabase_storage_manager.py` references an **`analysis_queue`** table with `ticker`, `status`, and `created_at` columns. This table could serve as the event-trigger mechanism, but it is currently only used for post-upload status marking (`status = 'completed'`), not for scheduling new production.

---

## 9. Known Gaps & Improvement Roadmap

### 9.1 Event-Driven Earnings Trigger & Approval Guards (Priority: HIGH)

**Problem**: The pipeline has no way to automatically start processing when a company releases earnings. Everything is manually invoked. However, a fully automated pipeline risks publishing bad data if the source API is corrupted.

**Proposed Solution**:
1. Schedule `enrich_earnings_dates.py` as a **daily Supabase Edge Function** or cron job.
2. Add a database trigger or Edge Function that fires when `last_earnings_date` is updated to a value newer than `last_earnings_period`:
   ```
   IF NEW.last_earnings_date > OLD.last_earnings_date
   AND NEW.last_earnings_date != last_earnings_period
   THEN INSERT INTO analysis_queue (ticker, status) VALUES (NEW.ticker_eod, 'pending_approval')
   ```
3. **Guard Check:** Implement a small dashboard or manual flip process where an operator reviews `pending_approval` items. Once the underlying fundamentals look sound, flip the status to `pending_production`.
4. The pipeline orchestrator (`pipeline_editor.py`) is updated to pull **only** `status = 'pending_production'` records from the `analysis_queue`. This isolates the automated runner to net-new, pre-verified targets.

### 9.2 Centralized Supabase Client (Priority: MEDIUM)

**Problem**: Every script (`sync_earnings_data.py`, `pipeline_editor.py`, `run_priority_99.py`, etc.) independently creates its own `create_client()` instance and reads env vars. Some use `SUPABASE_SERVICE_ROLE_KEY`, others use `SUPABASE_SERVICE_KEY` — inconsistent naming.

**Proposed Solution**: Create a shared `utils/supabase_client.py`:
```python
# utils/supabase_client.py
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

def get_client():
    url = os.environ["SUPABASE_URL"]
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_SERVICE_KEY")
    return create_client(url, key)
```

### 9.3 German Artifact Production Parity (Priority: MEDIUM)

**Problem**: The pipeline generates and uploads EN PDFs and audio via `pipeline_editor.py`, but German (`_de`) artifacts are produced by separate standalone scripts (`populate_sa_de_narratives_v4.py`). There is no unified batch production for DE PDFs and DE audio.

**Proposed Solution**: Extend `pipeline_editor.py` to accept a `--lang de` flag that generates DE-specific artifacts and populates `pdf_report_url_de` and `audio_report_url_de`.

### 9.4 Idempotent Upload & Error Recovery (Priority: MEDIUM)

**Problem**: If the pipeline crashes mid-way (e.g., PDF uploaded but audio generation fails), the record may be left in an inconsistent state (`pdf_report_url` set, `audio_report_url` null, `uploaded` still false).

**Proposed Solution**:
- Wrap each ticker's full cycle (PDF → Audio → Upload → DB Sync) in a transaction-like pattern.
- Only set `uploaded = true` after **all** artifact URLs are confirmed non-null.
- Add a `production_error` column for tickers that fail mid-pipeline, enabling targeted reruns.

### 9.5 `analysis_queue` as the Single Entry Point (Priority: HIGH)

**Problem**: The `analysis_queue` table exists and is referenced in `supabase_storage_manager.py`, but it is underutilized. It could serve as **the** unified trigger mechanism for the entire pipeline.

**Proposed Solution**:
1. The Kasona app (or a webhook from EODHD) inserts a row into `analysis_queue` when a user requests an analysis or when earnings are detected.
2. `pipeline_editor.py` gains a `--process-queue` mode that pulls `pending` items from `analysis_queue` instead of hardcoded ticker lists.
3. After successful production, the queue entry is marked `completed`; on failure, `failed` with an error message.

### 9.6 Eliminate Hardcoded Ticker Lists (Priority: LOW)

**Problem**: `run_priority_99.py`, `run_pep_production.py`, and `final_portfolio_audit.py` contain hardcoded ticker arrays (e.g., `TICKERS_99`, `TARGET_TICKERS`). These go stale as the portfolio evolves.

**Proposed Solution**: All ticker lists should be sourced dynamically from `kasona_portfolio_assets` filtered by `portfolio_id`.
