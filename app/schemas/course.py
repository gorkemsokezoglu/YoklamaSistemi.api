from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from datetime import datetime

class CourseBase(BaseModel):
    name: str
    code: str
    academician_id: Optional[UUID] = None
    attendances_rate_limit: Optional[float] = None


class CourseCreate(CourseBase):
    academician_id: UUID

class CourseUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    academician_id: Optional[UUID] = None
    attendances_rate_limit: Optional[float] = None

class CourseResponse(CourseBase):
    id: UUID
    academician_id: Optional[UUID]
    created_at: datetime

    class Config:
        from_attributes = True
