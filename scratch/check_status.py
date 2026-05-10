import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

tickers = ["STVN.US", "ZEAL.CO", "UBER.US"]

print(f"{'Ticker':<10} | {'Status':<10} | {'MD Len':<10} | {'PDF URL'}")
print("-" * 60)

for ticker in tickers:
    res = supabase.table("quarterly_earnings").select("ticker_eod, review_status, markdown_content, pdf_report_url").eq("ticker_eod", ticker).execute()
    if res.data:
        rec = res.data[0]
        md_len = len(rec.get("markdown_content") or "")
        pdf_url = rec.get("pdf_report_url") or "None"
        print(f"{rec['ticker_eod']:<10} | {rec['review_status']:<10} | {md_len:<10} | {pdf_url[:40]}...")
    else:
        print(f"{ticker:<10} | NOT FOUND")
