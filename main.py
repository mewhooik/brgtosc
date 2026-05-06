# main.py - Pydantic v1 Compatible
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field, validator  # v1 import
from curl_cffi import requests as curl_requests
import urllib.parse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="BTS API Proxy", version="1.0")
BASE_URL = "https://bridgetosuccess.learncentre.tech/public/study_api_sprint13_security_promo/"

# ✅ Pydantic v1 Model
class APICall(BaseModel):
    tag: str = Field(..., regex="^(allCourses|getCategoryMixed)$")
    userId: str = "13247"
    isEBook: int = 0
    courseId: str = None
    categoryId: str = None
    brand: str = None
    model: str = None
    
    # ✅ Pydantic v1 validator syntax
    @validator('tag')
    def tag_must_be_valid(cls, v):
        if v not in ["allCourses", "getCategoryMixed"]:
            raise ValueError('tag must be allCourses or getCategoryMixed')
        return v

def get_headers(brand="vivo", model="V2339A"):
    return {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "Keep-Alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Host": "bridgetosuccess.learncentre.tech",
        "Origin": "https://bridgetosuccess.learncentre.tech",
        "Referer": "https://bridgetosuccess.learncentre.tech/",
        "User-Agent": "okhttp/5.3.2",
        "ktx": "com.lct.bmightc",
        "ktxx": "11.0",
        "model": model,
        "brand": brand,
        "device_type": "android",
        "X-Requested-With": "com.lct.bmightc",
    }

@app.post("/proxy")
async def proxy(req: APICall, request: Request):
    try:
        # Build form body
        params = {k: v for k, v in req.dict(exclude_none=True).items() 
                  if k not in ["brand", "model"]}
        body_parts = [f"{k}={urllib.parse.quote(str(v), safe='')}" for k, v in params.items()]
        body = "&".join(body_parts)
        
        logger.info(f"[Proxy] tag={req.tag} | body={body[:100]}")
        
        headers = get_headers(
            brand=req.brand or "vivo",
            model=req.model or "V2339A"
        )
        
        # ✅ curl_cffi with Chrome impersonation
        resp = curl_requests.post(
            BASE_URL,
            data=body,
            headers=headers,
            impersonate="chrome120",
            timeout=30,
            allow_redirects=True
        )
        
        # Cloudflare check
        if "just a moment" in resp.text.lower() or "cf-browser" in resp.text.lower():
            logger.warning("🚫 Cloudflare protection detected")
            raise HTTPException(
                status_code=503,
                detail={"success": 0, "error": 1, "error_msg": "Cloudflare blocked request"}
            )
        
        return resp.json()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Proxy error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"success": 0, "error": 1, "error_msg": f"Proxy error: {str(e)}"}
        )

@app.get("/health")
async def health():
    return {"status": "ok", "service": "bts-proxy"}

# CORS
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
