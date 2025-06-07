from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas import course_selection_student as course_selection_student_schemas
from app.crud import crud_courseSelectionStudent as course_selection_student_crud
from app.database import get_db
from uuid import UUID
from typing import List
from app.models.models import User, Course
from app.utils.auth import get_current_user, check_student_role, check_academician_role

router = APIRouter(
    prefix="/api/v1/course-selections-student",
    tags=["Course Selections Student"]
)

@router.post("/", response_model=List[course_selection_student_schemas.CourseSelectionStudentResponse])
def create_course_selection_student(
    course_selection: course_selection_student_schemas.CourseSelectionStudentCreate, 
    current_user: User = Depends(check_student_role),
    db: Session = Depends(get_db)
):
    """
    Öğrencinin ders seçimi oluşturması (Sadece kendi için, birden fazla ders seçebilir)
    Ders programı çakışması kontrolü yapılır
    """
    # Öğrencinin kendi seçimi mi kontrol et
    if str(current_user.id) != str(course_selection.student_id):
        raise HTTPException(
            status_code=403,
            detail="Sadece kendiniz için ders seçimi yapabilirsiniz"
        )

    # Derslerin var olup olmadığını kontrol et
    for course_id in course_selection.course_ids:
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(
                status_code=404,
                detail=f"Ders bulunamadı: {course_id}"
            )

    # Aynı dersi tekrar seçmediğinden emin ol
    existing_selections = course_selection_student_crud.get_course_selections_by_student(db, current_user.id)
    existing_course_ids = {str(selection.course_id) for selection in existing_selections}
    
    for course_id in course_selection.course_ids:
        if str(course_id) in existing_course_ids:
            raise HTTPException(
                status_code=400,
                detail=f"Bu dersi zaten seçmişsiniz: {course_id}"
            )

    try:
        return course_selection_student_crud.create_multiple_course_selections(
            db, 
            course_selection.student_id, 
            course_selection.course_ids
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.get("/my-selections", response_model=List[course_selection_student_schemas.CourseSelectionStudentResponse])
def read_my_course_selections(
    current_user: User = Depends(check_student_role),
    db: Session = Depends(get_db)
):
    """
    Öğrencinin kendi ders seçimlerini getirme
    """
    return course_selection_student_crud.get_course_selections_by_student(db, current_user.id)

@router.get("/{course_selection_student_id}", response_model=course_selection_student_schemas.CourseSelectionStudentResponse)
def read_course_selection(
    course_selection_student_id: UUID, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Belirli bir ders seçimini getirme (Öğrenci kendi seçimini, akademisyen kendi dersinin seçimlerini görebilir)
    """
    db_course_selection_student = course_selection_student_crud.get_course_selection_student(db, course_selection_student_id)
    if not db_course_selection_student:
        raise HTTPException(status_code=404, detail="Ders seçimi bulunamadı")

    # Yetki kontrolü
    if current_user.role == "student":
        if str(current_user.id) != str(db_course_selection_student.student_id):
            raise HTTPException(
                status_code=403,
                detail="Bu ders seçimine erişim yetkiniz yok"
            )
    elif current_user.role == "academician":
        # Akademisyenin kendi dersi mi kontrol et
        course = db.query(Course).filter(
            Course.id == db_course_selection_student.course_id,
            Course.academician_id == current_user.id
        ).first()
        if not course:
            raise HTTPException(
                status_code=403,
                detail="Bu ders seçimine erişim yetkiniz yok"
            )
    
    return db_course_selection_student

@router.put("/{course_selection_student_id}", response_model=course_selection_student_schemas.CourseSelectionStudentResponse)
def update_course_selection(
    course_selection_student_id: UUID, 
    course_selection_student: course_selection_student_schemas.CourseSelectionStudentCreate, 
    current_user: User = Depends(check_student_role),
    db: Session = Depends(get_db)
):
    """
    Ders seçimini güncelleme (Öğrenci sadece kendi seçimini güncelleyebilir)
    """
    db_course_selection = course_selection_student_crud.get_course_selection_student(db, course_selection_student_id)
    if not db_course_selection:
        raise HTTPException(status_code=404, detail="Ders seçimi bulunamadı")

    # Öğrencinin kendi seçimi mi kontrol et
    if str(current_user.id) != str(db_course_selection.student_id):
        raise HTTPException(
            status_code=403,
            detail="Sadece kendi ders seçimlerinizi güncelleyebilirsiniz"
        )

    return course_selection_student_crud.update_course_selection_student(
        db, course_selection_student_id, course_selection_student
    )

@router.delete("/{course_selection_student_id}")
def delete_course_selection(
    course_selection_student_id: UUID, 
    current_user: User = Depends(check_student_role),
    db: Session = Depends(get_db)
):
    """
    Ders seçimini silme (Öğrenci sadece kendi seçimini silebilir)
    """
    db_course_selection = course_selection_student_crud.get_course_selection_student(db, course_selection_student_id)
    if not db_course_selection:
        raise HTTPException(status_code=404, detail="Ders seçimi bulunamadı")

    # Öğrencinin kendi seçimi mi kontrol et
    if str(current_user.id) != str(db_course_selection.student_id):
        raise HTTPException(
            status_code=403,
            detail="Sadece kendi ders seçimlerinizi silebilirsiniz"
        )

    course_selection_student_crud.delete_course_selection_student(db, course_selection_student_id)
    return {"message": "Ders seçimi başarıyla silindi"}

@router.get("/pending-approvals/{academician_id}", response_model=List[course_selection_student_schemas.CourseSelectionStudentResponse])
def get_pending_approvals(
    academician_id: UUID, 
    current_user: User = Depends(check_academician_role),
    db: Session = Depends(get_db)
):
    """
    Akademisyenin onay bekleyen ders seçimlerini getirme (Sadece kendi dersleri için)
    """
    # Akademisyenin kendisi mi kontrol et
    if str(current_user.id) != str(academician_id):
        raise HTTPException(
            status_code=403,
            detail="Sadece kendi derslerinizin onay bekleyen seçimlerini görebilirsiniz"
        )
    return course_selection_student_crud.get_pending_approvals_for_academician(db, academician_id)

@router.put("/approve/{course_selection_student_id}", response_model=course_selection_student_schemas.CourseSelectionStudentResponse)
def approve_course_selection(
    course_selection_student_id: UUID, 
    current_user: User = Depends(check_academician_role),
    db: Session = Depends(get_db)
):
    """
    Ders seçimini onaylama (Akademisyen sadece kendi derslerinin seçimlerini onaylayabilir)
    """
    db_course_selection = course_selection_student_crud.get_course_selection_student(db, course_selection_student_id)
    if not db_course_selection:
        raise HTTPException(status_code=404, detail="Ders seçimi bulunamadı")

    # Akademisyenin kendi dersi mi kontrol et
    course = db.query(Course).filter(
        Course.id == db_course_selection.course_id,
        Course.academician_id == current_user.id
    ).first()
    
    if not course:
        raise HTTPException(
            status_code=403,
            detail="Bu ders seçimini onaylama yetkiniz yok"
        )

    return course_selection_student_crud.approve_course_selection(db, course_selection_student_id)

@router.get("/course/{course_id}", response_model=List[course_selection_student_schemas.CourseSelectionStudentResponse])
def get_course_selections_by_course(
    course_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Belirli bir derse ait tüm öğrenci seçimlerini listeler.
    Akademisyenler sadece kendi derslerinin seçimlerini görebilir.
    Öğrenciler sadece kendi seçtikleri derslerin seçimlerini görebilir.
    """
    # Dersin var olup olmadığını kontrol et
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=404,
            detail="Ders bulunamadı"
        )

    # Yetki kontrolü
    if current_user.role == "academician":
        # Akademisyenin kendi dersi mi kontrol et
        if str(current_user.id) != str(course.academician_id):
            raise HTTPException(
                status_code=403,
                detail="Bu dersin seçimlerini görüntüleme yetkiniz yok"
            )
    elif current_user.role == "student":
        # Öğrencinin seçtiği bir ders mi kontrol et
        student_selection = course_selection_student_crud.get_course_selections_by_student(db, current_user.id)
        if not any(str(selection.course_id) == str(course_id) for selection in student_selection):
            raise HTTPException(
                status_code=403,
                detail="Bu dersin seçimlerini görüntüleme yetkiniz yok"
            )
    
    return course_selection_student_crud.get_course_selections_by_course(db, course_id)

@router.put("/reject/{course_selection_student_id}", response_model=course_selection_student_schemas.CourseSelectionStudentResponse)
def reject_course_selection(
    course_selection_student_id: UUID, 
    current_user: User = Depends(check_academician_role),
    db: Session = Depends(get_db)
):
    """
    Ders seçimini reddetme (Akademisyen sadece kendi derslerinin seçimlerini reddedebilir)
    """
    db_course_selection = course_selection_student_crud.get_course_selection_student(db, course_selection_student_id)
    if not db_course_selection:
        raise HTTPException(
            status_code=404,
            detail="Ders seçimi bulunamadı"
        )

    # Akademisyenin kendi dersi mi kontrol et
    course = db.query(Course).filter(
        Course.id == db_course_selection.course_id,
        Course.academician_id == current_user.id
    ).first()
    
    if not course:
        raise HTTPException(
            status_code=403,
            detail="Bu ders seçimini reddetme yetkiniz yok"
        )

    # Eğer seçim zaten onaylanmış veya reddedilmişse hata ver
    if db_course_selection.is_approved is not None:
        status = "onaylanmış" if db_course_selection.is_approved else "reddedilmiş"
        raise HTTPException(
            status_code=400,
            detail=f"Bu ders seçimi zaten {status}"
        )

    return course_selection_student_crud.reject_course_selection(db, course_selection_student_id)

@router.get("/course/{course_id}/students", response_model=List[course_selection_student_schemas.CourseStudentResponse])
def get_course_students(
    course_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Belirli bir derse kayıtlı olan öğrencilerin detaylı bilgilerini getirir.
    Akademisyenler kendi derslerinin, öğrenciler kayıtlı oldukları derslerin öğrenci listesini görebilir.
    """
    # Dersin var olup olmadığını kontrol et
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=404,
            detail="Ders bulunamadı"
        )

    # Yetki kontrolü
    if current_user.role == "academician":
        # Akademisyenin kendi dersi mi kontrol et
        if str(current_user.id) != str(course.academician_id):
            raise HTTPException(
                status_code=403,
                detail="Bu dersin öğrenci listesini görüntüleme yetkiniz yok"
            )
    elif current_user.role == "student":
        # Öğrencinin seçtiği bir ders mi kontrol et
        student_selection = course_selection_student_crud.get_course_selections_by_student(db, current_user.id)
        if not any(str(selection.course_id) == str(course_id) and selection.is_approved for selection in student_selection):
            raise HTTPException(
                status_code=403,
                detail="Bu dersin öğrenci listesini görüntüleme yetkiniz yok"
            )

    results = course_selection_student_crud.get_students_by_course(db, course_id)
    
    return [
        course_selection_student_schemas.CourseStudentResponse(
            student_id=student.user_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            faculty=student.faculty,
            department=student.department,
            student_number=student.student_number,
            selection_status=selection.is_approved,
            selection_date=selection.created_at
        )
        for selection, student, first_name, last_name, email in results
    ]

