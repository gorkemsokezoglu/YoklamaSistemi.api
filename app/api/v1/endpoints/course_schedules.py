from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_db
from app.crud import crud_courseSchedule
from app.schemas.courseSchedule import CourseSchedule, CourseScheduleCreate, CourseScheduleUpdate

router = APIRouter(
    prefix="/api/v1/course-schedules",
    tags=["Course Schedules"]
)

@router.get("/", response_model=List[CourseSchedule])
def read_course_schedules(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    schedules = crud_courseSchedule.get_course_schedules(db, skip=skip, limit=limit)
    return schedules

@router.get("/course/{course_id}", response_model=List[CourseSchedule])
def read_course_schedules_by_course(course_id: UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    schedules = crud_courseSchedule.get_course_schedules_by_course(db, course_id=course_id, skip=skip, limit=limit)
    return schedules

@router.get("/{schedule_id}", response_model=CourseSchedule)
def read_course_schedule(schedule_id: UUID, db: Session = Depends(get_db)):
    db_schedule = crud_courseSchedule.get_course_schedule(db, schedule_id=schedule_id)
    if db_schedule is None:
        raise HTTPException(status_code=404, detail="Course schedule not found")
    return db_schedule

