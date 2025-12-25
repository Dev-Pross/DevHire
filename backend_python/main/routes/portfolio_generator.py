import logging
import os
import mimetypes
import base64
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl, field_validator
from typing import List, Dict, Any, Optional
from agents.portfolio_agent import generate_portfolio_main as main
from main.routes import image2base64

class PortfolioRequest(BaseModel):
    resume_url: Optional[str] = None
    user_data: Optional[str] = None
    template: int = None

class PortfolioResponses(BaseModel):
    success: bool
    payload: str | None = None

class TemplatesResponse(BaseModel):
    image: str
    template: int

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

router = APIRouter()

@router.post("/portfolio", response_model= PortfolioResponses)
def portfolio_Builder(request: PortfolioRequest):
    try:
        if request.user_data and request.resume_url:
            raise HTTPException(
            status_code=500, 
            detail=f"Error processing Portfolio building too many params"
            )    
        log.info(f"template from request: {request.template}")
        code=""
        if request.resume_url and request.template is not None:
            code = main( template=request.template,url=request.resume_url)
        elif request.user_data and request.template is not None:
            code = main(template=request.template,user_data= request.user_data)
        # else:
        #     return PortfolioResponses(
        #         success=False,
        #         payload=None
        #     )
        
        if code:
            return PortfolioResponses(
                success=True,
                payload=code
            )
    except Exception as e:
        log.error(f"Error :{e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing Portfolio building: {str(e)}"
        )


@router.get('/portfolio/get-templates', response_model=List[TemplatesResponse])
def getTemplates():
    images = ['portfolio_1.png','portfolio_2.png','portfolio_3.png','portfolio_4.png','portfolio_5.png']
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


    