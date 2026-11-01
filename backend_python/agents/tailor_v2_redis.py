import json
import hashlib
import time
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Tuple
from config import redis_client

SESSION_TTL_SECONDS = 10800  # 3 hours
LOCK_TIMEOUT_SECONDS = 30
MAX_REVISIONS = 3

def compute_session_id(user_id: str, job_desc: str) -> str:
    """Computes deterministic session ID based on user_id and SHA-256 hash of JD text."""
    normalized_jd = job_desc.strip().encode("utf-8")
    jd_hash = hashlib.sha256(normalized_jd).hexdigest()[:16]
    return f"{user_id}:{jd_hash}"

def _session_key(session_id: str) -> str:
    return f"tailor_v2:{session_id}"

def _lock_key(session_id: str) -> str:
    return f"tailor_v2_lock:{session_id}"


def acquire_lock(session_id: str, timeout_secs: int = LOCK_TIMEOUT_SECONDS) -> bool:
    """
    Attempts to acquire a distributed mutex lock for the given session.
    Uses Redis SET NX EX to prevent concurrent revisions or race conditions.
    """
    if not redis_client:
        return True  # Fallback gracefully if redis is disabled in testing
    try:
        acquired = redis_client.set(_lock_key(session_id), "locked", nx=True, ex=timeout_secs)
        return bool(acquired)
    except Exception as e:
        print(f"Error acquiring Redis lock for {session_id}: {e}")
        return False


def release_lock(session_id: str) -> bool:
    """Releases the distributed mutex lock for the given session."""
    if not redis_client:
        return True
    try:
        redis_client.delete(_lock_key(session_id))
        return True
    except Exception as e:
        print(f"Error releasing Redis lock for {session_id}: {e}")
        return False


def save_new_session(
    user_id: str,
    job_desc: str,
    tailored_json: dict,
    resume_facts: dict,
    template: int = 0
) -> Dict[str, Any]:
    """
    Persists a new tailor session into Redis. If session already exists with revisions,
    preserves existing session to support deterministic re-entries.
    """
    session_id = compute_session_id(user_id, job_desc)
    key = _session_key(session_id)

    if not redis_client:
        now_iso = datetime.now(timezone.utc).isoformat()
        exp_iso = (datetime.now(timezone.utc) + timedelta(seconds=SESSION_TTL_SECONDS)).isoformat()
        return {
            "session_id": session_id,
            "tailored_json": tailored_json,
            "revisions_remaining": MAX_REVISIONS,
            "version": 1,
            "expires_at": exp_iso
        }

    # Check if session already exists
    existing = redis_client.hgetall(key)
    if existing and "tailored_json" in existing:
        revisions_used = int(existing.get("revisions_used", 0))
        version = int(existing.get("version", 1))
        ttl = redis_client.ttl(key)
        exp_dt = datetime.now(timezone.utc) + timedelta(seconds=max(0, ttl))
        return {
            "session_id": session_id,
            "tailored_json": json.loads(existing["tailored_json"]),
            "revisions_remaining": max(0, MAX_REVISIONS - revisions_used),
            "version": version,
            "expires_at": exp_dt.isoformat()
        }

    now = datetime.now(timezone.utc)
    expires_at = (now + timedelta(seconds=SESSION_TTL_SECONDS)).isoformat()

    session_data = {
        "user_id": user_id,
        "session_id": session_id,
        "tailored_json": json.dumps(tailored_json),
        "resume_facts": json.dumps(resume_facts),
        "job_description": job_desc,
        "revisions_used": 0,
        "version": 1,
        "template": template,
        "created_at": now.isoformat(),
        "expires_at": expires_at
    }

    # Atomic multi/pipeline set and expire
    pipe = redis_client.pipeline()
    pipe.hset(key, mapping=session_data)
    pipe.expire(key, SESSION_TTL_SECONDS)
    pipe.execute()

    return {
        "session_id": session_id,
        "tailored_json": tailored_json,
        "revisions_remaining": MAX_REVISIONS,
        "version": 1,
        "expires_at": expires_at
    }


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves and parses session hash from Redis."""
    if not redis_client:
        return None

    data = redis_client.hgetall(_session_key(session_id))
    if not data or "tailored_json" not in data:
        return None

    try:
        ttl = redis_client.ttl(_session_key(session_id))
        exp_dt = datetime.now(timezone.utc) + timedelta(seconds=max(0, ttl))
        revisions_used = int(data.get("revisions_used", 0))

        return {
            "session_id": session_id,
            "user_id": data.get("user_id"),
            "tailored_json": json.loads(data["tailored_json"]),
            "resume_facts": json.loads(data.get("resume_facts", "{}")),
            "job_description": data.get("job_description", ""),
            "revisions_used": revisions_used,
            "revisions_remaining": max(0, MAX_REVISIONS - revisions_used),
            "version": int(data.get("version", 1)),
            "template": int(data.get("template", 0)),
            "expires_at": exp_dt.isoformat()
        }
    except Exception as e:
        print(f"Error parsing session data for {session_id}: {e}")
        return None


def consume_revision_credit(session_id: str, max_revisions: int = MAX_REVISIONS) -> Tuple[bool, int]:
    """
    Atomically increments the revision counter inside Redis.
    If counter exceeds limit, rolls back immediately and returns (False, 0).
    Returns (True, revisions_remaining) on success.
    """
    if not redis_client:
        return True, max_revisions - 1

    key = _session_key(session_id)
    # Atomic increment
    new_count = redis_client.hincrby(key, "revisions_used", 1)

    if new_count > max_revisions:
        # Rollback immediately
        redis_client.hincrby(key, "revisions_used", -1)
        return False, 0

    return True, max_revisions - new_count


def refund_revision_credit(session_id: str, max_revisions: int = MAX_REVISIONS) -> int:
    """
    Rolls back revision counter by 1 in case of model or schema failure.
    Guarantees user is not charged for failed API calls.
    """
    if not redis_client:
        return max_revisions

    key = _session_key(session_id)
    new_count = redis_client.hincrby(key, "revisions_used", -1)
    if new_count < 0:
        redis_client.hset(key, "revisions_used", 0)
        new_count = 0

    return max(0, max_revisions - new_count)


def update_session_json(session_id: str, updated_format_dict: dict) -> Tuple[bool, int]:
    """
    Atomically stores the revised format JSON into the Redis hash and bumps the version.
    Returns (success, new_version).
    """
    if not redis_client:
        return True, 2

    key = _session_key(session_id)
    pipe = redis_client.pipeline()
    pipe.hset(key, "tailored_json", json.dumps(updated_format_dict))
    pipe.hincrby(key, "version", 1)
    results = pipe.execute()

    new_version = int(results[1]) if len(results) > 1 else 1
    return True, new_version
