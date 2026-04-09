import os
import subprocess
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_company_name(ticker):
    parts = ticker.split(".")
    return parts[0] if len(parts) > 0 else ticker

def run():
    print("[*] Fetching phase 1 tickers...")
    res = supabase.table("kasona_portfolio_assets").select("ticker, portfolio_id").in_("portfolio_id", ["991001-IPO", "991001-PEP", "991001-SA"]).execute()
    tickers_in_99 = [r["ticker"] for r in res.data]

    res2 = supabase.table("quarterly_earnings").select("*").eq("review_status", "approved").in_("investor_profile", ["991001-SA", "991001-IPO", "991001-PEP"]).execute()
    records = res2.data
    # Optionally filter further if specific lists are needed, for now we process the whole 99 cohort

    print(f"[*] Found {len(records)} outstanding records in the 99 portfolios matching target list.")
    
    for r in records:
        ticker = r["ticker_eod"]
        company = get_company_name(ticker)
        print(f"\n[*] Generating {ticker}...")
        
        md_file = f"output/{ticker}_earnings.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(r["markdown_content"])
        
        # Pre-calculate URLs for branding
        portfolio_subfolder = [p['portfolio_id'] for p in res.data if p['ticker'] == ticker][0]
        pdf_name = f"{ticker}_earnings.pdf"
        pdf_url = f"{SUPABASE_URL}/storage/v1/object/public/earnings-reports-pdf/{portfolio_subfolder}/{pdf_name}"
        mp3_name = f"{ticker}_audio.mp3"
        audio_url = f"{SUPABASE_URL}/storage/v1/object/public/earnings-reports-audio/{portfolio_subfolder}/{mp3_name}"

        subprocess.run([
            "python", "tools/generate_earnings_html.py", md_file
        ], check=False)
        subprocess.run([
            "python", "tools/generate_earnings_pdf.py", md_file, "--ticker", ticker
        ], check=False)
        subprocess.run([
            "python", "tools/generate_audio.py", 
            "--script", md_file, 
            "--company", company, 
            "--ticker-eod", ticker,
            "--pdf-url", pdf_url,
            "--audio-url", audio_url,
            "--fiscal-period", r.get("fiscal_period", "Q4 2025"),
            "--impact-score", str(r.get("impact_score", "N/A")),
            "--recommendation", str(r.get("recommendation", "N/A")),
            "--output", f"output/{mp3_name}"
        ], check=False)
        
        pdf_path = f"output/{pdf_name}"
        sp_path = f"{portfolio_subfolder}/{pdf_name}"
        
        print(f"[*] Syncing {pdf_path} to {sp_path}")
        with open(pdf_path, 'rb') as f:
            supabase.storage.from_('earnings-reports-pdf').upload(file=f, path=sp_path, file_options={"contentType": "application/pdf", "upsert": "true"})
        
        mp3_path = f"output/{mp3_name}"
        mp3_sp_path = f"{portfolio_subfolder}/{mp3_name}"
        print(f"[*] Syncing {mp3_path} to {mp3_sp_path}")
        with open(mp3_path, 'rb') as f:
            supabase.storage.from_('earnings-reports-audio').upload(file=f, path=mp3_sp_path, file_options={"contentType": "audio/mpeg", "upsert": "true"})

        # Read the generated audit script
        audio_script = None
        script_path = mp3_path.replace(".mp3", ".txt")
        if os.path.exists(script_path):
            with open(script_path, "r", encoding="utf-8") as sf:
                audio_script = sf.read()

        update_data = {
            "pdf_report_url": pdf_url, 
            "audio_report_url": audio_url, 
            "uploaded": True,
            "generated_at": "now()"
        }
        if audio_script:
            update_data["audio_script"] = audio_script

        supabase.table("quarterly_earnings").update(update_data).eq("id", r["id"]).execute()
        print(f"[OK] DONE {ticker}")
        
if __name__ == "__main__":
    run()
