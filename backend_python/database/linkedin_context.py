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
        rows_affected = cursor.rowcount
        conn.commit()
        
        if rows_affected == 0:
            print(f"⚠️ No user found with email '{user_id}' - context NOT saved!")
            print(f"   Hint: Check if user exists in database or if email is correct")
            return False
        
        print(f"✅ LinkedIn context saved for user {user_id} ({rows_affected} row(s) updated)")
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
        # Debug: Check if user exists first
        check_query = """
            SELECT email, linkedin_context IS NOT NULL as has_context 
            FROM public."User" 
            WHERE email = %s
        """
        cursor.execute(check_query, (user_id,))
        check_result = cursor.fetchone()
        
        if check_result:
            print(f"🔍 User found: {check_result[0]}, has_context: {check_result[1]}")
        else:
            print(f"⚠️ No user found with email: '{user_id}'")
            # List existing users for debugging (first 5)
            cursor.execute('SELECT email FROM public."User" LIMIT 5')
            existing = cursor.fetchall()
            print(f"   Existing users (sample): {[u[0] for u in existing]}")
            return None
        
        query = """
            SELECT linkedin_context 
            FROM public."User" 
            WHERE email = %s
        """
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        
        if result and result[0]:
            print(f"✅ Retrieved LinkedIn context for user {user_id}")
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
