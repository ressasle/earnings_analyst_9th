import os
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Corporate Tickers (84 Total)
TICKERS_99 = [
    "KLAR", "DATABRICKS", "DISCORD", "ANDURIL", "DEEL", "KRAKEN", "DESN.SW", "QXO.US", "VIT-B.ST", "REVOLUT", 
    "STRIPE", "CEREBRAS", "ARENIT.ST", "ANTHROPIC", "CANVA", "OPENAI", "MMGR-B.ST", "1SXP.DE", "YPSN.SW", "SPACEX", 
    "BERG-B.ST", "NVO.US", "BOREO.HE", "HLMA.LSE", "BANB.SW", "SFT.LSE", "ADDT-B.ST", "INDT.ST", "ASPO.HE", 
    "BRO.US", "DHR.US", "BRK-B.US", "BNZL.LSE", "CSU.TO", "LAGR-B.ST", "LLY.US", "ROVI.MC", "MEDP.US", 
    "ZEAL.CO", "LIFCO-B.ST", "STVN.US", "ASKER.ST", "ROKO-B.ST", "PPGN.SW", "ROP.US", "HIMS.US", "IMCD.AS", "WST.US"
]
TICKERS_GLOBAL = [
    "AAPL.US", "AMZN.US", "GOOGL.US", "MSFT.US", "META.US", "NVDA.US", "INTC.US", "TSLA.US", "NFLX.US", "CRM.US", 
    "PLTR.US", "UBER.US", "AMD.US", "ADDV-B.ST", "ALIF-B.ST", "BICO.ST", "COIC.ST", "HUM7.ST", "LATO-B.ST", 
    "NIMB.ST", "SBB-B.ST", "SF.ST", "STEV.ST", "TECO.ST", "VESTUM.ST", "VNV.ST", "VOLO.ST", "ASML.AS", "BEI.DE", 
    "BP.US", "DBSDY.US", "GIVN.SW", "MOVE.SW", "VNA.XETRA", "DIS.US", "NVO"
]
ALL_CORP = set(TICKERS_99 + TICKERS_GLOBAL)

def run_final_audit():
    print(f"[*] STARTING FINAL PORTFOLIO INTEGRITY AUDIT (APRIL 6)...")
    res = supabase.table("quarterly_earnings").select("ticker_eod, updated_at, uploaded, markdown_content").execute()
    data = res.data
    
    total_count = len(data)
    corp_count = 0
    non_corp_count = 0
    
    missing_today = []
    low_density = []
    not_uploaded = []
    
    for r in data:
        ticker = r['ticker_eod']
        updated_at = r['updated_at']
        uploaded = r['uploaded']
        content = r['markdown_content'] or ""
        word_count = len(content.split())
        
        is_corp = ticker in ALL_CORP
        if is_corp: corp_count += 1
        else: non_corp_count += 1
        
        # Check Today
        if "2026-04-06" not in updated_at:
            missing_today.append(ticker)
        
        # Check Uploaded
        if not uploaded:
            not_uploaded.append(ticker)
            
        # Check Density
        is_private = ticker.startswith("PRIVATE") or ticker in ["DATABRICKS", "DISCORD", "ANDURIL", "DEEL", "KRAKEN", "REVOLUT", "STRIPE", "CEREBRAS", "ANTHROPIC", "CANVA", "OPENAI", "SPACEX"]
        target = 3400 if is_private else 1515
        
        # If it's a corporate ticker, it must hit the density target
        if is_corp and word_count < target:
            low_density.append(f"{ticker} ({word_count}/{target})")

    print(f"\n[RESULTS]")
    print(f"Total Tickers: {total_count} (Corp: {corp_count}, Non-Corp: {non_corp_count})")
    print(f"Tickers Not Updated Today: {len(missing_today)}")
    if missing_today:
        print(f"  Sample: {missing_today[:5]}")
        
    print(f"Tickers Not Uploaded: {len(not_uploaded)}")
    if not_uploaded:
        print(f"  Sample: {not_uploaded[:5]}")
        
    print(f"Corporate Tickers with Low Density: {len(low_density)}")
    if low_density:
        print(f"  Sample: {low_density[:5]}")

    # Actionable items for corporate tickers
    corp_to_fix = [t for t in missing_today if t in ALL_CORP] + [t for t in not_uploaded if t in ALL_CORP]
    corp_to_fix = list(set(corp_to_fix))
    
    print(f"\n[ACTION] Corporate Tickers needing Fix/Regen: {len(corp_to_fix)}")
    if corp_to_fix:
        print(f"  List: {corp_to_fix}")

if __name__ == "__main__":
    run_final_audit()
