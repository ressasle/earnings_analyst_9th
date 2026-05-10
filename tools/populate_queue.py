import argparse
import sys
from utils.supabase_client import get_supabase_client

def populate_queue(tickers, language='en', priority=1):
    supabase = get_supabase_client()
    
    entries = []
    for ticker in tickers:
        entries.append({
            "ticker": ticker,
            "status": "pending",
            "language": language,
            "priority": priority
        })
    
    if not entries:
        print("[!] No tickers provided.")
        return

    print(f"[*] Adding {len(entries)} tickers to analysis_queue...")
    try:
        res = supabase.table("analysis_queue").insert(entries).execute()
        if res.data:
            print(f"[OK] Successfully added {len(res.data)} items to queue.")
        else:
            print("[!] Insertion failed, no data returned.")
    except Exception as e:
        print(f"[ERR] Failed to populate queue: {e}")

def main():
    parser = argparse.ArgumentParser(description="Populate the Kasona Analysis Queue")
    parser.add_argument("--tickers", required=True, help="Comma-separated list of tickers")
    parser.add_argument("--lang", default="en", choices=["en", "de"], help="Target language (en/de)")
    parser.add_argument("--priority", type=int, default=1, help="Processing priority (higher = sooner)")
    
    args = parser.parse_args()
    
    ticker_list = [t.strip() for t in args.tickers.split(",") if t.strip()]
    populate_queue(ticker_list, language=args.lang, priority=args.priority)

if __name__ == "__main__":
    main()
