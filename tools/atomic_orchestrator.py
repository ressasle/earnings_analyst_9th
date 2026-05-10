import os
import subprocess
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

# Ensure project root is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import Client
from utils.supabase_client import get_supabase_client

load_dotenv()

# Centralized client
supabase = get_supabase_client()
# Get URL for storage links (needed by scripts)
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
        res = supabase_client.table("kasona_company_reports").upsert(
            payload,
            on_conflict="ticker_eod,skill_id"
        ).execute()
        return len(res.data) > 0
    except Exception as exc:
        print(f"   [!] Master Index error: {exc}")
        return False

def run_orchestrator(target_ticker=None):
    print(f"[*] Atomic Orchestrator: Starting production...")
    
    # 1. Fetch approved records
    query = supabase.table("quarterly_earnings").select("*").eq("review_status", "approved").eq("fiscal_period", "Q1 2026")
    if target_ticker:
        query = query.eq("ticker_eod", target_ticker)
        
    res = query.execute()
    records = res.data
    
    if not records:
        print("[!] No 'approved' records found. Exiting.")
        return

    print(f"[*] Found {len(records)} records for processing.")
    
    for record in records:
        ticker = record["ticker_eod"]
        fp = record.get("fiscal_period") or "Q1 2026"
        company = record.get("company_name") or ticker
        quarter = record.get("quarter") or "Q1"
        year = record.get("fiscal_year") or 2026
        
        print(f"\n[>>>] Processing {ticker} - {fp}")
        if record.get("manual_ingestion"):
            print(f"   [MANUAL] Source: {record['manual_ingestion']}")
        
        md_file = f"output/{ticker}_{fp.replace(' ', '_')}.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(record["markdown_content"])
            
        # 1. Generate HTML & PDF
        print(f"   [+] Generating PDF...")
        subprocess.run(["python", "tools/generate_earnings_html.py", md_file], check=False)
        subprocess.run(["python", "tools/generate_earnings_pdf.py", md_file, "--ticker", ticker], check=False)
        
        # 2. Generate Audio (Neural)
        print(f"   [+] Generating Audio...")
        sys.stdout.flush()
        pdf_name = f"{ticker}_{fp.replace(' ', '_')}.pdf"
        mp3_name = f"{ticker}_{fp.replace(' ', '_')}.mp3"

        # Construct public URLs for branding
        pdf_url = f"{SUPABASE_URL}/storage/v1/object/public/earnings-reports-pdf/{ticker}/{quarter}_{year}_{pdf_name}"
        audio_url = f"{SUPABASE_URL}/storage/v1/object/public/earnings-reports-audio/{ticker}/{quarter}_{year}_{mp3_name}"

        # Derive benchmark label from stored ticker (QQQ → Nasdaq-100, else S&P 500)
        bm_ticker_stored = record.get("benchmark_ticker", "")
        benchmark_label = "Nasdaq-100" if str(bm_ticker_stored).upper() == "QQQ" else "S&P 500"

        cmd_args = [
            "python", "tools/generate_audio.py",
            "--script", str(md_file),
            "--company", str(company),
            "--ticker-eod", str(ticker),
            "--pdf-url", str(pdf_url),
            "--audio-url", str(audio_url),
            "--fiscal-period", str(fp),
            "--impact-score", str(record.get("impact_score", "N/A")),
            "--output", f"output/{mp3_name}",
        ]

        # Inject market reaction args when populated by enrich_price_movements.py
        move_7d = record.get("price_movement_7d_prior")
        move_post = record.get("price_movement_post_earnings")
        bm_move = record.get("benchmark_move_post")
        rel_perf = record.get("relative_performance")

        if move_7d is not None:
            cmd_args += ["--move-7d", str(move_7d)]
        if move_post is not None:
            cmd_args += ["--move-post", str(move_post)]
        if bm_ticker_stored:
            cmd_args += ["--benchmark-label", benchmark_label]
        if bm_move is not None:
            cmd_args += ["--benchmark-move", str(bm_move)]
        if rel_perf is not None:
            cmd_args += ["--relative-perf", str(rel_perf)]

        subprocess.run(cmd_args, check=False)
        
        # 3. Sync to Storage
        print(f"   [+] Syncing to Supabase Storage...")
        sys.stdout.flush()
        # PDF
        subprocess.run([
            "python", "tools/supabase_storage_manager.py",
            "--file", f"output/{pdf_name}",
            "--bucket", "earnings-reports-pdf",
            "--ticker", str(ticker),
            "--quarter", str(quarter),
            "--year", str(year),
            "--update-db" # Updates quarterly_earnings
        ], check=False)
        
        # Audio
        subprocess.run([
            "python", "tools/supabase_storage_manager.py",
            "--file", f"output/{mp3_name}",
            "--bucket", "earnings-reports-audio",
            "--ticker", str(ticker),
            "--quarter", str(quarter),
            "--year", str(year),
            "--update-db" # Updates quarterly_earnings
        ], check=False)

        # HTML
        html_name = f"{ticker}_{fp.replace(' ', '_')}.html"
        subprocess.run([
            "python", "tools/supabase_storage_manager.py",
            "--file", f"output/{html_name}",
            "--bucket", "earnings-reports-html",
            "--ticker", str(ticker),
            "--quarter", str(quarter),
            "--year", str(year),
            "--update-db" # Updates quarterly_earnings
        ], check=False)
        
        # 4. Push to Master Index (kasona_company_reports)
        pdf_url_de = record.get("pdf_report_url_de")
        audio_url_de = record.get("audio_report_url_de")
        
        push_to_master_index(
            ticker, company, pdf_url, audio_url, fp, supabase,
            pdf_url_de=pdf_url_de,
            audio_url_de=audio_url_de
        )
        
        print(f"[OK] Completed {ticker}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", help="Specific ticker to process")
    args = parser.parse_args()
    
    run_orchestrator(target_ticker=args.ticker)
