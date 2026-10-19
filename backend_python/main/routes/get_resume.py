import logging
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl, field_validator
from typing import List, Dict, Any, Optional
from agents.tailor import process_batch as tailor_main
from main.routes import image2base64


class _C:
    R = "\33[31m"
    G = "\33[32m"
    Y = "\33[33m"
    C = "\33[36m"
    M = "\33[35m"
    Z = "\33[0m"
_PALETTE = {"DEBUG": _C.C, "INFO": _C.G, "WARNING": _C.Y, "ERROR": _C.R, "CRITICAL": _C.M}
class _Fmt(logging.Formatter):
    def format(self, rec):
        rec.levelname = f"{_PALETTE.get(rec.levelname, _C.Z)}{rec.levelname}{_C.Z}"
        return super().format(rec)
hlr = logging.StreamHandler()
hlr.setFormatter(_Fmt("%(asctime)s | %(levelname)s | %(message)s"))
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper(), handlers=[hlr])
log = logging.getLogger("portfolio_route")


class TailorRequest(BaseModel):
    job_desc: Optional[str] = None
    resume_url: Optional[HttpUrl] = None
    user_data: Optional[str] = None
    template: int = None

class TemplatesResponse(BaseModel):
    image: str
    template: int  

class TailorResponses(BaseModel):
    success: bool
    payload: List[str]
    media: str
    is_fallback: bool = False
    message: Optional[str] = None

router = APIRouter()

import hashlib
import json
from config import redis_client

_REDIS_TTL_SECONDS = 7200  # 2 hours

def _get_cached_tailor_response(cache_key: str) -> Optional[Dict[str, Any]]:
    if not redis_client:
        return None
    try:
        raw = redis_client.get(f"tailor:{cache_key}")
        if raw:
            return json.loads(raw)
    except Exception as e:
        log.warning("Redis cache get error: %s", e)
    return None

def _set_cached_tailor_response(cache_key: str, data: Dict[str, Any]) -> None:
    if not redis_client:
        return
    try:
        redis_client.setex(f"tailor:{cache_key}", _REDIS_TTL_SECONDS, json.dumps(data))
    except Exception as e:
        log.warning("Redis cache set error: %s", e)

@router.post("/tailor",response_model=TailorResponses)
def tailor_resume(request: TailorRequest):
    try:
        if not request.resume_url and not request.user_data:
            raise HTTPException(
                status_code=400,
                detail="No resume provided. Please upload a resume in Profile before tailoring."
            )

        print(f"{request.template} - template from route")
        raw_desc = (request.job_desc or "").strip()
        norm_jd = "**MAKE GENERAL RESUME**" if not raw_desc or raw_desc.lower() == "general" else raw_desc
        
        # Check deterministic Redis cache for identical inputs
        cache_key = hashlib.sha256(f"{str(request.resume_url or '')}:{norm_jd}:{request.template}".encode("utf-8")).hexdigest()
        cached = _get_cached_tailor_response(cache_key)
        if cached:
            log.info("🎯 Redis Cache HIT for tailoring request (hash=%s)", cache_key[:12])
            return TailorResponses(**cached)

        resume_data = [{"job_url": "resume_", "job_description": norm_jd}]
        resume = []
        if request.resume_url:
            resume = tailor_main(request.resume_url, resume_data, template=request.template)
        else:
            resume = tailor_main(user_data=request.user_data, jobs=resume_data, template=request.template)
        if resume:
            logging.info("resume generated")
        # Extract just the base64 strings from the returned list for payload
        base64_list = [item["resume_binary"] for item in resume]
        is_fb = any(item.get("is_fallback") for item in resume) if resume else False
        msg = next((item.get("message") for item in resume if item.get("message")), None) if resume else None

        resp_dict = {
            "success": True,
            "payload": base64_list,
            "media": "application/pdf",
            "is_fallback": is_fb,
            "message": msg
        }
        # Only cache valid non-fallback responses so temporary provider issues don't stick
        if not is_fb and base64_list:
            _set_cached_tailor_response(cache_key, resp_dict)

        return TailorResponses(**resp_dict)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error in tailor route: {e}")
        user_msg = getattr(e, "user_message", None)
        if not user_msg and hasattr(e, "__cause__") and hasattr(e.__cause__, "user_message"):
            user_msg = e.__cause__.user_message
        if not user_msg:
            # Check if inner error message has known toast string
            user_msg = "Something went wrong. Please retry."
        raise HTTPException(
            status_code=500, 
            detail=user_msg
        )
    
@router.get('/tailor/get-templates', response_model=List[TemplatesResponse])
def getTemplates():
    images = ['templete-0.png','templete-1.png','templete-2.png','templete-3.png']
    base_folder = os.path.join(os.path.dirname(__file__),'templates')
    log.debug("base_folder : %s", base_folder)
    tempList = []
    try:
        for i, name in enumerate(images):
            file_path = os.path.join(base_folder,name)

            if os.path.exists(file_path):
                data_url = image2base64(file_path)
                log.info("url generated")
                log.info("template id %i and url %s", i, data_url[:20])
                tempList.append({
                    "image":data_url,
                    "template":i
                })
            else:
                log.error('folder not found: %s',file_path)
        # log.info(tempList)
        return tempList
    except Exception as e:
        log.error(f"Error :{e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing Portfolio building: {str(e)}"
        )

