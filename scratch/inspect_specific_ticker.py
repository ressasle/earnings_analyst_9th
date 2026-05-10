import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def inspect_ticker(ticker):
    print(f"\n--- {ticker} ---")
    res = supabase.table("kasona_company_reports").select("*").eq("ticker_eod", ticker).eq("skill_id", "quarterly_earnings").execute()
    for r in res.data:
        pdfs = r.get("quarterly_analysis_pdf_en", [])
        is_q1_2026 = any("Q1 2026" in p.get("label", "") for p in pdfs) if pdfs else False
        print(f"ID: {r['id']}, Created: {r['created_at']}, Q1_2026: {is_q1_2026}, PDF: {pdfs}")

if __name__ == "__main__":
    inspect_ticker("MRK.US")
