from sqlalchemy.orm import Session
from app.models.models import Academician, User
from app.schemas.academician import AcademicianCreate, AcademicianUpdate
from uuid import UUID
from datetime import datetime

def get_academician(db: Session, user_id: UUID):
    return db.query(Academician, User.first_name, User.last_name, User.email)\
        .join(User)\
        .filter(Academician.user_id == user_id)\
        .first()

def get_academicians(db: Session):
    return db.query(Academician, User.first_name, User.last_name, User.email).join(User).all()

def create_academician(db: Session, academician: AcademicianCreate, user_id: UUID):
    db_academician = Academician(
        user_id=user_id,
        faculty=academician.faculty,
        department=academician.department,
        academician_number=academician.academician_number,
        created_at=datetime.utcnow()
    )
    db.add(db_academician)
    db.commit()
    db.refresh(db_academician)
    return db_academician

def update_academician(db: Session, user_id: UUID, academician: AcademicianUpdate):
    db_academician = db.query(Academician).join(User).filter(Academician.user_id == user_id).first()
    if db_academician:
        db_academician.faculty = academician.faculty
        db_academician.department = academician.department
        db_academician.academician_number = academician.academician_number
        
        db_user = db.query(User).filter(User.id == db_academician.user_id).first()
        if db_user:
            db_user.first_name = academician.first_name
            db_user.last_name = academician.last_name
            db_user.email = academician.email
        
        db.commit()
        db.refresh(db_academician)
        return db_academician
    return None

def delete_academician(db: Session, user_id: UUID):
    db_academician = db.query(Academician).filter(Academician.user_id == user_id).first()
    if db_academician:
        db_user = db.query(User).filter(User.id == db_academician.user_id).first()
        if db_user:
            db.delete(db_user)
            db.commit()
            return db_academician
    return None