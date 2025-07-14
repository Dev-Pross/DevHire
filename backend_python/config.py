import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("PROJECT_URL")
SUPABASE_KEY = os.getenv("SUPABASE_API")
DB_URL = os.getenv("DATABASE_URL")

supabase = create_client(SUPABASE_URL,SUPABASE_KEY)