from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.models import Attendance, PerformanceRecord
from uuid import UUID
from datetime import datetime

class PerformanceCalculator:
    @staticmethod
    def calculate_and_update_attendance_rate(db: Session, student_id: UUID, course_id: UUID) -> float:
        """
        Öğrencinin belirli bir dersteki yoklama oranını hesaplar ve performance_records tablosuna kaydeder
        """
        try:
            # Tüm yoklama kayıtlarını al
            total_attendances = db.query(Attendance).filter(
                and_(
                    Attendance.student_id == student_id,
                    Attendance.course_id == course_id
                )
            ).all()

            if not total_attendances:
                return 0.0

            # Katıldığı dersleri say
            attended_classes = sum(1 for attendance in total_attendances if attendance.status)
            
            # Yoklama oranını hesapla
            attendance_rate = attended_classes / len(total_attendances)

            # Mevcut performance record'u kontrol et
            performance_record = db.query(PerformanceRecord).filter(
                and_(
                    PerformanceRecord.student_id == student_id,
                    PerformanceRecord.course_id == course_id
                )
            ).first()

            if performance_record:
                # Mevcut kaydı güncelle
                performance_record.attendance_rate = attendance_rate
            else:
                # Yeni kayıt oluştur
                performance_record = PerformanceRecord(
                    student_id=student_id,
                    course_id=course_id,
                    attendance_rate=attendance_rate
                )
                db.add(performance_record)

            db.commit()
            return attendance_rate

        except Exception as e:
            db.rollback()
            print(f"Performans hesaplanırken hata oluştu: {str(e)}")
            return 0.0 