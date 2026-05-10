import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

TICKERS = ["MRK.US", "BP.LSE", "LIFCO-B.ST", "UNP.US", "VIT-B.ST", "AI.PA", "DHR.US", "ISRG.US", "MMM.US", "NEE.US"]
FISCAL_PERIOD = "Q1 2026"

def check_dups():
    print(f"--- quarterly_earnings ---")
    print(f"{'Ticker':<15} | {'Count':<5} | {'IDs'}")
    print("-" * 50)
    for ticker in TICKERS:
        res = supabase.table("quarterly_earnings").select("id").eq("ticker_eod", ticker).eq("fiscal_period", FISCAL_PERIOD).execute()
        ids = [r['id'] for r in res.data]
        print(f"{ticker:<15} | {len(ids):<5} | {ids}")

    print(f"\n--- kasona_company_reports (Skill: quarterly_earnings) ---")
    print(f"{'Ticker':<15} | {'Count':<5} | {'IDs'}")
    print("-" * 50)
    for ticker in TICKERS:
        res = supabase.table("kasona_company_reports").select("id, quarterly_analysis_pdf_en").eq("ticker_eod", ticker).eq("skill_id", "quarterly_earnings").execute()
        # Filter for Q1 2026 in labels
        ids = []
        for r in res.data:
            pdfs = r.get("quarterly_analysis_pdf_en", [])
            if pdfs and any(FISCAL_PERIOD in p.get("label", "") for p in pdfs):
                ids.append(r['id'])
        print(f"{ticker:<15} | {len(ids):<5} | {ids}")

if __name__ == "__main__":
    check_dups()
