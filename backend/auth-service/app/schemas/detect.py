from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
import base64

class GetDetectDetailRequest(BaseModel):
    id: str
    
class GetDetectDetailResponse(BaseModel):
    id: int
    user_id: int
    image: str = Field(..., description="Base64 encoded image")
    image_mime_type: Optional[str] = None
    detected_ingredients: Optional[List[str]] = None
    recommendation: Optional[str] = None
    created_at: datetime

    @field_validator("image", mode="before")
    def convert_bytes_to_base64(cls, v):
        # ✅ Convert DB BYTEA → Base64 string
        if isinstance(v, (bytes, bytearray)):
            return base64.b64encode(v).decode("utf-8")
        return v

    class Config:
        from_attributes = True
    

class CreateDetectRequest(BaseModel):
    user_id: int
    image_base64: str
    image_mime_type: Optional[str]
    detected_ingredients: Optional[List[str]] = None
    recommendation: Optional[str] = None
    
class GetDetectDetailListResponse(BaseModel):
    id: int
    user_id: int
    image_mime_type: Optional[str] = None
    detected_ingredients: Optional[List[str]] = None
    recommendation: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class GetDetectsByDateResponse(BaseModel):
    total: int
    offset: int
    limit: int
    start_date: Optional[str]
    end_date: Optional[str]
    detects: List[GetDetectDetailListResponse]
    
    class Config:
        from_attributes = True
