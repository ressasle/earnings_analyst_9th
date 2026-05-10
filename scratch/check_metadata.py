import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

tickers = ["STVN.US", "ZEAL.CO"]

for ticker in tickers:
    res = supabase.table("quarterly_earnings").select("*").eq("ticker_eod", ticker).execute()
    if res.data:
        rec = res.data[0]
        print(f"--- {ticker} ---")
        for k in ["fiscal_period", "quarter", "fiscal_year", "company_name", "review_status"]:
            print(f"{k}: {rec.get(k)}")
