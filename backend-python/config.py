import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("PROJECT_URL")
SUPABASE_KEY = os.getenv("SUPABASE_API")

supabase = create_client(SUPABASE_URL,SUPABASE_KEY)