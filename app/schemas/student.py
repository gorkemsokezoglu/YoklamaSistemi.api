from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from base64 import b64decode
import re

class StudentBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    faculty: str
    department: str
    student_number: str
    class_: str

    @validator('student_number')
    def validate_student_number(cls, v):
        if not re.match(r'^S[0-9]{10}$', v):
            raise ValueError('Öğrenci numarası "S" ile başlamalı ve 10 rakam içermelidir (Örnek: S2023000111)')
        return v

class FaceDataCreate(BaseModel):
    face_image_base64: str

    def get_face_image_bytes(self) -> bytes:
        try:
            return b64decode(self.face_image_base64)
        except Exception as e:
            raise ValueError(f"Base64 formatında hata: {str(e)}")

class StudentCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    faculty: str
    department: str
    student_number: str
    class_: str
    role: str = "student"
    face_data: List[dict] | None = None  # face_data dictionary listesi olarak gelecek

    @validator('email')
    def validate_student_email(cls, v):
        if not v.endswith('@ogr.iuc.edu.tr'):
            raise ValueError('Lütfen geçerli bir öğrenci mail adresi giriniz (@ogr.iuc.edu.tr)')
        return v
    
    @validator('class_')
    def validate_class(cls, v):
        if v is None:
            raise ValueError('Sınıf bilgisi boş olamaz')
        valid_classes = ['1', '2', '3', '4', 'hazirlik']
        if str(v).lower() not in valid_classes:
            raise ValueError('Geçerli bir sınıf bilgisi giriniz (1, 2, 3, 4 veya hazirlik)')
        return str(v)
    
    @validator('student_number')
    def validate_student_number(cls, v):
        if not re.match(r'^S[0-9]{10}$', v):
            raise ValueError('Öğrenci numarası "S" ile başlamalı ve 10 rakam içermelidir (Örnek: S2023000111)')
        return v

class StudentResponse(StudentBase):
    user_id: UUID
    role: str

    class Config:
        from_attributes = True

class StudentUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    faculty: str | None = None
    department: str | None = None
    student_number: str | None = None
    class_: str | None = None