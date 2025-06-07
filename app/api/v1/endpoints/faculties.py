from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.crud import crud_faculty
from app.schemas.faculty import Faculty, FacultyCreate, FacultyUpdate

router = APIRouter(
    prefix="/api/v1/faculties",
    tags=["Faculties"]
)


@router.get("/", response_model=List[Faculty])
def read_faculties(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    faculties = crud_faculty.get_faculties(db, skip=skip, limit=limit)
    return faculties

@router.get("/{faculty_id}", response_model=Faculty)
def read_faculty(faculty_id: int, db: Session = Depends(get_db)):
    db_faculty = crud_faculty.get_faculty(db, faculty_id=faculty_id)
    if db_faculty is None:
        raise HTTPException(status_code=404, detail="Faculty not found")
    return db_faculty
