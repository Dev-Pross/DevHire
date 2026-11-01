import base64
import json
import logging
import requests
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import HttpUrl

from agents.tailor import (
    tailor_jobs,
    sanitize_tailored_job,
    escape_pydantic,
    render_one_page,
    Format,
    extract_resume_text_from_bytes,
    extract_facts,
    format_from_facts,
    build_raw_fallback_format,
    rerank_sections_by_jd
)
from agents.tailor_v2_models import (
    TailorV2GenerateRequest,
    TailorV2GenerateResponse,
    TailorV2ReviseRequest,
    TailorV2ReviseResponse,
    TailorV2SessionResponse,
    TailorV2ExportRequest,
    validate_section_key
)
from agents.tailor_v2_redis import (
    acquire_lock,
    release_lock,
    save_new_session,
    get_session,
    consume_revision_credit,
    refund_revision_credit,
    update_session_json,
    compute_session_id
)
from agents.tailor_chat_agent import (
    extract_sections_for_edit,
    revise_sections_with_llm,
    merge_revised_sections
)

log = logging.getLogger("tailor_v2_routes")
router = APIRouter(prefix="/tailor/v2", tags=["Tailor V2"])


@router.post("/generate", response_model=TailorV2GenerateResponse)
def generate_v2_resume(request: TailorV2GenerateRequest):
    """
    Step 1: Generates initial tailored JSON without compiling to PDF.
    Checks Redis for an existing session with the same user + JD first.
    If cached, returns immediately. Otherwise, extracts text, calls model, and saves to Redis.
    """
    log.info("Tailor v2 generate requested by user: %s (template: %d)", request.user_id, request.template)
    norm_jd = request.job_desc.strip()
    session_id = compute_session_id(request.user_id, norm_jd)

    # 0. Redis Cache Check for identical Job Description
    existing_session = get_session(session_id)
    if existing_session and existing_session.get("tailored_json"):
        log.info("⚡ [Redis Cache Hit] Reusing active session %s for user %s", session_id, request.user_id)
        return TailorV2GenerateResponse(
            success=True,
            session_id=existing_session["session_id"],
            tailored_json=Format(**existing_session["tailored_json"]),
            revisions_remaining=existing_session["revisions_remaining"],
            expires_at=existing_session["expires_at"],
            version=existing_session["version"]
        )

    # 1. Download original PDF and extract raw text
    try:
        pdf_bytes = requests.get(str(request.resume_url), timeout=60).content
        original_txt = extract_resume_text_from_bytes(pdf_bytes)
    except Exception as e:
        log.error("Failed to download or extract resume text: %s", e)
        raise HTTPException(status_code=400, detail=f"Failed to extract resume from URL: {e}")

    # 2. Run tailor_jobs to generate structured Format (no LaTeX escaping here!)
    banner_message = None
    try:
        tailored_format = tailor_jobs(original_txt, [norm_jd], template=request.template, is_pro=request.is_pro)
        if hasattr(tailored_format, "tailored_jobs"):
            for tj in (tailored_format.tailored_jobs or []):
                sanitize_tailored_job(getattr(tailored_format, "static_profile", None), tj)
            rerank_sections_by_jd(tailored_format, norm_jd)
    except Exception as e:
        log.warning("Tailor model generation failed: %s", e)
        is_free_limit = (not request.is_pro) or ("FREE_TIER_RATE_LIMIT" in str(e)) or ("429" in str(e))
        if is_free_limit:
            log.info("Free user fallback: mapping original resume into template %d for user %s", request.template, request.user_id)
            banner_message = "Our AI services are receiving constant pressure and unable to tailor. Loaded your verified original resume content. Upgrade to Pro for high-speed dedicated AI."
            try:
                facts = extract_facts(original_txt)
                tailored_format = format_from_facts(facts)
            except Exception as fb_err:
                log.warning("Facts extraction failed on fallback, using raw parser: %s", fb_err)
                tailored_format = build_raw_fallback_format(original_txt)
        else:
            raise HTTPException(status_code=502, detail=f"AI model tailoring failed: {e}")

    # 3. Extract baseline facts for grounding revisions
    resume_facts = {
        "candidate_name": getattr(tailored_format.static_profile, "fullname", ""),
        "experience": [e.model_dump() for e in (tailored_format.tailored_jobs[0].experience if tailored_format.tailored_jobs else [])],
        "projects": [p.model_dump() for p in (tailored_format.tailored_jobs[0].projects if tailored_format.tailored_jobs else [])],
        "education": [ed.model_dump() for ed in (tailored_format.static_profile.education or [])]
    }

    # 4. Save unescaped session to Redis with 3-hour TTL
    session_data = save_new_session(
        user_id=request.user_id,
        job_desc=norm_jd,
        tailored_json=tailored_format.model_dump(),
        resume_facts=resume_facts,
        template=request.template
    )

    return TailorV2GenerateResponse(
        success=True,
        session_id=session_data["session_id"],
        tailored_json=Format(**session_data["tailored_json"]),
        revisions_remaining=session_data["revisions_remaining"],
        expires_at=session_data["expires_at"],
        version=session_data["version"],
        banner_message=banner_message
    )


@router.post("/revise", response_model=TailorV2ReviseResponse)
def revise_v2_resume(request: TailorV2ReviseRequest):
    """
    Step 2: Section-level chat editing.
    Acquires concurrency lock, consumes atomic credit, executes isolated revise agent,
    merges updated sections into Redis hash, and returns updated sections.
    """
    session_id = request.session_id

    # 1. Acquire distributed mutex lock
    if not acquire_lock(session_id, timeout_secs=30):
        log.warning("Lock contention: revision already running for %s", session_id)
        raise HTTPException(status_code=409, detail="A revision is currently in progress. Please wait.")

    try:
        # 2. Fetch session from Redis
        session = get_session(session_id)
        if not session:
            release_lock(session_id)
            raise HTTPException(status_code=410, detail="Tailor session expired or not found. Please regenerate.")

        # 3. Validate user ownership
        if session.get("user_id") != request.user_id:
            release_lock(session_id)
            raise HTTPException(status_code=403, detail="Unauthorized access to this tailoring session.")

        current_format = Format(**session["tailored_json"])

        # 4. Validate all requested section keys against actual format boundaries
        for comment in request.comments:
            is_valid, err_msg = validate_section_key(comment.section_key, current_format)
            if not is_valid:
                release_lock(session_id)
                raise HTTPException(status_code=400, detail=f"Invalid section tag '{comment.section_key}': {err_msg}")

        # 5. Atomically consume revision credit
        ok, remaining = consume_revision_credit(session_id)
        if not ok:
            release_lock(session_id)
            raise HTTPException(status_code=429, detail="Revision limit reached (3/3 used). Upgrade or start new session.")

        # 6. Extract targeted section payloads & invoke isolated revision agent
        tagged_sections = extract_sections_for_edit(current_format, request.comments)
        try:
            updated_sections = revise_sections_with_llm(
                job_description=session.get("job_description", ""),
                resume_facts=session.get("resume_facts", {}),
                tagged_sections=tagged_sections,
                comments=request.comments,
                is_pro=request.is_pro
            )
        except Exception as model_err:
            log.error("Model failure during revise for %s: %s", session_id, model_err)
            # Automatic rollback on model failure
            refund_revision_credit(session_id)
            if "FREE_TIER_RATE_LIMIT" in str(model_err) or (not request.is_pro and "429" in str(model_err)):
                raise HTTPException(
                    status_code=429,
                    detail="Our AI services are receiving constant pressure and unable to tailor right now. Upgrade to Pro for high-speed dedicated AI."
                )
            raise HTTPException(status_code=502, detail=f"AI section revision failed: {model_err}")

        # 7. Merge revisions into current format and persist updated JSON in Redis
        merged_format = merge_revised_sections(current_format, updated_sections)
        facts = session.get("resume_facts") or {}
        new_loc = merged_format.static_profile.location
        if new_loc and new_loc != facts.get("location"):
            facts["location"] = new_loc

        _, new_version = update_session_json(session_id, merged_format.model_dump(), updated_facts=facts)

        return TailorV2ReviseResponse(
            success=True,
            session_id=session_id,
            tailored_json=merged_format,
            updated_sections=updated_sections,
            revisions_remaining=remaining,
            version=new_version
        )

    finally:
        # Always guarantee lock release
        release_lock(session_id)


@router.get("/session", response_model=TailorV2SessionResponse)
def get_v2_session(
    user_id: str = Query(..., description="User ID"),
    session_id: str = Query(..., description="Session ID")
):
    """
    Step 3: Session recovery on page refresh or reconnection.
    """
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    if session.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized access to this session.")

    return TailorV2SessionResponse(
        success=True,
        session_id=session_id,
        tailored_json=Format(**session["tailored_json"]),
        revisions_remaining=session["revisions_remaining"],
        expires_at=session["expires_at"],
        version=session["version"]
    )


@router.post("/export/pdf")
def export_v2_pdf(request: TailorV2ExportRequest):
    """
    Step 4: Primary (Option 1) LaTeX Vector PDF Export.
    Renders Format JSON through Jinja template and compiles via the proven compilation cascade.
    """
    format_data: Optional[Format] = None

    if request.tailored_json:
        format_data = request.tailored_json
    elif request.session_id:
        session = get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session expired or not found.")
        if session.get("user_id") != request.user_id:
            raise HTTPException(status_code=403, detail="Unauthorized.")
        format_data = Format(**session["tailored_json"])
    else:
        raise HTTPException(status_code=400, detail="Either session_id or tailored_json must be provided.")

    if not format_data.tailored_jobs:
        raise HTTPException(status_code=400, detail="Invalid resume: no tailored jobs found.")

    tj = format_data.tailored_jobs[0]
    template = request.template

    try:
        # Clone format and escape LaTeX special characters only at export time
        escaped_format = Format(**format_data.model_dump())
        escape_pydantic(escaped_format)
        escaped_tj = escaped_format.tailored_jobs[0]

        # Compile through render_one_page (which uses the ENGINES cascade)
        pdf_bytes = render_one_page(
            escaped_format.static_profile,
            escaped_tj,
            template,
            has_experience=bool(escaped_tj.experience)
        )

        if not pdf_bytes:
            raise HTTPException(status_code=500, detail="LaTeX compilation failed across all compile engines.")

        base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
        return {
            "success": True,
            "payload": [base64_pdf],
            "media": "application/pdf"
        }
    except Exception as e:
        log.error("PDF export compilation failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Export failed: {e}")
