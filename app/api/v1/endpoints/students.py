import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.models import Student, User, FaceData
from app.schemas.student import StudentCreate, StudentResponse, StudentUpdate
from app.services.face_capture_service import FaceCaptureService
from app.crud import crud_student
from app.utils.auth import get_current_user, check_student_role, check_academician_role, get_password_hash
import base64

router = APIRouter(
    prefix="/api/v1/students",
    tags=["students"]
)

@router.post("/", response_model=StudentResponse)
async def create_student(
    student: StudentCreate,
    db: Session = Depends(get_db)
):
    """
    Yeni öğrenci kaydı oluşturur ve yüz verisi toplar
    """
    try:
        # 1. Kullanıcı oluştur
        user = User(
            first_name=student.first_name,
            last_name=student.last_name,
            email=student.email,
            password=get_password_hash(student.password),
            role="student"
        )
        db.add(user)
        db.flush()  # ID'yi almak için flush yap

        # 2. Öğrenci oluştur
        new_student = Student(
            user_id=user.id,
            faculty=student.faculty,
            department=student.department,
            student_number=student.student_number,
            class_=student.class_
        )
        db.add(new_student)
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

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/with-face-data", response_model=StudentResponse)
def create_student_with_face_data(
    student: StudentCreate,
    db: Session = Depends(get_db)
):
    """
    Yeni öğrenci kaydı oluşturur ve yüz verilerini kaydeder
    """
    try:
        # Email kontrolü
        existing_user = db.query(User).filter(User.email == student.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bu email adresi zaten kayıtlı"
            )

        # 1. Kullanıcı oluştur
        user = User(
            first_name=student.first_name,
            last_name=student.last_name,
            email=student.email,
            password=get_password_hash(student.password),
            role="student"
        )
        db.add(user)
        db.flush()  # ID'yi almak için flush yap

        # 2. Öğrenci oluştur
        new_student = Student(
            user_id=user.id,
            faculty=student.faculty,
            department=student.department,
            student_number=student.student_number,
            class_=student.class_
        )
        db.add(new_student)
        db.flush()

        # 3. Yüz verilerini kaydet
        for face_data in student.face_data:
            try:
                # Base64 string'i bytes'a çevir
                face_image_bytes = face_data.get_face_image_bytes()
                
                # Yüz verisini kaydet
                db_face_data = FaceData(
                    student_id=user.id,
                    face_image=face_image_bytes
                )
                db.add(db_face_data)
            except Exception as e:
                print(f"Yüz verisi kaydedilirken hata oluştu: {str(e)}")
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Yüz verisi kaydedilemedi: {str(e)}"
                )

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

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/me", response_model=StudentResponse)
async def read_student_me(
    current_user: User = Depends(check_student_role),
    db: Session = Depends(get_db)
):
    """
    Giriş yapmış öğrencinin kendi bilgilerini getirir
    """
    student = crud_student.get_student(db, current_user.id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Öğrenci bulunamadı"
        )
    return student

@router.get("/{student_id}", response_model=StudentResponse)
def get_student(
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ID'ye göre öğrenci getirir
    """
    # Öğrenci kendi bilgilerine erişebilir
    if current_user.role == "student" and str(current_user.id) != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu bilgilere erişim yetkiniz yok"
        )
    
    student = crud_student.get_student(db, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Öğrenci bulunamadı"
        )
    return student

@router.get("/", response_model=List[StudentResponse])
def get_students(
    current_user: User = Depends(check_academician_role),
    db: Session = Depends(get_db)
):
    """
    Tüm öğrencileri getirir (Sadece akademisyenler erişebilir)
    """
    return crud_student.get_students(db)

@router.put("/me", response_model=StudentResponse)
async def update_student_me(
    student_update: StudentUpdate,
    current_user: User = Depends(check_student_role),
    db: Session = Depends(get_db)
):
    """
    Giriş yapmış öğrencinin kendi bilgilerini günceller
    """
    updated_student = crud_student.update_student(db, str(current_user.id), student_update)
    if not updated_student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Öğrenci bulunamadı"
        )
    return updated_student

@router.put("/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: str,
    student_update: StudentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Öğrenci bilgilerini günceller.
    Öğrenciler sadece kendi bilgilerini güncelleyebilir.
    Akademisyenler tüm öğrencilerin bilgilerini güncelleyebilir.
    """
    # Yetki kontrolü
    if current_user.role == "student" and str(current_user.id) != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sadece kendi bilgilerinizi güncelleyebilirsiniz"
        )
    
    # Öğrenciyi güncelle
    updated_student = crud_student.update_student(db, student_id, student_update)
    if not updated_student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Öğrenci bulunamadı"
        )
    return updated_student

@router.delete("/me")
async def delete_student_me(
    current_user: User = Depends(check_student_role),
    db: Session = Depends(get_db)
):
    """
    Giriş yapmış öğrencinin kendi hesabını siler
    """
    student = crud_student.get_student(db, current_user.id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Öğrenci bulunamadı"
        )
    
    crud_student.delete_student(db, current_user.id)
    return {"message": "Hesabınız başarıyla silindi"}
