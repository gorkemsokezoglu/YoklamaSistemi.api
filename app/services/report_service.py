from datetime import datetime
from pathlib import Path
import jinja2
from weasyprint import HTML
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.models import Attendance, Course, Student, User

class ReportService:
    def __init__(self):
        self.template_dir = Path(__file__).parent.parent / "templates"
        self.template_dir.mkdir(exist_ok=True)
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.template_dir))
        )

    def get_attendance_by_date_and_course(self, db: Session, course_id: str, date: datetime.date):
        """Belirli bir tarih ve ders için yoklama kayıtlarını getirir."""
        return (
            db.query(Attendance)
            .join(Student)
            .join(User)
            .filter(
                and_(
                    Attendance.course_id == course_id,
                    Attendance.date == date
                )
            )
            .all()
        )

    def generate_attendance_report(
        self,
        db: Session,
        course_id: str,
        date: datetime.date
    ) -> bytes:
        # Dersi al
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise ValueError("Ders bulunamadı")

        # Yoklama verilerini al
        attendance_records = self.get_attendance_by_date_and_course(
            db=db,
            course_id=course_id,
            date=date
        )

        # İstatistikleri hesapla
        present_count = sum(1 for a in attendance_records if a.status)
        absent_count = sum(1 for a in attendance_records if not a.status)
        total_count = len(attendance_records)

        # Şablonu yükle ve doldur
        template = self.env.get_template("attendance_report.html")
        
        html_content = template.render(
            course=course,
            date=date,
            attendance_records=attendance_records,
            present_count=present_count,
            absent_count=absent_count,
            total_count=total_count
        )

        # PDF oluştur
        pdf = HTML(string=html_content).write_pdf()
        return pdf 