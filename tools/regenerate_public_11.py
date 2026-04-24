import os
import subprocess
import json
from pathlib import Path
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: SUPABASE_URL or SUPABASE_KEY not found in .env")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

PUBLIC_TICKERS = [
    "AI.PA", "DHR.US", "ISRG.US", "MMM.US", "NFLX.US",
    "LONN.SW", "VACN.SW", "ASML.AS", "MC.PA", "RMS.PA", "SIKA.SW"
]

TEMP_DIR = Path("temp_reports")
OUTPUT_DIR = Path("final_artifacts")
TEMP_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

TOOLS_DIR = Path("tools")
HTML_SCRIPT = TOOLS_DIR / "generate_earnings_html.py"
PDF_SCRIPT = TOOLS_DIR / "generate_earnings_pdf.py"
AUDIO_SCRIPT = TOOLS_DIR / "generate_audio.py"

def process_ticker(ticker):
    print(f"\n[Processing {ticker}]")
    
    # Fetch from Supabase
    result = supabase.table("quarterly_earnings").select("*").ilike("ticker_eod", f"%{ticker}%").order("created_at", desc=True).limit(1).execute()
    
    if not result.data:
        print(f"  [Error] No record found for {ticker}")
        return

    row = result.data[0]
    md_content = row.get("markdown_content")
    company_name = row.get("company_name")
    fiscal_period = f"{row.get('quarter', 'Q1')} {row.get('fiscal_year', '2026')}"
    impact_score = row.get("impact_score", "N/A")
    recommendation = row.get("recommendation", "N/A")

    if not md_content:
        print(f"  [Error] No markdown content for {ticker}")
        return

    # Save temp MD file
    safe_ticker = ticker.replace(".", "_")
    md_file = TEMP_DIR / f"{safe_ticker}_report.md"
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(md_content)

    # 1. Generate HTML
    print("  [HTML] Generating...")
    subprocess.run([
        "python", str(HTML_SCRIPT), str(md_file),
        "--ticker", ticker,
        "--output-dir", str(OUTPUT_DIR)
    ], check=False)

    # 2. Generate PDF
    print("  [PDF] Generating...")
    subprocess.run([
        "python", str(PDF_SCRIPT), str(md_file),
        "--ticker", ticker,
        "--output-dir", str(OUTPUT_DIR)
    ], check=False)

    # 3. Generate Audio
    print("  [Audio] Generating...")
    audio_output = OUTPUT_DIR / f"{safe_ticker}_briefing.mp3"
    subprocess.run([
        "python", str(AUDIO_SCRIPT),
        "--script", str(md_file),
        "--company", company_name,
        "--output", str(audio_output),
        "--ticker-eod", ticker,
        "--fiscal-period", fiscal_period,
        "--impact-score", str(impact_score),
        "--recommendation", recommendation,
        "--voice", "en-US-ChristopherNeural"
    ], check=False)

def main():
    for ticker in PUBLIC_TICKERS:
        process_ticker(ticker)
    
    print("\n[Done] All reports processed.")
    print(f"Check {OUTPUT_DIR.resolve()} for output files.")

if __name__ == "__main__":
    main()
