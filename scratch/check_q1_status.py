import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

TICKERS = ["MRK.US", "BP.LSE", "LIFCO-B.ST", "UNP.US", "VIT-B.ST", "AI.PA", "DHR.US", "ISRG.US", "MMM.US", "NEE.US"]
FISCAL_PERIOD = "Q1 2026"

def check_status():
    print(f"{'Ticker':<15} | {'QE Table':<8} | {'MD Content':<10} | {'PDF URL':<8} | {'Audio URL':<9} | {'Master Index':<12}")
    print("-" * 90)
    
    for ticker in TICKERS:
        # Check quarterly_earnings table
        # Columns based on supabase_storage_manager.py: pdf_report_url, audio_report_url
        res_qe = supabase.table("quarterly_earnings").select("markdown_content, pdf_report_url, audio_report_url, review_status").eq("ticker_eod", ticker).eq("fiscal_period", FISCAL_PERIOD).execute()
        
        qe_exists = "YES" if res_qe.data else "NO"
        md_exists = "YES" if (res_qe.data and res_qe.data[0].get("markdown_content")) else "NO"
        pdf_exists = "YES" if (res_qe.data and res_qe.data[0].get("pdf_report_url")) else "NO"
        audio_exists = "YES" if (res_qe.data and res_qe.data[0].get("audio_report_url")) else "NO"
        
        # Check kasona_company_reports table (Master Index)
        # We look for published reports for this ticker and skill_id
        res_mi = supabase.table("kasona_company_reports").select("id, quarterly_analysis_pdf_en").eq("ticker_eod", ticker).eq("skill_id", "quarterly_earnings").execute()
        
        # We assume if there's a record with the PDF link for Q1 2026, it's correct.
        # Master index entries from targeted_orchestrator have labels like "Earnings Report Q1 2026"
        mi_exists = "NO"
        if res_mi.data:
            for report in res_mi.data:
                pdfs = report.get("quarterly_analysis_pdf_en", [])
                if pdfs and any("Q1 2026" in p.get("label", "") for p in pdfs):
                    mi_exists = "YES"
                    break
        
        print(f"{ticker:<15} | {qe_exists:<8} | {md_exists:<10} | {pdf_exists:<8} | {audio_exists:<9} | {mi_exists:<12}")

if __name__ == "__main__":
    check_status()
