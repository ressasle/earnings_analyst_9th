import os
import re
import sys
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not all([SUPABASE_URL, SUPABASE_KEY]):
    print("❌ Missing Supabase credentials.")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

PORTFOLIOS = ["991001-SA", "991001-IPO", "991001-PEP"]
FISCAL_PERIOD = "Q4 2025"

def extract_summary(md):
    if not md: return None
    # Look for Section 1
    match = re.search(r'## 1\.\s+(?:STRATEGIC\s+)?EXECUTIVE SUMMARY\s*\n+(.*?)(?=\n\n|\n##|$)', md, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # Fallback to first paragraph
    paragraphs = [p for p in md.split('\n\n') if p.strip() and not p.startswith('#')]
    if paragraphs:
        return paragraphs[0].strip()
    return None

def main():
    print(f"[*] Preparing reports for portfolios {PORTFOLIOS} ({FISCAL_PERIOD})...")
    
    for PORTFOLIO_ID in PORTFOLIOS:
        print(f"\n[*] Processing portfolio: {PORTFOLIO_ID}")
        # 1. Fetch tickers in portfolio
        res_assets = supabase.table("kasona_portfolio_assets").select("ticker_eod").eq("portfolio_id", PORTFOLIO_ID).execute()
        tickers = [r["ticker_eod"] for r in res_assets.data]
        
        if not tickers:
            print(f"[-] No tickers found for {PORTFOLIO_ID}.")
            continue

        # 2. Fetch quarterly earnings records
        res_reports = supabase.table("quarterly_earnings").select("*").in_("ticker_eod", tickers).eq("fiscal_period", FISCAL_PERIOD).execute()
        
        for record in res_reports.data:
            ticker = record["ticker_eod"]
            md = record.get("markdown_content")
            summary = record.get("executive_summary")
            
            updates = {
                "review_status": "approved"
            }
            
            # Reset uploaded if it was set to true earlier but we are reprocessing
            # Or if it's false, we keep it false.
            if record.get("uploaded") is True:
                 updates["uploaded"] = False
            
            if not summary and md:
                extracted = extract_summary(md)
                if extracted:
                    print(f"[*] Extracted summary for {ticker}")
                    updates["executive_summary"] = extracted
            
            supabase.table("quarterly_earnings").update(updates).eq("id", record["id"]).execute()
            print(f"[OK] {ticker} ({PORTFOLIO_ID}) marked as approved.")

if __name__ == "__main__":
    main()
