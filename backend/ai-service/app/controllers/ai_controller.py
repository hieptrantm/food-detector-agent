from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Header
import os
import uuid
from datetime import datetime
import httpx
from fastapi.responses import FileResponse
# from inference import get_model
import cv2
# import supervision as sv 
import numpy as np
from roboflow import Roboflow

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["upload"])

UPLOAD_DIR = os.path.join(os.getcwd(), "uploaded_images")
logger.info(f"Upload directory set to: {UPLOAD_DIR}")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initial yolo model
ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY", "3aXT515V4jLqQU31PvbC")
if not ROBOFLOW_API_KEY:
    logger.warning("ROBOFLOW_API_KEY not set in environment variables")

rf = Roboflow(api_key=ROBOFLOW_API_KEY)
project = rf.workspace().project("uet-ingredient-detector-dwfkr")
version = project.version(1)
model = version.model

# Token verification function (copy from main.py)
async def verify_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    token = authorization.split(" ")[1]
    AUTH_SERVICE_URL = "http://auth-service:8000"
    
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

@router.get("/images/{filename}")
async def get_image(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(file_path)

@router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    user=Depends(verify_token)
):
    logger.info(f"Received upload request from user: {user}")
    logger.info(f"File details - filename: {file.filename}, content_type: {file.content_type}")
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Validate file size (max 10MB)
    content = await file.read()
    file_size = len(content)
    
    if file_size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 10MB")
    
    # Create unique filename
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    file_name = f"{uuid.uuid4()}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, file_name)
    
    # Save file
    try:
        with open(file_path, "wb") as f:
            f.write(content)
        logger.info(f"Saved file to {file_path}, size: {file_size} bytes")
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Detect objects using the pre-loaded model
    try:
        # Decode image from bytes to cv2 format
        nparr = np.frombuffer(content, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise ValueError("Failed to decode image")
        
        logger.info(f"Image shape: {image.shape}")
        
        # Run prediction using Roboflow model
        result = model.predict(image, confidence=40, overlap=30)
        result_json = result.json()
        logger.info(f"Roboflow result: {result_json}")
        
        # Extract predictions from result
        predictions = result_json.get('predictions', [])
        
        # Prepare detection results
        detection_results = []
        for pred in predictions:
            # Convert center x,y,width,height to x1,y1,x2,y2 format
            x_center = pred['x']
            y_center = pred['y']
            width = pred['width']
            height = pred['height']
            
            x1 = x_center - width / 2
            y1 = y_center - height / 2
            x2 = x_center + width / 2
            y2 = y_center + height / 2
            
            detection_results.append({
                "label": pred['class'],
                "confidence": float(pred['confidence']),
                "bbox": [x1, y1, x2, y2]
            })
        
        logger.info(f"Detection results: {detection_results}")
        
        # Draw bounding boxes on image
        annotated_image = image.copy()
        for pred in predictions:
            x_center = int(pred['x'])
            y_center = int(pred['y'])
            width = int(pred['width'])
            height = int(pred['height'])
            
            x1 = int(x_center - width / 2)
            y1 = int(y_center - height / 2)
            x2 = int(x_center + width / 2)
            y2 = int(y_center + height / 2)
            
            # Draw rectangle
            cv2.rectangle(annotated_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Draw label with confidence
            label_text = f"{pred['class']}: {pred['confidence']:.2f}"
            cv2.putText(annotated_image, label_text, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Save annotated image
        annotated_file_name = f"annotated_{file_name}"
        annotated_file_path = os.path.join(UPLOAD_DIR, annotated_file_name)
        cv2.imwrite(annotated_file_path, annotated_image)

    except Exception as e:
        logger.error(f"Error during detection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")
    
    return {
        "filename": file_name,
        "content_type": file.content_type,
        "file_path": file_path,
        "file_size": file_size,
        "uploaded_at": datetime.utcnow().isoformat(),
        "user_id": user.get("id"),
        "image_url": f"/ai/images/{file_name}",
        "annotated_image_url": f"/ai/images/{annotated_file_name}",
        "detections": detection_results,
        "total_detections": len(detection_results)
    }