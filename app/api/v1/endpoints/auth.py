# app/routers/auth.py
from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from datetime import timedelta
from app.models.models import User, Student, Academician, FaceData
from app.database import get_db
from app.schemas.auth import UserCreate, UserResponse, LoginRequest, PasswordChange
from app.schemas.student import StudentCreate, StudentResponse, FaceDataCreate
from app.schemas.academician import AcademicianCreate, AcademicianResponse
from app.services.face_capture_service import FaceCaptureService
from app.services.email_service import EmailService
from app.services.verification_cache import verification_cache
from app.schemas.verification import VerificationCodeRequest, VerificationCodeVerify, VerificationCodeResponse, VerificationStatusResponse, ForgotPasswordRequest, ResetPasswordRequest, ResetPasswordResponse
from app.utils.auth import (
    verify_password,
    create_access_token,
    get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_user,
    create_verification_token,
    verify_verification_token
)
from app.core.config import settings
from typing import Union
from base64 import b64decode

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"]
)

@router.post("/token")
async def login_for_access_token(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Kullanıcı girişi yaparak access token alır
    """
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz email veya şifre",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Şifre kontrolü - hem hash'lenmiş hem de hash'lenmemiş şifreleri kontrol et
    is_password_valid = False
    try:
        # Önce hash'lenmiş şifre kontrolü
        is_password_valid = verify_password(login_data.password, user.password)
    except:
        # Hash'lenmemiş şifre kontrolü
        is_password_valid = (login_data.password == user.password)
        if is_password_valid:
            # Şifreyi hash'le ve güncelle
            user.password = get_password_hash(login_data.password)
            db.commit()

    if not is_password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz email veya şifre",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # E-posta doğrulama kontrolü
    if not user.verifiedEmail:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Lütfen önce e-posta adresinizi doğrulayın. E-posta kutunuzu kontrol edin.",
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role
    }

@router.post("/register", response_model=Union[StudentResponse, AcademicianResponse])
async def register(
    user_data: Union[StudentCreate, AcademicianCreate],
    db: Session = Depends(get_db)
):
    """
    Yeni kullanıcı kaydı oluşturur. Öğrenci ise yüz verilerini kaydeder.
    """
    try:
        # Debug için gelen veriyi logla
        print("Gelen kayıt verisi:", user_data.dict())

        # Email kontrolü
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bu email adresi zaten kayıtlı"
            )

        # Öğrenci kaydı için email kontrolü
        if user_data.role == "student" and not user_data.email.endswith('@ogr.iuc.edu.tr'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Öğrenci kaydı için lütfen geçerli bir okul mail adresi kullanın (@ogr.iuc.edu.tr)"
            )

        # Şifreyi hashle
        hashed_password = get_password_hash(user_data.password)

        # 1. Kullanıcı oluştur (verifiedEmail=False olarak)
        user = User(
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            email=user_data.email,
            password=hashed_password,
            role=user_data.role,
            verifiedEmail=False  # E-posta doğrulanmamış olarak başlat
        )
        db.add(user)
        db.flush()

        # 2. Rol bazlı kayıt işlemi
        if user_data.role == "student":
            # Öğrenci kaydı
            new_student = Student(
                user_id=user.id,
                faculty=user_data.faculty,
                department=user_data.department,
                student_number=user_data.student_number,
                class_=str(user_data.class_)
            )
            db.add(new_student)
            db.flush()
            
            # Yüz verilerini kaydet
            if hasattr(user_data, 'face_data') and user_data.face_data:
                try:
                    for face_data in user_data.face_data:
                        if isinstance(face_data, dict) and 'face_image_base64' in face_data:
                            try:
                                face_image_bytes = b64decode(face_data['face_image_base64'])
                                new_face_data = FaceData(
                                    student_id=new_student.user_id,
                                    face_image=face_image_bytes
                                )
                                db.add(new_face_data)
                            except Exception as e:
                                print(f"Yüz verisi işlenirken hata: {str(e)}")
                                continue
                except Exception as e:
                    print(f"Yüz verileri işlenirken hata: {str(e)}")
            
            db.commit()
            
            # E-posta doğrulama kodu gönder
            try:
                email_service = EmailService()
                verification_code = verification_cache.store_code(user.email, expire_minutes=3)
                user_name = f"{user.first_name} {user.last_name}"
                
                email_sent = email_service.send_verification_code(
                    to_email=user.email,
                    verification_code=verification_code,
                    user_name=user_name
                )
                
                if not email_sent:
                    print(f"E-posta gönderimi başarısız: {user.email}")
            except Exception as e:
                print(f"E-posta gönderimi hatası: {str(e)}")
            
            return StudentResponse(
                user_id=new_student.user_id,
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
                faculty=new_student.faculty,
                department=new_student.department,
                student_number=new_student.student_number,
                class_=new_student.class_,
                role=user.role
            )

        elif user_data.role == "academician":
            # Akademisyen kaydı
            new_academician = Academician(
                user_id=user.id,
                faculty=user_data.faculty,
                department=user_data.department,
                academician_number=user_data.academician_number
            )
            db.add(new_academician)
            db.commit()
            db.refresh(new_academician)  # Veritabanından güncel veriyi al
            
            # E-posta doğrulama kodu gönder
            try:
                email_service = EmailService()
                verification_code = verification_cache.store_code(user.email, expire_minutes=3)
                user_name = f"{user.first_name} {user.last_name}"
                
                email_sent = email_service.send_verification_code(
                    to_email=user.email,
                    verification_code=verification_code,
                    user_name=user_name
                )
                
                if not email_sent:
                    print(f"E-posta gönderimi başarısız: {user.email}")
            except Exception as e:
                print(f"E-posta gönderimi hatası: {str(e)}")
            
            return AcademicianResponse(
                user_id=new_academician.user_id,
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
                faculty=new_academician.faculty,
                department=new_academician.department,
                academician_number=new_academician.academician_number,
                role=user.role,
                created_at=new_academician.created_at
            )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Kullanıcının şifresini değiştirir
    """
    # Mevcut şifreyi kontrol et
    is_password_valid = verify_password(password_data.current_password, current_user.password)
    if not is_password_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mevcut şifre yanlış"
        )

    # Yeni şifre ve onay şifresinin eşleştiğini kontrol et
    if password_data.new_password != password_data.confirm_new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Yeni şifre ve onay şifresi eşleşmiyor"
        )

    # Yeni şifreyi hash'le ve güncelle
    current_user.password = get_password_hash(password_data.new_password)
    db.commit()

    return {"message": "Şifreniz başarıyla değiştirildi"}

@router.get("/verify-email")
async def verify_email(
    token: str = Query(..., description="E-posta doğrulama token'ı"),
    db: Session = Depends(get_db)
):
    """
    E-posta doğrulama token'ını kullanarak kullanıcının e-postasını doğrular (eski sistem)
    """
    # Token'ı doğrula ve email'i al
    email = verify_verification_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Geçersiz veya süresi dolmuş doğrulama linki"
        )
    
    # Kullanıcıyı bul
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kullanıcı bulunamadı"
        )
    
    # Zaten doğrulanmış mı kontrol et
    if user.verifiedEmail:
        return {"message": "E-posta adresi zaten doğrulanmış"}
    
    # E-postayı doğrulanmış olarak işaretle
    user.verifiedEmail = True
    db.commit()
    
    return {
        "message": "E-posta adresiniz başarıyla doğrulandı. Artık giriş yapabilirsiniz.",
        "email": email
    }

@router.post("/verify-code", response_model=VerificationStatusResponse)
async def verify_code(
    verification_data: VerificationCodeVerify,
    db: Session = Depends(get_db)
):
    """
    E-posta doğrulama kodunu kontrol eder (yeni sistem)
    """
    # Kullanıcıyı bul
    user = db.query(User).filter(User.email == verification_data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bu e-posta adresi ile kayıtlı kullanıcı bulunamadı"
        )
    
    # Zaten doğrulanmış mı kontrol et
    if user.verifiedEmail:
        return VerificationStatusResponse(
            message="E-posta adresi zaten doğrulanmış",
            email=verification_data.email,
            verified=True
        )
    
    # Kodu doğrula
    is_valid = verification_cache.verify_code(verification_data.email, verification_data.code, code_type="verification")
    
    if is_valid:
        # E-postayı doğrulanmış olarak işaretle
        user.verifiedEmail = True
        db.commit()
        
        return VerificationStatusResponse(
            message="E-posta adresiniz başarıyla doğrulandı! Artık giriş yapabilirsiniz.",
            email=verification_data.email,
            verified=True
        )
    else:
        # Kalan süreyi kontrol et
        remaining_time = verification_cache.get_remaining_time(verification_data.email, code_type="verification")
        
        if remaining_time is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Doğrulama kodu süresi dolmuş veya geçersiz. Lütfen yeni kod talep edin."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Geçersiz doğrulama kodu. Kalan süre: {remaining_time} saniye"
            )

@router.post("/resend-verification", response_model=VerificationCodeResponse)
async def resend_verification_code(
    request: VerificationCodeRequest,
    db: Session = Depends(get_db)
):
    """
    Doğrulama kodunu yeniden gönderir
    """
    # Kullanıcıyı bul
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bu e-posta adresi ile kayıtlı kullanıcı bulunamadı"
        )
    
    # Zaten doğrulanmış mı kontrol et
    if user.verifiedEmail:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="E-posta adresi zaten doğrulanmış"
        )
    
    # Aktif kod var mı kontrol et
    if verification_cache.has_active_code(request.email, code_type="verification"):
        remaining_time = verification_cache.get_remaining_time(request.email, code_type="verification")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Zaten aktif bir doğrulama kodunuz var. Kalan süre: {remaining_time} saniye"
        )
    
    # Yeni doğrulama kodu gönder
    try:
        email_service = EmailService()
        verification_code = verification_cache.store_code(request.email, expire_minutes=3, code_type="verification")
        user_name = f"{user.first_name} {user.last_name}"
        
        email_sent = email_service.send_verification_code(
            to_email=request.email,
            verification_code=verification_code,
            user_name=user_name
        )
        
        if not email_sent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="E-posta gönderimi başarısız"
            )
        
        return VerificationCodeResponse(
            message="Yeni doğrulama kodu e-posta adresinize gönderildi",
            remaining_time=180  # 3 dakika
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"E-posta gönderimi hatası: {str(e)}"
        )

@router.post("/forgot-password", response_model=VerificationCodeResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Şifre sıfırlama kodu gönderir
    """
    # Kullanıcıyı bul
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bu e-posta adresi ile kayıtlı kullanıcı bulunamadı"
        )
    
    # Aktif şifre sıfırlama kodu var mı kontrol et
    if verification_cache.has_active_code(request.email, code_type="reset"):
        remaining_time = verification_cache.get_remaining_time(request.email, code_type="reset")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Zaten aktif bir şifre sıfırlama kodunuz var. Kalan süre: {remaining_time} saniye"
        )
    
    # Şifre sıfırlama kodu gönder
    try:
        email_service = EmailService()
        reset_code = verification_cache.store_code(request.email, expire_minutes=5, code_type="reset")
        user_name = f"{user.first_name} {user.last_name}"
        
        email_sent = email_service.send_password_reset_code(
            to_email=request.email,
            reset_code=reset_code,
            user_name=user_name
        )
        
        if not email_sent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="E-posta gönderimi başarısız"
            )
        
        return VerificationCodeResponse(
            message="Şifre sıfırlama kodu e-posta adresinize gönderildi",
            remaining_time=300  # 5 dakika
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"E-posta gönderimi hatası: {str(e)}"
        )

@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Şifre sıfırlama kodunu kullanarak şifreyi değiştirir
    """
    # Kullanıcıyı bul
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bu e-posta adresi ile kayıtlı kullanıcı bulunamadı"
        )
    
    # Şifre onayını kontrol et
    if request.new_password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Yeni şifre ve onay şifresi eşleşmiyor"
        )
    
    # Şifre uzunluğunu kontrol et
    if len(request.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Şifre en az 6 karakter olmalıdır"
        )
    
    # Kodu doğrula
    is_valid = verification_cache.verify_code(request.email, request.code, code_type="reset")
    
    if not is_valid:
        # Kalan süreyi kontrol et
        remaining_time = verification_cache.get_remaining_time(request.email, code_type="reset")
        
        if remaining_time is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Şifre sıfırlama kodu süresi dolmuş veya geçersiz. Lütfen yeni kod talep edin."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Geçersiz şifre sıfırlama kodu. Kalan süre: {remaining_time} saniye"
            )
    
    # Şifreyi güncelle
    user.password = get_password_hash(request.new_password)
    db.commit()
    
    return ResetPasswordResponse(
        message="Şifreniz başarıyla değiştirildi. Artık yeni şifrenizle giriş yapabilirsiniz.",
        email=request.email
    )

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user)
):
    """
    Kullanıcı çıkış işlemi
    """
    return {
        "message": "Başarıyla çıkış yapıldı",
        "user_email": current_user.email
    }