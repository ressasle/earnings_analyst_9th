
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def check_ddog():
    res = supabase.table("quarterly_earnings")\
        .select("*")\
        .eq("ticker_eod", "DDOG.US")\
        .eq("fiscal_period", "Q1 2026")\
        .execute()
    print(res.data)

if __name__ == "__main__":
    check_ddog()
