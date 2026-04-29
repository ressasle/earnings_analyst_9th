import os
import subprocess
import sys
import time
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("[!] SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY missing.")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def push_to_master_index(
    ticker_eod: str,
    company_name: str,
    pdf_url: str,
    audio_url: str,
    fiscal_period: str,
    supabase_client: Client,
    pdf_url_de: str = None,
    audio_url_de: str = None
) -> bool:
    """Push quarterly earnings metadata to public.kasona_company_reports."""
    print(f"   [INDEX] Pushing metadata for {ticker_eod}...")
    
    # Prepare logs
    quarterly_pdf_en = [{"type": "earnings_pdf", "label": f"Earnings Report {fiscal_period}", "url": pdf_url}]
    quarterly_audio_en = [{"type": "earnings_audio", "label": f"Earnings Audio {fiscal_period}", "url": audio_url}]

    quarterly_pdf_de = []
    if pdf_url_de:
        quarterly_pdf_de.append({"type": "earnings_pdf", "label": f"Earnings Report {fiscal_period} (DE)", "url": pdf_url_de})

    quarterly_audio_de = []
    if audio_url_de:
        quarterly_audio_de.append({"type": "earnings_audio", "label": f"Earnings Audio {fiscal_period} (DE)", "url": audio_url_de})

    payload = {
        "ticker_eod": ticker_eod,
        "company_name": company_name,
        "report_date": datetime.now().isoformat(),
        "skill_id": "quarterly_earnings",
        "report_type": "Quarterly Earnings Analysis",
        "trigger_reason": "Batch Orchestration",
        "presentation_pdf_en": [],
        "presentation_pdf_de": [],
        "presentation_audio_en": [],
        "presentation_audio_de": [],
        "quarterly_analysis_pdf_en": quarterly_pdf_en,
        "quarterly_analysis_pdf_de": quarterly_pdf_de,
        "quarterly_analysis_audio_en": quarterly_audio_en,
        "quarterly_analysis_audio_de": quarterly_audio_de,
        "created_by": "n8n-automation",
        "review_status": "published",
        "updated_at": datetime.now().isoformat()
    }

    try:
        res = supabase_client.table("kasona_company_reports").upsert(payload).execute()
        return len(res.data) > 0
    except Exception as exc:
        print(f"   [!] Master Index error: {exc}")
        return False

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
        
        # 5. Log to Master Index
        pdf_url_de = record.get("pdf_report_url_de")
        audio_url_de = record.get("audio_report_url_de")
        
        push_to_master_index(
            ticker, company, pdf_url, audio_url, fp, supabase,
            pdf_url_de=pdf_url_de, 
            audio_url_de=audio_url_de
        )
        
        print(f"[OK] Completed {ticker}")

if __name__ == "__main__":
    run_orchestrator()
