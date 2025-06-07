# app/routers/auth.py
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from datetime import timedelta
from app.models.models import User, Student, Academician, FaceData
from app.database import get_db
from app.schemas.auth import UserCreate, UserResponse, LoginRequest, PasswordChange
from app.schemas.student import StudentCreate, StudentResponse, FaceDataCreate
from app.schemas.academician import AcademicianCreate, AcademicianResponse
from app.services.face_capture_service import FaceCaptureService
from app.utils.auth import (
    verify_password,
    create_access_token,
    get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_user
)
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

        # 1. Kullanıcı oluştur
        user = User(
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            email=user_data.email,
            password=hashed_password,
            role=user_data.role
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