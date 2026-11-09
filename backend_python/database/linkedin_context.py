from config import supabase
from datetime import datetime

def save_linkedin_context(user_id: str, context_data: dict):
    """Save LinkedIn context to database"""
    try:
        payload = {
            "linkedin_context": context_data,
            "context_updated_at": datetime.utcnow().isoformat(),
            "isConnected": True
        }
        query = supabase.table("User").update(payload)
        if "@" in str(user_id):
            response = query.eq("email", str(user_id)).execute()
        else:
            response = query.eq("id", str(user_id)).execute()
        
        if not response.data:
            print(f"⚠️ No user found with identifier '{user_id}' - context NOT saved!")
            return False
            
        print(f"✅ LinkedIn context saved for user {user_id}")
        return True
    except Exception as e:
        print(f"❌ Error saving context: {e}")
        return False

def get_linkedin_context(user_id: str):
    """Retrieve LinkedIn context from database"""
    try:
        query = supabase.table("User").select("linkedin_context")
        if "@" in str(user_id):
            response = query.eq("email", str(user_id)).execute()
        else:
            response = query.eq("id", str(user_id)).execute()
        
        if response.data and len(response.data) > 0:
            print(f"✅ Retrieved LinkedIn context for user {user_id}")
            return response.data[0].get("linkedin_context")
        
        print(f"⚠️ No user found with identifier: '{user_id}'")
        return None
    except Exception as e:
        print(f"❌ Error retrieving context: {e}")
        return None

def clear_linkedin_context(user_id: str):
    """Clear LinkedIn context from database"""
    try:
        payload = {
            "linkedin_context": None,
            "context_updated_at": None,
            "isConnected": False
        }
        query = supabase.table("User").update(payload)
        if "@" in str(user_id):
            response = query.eq("email", str(user_id)).execute()
        else:
            response = query.eq("id", str(user_id)).execute()
        
        print(f"🧹 LinkedIn context cleared for user {user_id}")
        return True
    except Exception as e:
        print(f"❌ Error clearing context: {e}")
        return False
