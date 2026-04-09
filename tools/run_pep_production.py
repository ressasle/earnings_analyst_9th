import os
import subprocess
import sys
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("[!] SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not found in .env")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

TARGET_TICKERS = [
    'ASKER', 'PPGN', '1SXP', 'DESN', 'MEDP', 'NVO', 
    'YPSN', 'ROVI', 'HIMS', 'LLY', 'BANB', 'WST', 'ZEAL', 'STVN'
]

def get_company_name(ticker):
    # Try to fetch from database if possible, otherwise use base
    return ticker.split(".")[0]

def run():
    print(f"[*] Starting production for {len(TARGET_TICKERS)} PEP tickers...")
    
    # Pre-fetch portfolio mappings to find folders
    asset_res = supabase.table("kasona_portfolio_assets").select("ticker, portfolio_id").in_("ticker", TARGET_TICKERS).execute()
    portfolio_map = {r['ticker']: r['portfolio_id'] for r in asset_res.data if r['portfolio_id'].startswith("991001")}
    
    # Fetch content from quarterly_earnings
    earnings_res = supabase.table("quarterly_earnings").select("*").in_("ticker_eod", TARGET_TICKERS).execute()
    records = {r['ticker_eod']: r for r in earnings_res.data}

    for ticker in TARGET_TICKERS:
        if ticker not in records:
            print(f"[!] No record found for {ticker} in quarterly_earnings. Skipping.")
            continue
        
        record = records[ticker]
        company = record.get("company_name", ticker)
        portfolio_subfolder = portfolio_map.get(ticker, "991001-PEP") # Default to PEP if mapping missing
        
        print(f"\n[>>>] Processing {ticker} ({company}) -> {portfolio_subfolder}")
        
        md_file = f"output/{ticker}_earnings.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(record["markdown_content"])
            
        # Artifact Paths
        pdf_name = f"{ticker}_earnings.pdf"
        pdf_url = f"{SUPABASE_URL}/storage/v1/object/public/earnings-reports-pdf/{portfolio_subfolder}/{pdf_name}"
        mp3_name = f"{ticker}_audio.mp3"
        audio_url = f"{SUPABASE_URL}/storage/v1/object/public/earnings-reports-audio/{portfolio_subfolder}/{mp3_name}"

        # 1. HTML Gen
        subprocess.run(["python", "tools/generate_earnings_html.py", md_file], check=False)
        
        # 2. PDF Gen
        subprocess.run(["python", "tools/generate_earnings_pdf.py", md_file, "--ticker", ticker], check=False)
        
        # 3. Audio Gen (Hardened version)
        subprocess.run([
            "python", "tools/generate_audio.py",
            "--script", md_file,
            "--company", company,
            "--ticker-eod", ticker,
            "--pdf-url", pdf_url,
            "--audio-url", audio_url,
            "--fiscal-period", record.get("fiscal_period", "Q4 2025"),
            "--impact-score", str(record.get("impact_score", "N/A")),
            "--recommendation", str(record.get("recommendation", "N/A")),
            "--output", f"output/{mp3_name}"
        ], check=False)

        # 4. Storage Sync (PDF)
        pdf_path = f"output/{pdf_name}"
        if os.path.exists(pdf_path):
            print(f"[*] Uploading PDF to {portfolio_subfolder}...")
            with open(pdf_path, 'rb') as f:
                supabase.storage.from_('earnings-reports-pdf').upload(
                    file=f, path=f"{portfolio_subfolder}/{pdf_name}", 
                    file_options={"contentType": "application/pdf", "upsert": "true"}
                )
        
        # 5. Storage Sync (Audio)
        mp3_path = f"output/{mp3_name}"
        if os.path.exists(mp3_path):
            print(f"[*] Uploading Audio to {portfolio_subfolder}...")
            with open(mp3_path, 'rb') as f:
                supabase.storage.from_('earnings-reports-audio').upload(
                    file=f, path=f"{portfolio_subfolder}/{mp3_name}", 
                    file_options={"contentType": "audio/mpeg", "upsert": "true"}
                )

        # 6. Database Sync
        script_path = mp3_path.replace(".mp3", ".txt")
        audio_script = None
        if os.path.exists(script_path):
            with open(script_path, "r", encoding="utf-8") as sf:
                audio_script = sf.read()

        update_payload = {
            "pdf_report_url": pdf_url,
            "audio_report_url": audio_url,
            "uploaded": True,
            "generated_at": "now()"
        }
        if audio_script:
            update_payload["audio_script"] = audio_script
            
        supabase.table("quarterly_earnings").update(update_payload).eq("id", record["id"]).execute()
        print(f"[OK] Completed {ticker}")

if __name__ == "__main__":
    run()
