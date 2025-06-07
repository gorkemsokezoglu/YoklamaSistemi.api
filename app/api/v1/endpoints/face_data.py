import base64
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models import models
from app.schemas import face_data as face_data_schemas
from app.crud import crud_faceData as face_data_crud
from app.database import get_db
from uuid import UUID
from typing import List
from app.models.models import FaceData, User
from app.utils.auth import get_current_user, check_student_role, check_academician_role

router = APIRouter(
    prefix="/api/v1/face-data",
    tags=["face-data"]
)

@router.post("/", response_model=face_data_schemas.FaceDataResponse)
async def create_face_data(
    face_data: face_data_schemas.FaceDataCreate,
    current_user: User = Depends(check_student_role),
    db: Session = Depends(get_db)
):
    """
    Mobil uygulamadan gelen tek bir yüz verisini kaydeder
    """
    # Öğrencinin kendi verisi mi kontrol et
    if str(current_user.id) != str(face_data.student_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sadece kendi yüz verinizi ekleyebilirsiniz"
        )

    try:
        # Base64 string'i bytes'a çevir
        face_image_bytes = base64.b64decode(face_data.face_image)
        
        # Yüz verisini kaydet
        db_face_data = FaceData(
            student_id=face_data.student_id,
            face_image=face_image_bytes
        )
        db.add(db_face_data)
        db.commit()
        db.refresh(db_face_data)
        return db_face_data
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Yüz verisi kaydedilemedi: {str(e)}"
        )

@router.post("/bulk", response_model=str)
async def create_multiple_face_data(
    face_data: face_data_schemas.FaceDataUpload,
    current_user: User = Depends(check_student_role),
    db: Session = Depends(get_db)
):
    """
    Mobil uygulamadan gelen birden fazla yüz verisini kaydeder
    """
    # Öğrencinin kendi verisi mi kontrol et
    if str(current_user.id) != str(face_data.student_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sadece kendi yüz verilerinizi ekleyebilirsiniz"
        )

    try:
        saved_count = 0
        for base64_image in face_data.face_images:
            try:
                # Base64 string'i bytes'a çevir
                face_image_bytes = base64.b64decode(base64_image)
                
                # Yüz verisini kaydet
                db_face_data = FaceData(
                    student_id=face_data.student_id,
                    face_image=face_image_bytes
                )
                db.add(db_face_data)
                saved_count += 1
            except Exception as e:
                print(f"Yüz verisi kaydedilirken hata oluştu: {str(e)}")
                continue
        
        db.commit()
        return f"{saved_count} adet yüz verisi başarıyla kaydedildi"
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Yüz verileri kaydedilemedi: {str(e)}"
        )

@router.get("/my-face-data", response_model=List[face_data_schemas.FaceDataResponse])
async def get_my_face_data(
    current_user: User = Depends(check_student_role),
    db: Session = Depends(get_db)
):
    """
    Öğrencinin kendi yüz verilerini getirir
    """
    return db.query(FaceData).filter(FaceData.student_id == current_user.id).all()

@router.get("/{student_id}", response_model=List[face_data_schemas.FaceDataResponse])
async def get_student_face_data(
    student_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Belirli bir öğrencinin yüz verilerini getirir
    """
    # Öğrenci kendi verilerine veya akademisyen tüm verilere erişebilir
    if current_user.role == "student" and str(current_user.id) != str(student_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sadece kendi yüz verilerinize erişebilirsiniz"
        )

    return db.query(FaceData).filter(FaceData.student_id == student_id).all()

@router.put("/{face_data_id}", response_model=face_data_schemas.FaceDataResponse)
async def update_face_data(
    face_data_id: UUID,
    face_data: face_data_schemas.FaceDataCreate,
    current_user: User = Depends(check_student_role),
    db: Session = Depends(get_db)
):
    """
    Yüz verisini günceller (Sadece öğrenciler kendi verilerini güncelleyebilir)
    """
    db_face_data = db.query(FaceData).filter(FaceData.id == face_data_id).first()
    if not db_face_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Yüz verisi bulunamadı"
        )

    # Öğrencinin kendi verisi mi kontrol et
    if str(current_user.id) != str(db_face_data.student_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sadece kendi yüz verinizi güncelleyebilirsiniz"
        )

    for key, value in face_data.dict().items():
        setattr(db_face_data, key, value)

    db.commit()
    db.refresh(db_face_data)
    return db_face_data

@router.delete("/{face_data_id}")
async def delete_face_data(
    face_data_id: UUID,
    current_user: User = Depends(check_student_role),
    db: Session = Depends(get_db)
):
    """
    Yüz verisini siler (Sadece öğrenciler kendi verilerini silebilir)
    """
    db_face_data = db.query(FaceData).filter(FaceData.id == face_data_id).first()
    if not db_face_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Yüz verisi bulunamadı"
        )

    # Öğrencinin kendi verisi mi kontrol et
    if str(current_user.id) != str(db_face_data.student_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sadece kendi yüz verinizi silebilirsiniz"
        )

    db.delete(db_face_data)
    db.commit()
    return {"message": "Yüz verisi başarıyla silindi"}

@router.post("/upload-multiple")
def upload_multiple_face_data(request: face_data_schemas.FaceDataUpload, db: Session = Depends(get_db)):
    for image_data in request.face_images:
        try:
            decoded_image = base64.b64decode(image_data)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid image data format.")
        
        face_record = models.FaceData(
            student_id=request.student_id,
            face_image=decoded_image
        )
        db.add(face_record)
    db.commit()
    return {"message": f"{len(request.face_images)} face data record(s) saved."}