from sqlalchemy.orm import Session
from app.models.models import Department
from app.schemas.department import DepartmentCreate, DepartmentUpdate
from typing import List, Optional

def get_department(db: Session, department_id: int) -> Optional[Department]:
    return db.query(Department).filter(Department.id == department_id).first()

def get_departments_by_faculty(db: Session, faculty_id: int, skip: int = 0, limit: int = 100) -> List[Department]:
    return db.query(Department).filter(Department.faculty_id == faculty_id).offset(skip).limit(limit).all()

def get_departments(db: Session, skip: int = 0, limit: int = 100) -> List[Department]:
    return db.query(Department).offset(skip).limit(limit).all()

def create_department(db: Session, department: DepartmentCreate) -> Department:
    db_department = Department(
        name=department.name,
        faculty_id=department.faculty_id
    )
    db.add(db_department)
    db.commit()
    db.refresh(db_department)
    return db_department

def update_department(db: Session, department_id: int, department: DepartmentUpdate) -> Optional[Department]:
    db_department = get_department(db, department_id)
    if db_department:
        update_data = department.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_department, field, value)
        db.commit()
        db.refresh(db_department)
    return db_department

def delete_department(db: Session, department_id: int) -> Optional[Department]:
    db_department = get_department(db, department_id)
    if db_department:
        db.delete(db_department)
        db.commit()
    return db_department 