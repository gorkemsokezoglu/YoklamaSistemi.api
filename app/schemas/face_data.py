# app/schemas/face_data.py
from pydantic import BaseModel
from uuid import UUID
from typing import List
from datetime import datetime

class FaceDataBase(BaseModel):
    student_id: UUID
    face_image: str  # base64 encoded image

class FaceDataCreate(FaceDataBase):
    pass

class FaceDataResponse(FaceDataBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class FaceDataUpload(BaseModel):
    student_id: UUID
    face_images: List[str]  # List of base64 encoded images
