import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import subprocess
import time
from datetime import datetime
from dotenv import load_dotenv
from supabase import Client
from utils.supabase_client import get_supabase_client

load_dotenv()

# Centralized client
supabase = get_supabase_client()
SUPABASE_URL = os.environ.get("SUPABASE_URL")

# Ensure subprocesses can find 'utils'
os.environ["PYTHONPATH"] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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
    print(f"   [INDEX] Pushing metadata for {ticker_eod}...")
    
    quarterly_pdf_en = [{"type": "earnings_pdf", "label": f"Earnings Report {fiscal_period}", "url": pdf_url}]
    quarterly_audio_en = [{"type": "earnings_audio", "label": f"Earnings Audio {fiscal_period}", "url": audio_url}]

    payload = {
        "ticker_eod": ticker_eod,
        "company_name": company_name,
        "report_date": datetime.now().isoformat(),
        "skill_id": "quarterly_earnings",
        "report_type": "Quarterly Earnings Analysis",
        "trigger_reason": "Manual Single-Asset Orchestration",
        "presentation_pdf_en": [],
        "presentation_pdf_de": [],
        "presentation_audio_en": [],
        "presentation_audio_de": [],
        "quarterly_analysis_pdf_en": quarterly_pdf_en,
        "quarterly_analysis_pdf_de": [],
        "quarterly_analysis_audio_en": quarterly_audio_en,
        "quarterly_analysis_audio_de": [],
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

def run_single_orchestration(ticker="GOOG.US"):
    print(f"[*] Starting orchestration for {ticker}...")
    
    # 1. Fetch the record
    res = supabase.table("quarterly_earnings").select("*").eq("ticker_eod", ticker).eq("fiscal_period", "Q1 2026").execute()
    if not res.data:
        print(f"[!] No record found for {ticker} Q1 2026")
        return
    
    record = res.data[0]
    fp = record.get("fiscal_period", "Q1 2026")
    quarter = record.get("quarter", "Q1")
    year = record.get("fiscal_year", 2026)
    company = record.get("company_name", "Alphabet Inc.")
    
    md_file = f"output/{ticker}_{fp.replace(' ', '_')}.md"
    os.makedirs("output", exist_ok=True)
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(record["markdown_content"])
        
    # 2. Generate HTML & PDF
    print(f"   [+] Generating HTML & PDF...")
    subprocess.run(["python", "tools/generate_earnings_html.py", md_file], check=False)
    subprocess.run(["python", "tools/generate_earnings_pdf.py", md_file, "--ticker", ticker], check=False)
    
    # 3. Generate Audio
    print(f"   [+] Generating Audio...")
    pdf_name = f"{ticker}_{fp.replace(' ', '_')}.pdf" # Based on generate_earnings_pdf.py logic (md_path.stem + ".pdf")
    mp3_name = f"{ticker}_audio.mp3"
    
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
        "--impact-score", str(record.get("impact_score", "92")),
        "--recommendation", str(record.get("recommendation", "Strong Buy")),
        "--output", f"output/{mp3_name}"
    ], check=False)
    
    # 4. Sync to Storage
    print(f"   [+] Syncing to Supabase Storage...")
    # PDF
    subprocess.run([
        "python", "tools/supabase_storage_manager.py",
        "--file", f"output/{pdf_name}",
        "--bucket", "earnings-reports-pdf",
        "--ticker", ticker,
        "--quarter", quarter,
        "--year", str(year),
        "--update-db"
    ], check=False)
    
    # Audio
    subprocess.run([
        "python", "tools/supabase_storage_manager.py",
        "--file", f"output/{mp3_name}",
        "--bucket", "earnings-reports-audio",
        "--ticker", ticker,
        "--quarter", quarter,
        "--year", str(year),
        "--update-db"
    ], check=False)
    
    # 5. Log to Artifacts Table
    print(f"   [+] Logging to Artifacts...")
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
    
    # 6. Log to Master Index
    push_to_master_index(ticker, company, pdf_url, audio_url, fp, supabase)
    
    # 7. Update status to 'completed'
    supabase.table("quarterly_earnings").update({"status": "completed"}).eq("id", record["id"]).execute()
    
    print(f"\n[OK] Orchestration Complete for {ticker}")
    print(f"PDF URL: {pdf_url}")
    print(f"Audio URL: {audio_url}")

if __name__ == "__main__":
    run_single_orchestration()
