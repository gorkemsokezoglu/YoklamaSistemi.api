from fastapi import APIRouter
from app.api.v1.endpoints import course_selections_student, users, students, academicians, courses, attendances, face_data, performance_records

api_router = APIRouter()

