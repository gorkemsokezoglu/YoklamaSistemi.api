from sqlalchemy.orm import Session
from app.models.models import CourseSelectionStudent, Course, Student, User, CourseSchedule
from uuid import UUID
from app.schemas import course_selection_student as course_selection_schemas
from typing import List, Tuple
from sqlalchemy import and_

def create_course_selection_student(db: Session, course_selection_student: course_selection_schemas.CourseSelectionStudentCreate) -> CourseSelectionStudent:
    db_course_selection_student = CourseSelectionStudent(**course_selection_student.dict())
    db.add(db_course_selection_student)
    db.commit()
    db.refresh(db_course_selection_student)
    return db_course_selection_student

def get_course_selections_student(db: Session) -> list:
    return db.query(CourseSelectionStudent)

def get_course_selection_student(db: Session, course_selection_student_id: UUID) -> CourseSelectionStudent:
    return db.query(CourseSelectionStudent).filter(CourseSelectionStudent.id == course_selection_student_id).first()

def update_course_selection_student(db: Session, course_selection_student_id: UUID, course_selection: course_selection_schemas.CourseSelectionStudentCreate) -> CourseSelectionStudent:
    db_course_selection_student = db.query(CourseSelectionStudent).filter(CourseSelectionStudent.id == course_selection_student_id).first()
    if db_course_selection_student:
        for var, value in vars(course_selection).items():
            setattr(db_course_selection_student, var, value) if value else None
        db.commit()
        db.refresh(db_course_selection_student)
        return db_course_selection_student
    return None

def delete_course_selection_student(db: Session, course_selection_student_id: UUID) -> CourseSelectionStudent:
    db_course_selection_student = db.query(CourseSelectionStudent).filter(CourseSelectionStudent.id == course_selection_student_id).first()
    if db_course_selection_student:
        db.delete(db_course_selection_student)
        db.commit()
        return db_course_selection_student
    return None

# Akademisyenin kendi derslerine yapılan başvuruları görmesi
def get_pending_approvals_for_academician(db: Session, academician_id: UUID) -> list:
    return (
        db.query(CourseSelectionStudent)
        .join(Course, CourseSelectionStudent.course_id == Course.id)
        .filter(Course.academician_id == academician_id)
        .filter(CourseSelectionStudent.is_approved == False)
        .all()
    )

# Akademisyenin başvuru onaylaması
def approve_course_selection(db: Session, course_selection_student_id: UUID) -> CourseSelectionStudent:
    db_course_selection_student = db.query(CourseSelectionStudent).filter(CourseSelectionStudent.id == course_selection_student_id).first()
    if db_course_selection_student:
        db_course_selection_student.is_approved = True
        db.commit()
        db.refresh(db_course_selection_student)
    return db_course_selection_student

def get_course_selections_by_student(db: Session, student_id: UUID) -> list:
    """
    Belirli bir öğrencinin tüm ders seçimlerini getirir
    """
    return db.query(CourseSelectionStudent).filter(CourseSelectionStudent.student_id == student_id).all()

def check_schedule_conflict(db: Session, student_id: UUID, course_id: UUID) -> Tuple[bool, str]:
    """
    Öğrencinin seçmek istediği ders ile mevcut derslerinin çakışıp çakışmadığını kontrol eder
    Returns: (çakışma_var_mı, çakışma_mesajı)
    """
    # Öğrencinin mevcut ders seçimlerini al
    current_selections = db.query(CourseSelectionStudent).filter(
        and_(
            CourseSelectionStudent.student_id == student_id,
            CourseSelectionStudent.is_approved != False  # None veya True olanlar
        )
    ).all()
    
    # Seçilmek istenen dersin programını al
    new_course_schedules = db.query(CourseSchedule).filter(
        CourseSchedule.course_id == course_id
    ).all()
    
    # Mevcut derslerin programlarını al
    for selection in current_selections:
        existing_schedules = db.query(CourseSchedule).filter(
            CourseSchedule.course_id == selection.course_id
        ).all()
        
        # Her bir mevcut ders programı ile yeni dersin programını karşılaştır
        for existing_schedule in existing_schedules:
            for new_schedule in new_course_schedules:
                # Aynı gün kontrolü
                if existing_schedule.weekday == new_schedule.weekday:
                    # Zaman çakışması kontrolü
                    if (
                        (new_schedule.start_time <= existing_schedule.end_time and 
                         new_schedule.end_time >= existing_schedule.start_time)
                    ):
                        course_name = db.query(Course.name).filter(Course.id == selection.course_id).first()[0]
                        return True, f"Bu ders, {course_name} dersi ile {existing_schedule.weekday} günü {existing_schedule.start_time}-{existing_schedule.end_time} saatleri arasında çakışıyor."
    
    return False, ""

def create_multiple_course_selections(db: Session, student_id: UUID, course_ids: List[UUID]) -> List[CourseSelectionStudent]:
    """
    Bir öğrenci için birden fazla ders seçimi oluşturur
    """
    created_selections = []
    
    # Her bir ders için çakışma kontrolü yap
    for course_id in course_ids:
        has_conflict, conflict_message = check_schedule_conflict(db, student_id, course_id)
        if has_conflict:
            # Eğer daha önce eklenmiş seçimler varsa onları geri al
            for selection in created_selections:
                db.delete(selection)
            db.commit()
            raise ValueError(conflict_message)
            
        selection = CourseSelectionStudent(
            student_id=student_id,
            course_id=course_id,
            is_approved=None
        )
        db.add(selection)
        created_selections.append(selection)
    
    db.commit()
    for selection in created_selections:
        db.refresh(selection)
    
    return created_selections

def get_course_selections_by_course(db: Session, course_id: UUID) -> List[CourseSelectionStudent]:
    """
    Belirli bir derse ait tüm öğrenci seçimlerini getirir
    """
    return db.query(CourseSelectionStudent)\
        .filter(CourseSelectionStudent.course_id == course_id)\
        .all()

def reject_course_selection(db: Session, course_selection_student_id: UUID) -> CourseSelectionStudent:
    """
    Akademisyenin ders seçimini reddetmesi
    """
    db_course_selection_student = db.query(CourseSelectionStudent).filter(CourseSelectionStudent.id == course_selection_student_id).first()
    if db_course_selection_student:
        db_course_selection_student.is_approved = False
        db.commit()
        db.refresh(db_course_selection_student)
    return db_course_selection_student

def get_students_by_course(db: Session, course_id: UUID) -> List[dict]:
    """
    Belirli bir derse kayıtlı olan öğrencilerin detaylı bilgilerini getirir
    """
    return (
        db.query(
            CourseSelectionStudent,
            Student,
            User.first_name,
            User.last_name,
            User.email
        )
        .join(Student, CourseSelectionStudent.student_id == Student.user_id)
        .join(User, Student.user_id == User.id)
        .filter(CourseSelectionStudent.course_id == course_id)
        .filter(CourseSelectionStudent.is_approved == True)
        .all()
    )
