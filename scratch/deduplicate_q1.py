import os
import json
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

TICKERS = ["MRK.US", "BP.LSE", "LIFCO-B.ST", "UNP.US", "VIT-B.ST", "AI.PA", "DHR.US", "ISRG.US", "MMM.US", "NEE.US"]
FISCAL_PERIOD = "Q1 2026"

def score_record(r):
    score = 0
    if r.get("markdown_content") and len(r.get("markdown_content")) > 100:
        score += 1
    if r.get("pdf_url"):
        score += 1
    if r.get("audio_url"):
        score += 1
    return score

def deduplicate():
    print(f"Starting deduplication for {FISCAL_PERIOD}...")
    
    for ticker in TICKERS:
        print(f"\nProcessing {ticker}...")
        
        # 1. Handle quarterly_earnings
        res = supabase.table("quarterly_earnings").select("*").eq("ticker_eod", ticker).eq("fiscal_period", FISCAL_PERIOD).execute()
        records = res.data
        
        if len(records) > 1:
            print(f"Found {len(records)} records in quarterly_earnings.")
            # Sort by score DESC, then updated_at DESC
            records.sort(key=lambda x: (score_record(x), x.get("updated_at", "")), reverse=True)
            
            master = records[0]
            dups = records[1:]
            
            print(f"Master ID: {master['id']} (Score: {score_record(master)})")
            
            for dup in dups:
                print(f"Deleting duplicate ID: {dup['id']} (Score: {score_record(dup)})")
                supabase.table("quarterly_earnings").delete().eq("id", dup['id']).execute()
        elif len(records) == 1:
            print(f"Only one record found for {ticker}. OK.")
            master = records[0]
        else:
            print(f"WARNING: No records found for {ticker}!")
            continue

        # 2. Handle kasona_company_reports
        # This table should have ONE record per ticker for skill_id='quarterly_earnings'
        res_cr = supabase.table("kasona_company_reports").select("*").eq("ticker_eod", ticker).eq("skill_id", "quarterly_earnings").execute()
        cr_records = res_cr.data
        
        if len(cr_records) > 1:
            print(f"Found {len(cr_records)} quarterly_earnings records in kasona_company_reports. Deduplicating...")
            cr_records.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
            cr_master = cr_records[0]
            cr_dups = cr_records[1:]
            
            for dup in cr_dups:
                print(f"Deleting duplicate Master Index ID: {dup['id']}")
                supabase.table("kasona_company_reports").delete().eq("id", dup['id']).execute()
            
            update_master_index(cr_master['id'], master)
        elif len(cr_records) == 1:
            print(f"One quarterly_earnings Master Index record found. Updating...")
            update_master_index(cr_records[0]['id'], master)
        else:
            print(f"Creating missing quarterly_earnings Master Index record for {ticker}...")
            # We need some basic info to create the record
            # Let's get company name from general metadata if possible, or just use ticker
            new_record = {
                "ticker_eod": ticker,
                "skill_id": "quarterly_earnings",
                "created_by": "Julian",
                "updated_at": "now()"
            }
            res_new = supabase.table("kasona_company_reports").insert(new_record).execute()
            if res_new.data:
                update_master_index(res_new.data[0]['id'], master)

def update_master_index(cr_id, qe_record):
    """
    Ensure kasona_company_reports entry correctly reflects the Q1 2026 data.
    """
    pdf_url = qe_record.get("pdf_url")
    audio_url = qe_record.get("audio_url")
    
    if not pdf_url:
        return

    # Fetch current state to avoid overwriting other periods
    res = supabase.table("kasona_company_reports").select("quarterly_analysis_pdf_en, quarterly_briefing_audio_en").eq("id", cr_id).execute()
    current = res.data[0]
    
    pdfs = current.get("quarterly_analysis_pdf_en") or []
    audios = current.get("quarterly_briefing_audio_en") or []
    
    # Update or add PDF
    updated_pdfs = []
    found_pdf = False
    for p in pdfs:
        if p.get("label") == FISCAL_PERIOD:
            p["url"] = pdf_url
            found_pdf = True
        updated_pdfs.append(p)
    if not found_pdf:
        updated_pdfs.append({"url": pdf_url, "label": FISCAL_PERIOD})
        
    # Update or add Audio
    updated_audios = []
    found_audio = False
    for a in audios:
        if a.get("label") == FISCAL_PERIOD:
            a["url"] = audio_url
            found_audio = True
        updated_audios.append(a)
    if not found_audio:
        if audio_url:
            updated_audios.append({"url": audio_url, "label": FISCAL_PERIOD})

    supabase.table("kasona_company_reports").update({
        "quarterly_analysis_pdf_en": updated_pdfs,
        "quarterly_briefing_audio_en": updated_audios,
        "updated_at": "now()"
    }).eq("id", cr_id).execute()
    print(f"Updated Master Index {cr_id} with Q1 2026 artifacts.")

if __name__ == "__main__":
    deduplicate()
