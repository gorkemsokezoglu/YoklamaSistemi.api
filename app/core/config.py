import os
from typing import Optional

class Settings:
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://admin:admin@localhost:5432/yoklama_db")
    
    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Gmail SMTP Ayarları
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    EMAIL_ADDRESS: str = os.getenv("EMAIL_ADDRESS", "yoklama.iuc@gmail.com")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "aklb ywkh hqga zejv")  # Gmail uygulama şifresi
    
    # Backend URL (doğrulama linklerinde kullanılacak)
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://192.168.1.107:8000")
    
    # Verification token expire time (minutes)
    VERIFICATION_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 saat

settings = Settings()
