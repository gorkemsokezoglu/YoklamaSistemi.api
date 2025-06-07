from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List
from datetime import datetime

class CourseSelectionStudentCreate(BaseModel):
    student_id: UUID
    course_ids: List[UUID]
    is_approved: Optional[bool] = None

class CourseSelectionStudentResponse(BaseModel):
    id: UUID
    student_id: UUID
    course_id: UUID
    is_approved: Optional[bool]
    created_at: datetime

    class Config:
        from_attributes = True

class BulkCourseSelectionCreate(BaseModel):
    student_id: UUID
    course_ids: List[UUID]

class CourseStudentResponse(BaseModel):
    student_id: UUID
    first_name: str
    last_name: str
    email: str
    faculty: str
    department: str
    student_number: str
    selection_status: bool
    selection_date: datetime

    class Config:
        from_attributes = True
