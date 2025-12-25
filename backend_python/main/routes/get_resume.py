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

router = APIRouter()

@router.post("/tailor",response_model=TailorResponses)
def tailor_resume(request: TailorRequest):
    try:
        print(f"{request.template} - template from route")
        resume_data = [{"job_url": "resume_", "job_description": request.job_desc or "**MAKE GENERAL RESUME**"}]
        # logging.info("resumedata: %s",resume_data)
        resume = []
        if request.resume_url:
            resume = tailor_main(request.resume_url, resume_data, template=request.template)
        else:
            resume = tailor_main(user_data=request.user_data, jobs=resume_data, template=request.template)
        if resume:
            logging.info("resume generated")
        # Extract just the base64 strings from the returned list for payload
        base64_list = [item["resume_binary"] for item in resume]
        return TailorResponses(
            success=True,
            payload=base64_list,
            media="application/pdf"
        )
    except Exception as e:
        logging.error(f"Error in apply_jobs_route: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing job applications: {str(e)}"
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

