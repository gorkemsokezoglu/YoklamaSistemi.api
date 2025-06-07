from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from datetime import datetime, time, timedelta
from app.models.models import CourseSchedule, Course, Attendance, Student, CourseSelectionStudent
from app.database import SessionLocal
from sqlalchemy import and_
import logging

# Loglama yapılandırması
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AttendanceScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        
    async def create_attendance_records(self):
        """
        Aktif dersler için yoklama kayıtlarını oluşturur
        """
        try:
            db = SessionLocal()
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
            
            # Şu anki saatte başlayan dersleri bul (sadece başlangıç saatinde)
            current_schedules = db.query(CourseSchedule).filter(
                and_(
                    CourseSchedule.weekday == current_weekday,
                    CourseSchedule.start_time <= current_time.time(),
                    CourseSchedule.start_time >= (current_time - timedelta(minutes=5)).time()  # Son 5 dakika içinde başlayan
                )
            ).all()
            
            logger.info(f"{len(current_schedules)} adet ders için yoklama kaydı oluşturulacak")
            
            for schedule in current_schedules:
                # Dersin kayıtlı ve onaylanmış öğrencilerini bul
                course = db.query(Course).filter(Course.id == schedule.course_id).first()
                if not course:
                    logger.warning(f"Ders bulunamadı: {schedule.course_id}")
                    continue
                
                # Onaylanmış kayıtları olan öğrencileri bul
                enrolled_students = db.query(Student).join(CourseSelectionStudent).filter(
                    and_(
                        CourseSelectionStudent.course_id == course.id,
                        CourseSelectionStudent.is_approved == True
                    )
                ).all()
                
                logger.info(f"{course.code} dersi için {len(enrolled_students)} öğrencinin yoklaması oluşturulacak")
                
                # Dersin tüm öğrencileri için yoklama kaydı oluştur
                for student in enrolled_students:
                    # Bugün için yoklama kaydı var mı kontrol et
                    existing_attendance = db.query(Attendance).filter(
                        and_(
                            Attendance.student_id == student.user_id,
                            Attendance.course_id == course.id,
                            Attendance.date == current_time.date()
                        )
                    ).first()
                    
                    # Yoklama kaydı yoksa oluştur
                    if not existing_attendance:
                        new_attendance = Attendance(
                            student_id=student.user_id,
                            course_id=course.id,
                            date=current_time.date(),
                            status=False  # Başlangıçta False olarak ayarla
                        )
                        db.add(new_attendance)
                        logger.debug(f"Yeni yoklama kaydı oluşturuldu: {student.user_id} - {course.code}")
            
            db.commit()
            logger.info("Tüm yoklama kayıtları başarıyla oluşturuldu")
            
        except Exception as e:
            logger.error(f"Yoklama kaydı oluşturulurken hata: {str(e)}")
            db.rollback()
        finally:
            db.close()
    
    def start(self):
        """
        Scheduler'ı başlatır
        """
        try:
            # Her 5 dakikada bir kontrol et
            self.scheduler.add_job(
                self.create_attendance_records,
                CronTrigger(minute='*/5'),  # Her 5 dakikada bir
                id='create_attendance_records',
                replace_existing=True
            )
            self.scheduler.start()
            logger.info("Attendance Scheduler başarıyla başlatıldı")
        except Exception as e:
            logger.error(f"Scheduler başlatılırken hata: {str(e)}")
    
    def stop(self):
        """
        Scheduler'ı durdurur
        """
        try:
            self.scheduler.shutdown()
            logger.info("Attendance Scheduler durduruldu")
        except Exception as e:
            logger.error(f"Scheduler durdurulurken hata: {str(e)}") 