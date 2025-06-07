from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from datetime import datetime

from app.models.models import Course, CourseSelectionAcademician

from app.schemas.course_selection_academician import (CourseSelectionAcademicianCreate)


def create_course_selection_academician(
    db: Session, data: CourseSelectionAcademicianCreate
) -> CourseSelectionAcademician:
    selection = CourseSelectionAcademician(**data.dict())
    db.add(selection)
    db.commit()
    db.refresh(selection)
    return selection

def get_course_selection_academician(
    db: Session, selection_id: UUID
) -> Optional[CourseSelectionAcademician]:
    return db.query(CourseSelectionAcademician).filter_by(id=selection_id).first()

def get_all_course_selections_academicians(db: Session) -> List[CourseSelectionAcademician]:
    return db.query(CourseSelectionAcademician).all()

def update_course_selection_academician(
    db: Session,
    selection_id: UUID,
    is_approved: Optional[bool] = None,
    reviewed_at: Optional[datetime] = None
) -> Optional[CourseSelectionAcademician]:
    selection = db.query(CourseSelectionAcademician).filter_by(id=selection_id).first()
    if not selection:
        return None

    if is_approved is not None:
        selection.is_approved = is_approved
        if is_approved:
            # Course tablosundaki academician_id'yi güncelle
            course = db.query(Course).filter_by(id=selection.course_id).first()
            if course:
                course.academician_id = selection.academician_id

    if reviewed_at is not None:
        selection.reviewed_at = reviewed_at

    db.commit()
    db.refresh(selection)
    return selection

def delete_course_selection_academician(
    db: Session, selection_id: UUID
) -> bool:
    selection = db.query(CourseSelectionAcademician).filter_by(id=selection_id).first()
    if not selection:
        return False
    db.delete(selection)
    db.commit()
    return True

