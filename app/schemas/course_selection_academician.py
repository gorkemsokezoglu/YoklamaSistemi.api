from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from datetime import datetime

class CourseSelectionAcademicianCreate(BaseModel):
    academician_id: UUID
    course_id: UUID
    is_approved: Optional[bool] = None

class CourseSelectionAcademicianOut(CourseSelectionAcademicianCreate):
    id: UUID
    requested_at: datetime
    reviewed_at: Optional[datetime] = None

    class Config:
        orm_mode = True
