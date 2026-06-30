import os
import uuid
import json
import time
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional, cast
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from config import supabase, redis_client, GCP_PROJECT_ID, GCP_REGION, WORKER_JOB_NAME, DEV_MODE

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

class JobStartRequest(BaseModel):
    user_id: str           # User email/id to associate
    workflow_type: str     # 'fetch_jobs' or 'apply_jobs'
    input_data: Dict[str, Any]
    job_id: Optional[str] = None


SESSION_STALE_SECONDS = int(os.getenv("SESSION_STALE_SECONDS", "300"))


def _worker_heartbeat_key(job_id: str) -> str:
    return f"worker_heartbeat:{job_id}"


def _stream_key(job_id: str) -> str:
    return f"stream:{job_id}"


def _get_stream_start_index(job_id: str) -> int:
    return _redis_llen_sync(_stream_key(job_id))


def _redis_llen_sync(key: str) -> int:
    if not redis_client:
        return 0

    try:
        length = redis_client.llen(key)
        if asyncio.iscoroutine(length):
            return 0
        return int(cast(Any, length))
    except Exception:
        return 0


def _redis_get_sync(key: str) -> Optional[str]:
    if not redis_client:
        return None

    try:
        value = redis_client.get(key)
        if asyncio.iscoroutine(value):
            return None
        if value is None:
            return None
        return str(cast(Any, value))
    except Exception:
        return None


def _redis_lrange_sync(key: str, start: int, end: int) -> list:
    if not redis_client:
        return []

    try:
        values = redis_client.lrange(key, start, end)
        if asyncio.iscoroutine(values):
            return []
        if isinstance(values, list):
            return values
        return list(cast(Any, values))
    except Exception:
        return []


def _parse_iso_timestamp(value: Optional[str]) -> Optional[float]:
    if not value:
        return None

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.timestamp()
    except Exception:
        return None


def _is_worker_heartbeat_fresh(job_id: str, stale_after_seconds: int = SESSION_STALE_SECONDS) -> bool:
    try:
        raw = _redis_get_sync(_worker_heartbeat_key(job_id))
        if not raw:
            return False

        try:
            heartbeat_at = float(raw)
        except (TypeError, ValueError):
            # Backward compatibility: any value means liveness signal exists.
            return True

        return (time.time() - heartbeat_at) <= stale_after_seconds
    except Exception:
        return False


def _should_resume_active_session(status: str, job_id: str, last_active_at: Optional[str]) -> bool:
    # scraper_raw sessions are resumable checkpoints by design.
    if status == "scraper_raw":
        return True

    if status not in ("pending", "running"):
        return False

    if _is_worker_heartbeat_fresh(job_id):
        return False

    last_active_ts = _parse_iso_timestamp(last_active_at)
    if last_active_ts is None:
        return True

    return (time.time() - last_active_ts) > SESSION_STALE_SECONDS


def _trigger_worker(job_id: str):
    """Start worker process/job for a workflow session id."""
    if DEV_MODE:
        import subprocess

        env = os.environ.copy()
        env["JOB_ID"] = job_id
        subprocess.Popen(["python", "worker.py"], env=env)
        print(f"🔧 DEV MODE: Started worker.py subprocess for JOB_ID={job_id}")
        return

    from google.cloud import run_v2

    print(f"☁️ Triggering Cloud Run Job '{WORKER_JOB_NAME}' for JOB_ID={job_id}")
    if not GCP_PROJECT_ID:
        raise RuntimeError("GCP_PROJECT_ID is not configured")

    client = run_v2.JobsClient()
    job_name = client.job_path(GCP_PROJECT_ID, GCP_REGION, WORKER_JOB_NAME)

    request = run_v2.RunJobRequest(
        name=job_name,
        overrides={
            "container_overrides": [
                {
                    "env": [
                        {"name": "JOB_ID", "value": job_id}
                    ]
                }
            ]
        }
    )
    client.run_job(request=request)


async def _wait_for_worker_started(job_id: str, timeout_seconds: int = 30, start_index: int = 0) -> bool:
    """Wait for a worker 'started' event in Redis. Returns False on timeout."""
    if not redis_client:
        return True

    stream_key = _stream_key(job_id)
    start_time = time.time()

    while time.time() - start_time < timeout_seconds:
        events = _redis_lrange_sync(stream_key, start_index, -1)
        for event in events:
            try:
                ev_data = json.loads(event)
                if ev_data.get("status") == "started":
                    return True
            except Exception:
                continue
        await asyncio.sleep(0.5)

    return False


async def _resume_existing_active_session(job_id: str, previous_status: str):
    """Re-launch worker for an existing active session when heartbeat is stale."""
    stream_start_index = _get_stream_start_index(job_id)

    try:
        _trigger_worker(job_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume existing {previous_status} job: {str(e)}")

    started = await _wait_for_worker_started(job_id, timeout_seconds=15, start_index=stream_start_index)
    if started:
        return {
            "job_id": job_id,
            "status": "running",
            "message": f"Resumed existing {previous_status} job"
        }

    # Keep session state intact; frontend can still stream/status-poll while worker boot catches up.
    return {
        "job_id": job_id,
        "status": previous_status,
        "message": f"Reattached to {previous_status} job. Worker resume signal pending"
    }

@router.post("/start")
async def start_job(req: JobStartRequest, background_tasks: BackgroundTasks):
    """
    Trigger a new background job. It inserts a run into DB,
    and returns only when the worker has started successfully (Redis latch),
    or after 30s timeout.
    """
    if req.workflow_type not in ('fetch_jobs', 'apply_jobs'):
        raise HTTPException(status_code=400, detail="Invalid workflow_type")
        
    # Retrieve actual user id from user email
    # Assuming user_id provided is email, as frontend seems to use email in places.
    # Let's check DB to get internal UUID. Or if req.user_id is already UUID?
    # In earlier implementations, user_id from frontend (Progress_user) was email.
    
    # We will search users by email OR id if it's already a UUID.
    user_res = supabase.table("User").select("id").eq("email", req.user_id).execute()
    if not user_res.data:
        # Check if it was passed by UUID directly
        user_res = supabase.table("User").select("id").eq("id", req.user_id).execute()
        if not user_res.data:
            raise HTTPException(status_code=404, detail=f"User {req.user_id} not found in DB")
    
    user_row = cast(Dict[str, Any], user_res.data[0])
    internal_user_id = str(user_row["id"])

    # Reconnection handling: if frontend provides a job_id, check if it's already running
    job_id = req.job_id
    if job_id:
        existing = supabase.table("workflow_sessions").select("status, workflow_type, last_active_at").eq("id", job_id).execute()
        if existing.data:
            existing_row = cast(Dict[str, Any], existing.data[0])
            status = str(existing_row.get("status") or "")
            existing_workflow = existing_row.get("workflow_type")
            existing_last_active_at = cast(Optional[str], existing_row.get("last_active_at"))

            if existing_workflow and existing_workflow != req.workflow_type:
                raise HTTPException(
                    status_code=409,
                    detail=f"Provided job_id belongs to workflow '{existing_workflow}', not '{req.workflow_type}'."
                )

            if status in ("pending", "running", "scraper_raw"):
                if _should_resume_active_session(status, job_id, existing_last_active_at):
                    print(f"🔁 Resuming stale {status} job: {job_id}")
                    return await _resume_existing_active_session(job_id, status)

                print(f"🔄 Reattaching to existing active job: {job_id}")
                return {"job_id": job_id, "status": status, "message": "Reattached to existing job"}
            else:
                # If the job is failed or completed, generate a new one
                job_id = str(uuid.uuid4())
    else:
        job_id = str(uuid.uuid4())

    try:
        supabase.table("workflow_sessions").insert({
            "id": job_id,
            "user_id": internal_user_id,
            "workflow_type": req.workflow_type,
            "status": "pending",
            "input_data": req.input_data
        }).execute()
    except Exception as e:
        error_msg = str(e)
        if "one_active_job_per_user" in error_msg or "429" in error_msg:
            # Let's see if we can find the active job for this user to return it
            active_res = supabase.table("workflow_sessions").select("id, workflow_type, status, last_active_at").eq("user_id", internal_user_id).neq("status", "completed").neq("status", "failed").execute()
            if active_res.data:
                active_job = cast(Dict[str, Any], active_res.data[0])

                # Only auto-reconnect if it's the exact same workflow type
                if active_job["workflow_type"] == req.workflow_type:
                    active_status = str(active_job.get("status") or "running")
                    active_job_id = str(active_job.get("id") or "")
                    if _should_resume_active_session(active_status, active_job_id, cast(Optional[str], active_job.get("last_active_at"))):
                        print(f"🔁 Resuming user's stale {active_status} active job: {active_job_id}")
                        return await _resume_existing_active_session(active_job_id, active_status)

                    print(f"🔄 Providing active job for auto-reconnect: {active_job_id}")
                    return {
                        "job_id": active_job_id,
                        "status": active_status,
                        "message": "Reattached to user's active job"
                    }
                else:
                    raise HTTPException(
                        status_code=429,
                        detail=f"Another workflow ({active_job['workflow_type']}) is currently running. Please wait for it to finish before starting {req.workflow_type}."
                    )
            raise HTTPException(status_code=429, detail="A job is already running for this user.")
        raise HTTPException(status_code=500, detail=f"Database error: {error_msg}")

    # Prepare Redis stream
    stream_key = _stream_key(job_id)
    if redis_client:
        # Clean up any old data randomly, though UUIDs are unique
        redis_client.delete(stream_key)

    # Trigger Worker
    try:
        _trigger_worker(job_id)
    except Exception as e:
        # Mark failed
        supabase.table("workflow_sessions").update({"status": "failed"}).eq("id", job_id).execute()
        raise HTTPException(status_code=500, detail=f"Failed to trigger worker: {str(e)}")

    # Redis Latch - Wait up to 30 seconds for worker to start
    # The worker pushes 'started' into the stream upon initialization.
    worker_started = await _wait_for_worker_started(job_id, timeout_seconds=30)
    if not worker_started:
        if redis_client:
            # If we timeout, we mark it failed so that worker will abort on boot.
            supabase.table("workflow_sessions").update({"status": "failed"}).eq("id", job_id).execute()
        raise HTTPException(status_code=504, detail="Worker initialization timeout")
    
    return {"message": "Job started successfully", "job_id": job_id}

@router.get("/stream")
async def stream_job(job_id: str):
    """
    Server-Sent Events (SSE) endpoint to stream progress from Redis.
    """
    stream_key = f"stream:{job_id}"
    
    async def event_generator():
        last_index = 0
        try:
            # Send initial connection success
            yield {
                "data": json.dumps({"progress": 0, "status": "connected", "message": "Connected to job stream"})
            }
            
            while True:
                if not redis_client:
                    yield {"data": json.dumps({"error": "Redis not configured", "status": "error"})}
                    break

                events = _redis_lrange_sync(stream_key, last_index, -1)
                for event in events:
                    yield {"data": event}
                    last_index += 1
                    
                    try:
                        ev_data = json.loads(event)
                        # Close stream on termination states
                        if ev_data.get("status") in ("done", "error") or ev_data.get("progress") == -1:
                            return
                    except:
                        pass
                
                # Check DB fallback in case worker died without writing 'error' to Redis
                if last_index > 0 and len(events) == 0:
                    status_res = supabase.table("workflow_sessions").select("status").eq("id", job_id).execute()
                    if status_res.data:
                        db_status = status_res.data[0]["status"]
                        if db_status in ("completed", "failed"):
                            yield {"data": json.dumps({
                                "status": "error" if db_status == "failed" else "done", 
                                "message": f"Job ended in DB with status: {db_status}"
                            })}
                            return

                await asyncio.sleep(1)
        except asyncio.CancelledError:
            print(f"SSE client disconnected for job {job_id}")

    return EventSourceResponse(event_generator())

@router.get("/status")
def get_job_status(job_id: str):
    """
    Fallback endpoint to query exact job state and results from DB.
    Useful if SSE disconnects or user comes back later.
    """
    res = supabase.table("workflow_sessions").select("status", "output_data", "input_data", "workflow_type", "last_active_at").eq("id", job_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Job not found")

    job_data = res.data[0]
    return {
        "job_id": job_id,
        "status": job_data["status"],
        "workflow_type": job_data["workflow_type"],
        "output_data": job_data.get("output_data", {}),
        "input_data": job_data.get("input_data", {}),
        "last_active_at": job_data["last_active_at"]
    }

class CleanupRequest(BaseModel):
    user_id: str

@router.post("/cleanup")
def cleanup_old_sessions(req: CleanupRequest):
    """
    Delete completed or failed sessions older than 30 days for this user.
    Keeps at least the 5 most recent sessions.
    """
    user_res = supabase.table("User").select("id").eq("email", req.user_id).execute()
    if not user_res.data:
        user_res = supabase.table("User").select("id").eq("id", req.user_id).execute()
        if not user_res.data:
            raise HTTPException(status_code=404, detail=f"User {req.user_id} not found in DB")
    
    internal_user_id = user_res.data[0]["id"]
    
    # Supabase Python client doesn't support complex aggregate deletes easily,
    # so we fetch the candidate IDs first
    res = supabase.table("workflow_sessions").select("id, created_at").eq("user_id", internal_user_id).in_("status", ["completed", "failed"]).order("created_at", desc=True).execute()
    
    if not res.data or len(res.data) <= 5:
        return {"message": "No cleanup needed", "deleted_count": 0}
        
    import datetime
    thirty_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)
    
    # Keep the 5 most recent, look at the rest
    candidates = res.data[5:]
    to_delete = []
    
    for row in candidates:
        try:
            # created_at format example: "2024-03-30T10:00:00+00:00"
            dt = datetime.datetime.fromisoformat(row["created_at"].replace('Z', '+00:00'))
            if dt < thirty_days_ago:
                to_delete.append(row["id"])
        except:
            # If date parse fails, append it just to be safe it gets cleaned up
            to_delete.append(row["id"])
            
    if not to_delete:
        return {"message": "No sessions older than 30 days found", "deleted_count": 0}
        
    # Delete in batches or one IN statement
    try:
        supabase.table("workflow_sessions").delete().in_("id", to_delete).execute()
        return {"message": "Cleanup successful", "deleted_count": len(to_delete)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete old sessions: {str(e)}")
