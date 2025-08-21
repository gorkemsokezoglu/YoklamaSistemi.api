from sqlalchemy.orm import Session
from app.models.models import FaceData
from app.schemas.face_data import FaceDataCreate, FaceDataUpload
from uuid import UUID
import base64
import cv2
import numpy as np
import face_recognition
import pickle

def image_to_encoding(base64_image: str) -> bytes:
    """
    Base64 formatındaki görüntüyü face encoding'e çevirir ve binary formatta döndürür
    """
    try:
        # Base64'ü decode et
        image_bytes = base64.b64decode(base64_image)
        
        # Bytes'ı numpy array'e dönüştür
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise ValueError("Görüntü decode edilemedi")
        
        # BGR'den RGB'ye dönüştür
        rgb_image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Face encoding hesapla
        face_encodings = face_recognition.face_encodings(rgb_image)
        
        if len(face_encodings) == 0:
            raise ValueError("Görüntüde yüz tespit edilemedi")
        
        # İlk encoding'i al ve pickle ile serialize et
        encoding = face_encodings[0]
        encoding_bytes = pickle.dumps(encoding)
        
        return encoding_bytes
        
    except Exception as e:
        raise ValueError(f"Encoding oluşturma hatası: {str(e)}")

def get_face_data(db: Session, face_data_id: UUID):
    return db.query(FaceData).filter(FaceData.id == face_data_id).first()

def get_face_data_by_student(db: Session, student_id: UUID):
    return db.query(FaceData).filter(FaceData.student_id == student_id).all()

def create_face_data(db: Session, face_data: FaceDataCreate):
    # Base64 görüntüyü encoding'e çevir
    try:
        encoding_bytes = image_to_encoding(face_data.face_image)
    except ValueError as e:
        raise e
    
    db_face_data = FaceData(
        student_id=face_data.student_id,
        face_image=encoding_bytes  # Artık encoding kaydediyoruz
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
    successful_count = 0
    for base64_image in face_data_upload.face_images:
        try:
            # Base64 görüntüyü encoding'e çevir
            encoding_bytes = image_to_encoding(base64_image)
            
            db_face = FaceData(
                student_id=face_data_upload.student_id,
                face_image=encoding_bytes  # Encoding kaydediyoruz
            )
            db.add(db_face)
            successful_count += 1
        except Exception as e:
            print(f"Yüz verisi işlenirken hata: {str(e)}")
            continue
    
    if successful_count > 0:
        db.commit()
    
    return f"{successful_count} face encoding(s) saved."
