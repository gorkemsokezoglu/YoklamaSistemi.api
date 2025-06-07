from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas import performance_record as performance_record_schemas
from app.crud import crud_performanceRecord as performance_record_crud
from app.database import get_db
from uuid import UUID
from typing import List
from app.models.models import PerformanceRecord, Course, User
from app.schemas.performance_record import PerformanceRecordCreate, PerformanceRecordResponse
from app.utils.auth import get_current_user, check_student_role, check_academician_role

router = APIRouter(
    prefix="/api/v1/performance-records",
    tags=["performance-records"]
)

@router.get("/my-records", response_model=List[PerformanceRecordResponse])
async def get_my_performance_records(
    current_user: User = Depends(check_student_role),
    db: Session = Depends(get_db)
):
    """
    Öğrencinin kendi performans kayıtlarını getirir
    """
    return db.query(PerformanceRecord).filter(PerformanceRecord.student_id == current_user.id).all()

@router.get("/course/{course_id}", response_model=List[PerformanceRecordResponse])
async def get_course_performance_records(
    course_id: UUID,
    current_user: User = Depends(check_academician_role),
    db: Session = Depends(get_db)
):
    """
    Belirli bir dersin performans kayıtlarını getirir (Sadece akademisyenler)
    """
    # Akademisyenin kendi dersi mi kontrol et
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.academician_id == current_user.id
    ).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ders bulunamadı veya bu derse erişim yetkiniz yok"
        )
    
    return db.query(PerformanceRecord).filter(PerformanceRecord.course_id == course_id).all()

@router.post("/", response_model=PerformanceRecordResponse)
async def create_performance_record(
    performance_record: PerformanceRecordCreate,
    current_user: User = Depends(check_academician_role),
    db: Session = Depends(get_db)
):
    """
    Yeni performans kaydı oluşturur (Sadece akademisyenler)
    """
    # Akademisyenin kendi dersi mi kontrol et
    course = db.query(Course).filter(
        Course.id == performance_record.course_id,
        Course.academician_id == current_user.id
    ).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ders bulunamadı veya bu derse erişim yetkiniz yok"
        )

    db_performance_record = PerformanceRecord(**performance_record.dict())
    db.add(db_performance_record)
    db.commit()
    db.refresh(db_performance_record)
    return db_performance_record

@router.put("/{record_id}", response_model=PerformanceRecordResponse)
async def update_performance_record(
    record_id: UUID,
    performance_record: PerformanceRecordCreate,
    current_user: User = Depends(check_academician_role),
    db: Session = Depends(get_db)
):
    """
    Performans kaydını günceller (Sadece akademisyenler)
    """
    db_record = db.query(PerformanceRecord).filter(PerformanceRecord.id == record_id).first()
    if not db_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Performans kaydı bulunamadı"
        )

    # Akademisyenin kendi dersi mi kontrol et
    course = db.query(Course).filter(
        Course.id == db_record.course_id,
        Course.academician_id == current_user.id
    ).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu performans kaydını güncelleme yetkiniz yok"
        )

    for key, value in performance_record.dict().items():
        setattr(db_record, key, value)

    db.commit()
    db.refresh(db_record)
    return db_record

@router.delete("/{record_id}")
async def delete_performance_record(
    record_id: UUID,
    current_user: User = Depends(check_academician_role),
    db: Session = Depends(get_db)
):
    """
    Performans kaydını siler (Sadece akademisyenler)
    """
    db_record = db.query(PerformanceRecord).filter(PerformanceRecord.id == record_id).first()
    if not db_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Performans kaydı bulunamadı"
        )

    # Akademisyenin kendi dersi mi kontrol et
    course = db.query(Course).filter(
        Course.id == db_record.course_id,
        Course.academician_id == current_user.id
    ).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu performans kaydını silme yetkiniz yok"
        )

    db.delete(db_record)
    db.commit()
    return {"message": "Performans kaydı başarıyla silindi"}