from pydantic import BaseModel, EmailStr
from typing import Optional

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    role: str

class UserCreate(UserBase):
    faculty: str
    department: str
    student_number: Optional[str] = None  # Sadece öğrenciler için
    academician_number: Optional[str] = None  # Sadece akademisyenler için
    face_image: Optional[bytes] = None

class UserResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: EmailStr
    role: str

    class Config:
        from_attributes = True

class PasswordChange(BaseModel):
    current_password: str
    new_password: str
    confirm_new_password: str 