from pydantic import BaseModel
from uuid import UUID
from datetime import date
from typing import Optional

class AttendanceBase(BaseModel):
    student_id: UUID
    course_id: UUID
    date: date
    status: Optional[bool] = None

class AttendanceCreate(AttendanceBase):
    pass

class AttendanceUpdate(BaseModel):
    status: Optional[bool] = None

class AttendanceOut(AttendanceBase):
    id: UUID

    class Config:
        from_attributes = True