from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class PerformanceRecordBase(BaseModel):
    student_id: UUID
    course_id: UUID
    attendance_rate: float

class PerformanceRecordCreate(PerformanceRecordBase):
    pass

class PerformanceRecordResponse(PerformanceRecordBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True