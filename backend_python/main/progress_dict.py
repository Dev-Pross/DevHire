job_progress={}
apply_progress={}
linkedin_login_context = None 


async def clear_login_context():
    """Clear/close the login context when user logs out"""
    global linkedin_login_context
    if linkedin_login_context:
        try:
            await linkedin_login_context.close()
            print("🚪 Login context closed!")
        except Exception as e:
            print(f"Error closing context: {e}")
    
    linkedin_login_context = None