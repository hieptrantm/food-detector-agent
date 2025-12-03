from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Header
import os
import uuid
from datetime import datetime
import httpx
from fastapi.responses import FileResponse
from inference import get_model
import cv2
import supervision as sv 
import numpy as np

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["upload"])

UPLOAD_DIR = os.path.join(os.getcwd(), "uploaded_images")
logger.info(f"Upload directory set to: {UPLOAD_DIR}")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initial yolo model
ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY", "")
if not ROBOFLOW_API_KEY:
    logger.warning("ROBOFLOW_API_KEY not set in environment variables")
model = get_model(model_id="uet-ingredient-detector-dwfkr/1", api_key=ROBOFLOW_API_KEY)

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
        nparr = np.frombuffer(content, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise ValueError("Failed to decode image")
        
        logger.info(f"Image shape: {image.shape}")
        
        # Run inference
        results = model.infer(image)[0]
        
        # Load results into supervision Detections
        detections = sv.Detections.from_inference(results)
        logger.info(f"Detections: {detections}")
        
        # Extract labels and confidences
        if 'class_name' in detections.data:
            labels = detections.data['class_name'].tolist() if hasattr(detections.data['class_name'], 'tolist') else list(detections.data['class_name'])
        else:
            labels = [f"Object {i}" for i in range(len(detections))]
        
        confidences = detections.confidence.tolist() if detections.confidence is not None else []
        bboxes = detections.xyxy if detections.xyxy is not None else []
        
        # Create annoted image (optional)
        bounding_box_annotator = sv.BoxAnnotator()
        label_annotator = sv.LabelAnnotator()
        
        annotated_image = bounding_box_annotator.annotate(
            scene=image.copy(), detections=detections)
        annotated_image = label_annotator.annotate(
            scene=annotated_image, detections=detections)
        
        # Save annotated image
        annotated_file_name = f"annotated_{file_name}"
        annotated_file_path = os.path.join(UPLOAD_DIR, annotated_file_name)
        cv2.imwrite(annotated_file_path, annotated_image)
        
        # Prepare detection results
        detection_results = []
        for i, label in enumerate(labels):
            bbox = bboxes[i].tolist() if i < len(bboxes) and hasattr(bboxes[i], 'tolist') else []
            detection_results.append({
                "label": label,
                "confidence": float(confidences[i]) if i < len(confidences) else 0.0,
                "bbox": bbox
            })
            
        logger.info(f"Detection results: {detection_results}")

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