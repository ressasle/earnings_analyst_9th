import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

tickers = ["STVN.US", "ZEAL.CO", "UBER.US"]

for ticker in tickers:
    print(f"\n--- {ticker} ---")
    res = supabase.table("quarterly_earnings").select("fiscal_period, review_status, markdown_content, created_at").eq("ticker_eod", ticker).execute()
    for row in res.data:
        md_len = len(row.get('markdown_content') or "")
        print(f"Period: {row['fiscal_period']} | Status: {row['review_status']} | MD Length: {md_len} | Created: {row['created_at']}")
