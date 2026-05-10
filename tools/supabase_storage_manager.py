#!/usr/bin/env python3
"""
supabase_storage_manager.py — Uploads earnings reports to Supabase Storage

Handles:
1. Uploading PDF and MP3 files to Supabase Storage buckets.
2. Generating public URLs for the uploaded files.
3. Updating the 'quarterly_earnings' table with the file URLs.

Usage:
    python3 tools/supabase_storage_manager.py --file output/AAPL_Q4_2025_earnings.pdf --bucket earnings-reports-pdf --ticker AAPL.US --quarter Q4 --year 2025
"""

import argparse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure project root is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.supabase_client import get_supabase_client

# Load environment variables from .env file
load_dotenv()

# Centralized configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://nayggiozebvwqnpjzvvn.supabase.co")

def upload_file(file_path: Path, bucket_name: str, ticker_eod: str, quarter: str, year: str) -> str:
    """
    Uploads a file to Supabase Storage and returns the public URL.
    """
    supabase = get_supabase_client()
    
    # Naming convention: {ticker_eod}/{quarter}_{fiscal_year}_{filename}
    file_name = file_path.name
    storage_path = f"{ticker_eod}/{quarter}_{year}_{file_name}"

    print(f"[*] Uploading {file_name} to bucket '{bucket_name}' as '{storage_path}'...")
    
    with open(file_path, 'rb') as f:
        # Note: In recent supabase-py/storage3, upsert should be a string "true" 
        # but passed in a dict that httpx can handle (headers must be strings).
        # We'll try the standard 'upsert' key which storage3 should map to 'x-upsert'.
        opts = {"upsert": "true"}
        if file_path.suffix.lower() == ".pdf":
            opts["content-type"] = "application/pdf"
        elif file_path.suffix.lower() == ".mp3":
            opts["content-type"] = "audio/mpeg"
        elif file_path.suffix.lower() == ".html":
            opts["content-type"] = "text/html"

        response = supabase.storage.from_(bucket_name).upload(
            path=storage_path,
            file=f,
            file_options=opts
        )

    # In supabase-py, the public URL can be constructed or fetched
    # Konstruiere die Public URL manuell (standard Supabase pattern)
    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{storage_path}"
    print(f"[OK] Uploaded successfully. Public URL: {public_url}")
    return public_url

def update_queue_status(ticker: str, status: str = 'completed'):
    """
    Updates the status of the latest pending request in analysis_queue for a ticker.
    """
    supabase = get_supabase_client()
    
    # We want to match the ticker root (e.g., AAPL) or full ticker (AAPL.US)
    ticker_root = ticker.split('.')[0]
    
    print(f"[*] Updating analysis_queue for {ticker} (root: {ticker_root}) to status '{status}'...")
    
    try:
        # Try finding entries for both root and full ticker, prioritizing pending ones
        for search_term in [ticker, ticker_root]:
            response = supabase.table("analysis_queue") \
                .select("id") \
                .eq("ticker", search_term) \
                .eq("status", "pending") \
                .order("created_at", desc=True) \
                .limit(1) \
                .execute()
                
            if response.data:
                queue_id = response.data[0]['id']
                supabase.table("analysis_queue").update({"status": status}).eq("id", queue_id).execute()
                print(f"[OK] Queue item {queue_id} marked as {status}.")
                return

        print(f"[WARN] No pending queue item found for ticker '{ticker}' or '{ticker_root}'.")
    except Exception as e:
        print(f"[ERR] Error updating queue status: {e}")

def update_database(ticker_eod: str, quarter: str, year: str, pdf_url: str = None, audio_url: str = None, html_url: str = None):
    """
    Updates the quarterly_earnings table with the report URLs.
    """
    supabase = get_supabase_client()
    
    update_data = {}
    if pdf_url:
        update_data["pdf_report_url"] = pdf_url
    if audio_url:
        update_data["audio_report_url"] = audio_url
    if html_url:
        update_data["html_report_url"] = html_url

    if not update_data:
        return

    print(f"[*] Updating database for {ticker_eod} ({quarter} {year})...")
    
    # Try to update the record. Unique constraint is on (ticker_eod, quarter, fiscal_year)
    try:
        response = supabase.table("quarterly_earnings").update(update_data).match({
            "ticker_eod": ticker_eod,
            "quarter": quarter,
            "fiscal_year": int(year)
        }).execute()
        
        if len(response.data) > 0:
            print(f"[OK] Database updated successfully.")
        else:
            print(f"[WARN] No matching record found in 'quarterly_earnings' to update.")
    except Exception as e:
        print(f"[ERR] Error updating database: {e}")

def main():
    parser = argparse.ArgumentParser(description="Supabase Storage Manager for Earnings Reports")
    parser.add_argument("--file", required=True, help="Path to the file to upload")
    parser.add_argument("--bucket", required=True, choices=["earnings-reports-pdf", "earnings-reports-audio", "earnings-reports-html"], help="Target bucket")
    parser.add_argument("--ticker", required=True, help="Ticker (SYMBOL.EXCHANGE)")
    parser.add_argument("--quarter", required=True, help="Quarter (e.g., Q1, FY)")
    parser.add_argument("--year", required=True, help="Fiscal Year (e.g., 2025)")
    parser.add_argument("--update-db", action="store_true", help="Update the database record with the URL")
    parser.add_argument("--update-queue", action="store_true", help="Mark the analysis_queue item as completed")

    args = parser.parse_args()
    file_path = Path(args.file)
    
    if not file_path.exists():
        print(f"[ERR] File not found: {file_path}")
        sys.exit(1)

    try:
        public_url = upload_file(file_path, args.bucket, args.ticker, args.quarter, args.year)
        
        if args.update_db:
            if args.bucket == "earnings-reports-pdf":
                update_database(args.ticker, args.quarter, args.year, pdf_url=public_url)
            elif args.bucket == "earnings-reports-audio":
                update_database(args.ticker, args.quarter, args.year, audio_url=public_url)
            elif args.bucket == "earnings-reports-html":
                update_database(args.ticker, args.quarter, args.year, html_url=public_url)
        
        if args.update_queue:
            # We only do this once, typically after the last artifact is uploaded
            update_queue_status(args.ticker, status='completed')
                
    except Exception as e:
        print(f"[ERR] Error during upload process: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
