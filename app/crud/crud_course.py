from sqlalchemy.orm import Session
from app.models.models import Course, Attendance, CourseSelectionStudent
from app.schemas.course import CourseCreate, CourseUpdate
from uuid import UUID
from datetime import date, timedelta
from sqlalchemy import and_

def get_course(db: Session, course_id: UUID):
    return db.query(Course).filter(Course.id == course_id).first()

def get_courses(db: Session):
    return db.query(Course).all()

def create_course(db: Session, course: CourseCreate):
    db_course = Course(
        name=course.name,
        code=course.code,
        academician_id=course.academician_id,
        attendances_rate_limit=course.attendances_rate_limit
    )
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course

def update_course(db: Session, course_id: UUID, course_update: CourseUpdate):
    db_course = db.query(Course).filter(Course.id == course_id).first()
    if not db_course:
        return None
    update_data = course_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_course, key, value)
    db.commit()
    db.refresh(db_course)
    return db_course

def delete_course(db: Session, course_id: UUID):
    db_course = db.query(Course).filter(Course.id == course_id).first()
    if not db_course:
        return None
    db.delete(db_course)
    db.commit()
    return db_course

def cancel_course_attendance(db: Session, course_id: UUID, cancel_date: date) -> bool:
    """
    Belirli bir dersin belirli bir tarihteki yoklamalarını iptal eder.
    Bu yoklamalar null olarak işaretlenir ve devamsızlık oranını etkilemez.
    """
    # Dersin kayıtlı öğrencilerini bul
    enrolled_students = db.query(CourseSelectionStudent).filter(
        and_(
            CourseSelectionStudent.course_id == course_id,
            CourseSelectionStudent.is_approved == True
        )
    ).all()

    if not enrolled_students:
        return False

    # Her öğrenci için yoklama kaydı oluştur
    for enrollment in enrolled_students:
        # Öğrencinin o gün için mevcut yoklama kaydı var mı kontrol et
        existing_attendance = db.query(Attendance).filter(
            and_(
                Attendance.course_id == course_id,
                Attendance.student_id == enrollment.student_id,
                Attendance.date == cancel_date
            )
        ).first()

        if existing_attendance:
            # Mevcut kaydı güncelle
            existing_attendance.status = None
        else:
            # Yeni kayıt oluştur
            new_attendance = Attendance(
                student_id=enrollment.student_id,
                course_id=course_id,
                date=cancel_date,
                status=None
            )
            db.add(new_attendance)

    db.commit()
    return True