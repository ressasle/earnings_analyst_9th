import os
import sys
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

TICKERS_99 = [
    "KLAR.US", "PRIVATE.DATABRICKS", "PRIVATE.DISCORD", "PRIVATE.ANDURIL", "PRIVATE.DEEL", "PRIVATE.KRAKEN",
    "DESN.SW", "QXO.US", "VIT-B.ST", "PRIVATE.REVOLUT", "PRIVATE.STRIPE", "PRIVATE.CEREBRAS", "ARENIT.ST",
    "PRIVATE.ANTHROPIC", "PRIVATE.CANVA", "PRIVATE.OPENAI", "MMGR-B.ST", "1SXP.DE", "YPSN.SW", "PRIVATE.SPACEX",
    "BERG-B.ST", "NOVO-B.CO", "BOREO.HE", "HLMA.LSE", "BANB.SW", "SFT.LSE", "ADDT-B.ST", "INDT.ST", "ASPO.HE",
    "BRO.US", "DHR.US", "BRK-B.US", "BNZL.LSE", "CSU.TO", "LAGR-B.ST", "LLY.US", "ROVI.MC", "MEDP.US",
    "ZEAL.CO", "LIFCO-B.ST", "STVN.US", "ASKER.ST", "ROKO-B.ST", "PPGN.SW", "ROP.US", "HIMS.US", "IMCD.AS", "WST.US"
]

MAPPING = {
    "KLAR.US": "KLAR",
    "PRIVATE.DATABRICKS": "DATABRICKS",
    "PRIVATE.DISCORD": "DISCORD",
    "PRIVATE.ANDURIL": "ANDURIL",
    "PRIVATE.DEEL": "DEEL",
    "PRIVATE.KRAKEN": "KRAKEN",
    "PRIVATE.REVOLUT": "REVOLUT",
    "PRIVATE.STRIPE": "STRIPE",
    "PRIVATE.CEREBRAS": "CEREBRAS",
    "PRIVATE.ANTHROPIC": "ANTHROPIC",
    "PRIVATE.CANVA": "CANVA",
    "PRIVATE.OPENAI": "OPENAI",
    "PRIVATE.SPACEX": "SPACEX",
    "NOVO-B.CO": "NVO.US"
}

def audit():
    print(f"{'Ticker (Asset)':<20} | {'Ticker (DB)':<20} | {'EN Length':<10} | {'Status'}")
    print("-" * 70)
    
    missing = []
    low_quality = []
    
    for t in TICKERS_99:
        db_t = MAPPING.get(t, t)
        res = supabase.table("quarterly_earnings").select("ticker_eod, markdown_content").eq("ticker_eod", db_t).execute()
        
        if not res.data:
            print(f"{t:<20} | {db_t:<20} | {'MISSING':<10} | FAIL")
            missing.append(t)
        else:
            content = res.data[0].get("markdown_content") or ""
            length = len(content)
            status = "OK" if length > 6500 else "LOW QUALITY"
            print(f"{t:<20} | {db_t:<20} | {length:<10} | {status}")
            if length <= 6500:
                low_quality.append(t)

    print("\nSUMMARY:")
    print(f"Total Tickers: {len(TICKERS_99)}")
    print(f"Missing in DB: {len(missing)}")
    print(f"Low Quality (< 6500 chars): {len(low_quality)}")
    if missing:
        print(f"Missing: {missing}")
    if low_quality:
        print(f"Low Quality: {low_quality}")

if __name__ == "__main__":
    audit()
