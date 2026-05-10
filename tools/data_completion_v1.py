import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
import google.generativeai as genai
import requests

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

# API Keys
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
EODHD_API_KEY = os.getenv("EODHD_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not all([SUPABASE_URL, SUPABASE_KEY, EODHD_API_KEY, GEMINI_API_KEY]):
    logger.error("Missing required API keys in .env")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
genai.configure(api_key=GEMINI_API_KEY)

def fetch_missing_entries():
    """Fetch rows from quarterly_earnings that need completion or translation."""
    logger.info("Fetching entries requiring replenishment or translation...")
    # Fetch rows where critical data is missing or translation columns are NULL
    # Using multiple OR conditions for flexibility
    query = supabase.table("quarterly_earnings").select("*").or_(
        "review_status.eq.pending,"
        "eps_actual.is.null,"
        "revenue_actual.is.null,"
        "markdown_content.is.null,"
        "markdown_content_de.is.null"
    )
    response = query.execute()
    return response.data





def get_eodhd_fundamentals(ticker):
    """Fetch fundamentals from EODHD."""
    url = f"https://eodhd.com/api/fundamentals/{ticker}?api_token={EODHD_API_KEY}&fmt=json"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

def get_eodhd_earnings(ticker):
    """Fetch specific earnings history from EODHD."""
    url = f"https://eodhd.com/api/calendar/earnings?api_token={EODHD_API_KEY}&symbols={ticker}&fmt=json"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

def synthesize_missing_data(row, fundamentals=None):
    """Use Gemini to infer missing fields and translate content to German."""
    model = genai.GenerativeModel('models/gemini-flash-latest')
    
    ticker = row.get('ticker_eod')
    current_content = row.get('markdown_content') or ''
    company_name = row.get('company_name', ticker)
    
    safe_fundamentals = {}
    if fundamentals:
        safe_fundamentals = {
            "General": fundamentals.get("General", {}),
            "Highlights": fundamentals.get("Highlights", {}),
            "Valuation": fundamentals.get("Valuation", {})
        }
    
    prompt = f"""
    You are a Senior Strategic Financial Analyst and Translator. 
    Analyze the following data for {company_name} ({ticker}).
    
    Existing Report Context: {current_content[:1000]}...
    Fundamental Data: {json.dumps(safe_fundamentals) if safe_fundamentals else 'Not available'}
    
    CRITICAL INSTRUCTIONS:
    - DO NOT use generic boilerplate like "Compounder thesis" or "Institutional analysis" unless it's strictly supported by recent data.
    - Be HIGHLY SPECIFIC to {company_name}'s recent performance, sector tailwinds, and risks.
    - Ensure the logic flows from the provided fundamentals (Valuation, Highlights).
    - If specific earnings metrics (EPS, Revenue) are in the fundamentals, use them accurately.
    
    Tasks:
    1. Determine a 1-100 Impact Score (influence on sector).
    2. Suggest a Guidance Signal (Positive, Negative, Neutral).
    3. Suggest a Recommendation (Buy, Sell, Hold, Accumulate, Strategic Buy).
    4. Provide financial metrics: eps_actual, eps_estimate, and revenue_actual (in millions/billions as appropriate).
    5. Write/Complete the 'markdown_content' (detailed professional logic summary, 600 words). Focus on strategic shifts, margins, and competitive positioning.
    6. Write a concise 'executive_summary' (main takeaways, 100 words).
    7. TRANSLATE tasks 5 and 6 into German for 'markdown_content_de' and 'executive_summary_de'.
    
    Return ONLY a JSON object with:
    {{
        "impact_score": int,
        "guidance_signal": "string",
        "recommendation": "string",
        "eps_actual": float,
        "eps_estimate": float,
        "revenue_actual": float,
        "markdown_content": "string",
        "executive_summary": "string",
        "markdown_content_de": "string",
        "executive_summary_de": "string",
        "analysis_date": "YYYY-MM-DD"
    }}
    """
    
    retries = 3
    for i in range(retries):
        try:
            response = model.generate_content(prompt)
            text = response.text.strip()
            if "{" in text and "}" in text:
                start = text.find("{")
                end = text.rfind("}") + 1
                json_str = text[start:end]
                return json.loads(json_str)
        except Exception as e:
            if "429" in str(e):
                wait_time = (i + 1) * 60 # Slower retry for batching
                logger.warning(f"Rate limit hit for {ticker}. Waiting {wait_time}s... (Attempt {i+1}/{retries})")
                logger.error(f"Full 429 Error: {e}")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to generate/parse Gemini response for {ticker}: {e}")
                break
    return None


import time

def replenish_data(limit=5):
    entries = fetch_missing_entries()
    logger.info(f"Found {len(entries)} entries requiring replenishment. Processing {min(limit, len(entries))}...")
    
    for row in entries[:limit]:
        ticker = row['ticker_eod']
        logger.info(f"Processing {ticker}...")
        
        fundamentals = None
        if ".US" in ticker or ".SW" in ticker or ".ST" in ticker or ".HE" in ticker:
            fundamentals = get_eodhd_fundamentals(ticker)
            
        synthetic_data = synthesize_missing_data(row, fundamentals)
        
        if synthetic_data:
            try:
                # Merge existing row data with synthetic data
                update_payload = {
                    "impact_score": synthetic_data.get("impact_score") or row.get("impact_score"),
                    "guidance_signal": synthetic_data.get("guidance_signal") or row.get("guidance_signal"),
                    "recommendation": synthetic_data.get("recommendation") or row.get("recommendation"),
                    "eps_actual": synthetic_data.get("eps_actual") or row.get("eps_actual"),
                    "eps_estimate": synthetic_data.get("eps_estimate") or row.get("eps_estimate"),
                    "revenue_actual": synthetic_data.get("revenue_actual") or row.get("revenue_actual"),
                    "markdown_content": synthetic_data.get("markdown_content") or row.get("markdown_content"),
                    "executive_summary": synthetic_data.get("executive_summary") or row.get("executive_summary"),
                    "markdown_content_de": synthetic_data.get("markdown_content_de") or row.get("markdown_content_de"),
                    "executive_summary_de": synthetic_data.get("executive_summary_de") or row.get("executive_summary_de"),
                    "analysis_date": synthetic_data.get("analysis_date") or row.get("analysis_date") or datetime.now().strftime("%Y-%m-%d"),
                    "review_status": "reviewed"
                }
                
                update_payload = {k: v for k, v in update_payload.items() if v is not None}
                
                res = supabase.table("quarterly_earnings").update(update_payload).eq("ticker_eod", ticker).execute()
                logger.info(f"Updated {ticker} in Supabase with status 'reviewed'.")
            except Exception as e:
                logger.error(f"Failed to update Supabase for {ticker}: {e}")
        else:
            logger.warning(f"Skipping {ticker} due to synthesis failure.")
        
        # Throttling to avoid 429 (Gemini Free Tier is often 1 RPM)
        time.sleep(70) 


if __name__ == "__main__":
    # Remove limit or set to a high number for full batch
    # Given the 1 RPM limit, we might want to run in chunks or just let it run.
    # Total rows: ~336. 336 * 70s = ~6.5 hours.
    replenish_data(limit=500)

