from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api_v1 import api_router
from app.database import engine, Base
from app.api.v1.endpoints import course_selections_academician, auth, course_selections_student, users, students, courses, academicians, attendances, face_data, performance_records, face_recognition, faculties, departments, course_schedules, reports, roboflow
from app.utils.auth import check_endpoint_permission
from app.services.attendance_scheduler import AttendanceScheduler

app = FastAPI(title="Yüz Tanıma Yoklama Sistemi API")

# Scheduler'ı başlat
attendance_scheduler = AttendanceScheduler()

@app.on_event("startup")
async def startup_event():
    """
    Uygulama başladığında çalışacak işlemler
    """
    # Scheduler'ı başlat
    attendance_scheduler.start()

@app.on_event("shutdown")
async def shutdown_event():
    """
    Uygulama kapandığında çalışacak işlemler
    """
    # Scheduler'ı durdur
    attendance_scheduler.stop()

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Güvenlik için production'da spesifik originler belirtilmeli
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

# Public endpoint'ler (yetkilendirme gerektirmeyen)
app.include_router(auth.router)

# Protected endpoint'ler (yetkilendirme gerektiren)
app.include_router(
    users.router,
    dependencies=[Depends(check_endpoint_permission)]
)
app.include_router(
    students.router
)
app.include_router(
    attendances.router,
    dependencies=[Depends(check_endpoint_permission)]
)
app.include_router(
    academicians.router
)
app.include_router(
    face_data.router,
    dependencies=[Depends(check_endpoint_permission)]
)
app.include_router(
    performance_records.router,
    dependencies=[Depends(check_endpoint_permission)]
)
app.include_router(
    course_selections_student.router
)
app.include_router(
    course_selections_academician.router,
    dependencies=[Depends(check_endpoint_permission)]
)
app.include_router(
    courses.router
)
app.include_router(
    face_recognition.router,
    dependencies=[Depends(check_endpoint_permission)]
)

# Yeni eklenen endpoint'ler
app.include_router(
    faculties.router
)
app.include_router(
    departments.router
)
app.include_router(
    course_schedules.router
)
app.include_router(
    reports.router,
    dependencies=[Depends(check_endpoint_permission)]
)
app.include_router(
    roboflow.router,
    prefix="/api/v1/roboflow",
    tags=["roboflow"]
)

app.include_router(
    api_router,
    prefix="/api/v1",
    dependencies=[Depends(check_endpoint_permission)]
)
