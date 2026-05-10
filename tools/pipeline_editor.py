#!/usr/bin/env python3
"""
pipeline_editor.py — Institutional Editor Skill Orchestrator.

Coordinates the generation of branded artifacts (PDF, Audio, HTML) 
from data residing in Supabase. Supports both Quarterly Earnings and 
structural Company Presentations.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Path configuration
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from utils.supabase_client import get_supabase_client

load_dotenv()

# Centralized client
supabase = get_supabase_client()
# Get URL for storage link construction
SUPABASE_URL = os.environ.get("SUPABASE_URL")
BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

def run_command(cmd):
    print(f"[*] Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERR] Error: {result.stderr}")
    else:
        print(f"[OK] {result.stdout.strip()}")
    return result.returncode == 0

def update_tracking_status(ticker, p_type, period=None):
    print(f"[*] Updating production tracking in kasona_portfolio_assets for {ticker}...")
    # Use a dict that can hold various types to avoid lint errors
    update_data: dict = {
        "production_updated_at": "now()"
    }
    if p_type == "earnings":
        update_data["earnings_produced"] = True
        update_data["last_earnings_period"] = period
    elif p_type == "presentation":
        update_data["presentation_produced"] = True
    
    try:
        # We try both ticker_eod and ticker for robustness
        res = supabase.table("kasona_portfolio_assets").update(update_data).eq("ticker_eod", ticker).execute()
        if not res.data:
            supabase.table("kasona_portfolio_assets").update(update_data).eq("ticker", ticker).execute()
        print(f"[OK] Production status updated for {ticker}.")
    except Exception as e:
        print(f"[ERR] Failed to update tracking for {ticker}: {e}")

def format_json_to_md(data):
    """Recursively convert a JSON object/list into Markdown bullets/sections."""
    if isinstance(data, str):
        try:
            if data.strip().startswith(('{', '[')):
                data = json.loads(data)
            else:
                return data
        except:
            return data
            
    md = ""
    if isinstance(data, dict):
        for k, v in data.items():
            key_clean = k.replace("_", " ").title()
            if isinstance(v, (dict, list)):
                md += f"\n**{key_clean}**:\n" + format_json_to_md(v)
            else:
                md += f"- **{key_clean}**: {v}\n"
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                md += "\n" + format_json_to_md(item)
            else:
                md += f"- {item}\n"
    return md

def upload_and_sync(ticker, file_path, p_type, folder="general", lang="en"):
    """Uploads file to storage and updates the respective database URL."""
    # Determine bucket
    if p_type == "earnings":
        if file_path.suffix == ".pdf": bucket = "earnings-reports-pdf"
        elif file_path.suffix == ".mp3": bucket = "earnings-reports-audio"
        else: bucket = "earnings-reports-html"
    else: # presentation
        if file_path.suffix == ".pdf": bucket = "earnings-reports-presentations"
        elif file_path.suffix == ".mp3": bucket = "earnings-presentation-podcasts"
        else: bucket = "earnings-reports-html"
    
    storage_path = f"{folder}/{file_path.name}"
    print(f"[*] Syncing {file_path.name} to bucket '{bucket}' path '{storage_path}'...")
    
    try:
        file_options = {"upsert": "true"}
        if file_path.suffix == ".pdf":
            file_options["content-type"] = "application/pdf"
        elif file_path.suffix == ".mp3":
            file_options["content-type"] = "audio/mpeg"
        elif file_path.suffix == ".html":
            file_options["content-type"] = "text/html"

        with open(file_path, "rb") as f:
            supabase.storage.from_(bucket).upload(
                path=storage_path,
                file=f,
                file_options=file_options
            )
        url = f"{SUPABASE_URL}/storage/v1/object/public/{bucket}/{storage_path}"
        
        # Update respective table
        table = "quarterly_earnings" if p_type == "earnings" else "company_presentation"
        
        # Handle language-specific columns
        col_suffix = "_de" if lang == "de" else ""
        if file_path.suffix == ".pdf":
            col = f"pdf_report_url{col_suffix}" if p_type == "earnings" else "pdf_url"
        elif file_path.suffix == ".mp3":
            col = f"audio_report_url{col_suffix}" if p_type == "earnings" else "audio_url"
        else: # .html
            col = f"html_report_url{col_suffix}" if p_type == "earnings" else "html_url"
        
        update_payload = {col: url, "generated_at": "now()"}
        
        # If it's audio, also try to upload the script text
        if file_path.suffix == ".mp3":
            script_path = file_path.with_suffix(".txt")
            if not script_path.exists():
                # Try .md as well
                script_path = file_path.parent / f"{ticker}_presentation.md"
            
            if script_path.exists():
                with open(script_path, "r", encoding="utf-8") as sf:
                    update_payload["audio_script"] = sf.read()
        
        supabase.table(table).update(update_payload).eq("ticker_eod", ticker).execute()
        print(f"[OK] {col} updated for {ticker}.")
        return url
    except Exception as e:
        print(f"[ERR] Sync failed for {ticker}: {e}")
        return None

def process_earnings(ticker, period="Q4 2025", lang="en"):
    print(f"[*] Editing Earnings for {ticker} ({period}) in {lang}...")
    
    # 1. Fetch data from Supabase
    res = supabase.table("quarterly_earnings").select("*").eq("ticker_eod", ticker).eq("fiscal_period", period).execute()
    if not res.data:
        print(f"[ERR] No record found for {ticker} in {period}. Run Data Populator first.")
        return False

    record = res.data[0]
    
    # Language-specific content
    md_col = "markdown_content_de" if lang == "de" else "markdown_content"
    md_content = record.get(md_col)
    company_name = record.get("company_name") or ticker
    fiscal_period = record.get("fiscal_period") or period
    impact_score = record.get("impact_score") or "N/A"
    recommendation = record.get("recommendation") or "N/A"

    if not md_content:
        print(f"[WARN] No {lang} markdown narrative found.")
        if lang == "en":
             print(f"[*] Generating template...")
             md_content = f"# Earnings Briefing: {company_name}\n\nGenerated from Supabase Data."
        else:
             print(f"[ERR] German content requested but markdown_content_de is empty.")
             return False

    # 2. Save narrative to file
    suffix = "_de" if lang == "de" else ""
    md_path = OUTPUT_DIR / f"{ticker}_earnings{suffix}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    # 3. Generate HTML (Optional, currently English only tool)
    if lang == "en":
        run_command([sys.executable, str(BASE_DIR / "tools" / "generate_earnings_html.py"), str(md_path)])

    # 4. Generate PDF
    # The PDF tool handles the text as provided in markdown
    run_command([sys.executable, str(BASE_DIR / "tools" / "generate_earnings_pdf.py"), str(md_path), "--ticker", ticker])

    # 5. Generate Audio
    res_prof = supabase.table("quarterly_earnings").select("investor_profile").eq("ticker_eod", ticker).execute()
    folder = res_prof.data[0].get("investor_profile") if res_prof.data else "general"
    if not folder: folder = "general"
    
    # Voice selection
    voice = "killian" if lang == "de" else "christopher"
    
    # Construction of potential URLs for the script audit trail
    pdf_url_proto = f"{SUPABASE_URL}/storage/v1/object/public/earnings-reports-pdf/{folder}/{ticker}_earnings{suffix}.pdf"
    audio_url_proto = f"{SUPABASE_URL}/storage/v1/object/public/earnings-reports-audio/{folder}/{ticker}_audio{suffix}.mp3"

    run_command([
        sys.executable, str(BASE_DIR / "tools" / "generate_audio.py"),
        "--script", str(md_path),
        "--company", company_name,
        "--ticker-eod", ticker,
        "--pdf-url", pdf_url_proto,
        "--audio-url", audio_url_proto,
        "--fiscal-period", str(fiscal_period),
        "--impact-score", str(impact_score),
        "--recommendation", str(recommendation),
        "--voice", voice,
        "--output", str(OUTPUT_DIR / f"{ticker}_audio{suffix}.mp3")
    ])

    # 6. Synchronize Artifacts (Upload to Storage & Refresh DB URLs)
    upload_and_sync(ticker, OUTPUT_DIR / f"{ticker}_earnings{suffix}.pdf", "earnings", folder, lang)
    upload_and_sync(ticker, OUTPUT_DIR / f"{ticker}_audio{suffix}.mp3", "earnings", folder, lang)

    # 7. Update Tracking Status
    update_tracking_status(ticker, "earnings", period)

    # 8. Mark as Uploaded (Only for primary language to avoid blocking the other in batch runs)
    if lang == "en":
        supabase.table("quarterly_earnings").update({"uploaded": True, "status": "uploaded"}).eq("ticker_eod", ticker).eq("fiscal_period", period).execute()

    print(f"[DONE] Artifacts generated and synced for {ticker} ({lang}).")
    return True

def process_presentation(ticker):
    print(f"[*] Editing Presentation for {ticker}...")
    res = supabase.table("company_presentation").select("*").eq("ticker_eod", ticker).execute()
    if not res.data:
        print(f"[ERR] No record found for {ticker}. Run Data Populator first.")
        return False

    record = res.data[0]
    company_name = record.get("company_name", ticker)
    
    # 1. Validation: Enforce Zero-Null Policy
    mandatory_pillars = [
        'description', 'history-evolution', 'strategic_vision', 'growth_roadmap',
        'rivalry', 'supplier-power', 'buyer-power', 'threat-of-entry', 'substitutes',
        'leadership-governance', 'risk-success-factors', 'investment_thesis',
        'bull-case', 'bear-case', 'ai_agent_firmenhistorie',
        'core-assets-capabilities', 'success-failure-factors'
    ]
    
    missing_pillars = []
    for p in mandatory_pillars:
        val = record.get(p, "")
        if not val or "No data available" in str(val) or len(str(val)) < 20:
            missing_pillars.append(p)
            
    pres_tools_dir = BASE_DIR.parent.parent / "presentation" / "tools"
    if missing_pillars:
        print(f"\n[CRITICAL] Zero-Null Policy Violation for {ticker}!")
        print(f"Missing Columns: {', '.join(missing_pillars)}")
        print(f"[*] Triggering automatic remediation...")
        run_command([sys.executable, str(pres_tools_dir / "remediate_all_pillars.py"), ticker])
        # Re-fetch data after remediation
        res = supabase.table("company_presentation").select("*").eq("ticker_eod", ticker).execute()
        record = res.data[0]

    # 2. Draft Markdown (High Fidelity)
    md_path = OUTPUT_DIR / f"{ticker}_presentation.md"
    
    # Construction logic ported from generate_ticker_artifacts.py
    md_content = f"""# Institutional Presentation: {company_name}
    
## 1. Company Overview
{record.get('description')}

## 2. History and Strategic Evolution
{record.get('history-evolution')}

### 2.1 Deep Institutional Heritage
{format_json_to_md(record.get('ai_agent_firmenhistorie'))}

### 2.2 Core Assets & Capabilities
{record.get('core-assets-capabilities')}

### 2.3 Success & Failure Factors
{record.get('success-failure-factors')}

## 3. Strategic Vision & Growth Roadmap
### Vision
{record.get('strategic_vision')}

### Roadmap
{record.get('growth_roadmap')}

## 4. Porter's Five Forces Analysis
### Competitive Rivalry
{record.get('rivalry')}

### Supplier Power
{record.get('supplier-power')}

### Buyer Power
{record.get('buyer-power')}

### Threat of New Entry
{record.get('threat-of-entry')}

### Threat of Substitutes
{record.get('substitutes')}

## 5. Leadership and Governance Audit
{record.get('leadership-governance')}

## 6. Risk and Success Factors
{record.get('risk-success-factors')}

## 7. Investment Thesis
### Professional Summary
{record.get('investment_thesis')}

### Bull Case (Upside Catalysts)
{record.get('bull-case')}

### Bear Case (Downside Risks)
{record.get('bear-case')}

## 8. Institutional Resources & External Validation
"""
    # Append Links if they exist
    links = []
    if record.get('youtube_ceo_interview'):
        links.append(f"- **Latest CEO Interview**: [Watch here]({record.get('youtube_ceo_interview')})")
    if record.get('youtube_podcast'):
        links.append(f"- **Strategic Deep Dive (Podcast)**: [Watch here]({record.get('youtube_podcast')})")
    
    linkedin_profiles = record.get('linkedin_profiles')
    if linkedin_profiles:
        if isinstance(linkedin_profiles, str) and linkedin_profiles.startswith('['):
            try: import json; linkedin_profiles = json.loads(linkedin_profiles)
            except: pass
            
        if isinstance(linkedin_profiles, list):
            md_content += "- **Executive Performance Context (LinkedIn)**:\n"
            for p in linkedin_profiles:
                if isinstance(p, dict):
                    name = p.get('name', 'Profile')
                    url = p.get('url', '#')
                    title = p.get('title', '').split('·')[0].strip()
                    md_content += f"    - [{name}]({url}) - {title}\n"
        else:
            md_content += f"- **Executive Performance Context**: [LinkedIn Profiles]({linkedin_profiles})\n"
            
    if record.get('l4_report'):
        md_content += f"\n### Institutional Benchmark Analysis\n{record.get('l4_report')}\n"
        
    if links:
        md_content += "\n".join(links) + "\n"
    elif not linkedin_profiles and not record.get('l4_report'):
        md_content += "No external institutional links currently mapped.\n"

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"[OK] Markdown drafted: {md_path}")

    # 3. Generate Artifacts
    safe_ticker = ticker.replace(".", "_").lower()
    
    # 3.1 PDF
    print("[*] Generating PDF...")
    pdf_tool = pres_tools_dir / "generate_presentation_pdf.py"
    run_command([sys.executable, str(pdf_tool), str(md_path), "--ticker", ticker, "--output-dir", str(OUTPUT_DIR)])
    
    # 3.2 HTML
    print("[*] Generating HTML...")
    html_tool = pres_tools_dir / "generate_presentation_html.py"
    run_command([sys.executable, str(html_tool), str(md_path), "--ticker", ticker, "--output-dir", str(OUTPUT_DIR)])
    
    # 3.3 Audio
    print("[*] Generating Audio...")
    audio_tool = pres_tools_dir / "generate_presentation_audio.py"
    audio_out = OUTPUT_DIR / f"{safe_ticker}_briefing.mp3"
    run_command([sys.executable, str(audio_tool), "--script", str(md_path), "--output", str(audio_out)])

    # 4. Sync & Status Update
    upload_and_sync(ticker, OUTPUT_DIR / f"{safe_ticker}_presentation.pdf", "presentation")
    upload_and_sync(ticker, OUTPUT_DIR / f"{safe_ticker}_presentation.html", "presentation")
    upload_and_sync(ticker, audio_out, "presentation")

    update_tracking_status(ticker, "presentation")
    supabase.table("company_presentation").update({
        "uploaded": True, 
        "status": "uploaded", 
        "markdown_content": md_content
    }).eq("ticker_eod", ticker).execute()
    
    print(f"[DONE] Presentation artifacts generated and synced for {ticker}.")
    return True

def process_approved_records(p_type, profile=None, lang="en"):
    """Processes all records that are approved but not yet marked as uploaded."""
    table = "quarterly_earnings" if p_type == "earnings" else "company_presentation"
    # If lang is de, we might want to process even if uploaded=True (if English was done but German wasn't)
    # However, to keep it simple, we'll check if the specific language artifact is missing
    if lang == "de":
        query = supabase.table(table).select("*").eq("review_status", "approved").is_("pdf_report_url_de", "null")
    else:
        query = supabase.table(table).select("*").eq("review_status", "approved").eq("uploaded", False)
    
    if profile:
        query = query.eq("investor_profile", profile)
    
    res = query.execute()
    
    if not res.data:
        print(f"[OK] No pending {p_type} records found for processing.")
        return

    print(f"[*] Found {len(res.data)} records to process.")
    for record in res.data:
        ticker = record.get("ticker_eod")
        try:
            if p_type == "earnings":
                period = record.get("fiscal_period", "Q4 2025")
                process_earnings(ticker, period, lang)
            else:
                process_presentation(ticker)
        except Exception as e:
            print(f"[ERR] Failed to process {ticker}: {e}")

def process_queue(p_type="earnings"):
    """Pulls and processes tasks from analysis_queue."""
    print(f"[*] Processing Analysis Queue for {p_type}...")
    
    # Fetch pending tasks ordered by priority
    res = supabase.table("analysis_queue").select("*").eq("status", "pending").order("priority", desc=True).execute()
    
    if not res.data:
        print("[OK] Queue is empty.")
        return

    print(f"[*] Found {len(res.data)} items in queue.")
    
    for item in res.data:
        item_id = item.get("id")
        ticker = item.get("ticker")
        lang = item.get("language") or "en"
        
        print(f"\n[QUEUE] Processing {ticker} (ID: {item_id}, Lang: {lang})...")
        
        # Mark as processing
        supabase.table("analysis_queue").update({"status": "processing", "updated_at": "now()"}).eq("id", item_id).execute()
        
        try:
            success = False
            if p_type == "earnings":
                # For queue processing, we need to find the latest period for this ticker
                period_res = supabase.table("quarterly_earnings").select("fiscal_period").eq("ticker_eod", ticker).order("fiscal_period", desc=True).limit(1).execute()
                if period_res.data:
                    period = period_res.data[0].get("fiscal_period")
                    success = process_earnings(ticker, period, lang)
                else:
                    print(f"[ERR] No earnings record found for {ticker}")
                    supabase.table("analysis_queue").update({"status": "failed", "error_log": "No earnings record found"}).eq("id", item_id).execute()
                    continue
            else:
                success = process_presentation(ticker)
            
            if success:
                supabase.table("analysis_queue").update({"status": "completed", "updated_at": "now()"}).eq("id", item_id).execute()
            else:
                supabase.table("analysis_queue").update({"status": "failed", "error_log": "Processing returned False"}).eq("id", item_id).execute()
                
        except Exception as e:
            print(f"[ERR] Queue item failed: {e}")
            supabase.table("analysis_queue").update({"status": "failed", "error_log": str(e)}).eq("id", item_id).execute()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker")
    parser.add_argument("--type", choices=["earnings", "presentation"], default="earnings")
    parser.add_argument("--period", default="Q4 2025")
    parser.add_argument("--lang", choices=["en", "de"], default="en")
    parser.add_argument("--batch-approved", action="store_true", help="Process all approved but not uploaded records")
    parser.add_argument("--process-queue", action="store_true", help="Process tasks from analysis_queue")
    parser.add_argument("--profile", help="Filter by investor_profile (e.g., 991001-SA)")
    args = parser.parse_args()

    if args.process_queue:
        process_queue(args.type)
    elif args.batch_approved:
        process_approved_records(args.type, args.profile, args.lang)
    elif args.ticker:
        if args.type == "earnings":
            process_earnings(args.ticker, args.period, args.lang)
        else:
            process_presentation(args.ticker)
    else:
        print("[ERR] Error: Must provide either --ticker, --batch-approved, or --process-queue")
        sys.exit(1)

if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
