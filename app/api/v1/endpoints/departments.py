from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.crud import crud_department
from app.schemas.department import Department

router = APIRouter(
    prefix="/api/v1/departments",
    tags=["Departments"]
)

@router.get("/", response_model=List[Department])
def read_departments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    departments = crud_department.get_departments(db, skip=skip, limit=limit)
    return departments

@router.get("/faculty/{faculty_id}", response_model=List[Department])
def read_departments_by_faculty(faculty_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    departments = crud_department.get_departments_by_faculty(db, faculty_id=faculty_id, skip=skip, limit=limit)
    return departments

@router.get("/{department_id}", response_model=Department)
def read_department(department_id: int, db: Session = Depends(get_db)):
    db_department = crud_department.get_department(db, department_id=department_id)
    if db_department is None:
        raise HTTPException(status_code=404, detail="Department not found")
    return db_department
