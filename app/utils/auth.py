from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User
from app.core.config import settings

# JWT ayarları
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# Öğrencilerin erişebileceği endpoint'ler ve HTTP metodları
STUDENT_ALLOWED_ENDPOINTS: Dict[str, List[str]] = {
    # Attendances - Öğrenci erişimi
    "/api/v1/attendances": ["GET"],
    "/api/v1/attendances/myAttendances": ["GET"],
    "/api/v1/attendances/{attendance_id}": ["GET"],
    
    # Students - GET ve UPDATE
    "/api/v1/students/me": ["GET", "PUT"],
    "/api/v1/students/{user_id}": ["PUT"],
    
    # Academicians - Sadece GET
    "/api/v1/academicians": ["GET"],
    "/api/v1/academicians/{id}": ["GET"],
    
    # Face Data - Tüm metodlar
    "/api/v1/face-data": ["GET", "POST", "PUT", "DELETE"],
    "/api/v1/face-data/my-face-data": ["GET"],
    "/api/v1/face-data/upload-multiple": ["POST"],
    
    # Performance Records - Sadece GET
    "/api/v1/performance-records/my-records": ["GET"],
    
    # Courses - Sadece GET
    "/api/v1/courses": ["GET"],
    "/api/v1/courses/{id}": ["GET"],
    
    # Course Selections Student - Tüm metodlar
    "/api/v1/course-selections-student": ["GET", "POST", "PUT", "DELETE"],
    "/api/v1/course-selections-student/my-selections": ["GET"],
    "/api/v1/course-selections-student/{id}": ["GET", "PUT", "DELETE"],
    
    # Face Recognition
    "/api/v1/face-recognition/identify/{course_id}": ["POST"],
    
    # Auth endpoints
    "/auth/token": ["POST"],
    "/auth/register": ["POST"],
    "/auth/change-password": ["POST"],
    "/api/v1/auth/logout": ["POST"]
}

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_verification_token(email: str) -> str:
    """
    E-posta doğrulama için token oluşturur
    """
    expire = datetime.utcnow() + timedelta(minutes=settings.VERIFICATION_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": email,
        "exp": expire,
        "type": "email_verification"
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_verification_token(token: str) -> Optional[str]:
    """
    E-posta doğrulama token'ını doğrular ve email'i döner
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if email is None or token_type != "email_verification":
            return None
            
        return email
    except JWTError:
        return None

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Kimlik doğrulama başarısız",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

def check_endpoint_permission(request: Request, current_user: User = Depends(get_current_user)):
    """
    Endpoint ve HTTP metod bazlı yetkilendirme kontrolü.
    Akademisyenler tüm endpoint'lere erişebilir.
    Öğrenciler sadece izin verilen endpoint'lere ve metodlara erişebilir.
    """
    if current_user.role == "academician":
        return current_user

    # Öğrenci kontrolü
    if current_user.role == "student":
        current_path = request.url.path
        current_method = request.method
        
        # Dinamik path parametrelerini kontrol et
        for allowed_path, allowed_methods in STUDENT_ALLOWED_ENDPOINTS.items():
            # Path parametresi içeren endpoint'leri kontrol et
            if "{" in allowed_path:
                # Path pattern'ini regex pattern'e çevir
                pattern = allowed_path.replace("{id}", "[^/]+")
                if current_path.startswith(pattern.split("{")[0]) and current_method in allowed_methods:
                    return current_user
            # Tam eşleşen endpoint'leri kontrol et
            elif current_path == allowed_path and current_method in allowed_methods:
                return current_user
        
        # Erişim izni yoksa
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu endpoint'e erişim yetkiniz yok"
        )
    
    return current_user

def check_academician_role(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "academician":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için akademisyen yetkisi gerekiyor"
        )
    return current_user

def check_student_role(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için öğrenci yetkisi gerekiyor"
        )
    return current_user 