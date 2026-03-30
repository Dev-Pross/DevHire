import os
import redis
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("PROJECT_URL")
SUPABASE_KEY = os.getenv("SUPABASE_API")
DB_URL = os.getenv("DATABASE_URL")
GOOGLE_API = os.getenv("GOOGLE_API")
GROQ_API = os.getenv("GROQ_API")

LINKEDIN_ID = os.getenv("LINKEDIN_ID")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

REDIS_URL = os.getenv("REDIS_URL")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_REGION = os.getenv("GCP_REGION", "asia-south1")
WORKER_JOB_NAME = os.getenv("WORKER_JOB_NAME", "devhire-worker")
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

redis_client = None
if REDIS_URL:
    try:
        redis_client = redis.from_url(
            REDIS_URL, 
            decode_responses=True,
            ssl_cert_reqs="none" # For Upstash Rediss
        )
    except Exception as e:
        print(f"Failed to initialize Redis client: {e}")

# Normalise the Playwright context creation parameters so every context uses
# identical characteristics. LinkedIn is sensitive to user-agent, locale and
# timezone mismatches, so keeping these consistent prevents forced logouts.
LINKEDIN_CONTEXT_OPTIONS = {
    "user_agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "viewport": {"width": 1366, "height": 768},
    "locale": "en-US",
    "timezone_id": "Asia/Calcutta",
}