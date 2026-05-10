import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

ticker = "STVN.US"
res = supabase.table("quarterly_earnings").select("markdown_content").eq("ticker_eod", ticker).execute()
if res.data:
    print(res.data[0]["markdown_content"][:2000])
