import os
import subprocess
import sys
import time
from datetime import datetime
from dotenv import load_dotenv
from supabase import Client
from utils.supabase_client import get_supabase_client

load_dotenv()

# Centralized client
supabase = get_supabase_client()
SUPABASE_URL = os.environ.get("SUPABASE_URL")

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
    
    quarterly_pdf_en = [{"type": "earnings_pdf", "label": f"Earnings Report {fiscal_period}", "url": pdf_url}]
    quarterly_audio_en = [{"type": "earnings_audio", "label": f"Earnings Audio {fiscal_period}", "url": audio_url}]

    payload = {
        "ticker_eod": ticker_eod,
        "company_name": company_name,
        "report_date": datetime.now().isoformat(),
        "skill_id": "quarterly_earnings",
        "report_type": "Quarterly Earnings Analysis",
        "trigger_reason": "Single Orchestration",
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

def run_single_orchestrator(ticker_filter: str):
    print(f"[*] Single Orchestrator: Starting production for {ticker_filter}...")
    
    # 1. Fetch record for specific ticker
    res = supabase.table("quarterly_earnings").select("*").eq("ticker_eod", ticker_filter).eq("review_status", "approved").order("created_at", desc=True).limit(1).execute()
    records = res.data
    
    if not records:
        print(f"[!] No 'approved' records found for {ticker_filter}. Exiting.")
        return

    record = records[0]
    ticker = record["ticker_eod"]
    fp = record.get("fiscal_period", "Q1 2026")
    quarter = record.get("quarter", "Q1") or "Q1"
    year = record.get("fiscal_year", 2026) or 2026
    company = record.get("company_name", ticker)
    
    print(f"\n[>>>] Processing {ticker} - {fp}")
    
    md_file = f"output/{ticker}_{fp.replace(' ', '_')}.md"
    if not os.path.exists("output"):
        os.makedirs("output")
        
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(record["markdown_content"])
        
    # 1. Generate HTML & PDF
    print(f"   [+] Generating PDF...")
    subprocess.run(["python", "tools/generate_earnings_html.py", md_file], check=False)
    subprocess.run(["python", "tools/generate_earnings_pdf.py", md_file, "--ticker", ticker], check=False)
    
    # 2. Generate Audio (Neural)
    print(f"   [+] Generating Audio...")
    pdf_name = f"{ticker}_{fp.replace(' ', '_')}.pdf"
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
        "--impact-score", str(record.get("impact_score", "N/A")),
        "--recommendation", str(record.get("recommendation", "N/A")),
        "--output", f"output/{mp3_name}"
    ], check=False)
    
    # 3. Sync to Storage
    print(f"   [+] Syncing to Supabase Storage...")
    subprocess.run([
        "python", "tools/supabase_storage_manager.py",
        "--file", f"output/{pdf_name}",
        "--bucket", "earnings-reports-pdf",
        "--ticker", ticker,
        "--quarter", quarter,
        "--year", str(year),
        "--update-db"
    ], check=False)
    
    subprocess.run([
        "python", "tools/supabase_storage_manager.py",
        "--file", f"output/{mp3_name}",
        "--bucket", "earnings-reports-audio",
        "--ticker", ticker,
        "--quarter", quarter,
        "--year", str(year),
        "--update-db"
    ], check=False)
    
    # 4. Log to Master Index
    push_to_master_index(ticker, company, pdf_url, audio_url, fp, supabase)
    print(f"[OK] Completed {ticker}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_single_orchestrator(sys.argv[1])
    else:
        run_single_orchestrator("GOOG.US")
