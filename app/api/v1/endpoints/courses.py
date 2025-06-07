from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import date
from app.database import get_db
from app.models.models import Course, User
from app.schemas.course import CourseCreate, CourseResponse, CourseUpdate
from app.utils.auth import get_current_user, check_academician_role
from app.crud import crud_course

router = APIRouter(
    prefix="/api/v1/courses",
    tags=["courses"]
)

@router.get("/", response_model=List[CourseResponse])
async def get_courses(
    db: Session = Depends(get_db)
):
    """
    Tüm dersleri getirir (Public endpoint)
    """
    return db.query(Course).all()

@router.get("/my-courses", response_model=List[CourseResponse])
async def get_my_courses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Kullanıcının kendi derslerini getirir
    Öğrenci: Kayıtlı olduğu dersler
    Akademisyen: Verdiği dersler
    """
    if current_user.role == "student":
        return db.query(Course).join(Course.students).filter(User.id == current_user.id).all()
    else:
        return db.query(Course).filter(Course.academician_id == current_user.id).all()

@router.post("/", response_model=CourseResponse)
async def create_course(
    course: CourseCreate,
    current_user: User = Depends(check_academician_role),
    db: Session = Depends(get_db)
):
    """
    Yeni ders oluşturur (Sadece akademisyenler)
    """
    db_course = Course(**course.dict())
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course

@router.get("/{course_id}", response_model=CourseResponse)
async def get_course_by_id(
    course_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Belirli bir dersin detaylarını getirir (Public endpoint)
    """
    db_course = db.query(Course).filter(Course.id == course_id).first()
    if not db_course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ders bulunamadı"
        )
    return db_course

@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: UUID,
    course: CourseUpdate,
    current_user: User = Depends(check_academician_role),
    db: Session = Depends(get_db)
):
    """
    Ders bilgilerini günceller (Sadece akademisyenler)
    """
    db_course = db.query(Course).filter(Course.id == course_id).first()
    if not db_course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ders bulunamadı"
        )

    # Akademisyenin kendi dersi mi kontrol et
    if db_course.academician_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu dersi güncelleme yetkiniz yok"
        )

    for key, value in course.dict(exclude_unset=True).items():
        setattr(db_course, key, value)

    db.commit()
    db.refresh(db_course)
    return db_course

@router.delete("/{course_id}")
async def delete_course(
    course_id: UUID,
    current_user: User = Depends(check_academician_role),
    db: Session = Depends(get_db)
):
    """
    Dersi siler (Sadece akademisyenler)
    """
    db_course = db.query(Course).filter(Course.id == course_id).first()
    if not db_course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ders bulunamadı"
        )

    # Akademisyenin kendi dersi mi kontrol et
    if db_course.academician_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu dersi silme yetkiniz yok"
        )

    db.delete(db_course)
    db.commit()
    return {"message": "Ders başarıyla silindi"}

@router.post("/{course_id}/cancel")
async def cancel_course_attendance(
    course_id: UUID,
    cancel_date: date,
    current_user: User = Depends(check_academician_role),
    db: Session = Depends(get_db)
):
    """
    Belirli bir dersin belirli bir tarihteki yoklamalarını iptal eder.
    Bu yoklamalar null olarak işaretlenir ve devamsızlık oranını etkilemez.
    Sadece akademisyenler kendi dersleri için bu işlemi yapabilir.
    """
    # Dersin var olup olmadığını kontrol et
    db_course = db.query(Course).filter(Course.id == course_id).first()
    if not db_course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ders bulunamadı"
        )

    # Akademisyenin kendi dersi mi kontrol et
    if db_course.academician_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu ders için yoklama iptali yapma yetkiniz yok"
        )

    # Yoklamaları iptal et
    success = crud_course.cancel_course_attendance(db, course_id, cancel_date)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu ders için kayıtlı öğrenci bulunamadı"
        )

    return {"message": f"{cancel_date} tarihli ders yoklaması başarıyla iptal edildi"}
