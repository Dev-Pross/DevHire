import psycopg2
from psycopg2.extras import Json
from datetime import datetime
from config import DB_URL  # Import your database connection string

def get_db_connection():
    """Create a database connection"""
    return psycopg2.connect(DB_URL)

def save_linkedin_context(user_id: str, context_data: dict):
    """Save LinkedIn context to database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = """
            UPDATE  public."User" 
            SET linkedin_context = %s, 
                context_updated_at = %s 
            WHERE email = %s
        """
        cursor.execute(query, (Json(context_data), datetime.utcnow(), user_id))
        conn.commit()
        print(f"✅ LinkedIn context saved for user {user_id}")
        return True
    except Exception as e:
        conn.rollback()
        print(f"❌ Error saving context: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def get_linkedin_context(user_id: str):
    """Retrieve LinkedIn context from database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = """
            SELECT linkedin_context 
            FROM public."User" 
            WHERE email = %s
        """
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        
        if result and result[0]:
            print("context:",result)
            return result[0]  # Return only the context data
        return None
    except Exception as e:
        print(f"❌ Error retrieving context: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def clear_linkedin_context(user_id: str):
    """Clear LinkedIn context from database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = """
            UPDATE public."User"
            SET linkedin_context = NULL,
            context_updated_at = NULL
            WHERE email = %s;
        """
        cursor.execute(query, (user_id,))
        conn.commit()
        print(f"🧹 LinkedIn context cleared for user {user_id}")
        return True
    except Exception as e:
        conn.rollback()
        print(f"❌ Error clearing context: {e}")
        return False
    finally:
        cursor.close()
        conn.close()
