import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def inspect_duplicates(company_name):
    print(f"\n--- {company_name} ---")
    res = supabase.table("quarterly_earnings").select("id, ticker_eod, company_name, fiscal_period, created_at, markdown_content, pdf_report_url").ilike("company_name", company_name).execute()
    for d in res.data:
        print(f"ID: {d['id']}, Ticker: {d['ticker_eod']}, Period: {d['fiscal_period']}, Created: {d['created_at']}, MD: {bool(d['markdown_content'])}, PDF: {bool(d['pdf_report_url'])}")

if __name__ == "__main__":
    inspect_duplicates("Snowflake Inc.")
    inspect_duplicates("BP PLC")
    inspect_duplicates("Danaher Corp")
