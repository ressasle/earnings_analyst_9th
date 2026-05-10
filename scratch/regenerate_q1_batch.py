import os
import time
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
import requests
import sys

# Import functions from data_completion_v1
sys.path.append(os.path.join(os.getcwd(), 'tools'))
from data_completion_v1 import synthesize_missing_data, get_eodhd_fundamentals

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
EODHD_API_KEY = os.getenv("EODHD_API_KEY")

if not all([SUPABASE_URL, SUPABASE_KEY, EODHD_API_KEY]):
    logger.error("Missing required API keys in .env")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

TICKERS = ["MRK.US", "BP.LSE", "LIFCO-B.ST", "UNP.US", "VIT-B.ST", "AI.PA", "DHR.US", "ISRG.US", "MMM.US", "NEE.US"]
FISCAL_PERIOD = "Q1 2026"

def ensure_q1_record(ticker):
    """Ensure a record exists for Q1 2026. If not, create a skeleton."""
    logger.info(f"Ensuring Q1 2026 record exists for {ticker}...")
    
    # Check if exists
    res = supabase.table("quarterly_earnings").select("id").eq("ticker_eod", ticker).eq("fiscal_period", FISCAL_PERIOD).execute()
    
    if res.data:
        logger.info(f"Record for {ticker} {FISCAL_PERIOD} already exists.")
        return res.data[0]
    
    # Create skeleton
    logger.info(f"Creating new record for {ticker} {FISCAL_PERIOD}...")
    
    # Fetch some basics from EODHD if possible
    url = f"https://eodhd.com/api/fundamentals/{ticker}?api_token={EODHD_API_KEY}&fmt=json"
    resp = requests.get(url)
    fundamentals = resp.json() if resp.status_code == 200 else {}
    
    company_name = ticker
    if fundamentals:
        company_name = fundamentals.get("General", {}).get("Name", ticker)
    
    data = {
        "ticker_eod": ticker,
        "company_name": company_name,
        "fiscal_period": FISCAL_PERIOD,
        "review_status": "pending",
        "status": "pending"
    }
    
    insert_res = supabase.table("quarterly_earnings").insert(data).execute()
    
    # If insert didn't return data, fetch it
    if not insert_res.data:
        res = supabase.table("quarterly_earnings").select("*").eq("ticker_eod", ticker).eq("fiscal_period", FISCAL_PERIOD).execute()
        return res.data[0]
        
    return insert_res.data[0]

def process_batch():
    report_data = []
    
    for ticker in TICKERS:
        try:
            row = ensure_q1_record(ticker)
            logger.info(f"Synthesizing data for {ticker}...")
            
            fundamentals = get_eodhd_fundamentals(ticker)
            synthetic_data = synthesize_missing_data(row, fundamentals)
            
            if synthetic_data:
                update_payload = {
                    "impact_score": synthetic_data.get("impact_score"),
                    "guidance_signal": synthetic_data.get("guidance_signal"),
                    "recommendation": synthetic_data.get("recommendation"),
                    "eps_actual": synthetic_data.get("eps_actual"),
                    "eps_estimate": synthetic_data.get("eps_estimate"),
                    "revenue_actual": synthetic_data.get("revenue_actual"),
                    "markdown_content": synthetic_data.get("markdown_content"),
                    "executive_summary": synthetic_data.get("executive_summary"),
                    "markdown_content_de": synthetic_data.get("markdown_content_de"),
                    "executive_summary_de": synthetic_data.get("executive_summary_de"),
                    "analysis_date": synthetic_data.get("analysis_date") or datetime.now().strftime("%Y-%m-%d"),
                    "review_status": "approved", # Directly to approved for orchestration
                    "status": "approved"
                }
                
                # Cleanup None values
                update_payload = {k: v for k, v in update_payload.items() if v is not None}
                
                supabase.table("quarterly_earnings").update(update_payload).eq("id", row['id']).execute()
                logger.info(f"Successfully updated and approved {ticker}.")
                
                report_data.append({
                    "ticker": ticker,
                    "impact": update_payload.get("impact_score"),
                    "rec": update_payload.get("recommendation"),
                    "guidance": update_payload.get("guidance_signal"),
                    "eps": update_payload.get("eps_actual"),
                    "rev": update_payload.get("revenue_actual")
                })
            else:
                logger.warning(f"Synthesis failed for {ticker}")
            
            # Rate limiting for Gemini (1 RPM)
            logger.info("Sleeping 70s to respect Gemini Free Tier rate limits...")
            time.sleep(70)
            
        except Exception as e:
            import traceback
            logger.error(f"Error processing {ticker}: {e}")
            logger.error(traceback.format_exc())
            
    # Save report data to a file for the final response
    with open('scratch/batch_report.json', 'w') as f:
        json.dump(report_data, f, indent=2)
    
    logger.info("Batch processing complete.")

if __name__ == "__main__":
    process_batch()
