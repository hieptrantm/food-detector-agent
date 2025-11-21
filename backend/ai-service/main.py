from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import httpx
import random
import base64
import cv2
import numpy as np
from inference import get_model
import supervision as sv
from config import YOLO_MODEL_DETECTOR
import os
from dotenv import load_dotenv

import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Create a logger
logger = logging.getLogger(__name__)

# Load Model API key
load_dotenv()
api_key = os.getenv('ROBOFLOW_API_KEY')
logger.info(f"API KEY LOADED: {api_key}")
os.environ['ROBOFLOW_API_KEY'] = api_key

app = FastAPI(title="AI Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AUTH_SERVICE_URL = "http://auth-service:8000"
# AUTH_SERVICE_URL = "http://localhost:8000"  # For local testing

class DetectionRequest(BaseModel):
    text: str

class ImageDetectionRequest(BaseModel):
    image: str  # base64 encoded image

class DetectionResponse(BaseModel):
    is_spam: bool
    confidence: float
    category: str

class ImageDetectionResponse(BaseModel):
    ingredients: list
    annotated_image: str  # base64 encoded image
    detections_count: int

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

@app.post("/ai/detect", response_model=DetectionResponse)
async def detect_spam(
    request: DetectionRequest,
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

@app.post("/ai/detect-image", response_model=ImageDetectionResponse)
# mock detector, change to yolo detector folder later
async def detect_image(
    request: ImageDetectionRequest,
    user=Depends(verify_token)
):
    try:
        # Decode base64 image
        image_data = base64.b64decode(request.image.split(',')[1])
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image data")
        # Load pre-trained YOLOv8 model for ingredient detection
        model = get_model(model_id=YOLO_MODEL_DETECTOR)
        
        # Run inference
        results = model.infer(image)[0]
        
        # Load results into supervision API
        detections = sv.Detections.from_inference(results)
        
        # Extract labels
        labels = detections.data.get('class_name', [])
        if isinstance(labels, np.ndarray):
            labels = labels.tolist()
        
        # Create annotators
        bounding_box_annotator = sv.BoxAnnotator()
        label_annotator = sv.LabelAnnotator()
        
        # Annotate image
        annotated_image = bounding_box_annotator.annotate(
            scene=image, detections=detections)
        annotated_image = label_annotator.annotate(
            scene=annotated_image, detections=detections)
        
        # Encode annotated image to base64
        _, buffer = cv2.imencode('.jpg', annotated_image)
        annotated_image_base64 = base64.b64encode(buffer).decode()
        
        return {
            "ingredients": list(set(labels)),  # Get unique ingredients
            "annotated_image": f"data:image/jpeg;base64,{annotated_image_base64}",
            "detections_count": len(labels)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")

@app.get("/ai/health")
def health():
    return {"status": "healthy", "user": "verified"}