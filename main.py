from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from curl_cffi import requests as curl_requests
import urllib.parse, os

app = FastAPI()
BASE_URL = "https://bridgetosuccess.learncentre.tech/public/study_api_sprint13_security_promo/"

class APICall(BaseModel):
    tag: str
    userId: str = "13247"
    isEBook: int = 0
    courseId: str = None
    categoryId: str = None

@app.post("/proxy")
async def proxy(req: APICall):
    params = {k: v for k, v in req.dict().items() if v is not None}
    body = "&".join([f"{k}={urllib.parse.quote(str(v), safe='')}" for k,v in params.items()])
    
    headers = {
        "User-Agent": "okhttp/5.3.2",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "ktx": "com.lct.bmightc", "ktxx": "11.0",
        "brand": "vivo", "model": "V2339A", "device_type": "android",
    }
    
    try:
        resp = curl_requests.post(BASE_URL, data=body, headers=headers, impersonate="chrome120", timeout=30)
        if "just a moment" in resp.text.lower():
            raise HTTPException(503, "Cloudflare protection")
        return resp.json()
    except Exception as e:
        raise HTTPException(500, str(e))
