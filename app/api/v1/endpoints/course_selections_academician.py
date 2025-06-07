from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.crud import crud_courseSelectionAcademician as course_selection_academician_crud
from app.models.models import Course, CourseSelectionAcademician
from app.schemas.course_selection_academician import (
    CourseSelectionAcademicianCreate,
    CourseSelectionAcademicianOut
)

router = APIRouter(
    prefix="/api/v1/course-selections-academicians",
    tags=["Course Selection - Academicians"]
)

@router.post("/", response_model=CourseSelectionAcademicianOut, status_code=status.HTTP_201_CREATED)
def create_selection(
    selection: CourseSelectionAcademicianCreate,
    db: Session = Depends(get_db)
):
    return course_selection_academician_crud.create_course_selection_academician(db, selection)

@router.get("/{selection_id}", response_model=CourseSelectionAcademicianOut)
def get_selection(
    selection_id: UUID,
    db: Session = Depends(get_db)
):
    selection = course_selection_academician_crud.get_course_selection_academician(db, selection_id)
    if not selection:
        raise HTTPException(status_code=404, detail="Selection not found")
    return selection

@router.get("/", response_model=List[CourseSelectionAcademicianOut])
def list_selections(
    db: Session = Depends(get_db)
):
    return course_selection_academician_crud.get_all_course_selections_academicians(db)

@router.put("/{selection_id}", response_model=CourseSelectionAcademicianOut)
def update_selection(
    selection_id: UUID,
    is_approved: Optional[bool] = None,
    reviewed_at: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    updated = course_selection_academician_crud.update_course_selection_academician(
        db, selection_id, is_approved=is_approved, reviewed_at=reviewed_at
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Selection not found")
    return updated

@router.delete("/{selection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_selection(
    selection_id: UUID,
    db: Session = Depends(get_db)
):
    success = course_selection_academician_crud.delete_course_selection_academician(db, selection_id)
    if not success:
        raise HTTPException(status_code=404, detail="Selection not found")
    
