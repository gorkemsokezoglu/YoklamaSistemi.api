from pydantic import BaseModel
from typing import Optional
from datetime import time, datetime
from uuid import UUID

class CourseScheduleBase(BaseModel):
    course_id: UUID
    weekday: str
    start_time: time
    end_time: time
    location: Optional[str] = None

class CourseScheduleCreate(CourseScheduleBase):
    pass

class CourseScheduleUpdate(CourseScheduleBase):
    course_id: Optional[UUID] = None
    weekday: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    location: Optional[str] = None

class CourseScheduleInDB(CourseScheduleBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CourseSchedule(CourseScheduleInDB):
    pass
