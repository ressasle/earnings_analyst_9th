# 08_quarterly-earnings-analyst

This repository contains the Kasona Institutional Earnings Analyst Skill. It orchestrates the automated fetching, analysis, and artifact generation (PDF, Neural Audio) for quarterly earnings events across our tracking portfolios.

## System Architecture

The pipeline follows a structured **Data → Narrative → Artifact → Sync** flow:
1. **Data Sync**: Pulls financials and consensus from the EODHD API (`sync_earnings_data.py`).
2. **Narrative Construction**: Transforms the data into deep-dive, 1,500+ word institutional briefs using specialized narratives (`Giga_Expansion_1515.py` etc.).
3. **Artifact Production**: Generates branded PDFs and TTS MP3 audio (`pipeline_editor.py`).
4. **Storage & Database Sync**: Uploads the artifacts to Supabase storage and attaches their URL references in `quarterly_earnings` while tracking delivery progress in `kasona_portfolio_assets`.

## Documentation & SOPs

- **[SKILL.md](./SKILL.md)**: The foundational logic, branding constraints, required columns, and explicit data flow maps. This is the single source of truth for the system architecture.
- **[OPERATOR_SOP.md](./OPERATOR_SOP.md)**: The human-in-the-loop guide. Details the weekly start-up workflow, trigger tracking, required density checks, and definition of done.
- **[CHANGELOG_KELVIN.md](./CHANGELOG_KELVIN.md)**: Details the evolution of this repository from the original handover state, documenting specific improvements in database tracking and the automated trigger roadmap.

## Running the Pipeline

**1. Enrich Trigger Dates**
```bash
python tools/enrich_earnings_dates.py
```
**2. Sync Specific Ticker**
```bash
python tools/sync_earnings_data.py --ticker <TICKER> --period <PERIOD> --year <YEAR>
```
**3. Generate Narrative**
```bash
python tools/Giga_Expansion_1515.py --ticker <TICKER>
```
**4. Batch Produce & Upload**
```bash
python tools/pipeline_editor.py --batch-approved --type earnings
```
