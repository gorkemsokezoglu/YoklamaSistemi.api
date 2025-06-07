# Yalnızca swaggerdan deneme amaçlı kullanılan bir servistir.

from uuid import UUID
import cv2
import numpy as np
from typing import List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.models import FaceData

class FaceCaptureService:
    def __init__(self, db: Session):
        self.db = db
        
    def capture_photos(self, video_source: int = 0) -> List[bytes]:
        """
        Webcam'den 5 adet fotoğraf alır
        """
        cap = cv2.VideoCapture(video_source)
        if not cap.isOpened():
            raise ValueError("Kamera açılamadı")

        photos = []
        photo_count = 0
        total_photos = 5

        try:
            while photo_count < total_photos:
                ret, frame = cap.read()
                if not ret:
                    break

                # Kalan fotoğraf sayısını göster
                cv2.putText(frame, f"Kalan fotoğraf: {total_photos - photo_count}", (10, 30),
                          cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                # Görüntüyü göster
                cv2.imshow('Fotoğraf Çek', frame)
                
                # 'c' tuşuna basılırsa fotoğrafı kaydet
                key = cv2.waitKey(1) & 0xFF
                if key == ord('c'):
                    # Görüntüyü binary formata dönüştür
                    _, buffer = cv2.imencode('.jpg', frame)
                    photo_binary = buffer.tobytes()
                    photos.append(photo_binary)
                    photo_count += 1
                    print(f"Fotoğraf {photo_count}/{total_photos} kaydedildi!")
                
                # 'q' tuşuna basılırsa çık
                if key == ord('q'):
                    break

        finally:
            cap.release()
            cv2.destroyAllWindows()

        if len(photos) < total_photos:
            raise ValueError(f"Sadece {len(photos)} fotoğraf çekilebildi. {total_photos} fotoğraf gerekli.")

        return photos

    def save_photos(self, student_id: UUID, photos: List[bytes]) -> bool:
        """
        Alınan fotoğrafları veritabanına kaydeder
        """
        try:
            for photo in photos:
                face_data = FaceData(
                    student_id=student_id,
                    face_image=photo,
                    created_at=datetime.now()
                )
                self.db.add(face_data)
            
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Fotoğraflar kaydedilirken hata oluştu: {str(e)}")
            return False 