from pydantic import BaseModel, EmailStr
from typing import Optional

class VerificationCodeRequest(BaseModel):
    email: EmailStr

class VerificationCodeVerify(BaseModel):
    email: EmailStr
    code: str

class VerificationCodeResponse(BaseModel):
    message: str
    remaining_time: Optional[int] = None
    attempts_left: Optional[int] = None

class VerificationStatusResponse(BaseModel):
    message: str
    email: str
    verified: bool

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str
    confirm_password: str

class ResetPasswordResponse(BaseModel):
    message: str
    email: str 