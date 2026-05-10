import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

tickers = ["STVN.US", "ZEAL.CO", "UBER.US"]

print(f"{'Ticker':<10} | {'PDF':<5} | {'HTML':<5} | {'Audio':<5}")
print("-" * 40)

for ticker in tickers:
    res = supabase.table("quarterly_earnings").select("ticker_eod, pdf_report_url, html_report_url, audio_report_url").eq("ticker_eod", ticker).execute()
    if res.data:
        rec = res.data[0]
        pdf = "YES" if rec.get("pdf_report_url") else "NO"
        html = "YES" if rec.get("html_report_url") else "NO"
        audio = "YES" if rec.get("audio_report_url") else "NO"
        print(f"{rec['ticker_eod']:<10} | {pdf:<5} | {html:<5} | {audio:<5}")
