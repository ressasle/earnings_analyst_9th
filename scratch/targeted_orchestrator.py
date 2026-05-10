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

TICKERS = ["MRK.US", "BP.LSE", "LIFCO-B.ST", "UNP.US", "VIT-B.ST", "AI.PA", "DHR.US", "ISRG.US", "MMM.US", "NEE.US"]
FISCAL_PERIOD = "Q1 2026"

def push_to_master_index(ticker_eod, company_name, pdf_url, audio_url, fiscal_period, supabase_client):
    print(f"   [INDEX] Pushing metadata for {ticker_eod}...")
    payload = {
        "ticker_eod": ticker_eod,
        "company_name": company_name,
        "report_date": datetime.now().isoformat(),
        "skill_id": "quarterly_earnings",
        "report_type": "Quarterly Earnings Analysis",
        "trigger_reason": "Batch Orchestration Targeted",
        "quarterly_analysis_pdf_en": [{"type": "earnings_pdf", "label": f"Earnings Report {fiscal_period}", "url": pdf_url}],
        "quarterly_analysis_audio_en": [{"type": "earnings_audio", "label": f"Earnings Audio {fiscal_period}", "url": audio_url}],
        "created_by": "n8n-automation",
        "review_status": "published",
        "updated_at": datetime.now().isoformat()
    }
    try:
        supabase_client.table("kasona_company_reports").upsert(payload).execute()
        return True
    except Exception as exc:
        print(f"   [!] Master Index error: {exc}")
        return False

def run_targeted_orchestrator():
    print(f"[*] Targeted Orchestrator: Processing {len(TICKERS)} tickers for {FISCAL_PERIOD}...")
    
    for ticker in TICKERS:
        res = supabase.table("quarterly_earnings").select("*").eq("ticker_eod", ticker).eq("fiscal_period", FISCAL_PERIOD).execute()
        if not res.data:
            print(f"[!] No record found for {ticker} {FISCAL_PERIOD}. Skipping.")
            continue
        
        record = res.data[0]
        company = record.get("company_name") or ticker
        quarter = record.get("quarter") or "Q1"
        year = record.get("fiscal_year") or 2026
        
        print(f"\n[>>>] Processing {ticker} - {FISCAL_PERIOD}")
        
        md_file = f"output/{ticker}_{FISCAL_PERIOD.replace(' ', '_')}.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(record["markdown_content"])
            
        print(f"   [+] Generating PDF...")
        subprocess.run(["python", "tools/generate_earnings_html.py", md_file], check=False)
        subprocess.run(["python", "tools/generate_earnings_pdf.py", md_file, "--ticker", ticker], check=False)
        
        print(f"   [+] Generating Audio...")
        pdf_name = f"{ticker}_{FISCAL_PERIOD.replace(' ', '_')}.pdf"
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
            "--fiscal-period", FISCAL_PERIOD,
            "--impact-score", str(record.get("impact_score", "N/A")),
            "--recommendation", str(record.get("recommendation", "N/A")),
            "--output", f"output/{mp3_name}"
        ], check=False)
        
        print(f"   [+] Syncing to Supabase Storage...")
        subprocess.run(["python", "tools/supabase_storage_manager.py", "--file", f"output/{pdf_name}", "--bucket", "earnings-reports-pdf", "--ticker", ticker, "--quarter", quarter, "--year", str(year), "--update-db"], check=False)
        subprocess.run(["python", "tools/supabase_storage_manager.py", "--file", f"output/{mp3_name}", "--bucket", "earnings-reports-audio", "--ticker", ticker, "--quarter", quarter, "--year", str(year), "--update-db"], check=False)
        
        push_to_master_index(ticker, company, pdf_url, audio_url, FISCAL_PERIOD, supabase)
        print(f"[OK] Completed {ticker}")

if __name__ == "__main__":
    run_targeted_orchestrator()
