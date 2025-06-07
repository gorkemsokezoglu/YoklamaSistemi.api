from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.academician import AcademicianCreate, AcademicianOut, AcademicianUpdate
from app.crud import crud_academician as academician_crud
from app.database import get_db
from typing import List
from app.models.models import User, Academician
from app.utils.auth import get_current_user, check_academician_role

router = APIRouter(
    prefix="/api/v1/academicians",
    tags=["Academicians"]
)

@router.get("/me", response_model=AcademicianOut)
async def read_academician_me(
    current_user: User = Depends(check_academician_role),
    db: Session = Depends(get_db)
):
    """
    Giriş yapmış akademisyenin kendi bilgilerini getirir
    """
    result = academician_crud.get_academician(db, current_user.id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Akademisyen bulunamadı"
        )
    
    academician, first_name, last_name, email = result
    return AcademicianOut(
        user_id=academician.user_id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        faculty=academician.faculty,
        department=academician.department,
        academician_number=academician.academician_number,
        created_at=academician.created_at
    )

@router.post("/", response_model=AcademicianOut)
def create_academician(
    academician_data: AcademicianCreate,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(User.email == academician_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")

    user = User(
        first_name=academician_data.first_name,
        last_name=academician_data.last_name,
        email=academician_data.email,
        password=academician_data.password,
        role="academician"
    )
    db.add(user)
    db.flush()

    academician = Academician(
        user_id=user.id,
        faculty=academician_data.faculty,
        department=academician_data.department,
        academician_number=academician_data.academician_number
    )
    db.add(academician)
    db.commit()
    db.refresh(academician)
    
    return AcademicianOut(
        user_id=academician.user_id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        faculty=academician.faculty,
        department=academician.department,
        academician_number=academician.academician_number,
        created_at=academician.created_at
    )

@router.get("/", response_model=List[AcademicianOut])
def read_academicians(db: Session = Depends(get_db)):
    results = academician_crud.get_academicians(db)
    return [
        AcademicianOut(
            user_id=academician.user_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            faculty=academician.faculty,
            department=academician.department,
            academician_number=academician.academician_number,
            created_at=academician.created_at
        )
        for academician, first_name, last_name, email in results
    ]

@router.get("/{user_id}", response_model=AcademicianOut)
def read_academician(user_id: UUID, db: Session = Depends(get_db)):
    result = academician_crud.get_academician(db, user_id)
    if not result:
        raise HTTPException(status_code=404, detail="Academician not found")
    
    academician, first_name, last_name, email = result
    return AcademicianOut(
        user_id=academician.user_id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        faculty=academician.faculty,
        department=academician.department,
        academician_number=academician.academician_number,
        created_at=academician.created_at
    )

@router.put("/{user_id}", response_model=AcademicianOut)
def update_academician(user_id: UUID, academician: AcademicianUpdate, db: Session = Depends(get_db)):
    db_academician = academician_crud.update_academician(db, user_id, academician)
    if db_academician is None:
        raise HTTPException(status_code=404, detail="Academician not found")
    
    user = db.query(User).filter(User.id == user_id).first()
    return AcademicianOut(
        user_id=db_academician.user_id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        faculty=db_academician.faculty,
        department=db_academician.department,
        academician_number=db_academician.academician_number,
        created_at=db_academician.created_at
    )

@router.delete("/{user_id}", response_model=AcademicianOut)
def delete_academician(user_id: UUID, db: Session = Depends(get_db)):
    db_academician = academician_crud.delete_academician(db, user_id)
    if db_academician is None:
        raise HTTPException(status_code=404, detail="Academician not found")
    
    user = db.query(User).filter(User.id == user_id).first()
    return AcademicianOut(
        user_id=db_academician.user_id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        faculty=db_academician.faculty,
        department=db_academician.department,
        academician_number=db_academician.academician_number,
        created_at=db_academician.created_at
    )
