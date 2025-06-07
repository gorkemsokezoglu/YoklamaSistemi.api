from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import base64
import requests
import os
from datetime import datetime
from uuid import UUID
from dotenv import load_dotenv
from app.database import get_db
from app.crud.crud_student import get_students_by_student_numbers
from app.schemas.student import StudentResponse
from app.models.models import Attendance, Course, CourseSchedule, User
from app.utils.auth import check_academician_role

# .env dosyasından ortam değişkenlerini yükle
load_dotenv()

router = APIRouter(
    tags=["roboflow"]
)

# Roboflow API anahtarı ve diğer ayarlar
ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY", "NBFfLau2OXkvLq0gcpp7")
WORKSPACE_NAME = os.getenv("ROBOFLOW_WORKSPACE_NAME", "ozlem-2qeuz")
WORKFLOW_ID = os.getenv("ROBOFLOW_WORKFLOW_ID", "main")

@router.post("/take-attendance/{course_id}", response_model=Dict[str, Any])
async def take_attendance(
    course_id: UUID,
    image: UploadFile = File(...),
    current_user: User = Depends(check_academician_role),
    db: Session = Depends(get_db)
):
    """
    Akademisyenin çektiği fotoğrafı kullanarak derste olan öğrencileri tespit eder ve
    yoklama kaydı oluşturur.
    """
    # Dersin var olup olmadığını ve akademisyene ait olup olmadığını kontrol et
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=404,
            detail="Ders bulunamadı"
        )
    
    if str(course.academician_id) != str(current_user.id):
        raise HTTPException(
            status_code=403,
            detail="Bu ders için yoklama alma yetkiniz yok"
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

    # Ders programını kontrol et
    course_schedule = db.query(CourseSchedule).filter(
        CourseSchedule.course_id == course_id,
        CourseSchedule.weekday == current_weekday,
        CourseSchedule.start_time <= current_time.time(),
        CourseSchedule.end_time >= current_time.time()
    ).first()

    if not course_schedule:
        raise HTTPException(
            status_code=400,
            detail="Bu ders şu anda aktif değil"
        )

    if not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400, 
            detail="Lütfen bir görüntü dosyası yükleyin."
        )

    try:
        # Yüklenen dosyayı oku
        contents = await image.read()

        # Görüntüyü base64'e dönüştür
        encoded_image = base64.b64encode(contents).decode('utf-8')

        # API endpoint'i
        url = f"https://serverless.roboflow.com/infer/workflows/{WORKSPACE_NAME}/{WORKFLOW_ID}"

        # İstek başlıkları
        headers = {
            "Content-Type": "application/json"
        }

        # İstek verisi
        payload = {
            "api_key": ROBOFLOW_API_KEY,
            "inputs": {
                "image": {
                    "type": "base64",
                    "value": encoded_image
                }
            }
        }

        print(f"Sending request to: {url}")  # Debug için URL'i yazdır
        
        # Roboflow API'sine POST isteği gönder
        response = requests.post(
            url, 
            headers=headers, 
            json=payload
        )
        
        print(f"Response status code: {response.status_code}")  # Debug için

        if response.status_code != 200:
            error_detail = "Bilinmeyen hata"
            try:
                error_json = response.json()
                if isinstance(error_json, dict):
                    error_detail = error_json.get('error', error_json.get('message', error_json.get('detail', str(error_json))))
            except:
                error_detail = response.text
                
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Roboflow API'den hata yanıtı: {error_detail}"
            )

        # Roboflow'dan gelen yanıtı işle
        roboflow_results: Dict[str, Any] = response.json()
        
        # Öğrenci numaralarını çıkar ve tekrar edenleri kaldır
        outputs = roboflow_results.get("outputs", [])
        if not outputs or not outputs[0].get("property_definition"):
            print("No student numbers found in response:", roboflow_results)
            return {"message": "Fotoğrafta öğrenci tespit edilemedi", "attendance_records": []}

        # Öğrenci numaralarını al ve tekrar edenleri kaldır
        student_numbers = []
        seen = set()
        for student_number in outputs[0]["property_definition"]:
            if student_number and student_number not in seen:
                student_numbers.append(student_number)
                seen.add(student_number)

        if not student_numbers:
            print("No valid student numbers found in outputs:", outputs)
            return {"message": "Geçerli öğrenci numarası bulunamadı", "attendance_records": []}

        print(f"Detected student numbers: {student_numbers}")  # Debug için

        # Veritabanından öğrenci bilgilerini çek
        detected_students = get_students_by_student_numbers(db, student_numbers)

        if not detected_students:
            print(f"No students found in database for numbers: {student_numbers}")
            return {"message": "Tespit edilen öğrenciler veritabanında bulunamadı", "attendance_records": []}

        # Yoklama kayıtlarını oluştur
        attendance_records = []
        current_date = current_time.date()

        for student in detected_students:
            # Aynı gün için zaten kayıt var mı kontrol et
            existing_attendance = db.query(Attendance).filter(
                Attendance.student_id == student.user_id,
                Attendance.course_id == course_id,
                Attendance.date == current_date
            ).first()

            if existing_attendance:
                attendance_records.append({
                    "student_number": student.student_number,
                    "student_name": f"{student.first_name} {student.last_name}",
                    "status": "already_exists",
                    "message": "Yoklama kaydı zaten mevcut"
                })
                continue

            # Yeni yoklama kaydı oluştur
            new_attendance = Attendance(
                student_id=student.user_id,
                course_id=course_id,
                date=current_date,
                status=True  # Derste var olarak işaretle
            )
            db.add(new_attendance)
            
            attendance_records.append({
                "student_number": student.student_number,
                "student_name": f"{student.first_name} {student.last_name}",
                "status": "created",
                "message": "Yoklama kaydı oluşturuldu"
            })

        # Değişiklikleri kaydet
        db.commit()

        return {
            "message": f"{len(attendance_records)} öğrenci için yoklama işlemi tamamlandı",
            "course_info": {
                "name": course.name,
                "code": course.code,
                "date": current_date.isoformat(),
                "time": current_time.strftime("%H:%M:%S"),
                "weekday": current_weekday
            },
            "attendance_records": attendance_records
        }

    except requests.exceptions.RequestException as e:
        print(f"Request error: {str(e)}")  # Debug için hata detayını yazdır
        raise HTTPException(
            status_code=500, 
            detail=f"Roboflow API isteği sırasında hata oluştu: {str(e)}"
        )
    except Exception as e:
        print(f"Unexpected error: {str(e)}")  # Debug için hata detayını yazdır
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Bir hata oluştu: {str(e)}"
        ) 