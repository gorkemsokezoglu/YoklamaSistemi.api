from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from uuid import UUID
from datetime import datetime
import re

class AcademicianBase(BaseModel):
    faculty: str
    department: str
    academician_number: str

    @validator('academician_number')
    def validate_academician_number(cls, v):
        if not re.match(r'^A[0-9]{8}$', v):
            raise ValueError('Akademisyen numarası "A" ile başlamalı ve 8 rakam içermelidir (Örnek: A23000111)')
        return v

class AcademicianCreate(AcademicianBase):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    role: str = "academician"

    @validator('email')
    def validate_academician_email(cls, v):
        if not v.endswith('@iuc.edu.tr'):
            raise ValueError('Lütfen geçerli bir akademisyen mail adresi giriniz (@iuc.edu.tr)')
        return v

class AcademicianUpdate(AcademicianBase):
    first_name: str
    last_name: str
    email: EmailStr

    @validator('email')
    def validate_academician_email(cls, v):
        if not v.endswith('@iuc.edu.tr'):
            raise ValueError('Lütfen geçerli bir akademisyen mail adresi giriniz (@iuc.edu.tr)')
        return v

class AcademicianResponse(AcademicianBase):
    user_id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True

class AcademicianOut(AcademicianBase):
    user_id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True