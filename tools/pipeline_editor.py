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
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not all([SUPABASE_URL, SUPABASE_KEY]):
    print("[ERR] Missing Supabase credentials.")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
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

def upload_and_sync(ticker, file_path, p_type, folder="general"):
    """Uploads file to storage and updates the respective database URL."""
    bucket = "earnings-reports-pdf" if file_path.suffix == ".pdf" else "earnings-reports-audio"
    if p_type == "presentation":
        bucket = "company-presentation-pdf" # Presentations only have PDFs for now
    
    storage_path = f"{folder}/{file_path.name}"
    print(f"[*] Syncing {file_path.name} to bucket '{bucket}' path '{storage_path}'...")
    
    try:
        file_options = {"upsert": "true"}
        if file_path.suffix == ".pdf":
            file_options["content-type"] = "application/pdf"
        elif file_path.suffix == ".mp3":
            file_options["content-type"] = "audio/mpeg"

        with open(file_path, "rb") as f:
            supabase.storage.from_(bucket).upload(
                path=storage_path,
                file=f,
                file_options=file_options
            )
        url = f"{SUPABASE_URL}/storage/v1/object/public/{bucket}/{storage_path}"
        
        # Update respective table
        table = "quarterly_earnings" if p_type == "earnings" else "company_presentation"
        col = "pdf_report_url" if file_path.suffix == ".pdf" else "audio_report_url"
        
        update_payload = {col: url, "generated_at": "now()"}
        
        # If it's audio, also try to upload the script text
        if file_path.suffix == ".mp3":
            script_path = file_path.with_suffix(".txt")
            if script_path.exists():
                with open(script_path, "r", encoding="utf-8") as sf:
                    update_payload["audio_script"] = sf.read()
        
        supabase.table(table).update(update_payload).eq("ticker_eod", ticker).execute()
        print(f"[OK] {col} updated for {ticker}.")
        return url
    except Exception as e:
        print(f"[ERR] Sync failed for {ticker}: {e}")
        return None

def process_earnings(ticker, period="Q4 2025"):
    print(f"[*] Editing Earnings for {ticker} ({period})...")
    
    # 1. Fetch data from Supabase
    res = supabase.table("quarterly_earnings").select("*").eq("ticker_eod", ticker).eq("fiscal_period", period).execute()
    if not res.data:
        print(f"[ERR] No record found for {ticker} in {period}. Run Data Populator first.")
        return

    record = res.data[0]
    md_content = record.get("markdown_content")
    company_name = record.get("company_name") or ticker
    fiscal_period = record.get("fiscal_period") or period
    impact_score = record.get("impact_score") or "N/A"
    recommendation = record.get("recommendation") or "N/A"

    if not md_content:
        print(f"[*] No markdown narrative found. Generating template...")
        # Template generation logic (or instruction for agent to provide content)
        md_content = f"# Earnings Briefing: {company_name}\n\nGenerated from Supabase Data."

    # 2. Save narrative to file
    md_path = OUTPUT_DIR / f"{ticker}_earnings.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    # 3. Generate HTML
    run_command([sys.executable, str(BASE_DIR / "tools" / "generate_earnings_html.py"), str(md_path)])

    # 4. Generate PDF
    run_command([sys.executable, str(BASE_DIR / "tools" / "generate_earnings_pdf.py"), str(md_path), "--ticker", ticker])

    # 5. Generate Audio
    # We need the URLs which are updated later, so we pre-calculate them for the script
    res_prof = supabase.table("quarterly_earnings").select("investor_profile").eq("ticker_eod", ticker).execute()
    folder = res_prof.data[0].get("investor_profile") if res_prof.data else "general"
    if not folder: folder = "general"
    
    pdf_url = f"{SUPABASE_URL}/storage/v1/object/public/earnings-reports-pdf/{folder}/{ticker}_earnings.pdf"
    audio_url = f"{SUPABASE_URL}/storage/v1/object/public/earnings-reports-audio/{folder}/{ticker}_audio.mp3"

    run_command([
        sys.executable, str(BASE_DIR / "tools" / "generate_audio.py"),
        "--script", str(md_path),
        "--company", company_name,
        "--ticker-eod", ticker,
        "--pdf-url", pdf_url,
        "--audio-url", audio_url,
        "--fiscal-period", str(fiscal_period),
        "--impact-score", str(impact_score),
        "--recommendation", str(recommendation),
        "--output", str(OUTPUT_DIR / f"{ticker}_audio.mp3")
    ])

    # 6. Synchronize Artifacts (Upload to Storage & Refresh DB URLs)
    pdf_url_final = upload_and_sync(ticker, OUTPUT_DIR / f"{ticker}_earnings.pdf", "earnings", folder)
    audio_url_final = upload_and_sync(ticker, OUTPUT_DIR / f"{ticker}_audio.mp3", "earnings", folder)

    # 7. Update Tracking Status
    update_tracking_status(ticker, "earnings", period)

    # 8. Mark as Uploaded
    supabase.table("quarterly_earnings").update({"uploaded": True, "status": "uploaded"}).eq("ticker_eod", ticker).eq("fiscal_period", period).execute()

    print(f"[DONE] Artifacts generated and synced for {ticker}.")

def process_presentation(ticker):
    print(f"[*] Editing Presentation for {ticker}...")
    res = supabase.table("company_presentation").select("*").eq("ticker_eod", ticker).execute()
    if not res.data:
        print(f"[ERR] No record found for {ticker}. Run Data Populator first.")
        return

    record = res.data[0]
    company_name = record.get("company_name", ticker)
    
    # Logic for presentation PDF (Landscape)
    # This uses presentation/tools/generate_presentation_pdf.py
    pres_tool = BASE_DIR.parent / "presentation" / "tools" / "generate_presentation_pdf.py"
    md_path = OUTPUT_DIR / f"{ticker}_presentation.md"
    
    # Simplified content construction if markdown_content is missing
    if not record.get("markdown_content"):
         md_content = f"# Presentation: {company_name}\n\n## Investment Thesis\n{record.get('investment_thesis')}"
         with open(md_path, "w", encoding="utf-8") as f:
             f.write(md_content)
    
    success = run_command([sys.executable, str(pres_tool), str(md_path), "--ticker", ticker])
    
    if success:
        # Update Tracking Status
        update_tracking_status(ticker, "presentation")
        # Mark as uploaded
        supabase.table("company_presentation").update({"uploaded": True, "status": "uploaded"}).eq("ticker_eod", ticker).execute()

def process_approved_records(p_type, profile=None):
    """Processes all records that are approved but not yet marked as uploaded."""
    table = "quarterly_earnings" if p_type == "earnings" else "company_presentation"
    print(f"[*] Querying for approved but not uploaded {p_type}...")
    
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
                process_earnings(ticker, period)
            else:
                process_presentation(ticker)
        except Exception as e:
            print(f"[ERR] Failed to process {ticker}: {e}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker")
    parser.add_argument("--type", choices=["earnings", "presentation"], default="earnings")
    parser.add_argument("--period", default="Q4 2025")
    parser.add_argument("--batch-approved", action="store_true", help="Process all approved but not uploaded records")
    parser.add_argument("--profile", help="Filter by investor_profile (e.g., 991001-SA)")
    args = parser.parse_args()

    if args.batch_approved:
        process_approved_records(args.type, args.profile)
    elif args.ticker:
        if args.type == "earnings":
            process_earnings(args.ticker, args.period)
        else:
            process_presentation(args.ticker)
    else:
        print("[ERR] Error: Must provide either --ticker or --batch-approved")
        sys.exit(1)

if __name__ == "__main__":
    main()
