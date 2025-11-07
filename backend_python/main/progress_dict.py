job_progress={}
apply_progress={}

# Shared storage for the LinkedIn Playwright session state.
linkedin_login_context = None

# Normalise the Playwright context creation parameters so every context uses
# identical characteristics. LinkedIn is sensitive to user-agent, locale and
# timezone mismatches, so keeping these consistent prevents forced logouts.
LINKEDIN_CONTEXT_OPTIONS = {
    "user_agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "viewport": {"width": 1920, "height": 1080},
    "locale": "en-US",
    "timezone_id": "Asia/Calcutta",
}


async def clear_login_context():
    """Clear the cached login state when the user logs out."""
    global linkedin_login_context

    # Older runs stored the raw Playwright context object; make sure we close it
    # if present while still handling the new dictionary-based storage state.
    context_candidate = linkedin_login_context
    if context_candidate and hasattr(context_candidate, "close"):
        try:
            await context_candidate.close()
            print("🚪 Login context closed!")
        except Exception as e:
            print(f"Error closing context: {e}")

    linkedin_login_context = None