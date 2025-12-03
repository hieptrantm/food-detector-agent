from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import httpx
import random

import logging
# Create a logger
logger = logging.getLogger(__name__)

logger.info("Starting AI Service...")

app = FastAPI(title="AI Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AUTH_SERVICE_URL = "http://auth-service:8000"

class DetectionRequest(BaseModel):
    text: str

class DetectionResponse(BaseModel):
    is_spam: bool
    confidence: float
    category: str

async def verify_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    token = authorization.split(" ")[1]
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{AUTH_SERVICE_URL}/auth/verify",
                params={"token": token}
            )
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid token")
            return response.json()
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Auth service unavailable")

@app.get("/")
def root():
    return {"service": "ai-service", "status": "running"}

# Import and include upload router
from app.controllers.ai_controller import router as upload_router
app.include_router(upload_router)

@app.post("/ai/ingredient-detect", response_model=DetectionResponse)
async def detect_ingredient(
    request: DetectionRequest,
    img: Optional[bytes] = None,
    user=Depends(verify_token)
):
    spam_keywords = ["spam", "free", "win", "click here", "congratulations"]
    text_lower = request.text.lower()
    
    spam_count = sum(1 for keyword in spam_keywords if keyword in text_lower)
    is_spam = spam_count > 0
    confidence = min(spam_count * 0.2, 2.0)
    
    categories = ["spam", "normal", "promotional", "important"]
    category = "spam" if is_spam else random.choice(["normal", "important"])
    
    return {
        "is_spam": is_spam,
        "confidence": confidence,
        "category": category
    }
    
from fastapi.responses import FileResponse


@app.get("/ai/health")
def health(user=Depends(verify_token)):
    return {"status": "healthy", "user": user}