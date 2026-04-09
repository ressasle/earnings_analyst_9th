---
name: quarterly-earnings-analyst
description: >
  Generates institutional-grade earnings reports (PDF/Audio) and company presentations for Kasona.
  Modularized into Data Population (Supabase SSOT) and Institutional Editing (Artifact Production).
---

## 1. Modular Architecture

| Module | Role | Responsible Tools |
| --- | --- | --- |
| **Data Populator** | Ingests data and populates Supabase SSOT. | `sync_earnings_data.py`, `sync_presentation_data.py` |
| **Institutional Editor** | Generates branded artifacts (PDF → Audio). | `pipeline_editor.py`, `generate_earnings_pdf.py`, `generate_audio.py` |
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
│   ├── sync_earnings_data.py   ← Data Populator (Ingestion)
│   ├── pipeline_editor.py      ← **Atomic Orchestrator** (Gen + Sync)
│   ├── Giga_Expansion_1515.py  ← Giga-Density Narrative Generator
│   ├── generate_earnings_pdf.py← PDF Generator Engine
│   ├── generate_audio.py       ← Branded Audio Engine (TTS)
│   ├── final_audit_99.py       ← Institutional Audit Script
│   ├── purge_and_sync_institutional.py ← Recovery Tool (Hard Clean)
│   └── upload_artifacts.py     ← Legacy/Manual Sync Utility
├── output/                     ← Staging area for artifacts
└── resources/                  ← Brand Assets (Logos, CSS)
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
- `review_status`: Must be `approved`.
- `uploaded`: Set to `true` after successful processing.
- `status`: Set to `published` once artifacts are synced.

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
To track client delivery progress across the entire institutional portfolio, the following columns are mandatory:
- `earnings_produced`: Boolean (True if status='published' in quarterly_earnings).
- `last_earnings_period`: Text (e.g., "Q4 2025" or "FY 2025").
- `presentation_produced`: Boolean (True if status='published' in company_presentation).
- `last_presentation_period`: Text (e.g., "2026-03-31").
- `production_updated_at`: Timestamp of the latest artifact synchronization.

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
