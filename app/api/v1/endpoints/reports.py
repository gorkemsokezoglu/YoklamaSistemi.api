from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.report_service import ReportService
from app.utils.auth import get_current_user
from app.models.models import User
from uuid import UUID

router = APIRouter(
    prefix="/api/v1/reports",
    tags=["reports"]
)

report_service = ReportService()

@router.get("/attendance/{course_id}/{date}")
def get_attendance_report(
    course_id: UUID,
    date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response:
    """
    Belirli bir dersin belirli bir tarihteki yoklama raporunu PDF olarak döndürür.
    
    Parameters:
    - course_id: Dersin UUID'si
    - date: Yoklama tarihi (YYYY-MM-DD formatında)
    
    Returns:
    - PDF formatında yoklama raporu
    """
    try:
        # Yetki kontrolü - sadece akademisyenler rapor alabilir
        if current_user.role != "academician":
            raise HTTPException(
                status_code=403,
                detail="Bu işlem için akademisyen yetkisi gereklidir"
            )

        pdf_content = report_service.generate_attendance_report(
            db=db,
            course_id=str(course_id),
            date=date
        )
        
        filename = f"yoklama_raporu_{course_id}_{date}.pdf"
        
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Rapor oluşturulurken bir hata oluştu: {str(e)}"
        ) 