# app/routers/attendances.py
import cv2
# import face_recognition
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.models import User, Attendance, Course
from app.schemas import attendance as attendance_schemas
from app.crud import crud_attendance as attendance_crud
from app.database import get_db
from uuid import UUID
from typing import List
from datetime import date
from app.utils.auth import get_current_user, check_student_role, check_academician_role

router = APIRouter(
    prefix="/api/v1/attendances",
    tags=["attendances"]
)

@router.post("/", response_model=attendance_schemas.AttendanceOut)
def create_attendance(attendance: attendance_schemas.AttendanceCreate, db: Session = Depends(get_db)):
    return attendance_crud.create_attendance(db, attendance)

@router.get("/", response_model=List[attendance_schemas.AttendanceOut])
def read_attendances(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Tüm yoklama kayıtlarını getirir
    Öğrenci: Sadece kendi kayıtlarını görür
    Akademisyen: Kendi derslerinin kayıtlarını görür
    """
    if current_user.role == "student":
        return db.query(Attendance).filter(Attendance.student_id == current_user.id).all()
    elif current_user.role == "academician":
        return db.query(Attendance).join(Course).filter(Course.academician_id == current_user.id).all()
    else:
        return db.query(Attendance).all()

@router.get("/{attendance_id}", response_model=attendance_schemas.AttendanceOut)
def read_attendance(
    attendance_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Belirli bir yoklama kaydını getirir
    Öğrenci: Sadece kendi kaydını görür
    Akademisyen: Kendi dersinin kaydını görür
    """
    db_attendance = attendance_crud.get_attendance(db, attendance_id)
    if db_attendance is None:
        raise HTTPException(status_code=404, detail="Yoklama kaydı bulunamadı")

    # Yetki kontrolü
    if current_user.role == "student" and db_attendance.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu yoklama kaydına erişim yetkiniz yok"
        )
    elif current_user.role == "academician":
        course = db.query(Course).filter(
            Course.id == db_attendance.course_id,
            Course.academician_id == current_user.id
        ).first()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu yoklama kaydına erişim yetkiniz yok"
            )

    return db_attendance

@router.put("/{attendance_id}", response_model=attendance_schemas.AttendanceOut)
def update_attendance(attendance_id: UUID, attendance: attendance_schemas.AttendanceUpdate, db: Session = Depends(get_db)):
    db_attendance = attendance_crud.update_attendance(db, attendance_id, attendance)
    if db_attendance is None:
        raise HTTPException(status_code=404, detail="Attendance not found")
    return db_attendance

@router.delete("/{attendance_id}", response_model=attendance_schemas.AttendanceOut)
def delete_attendance(attendance_id: UUID, db: Session = Depends(get_db)):
    db_attendance = attendance_crud.delete_attendance(db, attendance_id)
    if db_attendance is None:
        raise HTTPException(status_code=404, detail="Attendance not found")
    return db_attendance

@router.get("/myAttendances/", response_model=List[attendance_schemas.AttendanceOut])
async def get_my_attendances(
    course_id: UUID = None,
    start_date: date = None,
    end_date: date = None,
    current_user: User = Depends(check_student_role),
    db: Session = Depends(get_db)
):
    """
    Öğrencinin kendi yoklama kayıtlarını getirir
    """
    query = db.query(Attendance).filter(Attendance.student_id == current_user.id)
    
    if course_id:
        query = query.filter(Attendance.course_id == course_id)
    if start_date:
        query = query.filter(Attendance.date >= start_date)
    if end_date:
        query = query.filter(Attendance.date <= end_date)
        
    return query.all()

@router.get("/course/{course_id}", response_model=List[attendance_schemas.AttendanceOut])
async def get_course_attendances(
    course_id: UUID,
    start_date: date = None,
    end_date: date = None,
    current_user: User = Depends(check_academician_role),
    db: Session = Depends(get_db)
):
    """
    Belirli bir dersin yoklama kayıtlarını getirir (Sadece akademisyenler erişebilir)
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
    
    query = db.query(Attendance).filter(Attendance.course_id == course_id)
    
    if start_date:
        query = query.filter(Attendance.date >= start_date)
    if end_date:
        query = query.filter(Attendance.date <= end_date)
        
    return query.all()

@router.post("/{course_id}", response_model=attendance_schemas.AttendanceOut)
async def create_attendance(
    course_id: UUID,
    attendance: attendance_schemas.AttendanceCreate,
    current_user: User = Depends(check_academician_role),
    db: Session = Depends(get_db)
):
    """
    Yeni yoklama kaydı oluşturur (Sadece akademisyenler)
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
    
    # Aynı tarihte yoklama var mı kontrol et
    existing_attendance = db.query(Attendance).filter(
        Attendance.course_id == course_id,
        Attendance.student_id == attendance.student_id,
        Attendance.date == attendance.date
    ).first()
    
    if existing_attendance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu tarihte zaten yoklama kaydı mevcut"
        )
    
    new_attendance = Attendance(
        course_id=course_id,
        student_id=attendance.student_id,
        date=attendance.date,
        status=attendance.status
    )
    
    db.add(new_attendance)
    db.commit()
    db.refresh(new_attendance)
    
    return new_attendance

@router.put("/{attendance_id}", response_model=attendance_schemas.AttendanceOut)
async def update_attendance(
    attendance_id: UUID,
    attendance: attendance_schemas.AttendanceCreate,
    current_user: User = Depends(check_academician_role),
    db: Session = Depends(get_db)
):
    """
    Yoklama kaydını günceller (Sadece akademisyenler)
    """
    db_attendance = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    
    if not db_attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Yoklama kaydı bulunamadı"
        )
    
    # Akademisyenin kendi dersi mi kontrol et
    course = db.query(Course).filter(
        Course.id == db_attendance.course_id,
        Course.academician_id == current_user.id
    ).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu yoklama kaydını güncelleme yetkiniz yok"
        )
    
    db_attendance.status = attendance.status
    db_attendance.date = attendance.date
    
    db.commit()
    db.refresh(db_attendance)
    
    return db_attendance

@router.delete("/{attendance_id}")
async def delete_attendance(
    attendance_id: UUID,
    current_user: User = Depends(check_academician_role),
    db: Session = Depends(get_db)
):
    """
    Yoklama kaydını siler (Sadece akademisyenler)
    """
    db_attendance = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    
    if not db_attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Yoklama kaydı bulunamadı"
        )
    
    # Akademisyenin kendi dersi mi kontrol et
    course = db.query(Course).filter(
        Course.id == db_attendance.course_id,
        Course.academician_id == current_user.id
    ).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu yoklama kaydını silme yetkiniz yok"
        )
    
    db.delete(db_attendance)
    db.commit()
    
    return {"message": "Yoklama kaydı başarıyla silindi"}

