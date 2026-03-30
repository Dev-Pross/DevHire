import os
import sys
import json
import time

from config import supabase, redis_client

def get_job_id():
    job_id = os.getenv("JOB_ID")
    if not job_id:
        print("❌ Error: JOB_ID environment variable not set")
        sys.exit(1)
    return job_id

def log_to_redis(job_id, event_or_progress, status=None, message=None, extra=None):
    if not redis_client:
        return
    
    # Allow passing a full dictionary containing all event data
    if isinstance(event_or_progress, dict):
        event = event_or_progress
    else:
        # Fallback for old positional calls
        event = {
            "progress": event_or_progress,
            "status": status,
            "message": message
        }
        if extra:
            event.update(extra)
        
    stream_key = f"stream:{job_id}"
    try:
        redis_client.rpush(stream_key, json.dumps(event))
        # Keep stream reasonably sized or expire it after a day
        redis_client.expire(stream_key, 86400)
    except Exception as e:
        print(f"Redis log error: {e}")

def fail_job(job_id, error_message):
    print(f"❌ Failing job: {error_message}")
    supabase.table("workflow_sessions").update({
        "status": "failed"
    }).eq("id", job_id).execute()
    log_to_redis(job_id, -1, "error", error_message)
    sys.exit(1)

def run_fetch_jobs_pipeline(job_id, job_data):
    """
    Orchestrate the parsing, scraping, and LLM batch pipeline
    """
    from agents.scraper_agent import run_scraper_pipeline
    
    log_to_redis(job_id, 10, "in_progress", "Initializing job discovery pipeline...")
    
    try:
        # Run refactored scraper pipeline
        # It handles state resumption natively through the DB output_data
        run_scraper_pipeline(job_id, job_data, log_callback=lambda ev: log_to_redis(job_id, ev) if isinstance(ev, dict) else log_to_redis(job_id, ev, "in_progress", "Processing..."))
        
        # Once done, it will mark itself as completed in DB, just send the final SSE ping
        log_to_redis(job_id, 100, "done", "Job discovery completed successfully!")
        
    except Exception as e:
        fail_job(job_id, f"Scraper execution failed: {str(e)}")

def run_apply_jobs_pipeline(job_id, job_data):
    """
    Orchestrate the auto-apply pipeline
    """
    from agents.apply_agent import run_apply_pipeline
    
    log_to_redis(job_id, 10, "in_progress", "Initializing job application pipeline...")
    
    try:
        run_apply_pipeline(job_id, job_data, log_callback=lambda ev: log_to_redis(job_id, ev) if isinstance(ev, dict) else log_to_redis(job_id, ev, "in_progress", "Processing..."))
        log_to_redis(job_id, 100, "done", "Job application completed successfully!")
        
    except Exception as e:
        fail_job(job_id, f"Auto-applier execution failed: {str(e)}")

def main():
    job_id = get_job_id()
    print(f"🚀 Worker starting for JOB_ID: {job_id}")
    
    # 1. Fetch Session from DB
    res = supabase.table("workflow_sessions").select("*").eq("id", job_id).execute()
    if not res.data:
        print(f"❌ Error: Job {job_id} not found in DB")
        sys.exit(1)
        
    job_data = res.data[0]
    status = job_data["status"]
    
    # 2. Check for cancelled/failed jobs immediately
    if status == "failed":
        print(f"⚠️ Job {job_id} is already marked as failed. Aborting.")
        sys.exit(0)
    elif status == "completed":
        print(f"✅ Job {job_id} is already completed. Aborting.")
        sys.exit(0)
        
    # 3. Release the API latch if this is the first boot
    if status == "pending":
        supabase.table("workflow_sessions").update({
            "status": "running",
            "last_active_at": "now()"
        }).eq("id", job_id).execute()
        job_data["status"] = "running"
        
        # Important: this "started" status signals jobs_api.py to return HTTP 200
        log_to_redis(job_id, 0, "started", "Worker container initialized")
        time.sleep(1) # Give API a moment to catch the event
    
    # 4. Route to pipeline
    wf_type = job_data["workflow_type"]
    if wf_type == "fetch_jobs":
        run_fetch_jobs_pipeline(job_id, job_data)
    elif wf_type == "apply_jobs":
        run_apply_jobs_pipeline(job_id, job_data)
    else:
        fail_job(job_id, f"Unknown workflow type: {wf_type}")

if __name__ == "__main__":
    main()
