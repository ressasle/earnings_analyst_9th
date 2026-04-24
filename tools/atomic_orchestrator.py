import os
import subprocess
import sys
import time
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("[!] SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY missing.")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def run_orchestrator():
    print("[*] Atomic Orchestrator: Starting production for all 'approved' records...")
    
    # 1. Fetch approved records
    res = supabase.table("quarterly_earnings").select("*").eq("review_status", "approved").execute()
    records = res.data
    
    if not records:
        print("[!] No 'approved' records found. Exiting.")
        return

    print(f"[*] Found {len(records)} records for processing.")
    
    for record in records:
        ticker = record["ticker_eod"]
        fp = record.get("fiscal_period", "Q1 2026")
        quarter = record.get("quarter", "Q1")
        year = record.get("fiscal_year", 2026)
        company = record.get("company_name", ticker)
        
        print(f"\n[>>>] Processing {ticker} - {fp}")
        
        md_file = f"output/{ticker}_{fp.replace(' ', '_')}.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(record["markdown_content"])
            
        # 1. Generate HTML & PDF
        print(f"   [+] Generating PDF...")
        subprocess.run(["python", "tools/generate_earnings_html.py", md_file], check=False)
        subprocess.run(["python", "tools/generate_earnings_pdf.py", md_file, "--ticker", ticker], check=False)
        
        # 2. Generate Audio (Neural)
        print(f"   [+] Generating Audio...")
        pdf_name = f"{ticker}_earnings.pdf" # PDF script outputs this
        mp3_name = f"{ticker}_audio.mp3"
        
        # Construct public URL for branding (heuristic from scripts)
        # Note: the actual upload will happen next, but the script puts these URLs IN the audio script
        pdf_url = f"{SUPABASE_URL}/storage/v1/object/public/earnings-reports-pdf/{ticker}/{quarter}_{year}_{pdf_name}"
        audio_url = f"{SUPABASE_URL}/storage/v1/object/public/earnings-reports-audio/{ticker}/{quarter}_{year}_{mp3_name}"

        subprocess.run([
            "python", "tools/generate_audio.py",
            "--script", md_file,
            "--company", company,
            "--ticker-eod", ticker,
            "--pdf-url", pdf_url,
            "--audio-url", audio_url,
            "--fiscal-period", fp,
            "--impact-score", str(record.get("impact_score", "N/A")),
            "--recommendation", str(record.get("recommendation", "N/A")),
            "--output", f"output/{mp3_name}"
        ], check=False)
        
        # 3. Sync to Storage
        print(f"   [+] Syncing to Supabase Storage...")
        # PDF
        subprocess.run([
            "python", "tools/supabase_storage_manager.py",
            "--file", f"output/{pdf_name}",
            "--bucket", "earnings-reports-pdf",
            "--ticker", ticker,
            "--quarter", quarter,
            "--year", str(year),
            "--update-db" # Updates quarterly_earnings
        ], check=False)
        
        # Audio
        subprocess.run([
            "python", "tools/supabase_storage_manager.py",
            "--file", f"output/{mp3_name}",
            "--bucket", "earnings-reports-audio",
            "--ticker", ticker,
            "--quarter", quarter,
            "--year", str(year),
            "--update-db" # Updates quarterly_earnings
        ], check=False)
        
        # 4. Log to Artifacts Table
        # Fetch audit script saved by generate_audio.py
        script_path = f"output/{mp3_name.replace('.mp3', '.txt')}"
        audio_script = ""
        if os.path.exists(script_path):
            with open(script_path, "r", encoding="utf-8") as asf:
                audio_script = asf.read()

        artifact_data = {
            "earnings_id": record["id"],
            "ticker_eod": ticker,
            "fiscal_period": fp,
            "pdf_url": pdf_url,
            "audio_url": audio_url,
            "audio_script": audio_script
        }
        supabase.table("quarterly_earnings_artifacts").insert(artifact_data).execute()
        
        print(f"[OK] Completed {ticker}")

if __name__ == "__main__":
    run_orchestrator()
