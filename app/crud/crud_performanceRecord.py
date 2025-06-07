from sqlalchemy.orm import Session
from app.models.models import PerformanceRecord
from app.schemas.performance_record import PerformanceRecordCreate
from uuid import UUID

def get_performance_record(db: Session, performance_record_id: UUID):
    return db.query(PerformanceRecord).filter(PerformanceRecord.id == performance_record_id).first()

def get_performance_records_by_student(db: Session, student_id: UUID):
    return db.query(PerformanceRecord).filter(PerformanceRecord.student_id == student_id).all()

def create_performance_record(db: Session, performance_record: PerformanceRecordCreate):
    db_performance_record = PerformanceRecord(
        student_id=performance_record.student_id,
        course_id=performance_record.course_id,
        attendance_rate=performance_record.attendance_rate
    )
    db.add(db_performance_record)
    db.commit()
    db.refresh(db_performance_record)
    return db_performance_record

def update_performance_record(db: Session, performance_record_id: UUID, performance_record: PerformanceRecordCreate):
    db_performance_record = db.query(PerformanceRecord).filter(PerformanceRecord.id == performance_record_id).first()
    if db_performance_record:
        db_performance_record.attendance_rate = performance_record.attendance_rate
        db.commit()
        db.refresh(db_performance_record)
        return db_performance_record
    return None

def delete_performance_record(db: Session, performance_record_id: UUID):
    db_performance_record = db.query(PerformanceRecord).filter(PerformanceRecord.id == performance_record_id).first()
    if not db_performance_record:
        return None
    db.delete(db_performance_record)
    db.commit()
    return db_performance_record