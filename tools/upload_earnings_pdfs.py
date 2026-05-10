#!/usr/bin/env python3
"""
Upload earnings PDFs to Supabase storage bucket and update DB records.
Usage: python upload_earnings_pdfs.py --ticker STVN.US --pdf /path/to/report.pdf --period "Q1 2026"
"""
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not all([SUPABASE_URL, SUPABASE_KEY]):
    print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY environment variables.")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

BUCKET = "earnings-reports-pdf"


def upload_pdf(ticker: str, pdf_path: Path, period: str):
    # Construct storage path: TICKER/Q1_2026_TICKER_Q1_2026_earnings.pdf
    period_slug = period.replace(" ", "_")
    ticker_slug = ticker.replace(".", "_")
    storage_filename = f"{period_slug}_{ticker_slug}_{period_slug}_earnings.pdf"
    storage_path = f"{ticker}/{storage_filename}"

    print(f"[*] Uploading {pdf_path.name} -> {BUCKET}/{storage_path}")

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    try:
        # Try upload, upsert if exists
        res = supabase.storage.from_(BUCKET).upload(
            path=storage_path,
            file=pdf_bytes,
            file_options={"content-type": "application/pdf", "upsert": "true"}
        )
        print(f"   [OK] Upload successful.")
    except Exception as e:
        print(f"   [ERR] Upload failed: {e}")
        return None

    # Build public URL
    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{storage_path}"
    print(f"   [URL] {public_url}")

    # Update quarterly_earnings table
    try:
        update_res = supabase.table("quarterly_earnings").update({
            "pdf_report_url": public_url,
            "review_status": "approved",
            "updated_at": datetime.now().isoformat()
        }).eq("ticker_eod", ticker).eq("fiscal_period", period).execute()
        
        if update_res.data:
            print(f"   [DB] quarterly_earnings updated for {ticker} / {period}")
        else:
            print(f"   [DB] No row matched for {ticker} / {period} — inserting stub...")
            supabase.table("quarterly_earnings").upsert({
                "ticker_eod": ticker,
                "fiscal_period": period,
                "pdf_report_url": public_url,
                "review_status": "approved",
                "updated_at": datetime.now().isoformat()
            }, on_conflict="ticker_eod,fiscal_period").execute()
            print(f"   [DB] Upserted stub record.")
    except Exception as e:
        print(f"   [ERR] DB update failed: {e}")

    return public_url


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload earnings PDF to Supabase storage")
    parser.add_argument("--ticker", required=True, help="Ticker symbol, e.g. STVN.US")
    parser.add_argument("--pdf", required=True, help="Path to the PDF file")
    parser.add_argument("--period", default="Q1 2026", help="Fiscal period label")
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        sys.exit(1)

    url = upload_pdf(args.ticker, pdf_path, args.period)
    if url:
        print(f"\n[OK] Done. Public URL:\n   {url}")
    else:
        print("\n[FAIL] Upload failed.")
        sys.exit(1)
