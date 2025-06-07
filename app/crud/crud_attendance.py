# app/crud/attendances.py

from sqlalchemy.orm import Session
from app.models.models import Attendance
from app.schemas.attendance import AttendanceCreate, AttendanceUpdate
from uuid import UUID

def get_attendance(db: Session, attendance_id: UUID):
    return db.query(Attendance).filter(Attendance.id == attendance_id).first()

def get_attendances(db: Session):
    return db.query(Attendance).all()

def create_attendance(db: Session, attendance: AttendanceCreate):
    db_attendance = Attendance(
        student_id=attendance.student_id,
        course_id=attendance.course_id,
        date=attendance.date,
        status=attendance.status
    )
    db.add(db_attendance)
    db.commit()
    db.refresh(db_attendance)
    return db_attendance

def update_attendance(db: Session, attendance_id: UUID, attendance_update: AttendanceUpdate):
    db_attendance = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    if not db_attendance:
        return None
    for key, value in attendance_update.dict(exclude_unset=True).items():
        setattr(db_attendance, key, value)
    db.commit()
    db.refresh(db_attendance)
    return db_attendance

def delete_attendance(db: Session, attendance_id: UUID):
    db_attendance = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    if not db_attendance:
        return None
    db.delete(db_attendance)
    db.commit()
    return db_attendance
