from sqlalchemy.orm import Session
from app.models.models import Student, User
from app.schemas.student import StudentCreate, StudentResponse, StudentUpdate
from typing import List, Optional
from uuid import UUID
from app.utils.auth import get_password_hash

def get_students(db: Session) -> List[StudentResponse]:
    """
    Tüm öğrencileri getirir
    """
    students = db.query(Student).all()
    result = []
    
    for student in students:
        user = db.query(User).filter(User.id == student.user_id).first()
        result.append(StudentResponse(
            user_id=student.user_id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            faculty=student.faculty,
            department=student.department,
            student_number=student.student_number,
            class_=student.class_,
            role=user.role
        ))
    
    return result

def get_student(db: Session, student_id: str) -> StudentResponse:
    """
    ID'ye göre öğrenci getirir
    """
    student = db.query(Student).filter(Student.user_id == student_id).first()
    if student:
        user = db.query(User).filter(User.id == student.user_id).first()
        return StudentResponse(
            user_id=student.user_id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            faculty=student.faculty,
            department=student.department,
            student_number=student.student_number,
            class_=student.class_,
            role=user.role
        )
    return None

def get_student_by_id(db: Session, student_id: str) -> Student:
    """
    ID'ye göre öğrenci modelini getirir
    """
    return db.query(Student).filter(Student.user_id == student_id).first()

def create_student(db: Session, student: StudentCreate) -> StudentResponse:
    """
    Yeni öğrenci oluşturur
    """
    # Şifreyi hash'le
    hashed_password = get_password_hash(student.password)

    # Önce User oluştur
    db_user = User(
        first_name=student.first_name,
        last_name=student.last_name,
        email=student.email,
        password=hashed_password,
        role=student.role
    )
    db.add(db_user)
    db.flush()

    # Sonra Student oluştur
    db_student = Student(
        user_id=db_user.id,
        faculty=student.faculty,
        department=student.department,
        student_number=student.student_number,
        class_=student.class_
    )
    db.add(db_student)
    db.commit()
    db.refresh(db_student)

    return StudentResponse(
        user_id=db_student.user_id,
        first_name=db_user.first_name,
        last_name=db_user.last_name,
        email=db_user.email,
        faculty=db_student.faculty,
        department=db_student.department,
        student_number=db_student.student_number,
        class_=db_student.class_,
        role=db_user.role
    )

def update_student(db: Session, student_id: str, student_update: StudentUpdate) -> Optional[StudentResponse]:
    """
    Öğrenci bilgilerini günceller
    """
    # Öğrenci ve kullanıcı kayıtlarını al
    student = db.query(Student).filter(Student.user_id == student_id).first()
    if not student:
        return None
    
    user = db.query(User).filter(User.id == student.user_id).first()
    if not user:
        return None

    # User modelini güncelle
    if student_update.first_name is not None:
        user.first_name = student_update.first_name
    if student_update.last_name is not None:
        user.last_name = student_update.last_name
    if student_update.email is not None:
        user.email = student_update.email

    # Student modelini güncelle
    if student_update.faculty is not None:
        student.faculty = student_update.faculty
    if student_update.department is not None:
        student.department = student_update.department
    if student_update.student_number is not None:
        student.student_number = student_update.student_number
    if student_update.class_ is not None:
        student.class_ = student_update.class_

    db.commit()
    db.refresh(student)
    db.refresh(user)

    return StudentResponse(
        user_id=student.user_id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        faculty=student.faculty,
        department=student.department,
        student_number=student.student_number,
        class_=student.class_,
        role=user.role
    )

def delete_student(db: Session, student_id: str):
    """
    Öğrenciyi ve ilişkili tüm verileri siler
    """
    student = db.query(Student).filter(Student.user_id == student_id).first()
    if student:
        # Student kaydını sil (cascade ile diğer kayıtlar otomatik silinecek)
        db.delete(student)
        db.commit()
    return student

def get_student_by_student_number(db: Session, student_number: str) -> Optional[StudentResponse]:
    """
    Öğrenci numarasına göre öğrenci bilgilerini getirir
    """
    student = db.query(Student).filter(Student.student_number == student_number).first()
    if student:
        user = db.query(User).filter(User.id == student.user_id).first()
        return StudentResponse(
            user_id=student.user_id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            faculty=student.faculty,
            department=student.department,
            student_number=student.student_number,
            class_=student.class_,
            role=user.role
        )
    return None

def get_students_by_student_numbers(db: Session, student_numbers: List[str]) -> List[StudentResponse]:
    """
    Öğrenci numaralarına göre öğrenci bilgilerini getirir
    """
    students = db.query(Student).filter(Student.student_number.in_(student_numbers)).all()
    result = []
    
    for student in students:
        user = db.query(User).filter(User.id == student.user_id).first()
        result.append(StudentResponse(
            user_id=student.user_id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            faculty=student.faculty,
            department=student.department,
            student_number=student.student_number,
            class_=student.class_,
            role=user.role
        ))
    
    return result
