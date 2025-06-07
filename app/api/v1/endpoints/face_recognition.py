from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.models.models import Attendance, CourseSchedule, FaceData, Student, User, Course
from app.schemas.face_recognition import FaceRecognitionRequest
from app.services.face_recognition_service import FaceRecognitionService
from app.utils.auth import get_current_user, check_student_role
from app.services.performance_calculator import PerformanceCalculator

router = APIRouter(
    prefix="/api/v1/face-recognition",
    tags=["face-recognition"]
)


@router.post("/identify/{course_id}", status_code=status.HTTP_200_OK)
async def identify_face(
    course_id: UUID,
    current_user: User = Depends(check_student_role),
    db: Session = Depends(get_db)
):
    """
    Sadece yüz tanıma işlemi gerçekleştirir ve öğrenci bilgilerini döndürür.
    Eğer ders aktif ise yoklama kaydı oluşturur.
    """
    # Önce dersin var olup olmadığını kontrol et
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ders bulunamadı"
        )

    try:
        # FaceRecognitionService'i başlat
        face_service = FaceRecognitionService(db)
        
        # Yüz tanıma işlemini başlat
        recognized_student_id = face_service.start_recognition()
        
        if not recognized_student_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Yüz tanıma başarısız oldu veya işlem iptal edildi"
            )

        # Tanınan yüzün giriş yapmış öğrenciye ait olup olmadığını kontrol et
        if recognized_student_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tanınan yüz giriş yapmış öğrenciye ait değil"
            )

        # Öğrenci bilgilerini getir
        student = db.query(Student).join(User).filter(
            Student.user_id == current_user.id
        ).first()

        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Öğrenci bulunamadı"
            )

        # Mevcut gün ve saat bilgisini al
        current_time = datetime.now()
        weekdays = {
            0: 'Monday',
            1: 'Tuesday',
            2: 'Wednesday',
            3: 'Thursday',
            4: 'Friday',
            5: 'Saturday',
            6: 'Sunday'
        }
        current_weekday = weekdays[current_time.weekday()]

        # Ders programını kontrol et - gün ve saat kontrolü
        course_schedule = db.query(CourseSchedule).filter(
            CourseSchedule.course_id == course_id,
            CourseSchedule.weekday == current_weekday,
            CourseSchedule.start_time <= current_time.time(),
            CourseSchedule.end_time >= current_time.time()
        ).first()

        # Eğer aktif bir ders saati yoksa, sadece günün programını göster
        if not course_schedule:
            course_schedule = db.query(CourseSchedule).filter(
                CourseSchedule.course_id == course_id,
                CourseSchedule.weekday == current_weekday
            ).first()

        schedule_info = None
        attendance_info = None
        is_active = False
        response_message = "Yüz tanıma başarılı"

        if course_schedule:
            is_active = (course_schedule.start_time <= current_time.time() <= course_schedule.end_time)
            schedule_info = {
                "weekday": course_schedule.weekday,
                "start_time": course_schedule.start_time.strftime("%H:%M"),
                "end_time": course_schedule.end_time.strftime("%H:%M"),
                "location": course_schedule.location,
                "is_active": is_active,
                "status": "active" if is_active else "not_started" if current_time.time() < course_schedule.start_time else "ended"
            }

            if not is_active:
                if current_time.time() < course_schedule.start_time:
                    response_message = f"Ders henüz başlamadı. Ders başlangıç saati: {course_schedule.start_time.strftime('%H:%M')}"
                else:
                    response_message = f"Ders sona erdi. Ders bitiş saati: {course_schedule.end_time.strftime('%H:%M')}"
            
            # Ders aktifse yoklama kaydı oluştur
            if is_active:
                # Önce bugün için yoklama alınıp alınmadığını kontrol et
                existing_attendance = db.query(Attendance).filter(
                    Attendance.student_id == current_user.id,
                    Attendance.course_id == course_id,
                    Attendance.date == current_time.date()
                ).first()

                if existing_attendance:
                    if existing_attendance.status:
                        response_message = "Bu ders için zaten yoklama alınmış"
                        attendance_info = {
                            "id": existing_attendance.id,
                            "status": "already_exists",
                            "message": response_message
                        }
                    else:
                        # Mevcut yoklama kaydını güncelle
                        existing_attendance.status = True
                        db.commit()
                        db.refresh(existing_attendance)
                        
                        response_message = "Yoklama kaydınız başarıyla güncellendi"
                        attendance_info = {
                            "id": existing_attendance.id,
                            "status": "updated",
                            "message": response_message
                        }
                else:
                    # Yeni yoklama kaydı oluştur
                    new_attendance = Attendance(
                        student_id=current_user.id,
                        course_id=course_id,
                        date=current_time.date(),
                        status=True  # present olarak işaretle
                    )
                    
                    db.add(new_attendance)
                    db.commit()
                    db.refresh(new_attendance)

                    response_message = "Yoklama kaydınız başarıyla oluşturuldu"
                    attendance_info = {
                        "id": new_attendance.id,
                        "status": "created",
                        "message": response_message
                    }
        else:
            response_message = "Şu anda ders takvimi içinde değilsiniz"

        response_data = {
            "message": response_message,
            "student_info": {
                "id": student.user_id,
                "student_number": student.student_number,
                "faculty": student.faculty,
                "department": student.department,
                "first_name": student.user.first_name,
                "last_name": student.user.last_name,
                "email": student.user.email
            },
            "datetime_info": {
                "weekday": current_weekday,
                "date": current_time.date().isoformat(),
                "time": current_time.time().strftime("%H:%M:%S")
            },
            "course_info": {
                "id": course.id,
                "name": course.name,
                "code": course.code,
                "schedule": schedule_info
            }
        }

        # Eğer yoklama bilgisi varsa response'a ekle
        if attendance_info:
            response_data["attendance"] = attendance_info

        # Eğer yoklama kaydı oluşturuldu, güncellendi veya zaten varsa performansı hesapla
        if attendance_info and attendance_info["status"] in ["created", "updated", "already_exists"]:
            attendance_rate = PerformanceCalculator.calculate_and_update_attendance_rate(
                db=db,
                student_id=current_user.id,
                course_id=course_id
            )
            response_data["performance"] = {
                "attendance_rate": attendance_rate,
                "message": "Devam oranı güncellendi"
            }

        return response_data

    except HTTPException as he:
        # HTTP hataları olduğu gibi yönlendir
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Yüz tanıma işlemi sırasında bir hata oluştu: {str(e)}"
        )