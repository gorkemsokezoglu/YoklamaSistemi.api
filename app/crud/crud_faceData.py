from sqlalchemy.orm import Session
from app.models.models import FaceData
from app.schemas.face_data import FaceDataCreate, FaceDataUpload
from uuid import UUID
import base64

def get_face_data(db: Session, face_data_id: UUID):
    return db.query(FaceData).filter(FaceData.id == face_data_id).first()

def get_face_data_by_student(db: Session, student_id: UUID):
    return db.query(FaceData).filter(FaceData.student_id == student_id).all()

def create_face_data(db: Session, face_data: FaceDataCreate):
    db_face_data = FaceData(
        student_id=face_data.student_id,
        face_image=face_data.face_image
    )
    db.add(db_face_data)
    db.commit()
    db.refresh(db_face_data)
    return db_face_data

def delete_face_data_by_student(db: Session, student_id: UUID) -> int:
    records = db.query(FaceData).filter(FaceData.student_id == student_id).all()
    if not records:
        return 0
    for record in records:
        db.delete(record)
    db.commit()
    return len(records)

# ✅ Çoklu base64 yüz verisi ekleyen fonksiyon
def create_multiple_face_data(db: Session, face_data_upload: FaceDataUpload):
    for base64_image in face_data_upload.face_images:
        try:
            decoded_image = base64.b64decode(base64_image)
        except Exception:
            raise ValueError("Invalid base64 image data.")
        
        db_face = FaceData(
            student_id=face_data_upload.student_id,
            face_image=decoded_image
        )
        db.add(db_face)
    db.commit()
    return f"{len(face_data_upload.face_images)} face data record(s) saved."
