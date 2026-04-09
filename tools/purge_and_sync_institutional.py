#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not all([SUPABASE_URL, SUPABASE_KEY]):
    print("[ERR] Missing Supabase credentials.")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"

PDF_BUCKET   = "earnings-reports-pdf"
AUDIO_BUCKET = "earnings-reports-audio"
TARGET_FOLDERS = ['991001-SA', '991001-PEP', '991001-IPO']

def purge_folder(bucket, folder):
    print(f"  Purging bucket '{bucket}' folder '{folder}'...")
    try:
        # 1. List files
        res = supabase.storage.from_(bucket).list(folder)
        if not res:
            print(f"    No files found in {folder}.")
            return
        
        file_names = [f['name'] for f in res if f['name'] != '.emptyKeep']
        if not file_names:
            print(f"    Folder {folder} is already clean.")
            return

        # 2. Remove files
        paths = [f"{folder}/{name}" for name in file_names]
        supabase.storage.from_(bucket).remove(paths)
        print(f"    [OK] Deleted {len(paths)} files from {folder}.")
    except Exception as e:
        print(f"    [ERR] Purge failed for {folder}: {e}")

def upload_artifact(file_path, bucket, folder):
    storage_path = f"{folder}/{file_path.name}"
    content_type = "application/pdf" if file_path.suffix == ".pdf" else "audio/mpeg"
    try:
        with open(file_path, "rb") as f:
            supabase.storage.from_(bucket).upload(
                path=storage_path,
                file=f,
                file_options={"upsert": "true", "content-type": content_type}
            )
        return f"{SUPABASE_URL}/storage/v1/object/public/{bucket}/{storage_path}"
    except Exception as e:
        print(f"      [ERR] Upload failed for {file_path.name}: {e}")
        return None

def main():
    print("=== Institutional Purge and Sync (Atomic Match 31st) ===")
    
    # 1. Atomic Purge
    for folder in TARGET_FOLDERS:
        purge_folder(PDF_BUCKET, folder)
        purge_folder(AUDIO_BUCKET, folder)

    # 2. Re-Sync based on Ticker Mapping
    print("\n--- Re-syncing 31st Artifacts ---")
    tickers_res = supabase.table("kasona_portfolio_assets").select("ticker_eod, portfolio_id").in_("portfolio_id", TARGET_FOLDERS).execute()
    
    success_count = 0
    for item in tickers_res.data:
        ticker = item['ticker_eod']
        folder = item['portfolio_id']
        safe = ticker.replace("/", "-")
        # Handle PRIVATE prefix mismatch (e.g. PRIVATE.OPENAI -> OPENAI)
        clean_safe = safe.replace("PRIVATE.", "")
        
        pdf_file   = OUTPUT_DIR / f"{safe}_earnings.pdf"
        if not pdf_file.exists(): pdf_file = OUTPUT_DIR / f"{clean_safe}_earnings.pdf"
        
        audio_file = OUTPUT_DIR / f"{safe}_audio.mp3"
        if not audio_file.exists(): audio_file = OUTPUT_DIR / f"{clean_safe}_audio.mp3"
        
        if pdf_file.exists() and audio_file.exists():
            print(f"  [{ticker}] Uploading fresh artifacts to {folder}...")
            pdf_url = upload_artifact(pdf_file, PDF_BUCKET, folder)
            audio_url = upload_artifact(audio_file, AUDIO_BUCKET, folder)
            
            if pdf_url and audio_url:
                # Try updating with original ticker (PRIVATE.OPENAI)
                res_upd = supabase.table("quarterly_earnings").update({
                    "pdf_report_url": pdf_url, 
                    "audio_report_url": audio_url,
                    "investor_profile": folder,
                    "generated_at": "now()"
                }).eq("ticker_eod", ticker).execute()
                
                # If no rows updated, try with clean_safe (OPENAI)
                if not res_upd.data:
                    supabase.table("quarterly_earnings").update({
                        "pdf_report_url": pdf_url, 
                        "audio_report_url": audio_url,
                        "investor_profile": folder,
                        "generated_at": "now()"
                    }).eq("ticker_eod", clean_safe).execute()
                
                success_count += 1
        else:
            print(f"  [{ticker}] SKIP: Missing local files for {safe}")

    print(f"\nDONE -- Re-synced {success_count} tickers to 31st state.")

if __name__ == "__main__":
    main()
