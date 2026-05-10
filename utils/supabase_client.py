import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def get_supabase_client() -> Client:
    """
    Standardized Supabase client initialization.
    Prioritizes SUPABASE_SERVICE_ROLE_KEY for administrative access.
    """
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_SERVICE_KEY")
    
    if not url or not key:
        raise ValueError("Missing Supabase credentials in environment variables (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY/SUPABASE_SERVICE_KEY).")
        
    return create_client(url, key)
