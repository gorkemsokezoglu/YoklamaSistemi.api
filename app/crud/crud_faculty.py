from sqlalchemy.orm import Session
from app.models.models import Faculty
from app.schemas.faculty import FacultyCreate, FacultyUpdate
from typing import List, Optional

def get_faculty(db: Session, faculty_id: int) -> Optional[Faculty]:
    return db.query(Faculty).filter(Faculty.id == faculty_id).first()

def get_faculty_by_name(db: Session, name: str) -> Optional[Faculty]:
    return db.query(Faculty).filter(Faculty.name == name).first()

def get_faculties(db: Session, skip: int = 0, limit: int = 100) -> List[Faculty]:
    return db.query(Faculty).offset(skip).limit(limit).all()

def create_faculty(db: Session, faculty: FacultyCreate) -> Faculty:
    db_faculty = Faculty(name=faculty.name)
    db.add(db_faculty)
    db.commit()
    db.refresh(db_faculty)
    return db_faculty

def update_faculty(db: Session, faculty_id: int, faculty: FacultyUpdate) -> Optional[Faculty]:
    db_faculty = get_faculty(db, faculty_id)
    if db_faculty:
        update_data = faculty.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_faculty, field, value)
        db.commit()
        db.refresh(db_faculty)
    return db_faculty

def delete_faculty(db: Session, faculty_id: int) -> Optional[Faculty]:
    db_faculty = get_faculty(db, faculty_id)
    if db_faculty:
        db.delete(db_faculty)
        db.commit()
    return db_faculty 