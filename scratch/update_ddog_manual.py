import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

ticker = "DDOG.US"
period = "Q1 2026"
manual_text = """1. Datadog (DDOG) – Q1 2026 Earnings Review
Our Datadog 101 can be found here. It offers a condensed overview of the product suite, how they provide value and how they make money. We will be referencing products throughout the piece that are defined in this article.

a. Key Points
Added two more large AI model players as customers.
Non-AI revenue growth continues to accelerate.
Several new AI products were fully launched during the quarter.

b. Demand
Beat revenue estimate by 5% & beat guidance by 5.2%.
Beat billings estimate by 9%.
Beat net revenue retention estimate (NRR) by 2 points.

c. Profits
Missed 80.7% GPM estimate by 50 basis points (bps; 1 basis point = 0.01%).
Successful ramping of their new and lower-margin products is modestly weighing on GPM at the moment.
Beat EBIT estimate by 9.6% & beat guide by 11.5%.
Most of Datadog's AI-related spend is OpEx, not CapEx."""

def update_manual_ingestion():
    print(f"[*] Updating manual_ingestion for {ticker}...")
    try:
        res = supabase.table("quarterly_earnings").upsert({
            "ticker_eod": ticker,
            "fiscal_period": period,
            "manual_ingestion": manual_text
        }, on_conflict="ticker_eod,fiscal_period").execute()
        print(f"   [OK] Manual ingestion updated in Supabase.")
    except Exception as e:
        print(f"   [ERR] Failed to update: {e}")

if __name__ == "__main__":
    update_manual_ingestion()
