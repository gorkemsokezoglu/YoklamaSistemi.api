from sqlalchemy.orm import Session
from app.models.models import CourseSchedule
from app.schemas.courseSchedule import CourseScheduleCreate, CourseScheduleUpdate
from typing import List, Optional
from uuid import UUID

def get_course_schedule(db: Session, schedule_id: UUID) -> Optional[CourseSchedule]:
    return db.query(CourseSchedule).filter(CourseSchedule.id == schedule_id).first()

def get_course_schedules_by_course(db: Session, course_id: UUID, skip: int = 0, limit: int = 100) -> List[CourseSchedule]:
    return db.query(CourseSchedule).filter(CourseSchedule.course_id == course_id).offset(skip).limit(limit).all()

def get_course_schedules(db: Session, skip: int = 0, limit: int = 100) -> List[CourseSchedule]:
    return db.query(CourseSchedule).offset(skip).limit(limit).all()

def create_course_schedule(db: Session, schedule: CourseScheduleCreate) -> CourseSchedule:
    db_schedule = CourseSchedule(
        course_id=schedule.course_id,
        weekday=schedule.weekday,
        start_time=schedule.start_time,
        end_time=schedule.end_time,
        location=schedule.location
    )
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule

def update_course_schedule(db: Session, schedule_id: UUID, schedule: CourseScheduleUpdate) -> Optional[CourseSchedule]:
    db_schedule = get_course_schedule(db, schedule_id)
    if db_schedule:
        update_data = schedule.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_schedule, field, value)
        db.commit()
        db.refresh(db_schedule)
    return db_schedule

def delete_course_schedule(db: Session, schedule_id: UUID) -> Optional[CourseSchedule]:
    db_schedule = get_course_schedule(db, schedule_id)
    if db_schedule:
        db.delete(db_schedule)
        db.commit()
    return db_schedule 