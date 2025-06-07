from uuid import UUID
import cv2
import numpy as np
from typing import Tuple, Optional, List
import face_recognition
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.models import FaceData, Student

class FaceRecognitionService:
    def __init__(self, db: Session):
        # Yüz tanıma için gerekli model yükleme işlemleri
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.db = db
        
    def detect_face(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """
        Görüntüde yüz tespiti yapar
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        
        if len(faces) == 0:
            return None
            
        # İlk tespit edilen yüzü al
        x, y, w, h = faces[0]
        face_image = frame[y:y+h, x:x+w]
        return face_image

    def get_face_encoding(self, face_image: np.ndarray) -> Optional[np.ndarray]:
        """
        Yüz görüntüsünden encoding oluşturur
        """
        try:
            # BGR'den RGB'ye dönüştür
            rgb_image = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
            # Yüz encoding'ini hesapla
            face_encodings = face_recognition.face_encodings(rgb_image)
            
            if len(face_encodings) > 0:
                return face_encodings[0]
            return None
        except Exception as e:
            print(f"Encoding oluşturma hatası: {str(e)}")
            return None

    def bytes_to_image(self, image_bytes: bytes) -> Optional[np.ndarray]:
        """
        Bytes formatındaki görüntüyü numpy dizisine dönüştürür
        """
        try:
            # Bytes'ı numpy array'e dönüştür
            nparr = np.frombuffer(image_bytes, np.uint8)
            # Numpy array'i görüntüye decode et
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                raise ValueError("Görüntü decode edilemedi")
                
            return img
            
        except Exception as e:
            print(f"Görüntü dönüştürme hatası: {str(e)}")
            return None

    def get_all_face_encodings(self) -> List[Tuple[UUID, np.ndarray]]:
        """
        Veritabanındaki tüm yüz encoding'lerini getirir
        """
        face_data_records = self.db.query(FaceData).all()
        encodings = []
        
        for record in face_data_records:
            try:
                print(f"İşleniyor: Student ID {record.student_id}")
                
                # Veri kontrolü
                if not record.face_image:
                    print(f"Uyarı: {record.student_id} ID'li öğrencinin yüz verisi boş")
                    continue
                
                # Görüntüyü numpy dizisine dönüştür
                face_image = self.bytes_to_image(record.face_image)
                
                if face_image is None:
                    print(f"Uyarı: {record.student_id} ID'li öğrencinin görüntüsü decode edilemedi")
                    continue
                
                # RGB formatına dönüştür
                rgb_image = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
                
                # Yüz encoding'ini hesapla
                face_encodings = face_recognition.face_encodings(rgb_image)
                
                if len(face_encodings) > 0:
                    print(f"Başarılı: {record.student_id} ID'li öğrencinin yüz encoding'i oluşturuldu")
                    encodings.append((record.student_id, face_encodings[0]))
                else:
                    print(f"Uyarı: {record.student_id} ID'li öğrencinin yüzü tespit edilemedi")
                    
            except Exception as e:
                print(f"Encoding oluşturma hatası (student_id: {record.student_id}): {str(e)}")
                continue
            
        print(f"Toplam {len(encodings)} adet yüz encoding'i oluşturuldu")
        return encodings

    def find_matching_student(self, face_encoding: np.ndarray) -> Optional[UUID]:
        """
        Verilen yüz encoding'i ile eşleşen öğrenciyi bulur
        """
        known_encodings = self.get_all_face_encodings()
        
        for student_id, known_encoding in known_encodings:
            # Yüzleri karşılaştır
            results = face_recognition.compare_faces([known_encoding], face_encoding, tolerance=0.6)
            if results[0]:
                return student_id
                
        return None

    def process_frame(self, frame: np.ndarray) -> Tuple[Optional[UUID], Optional[np.ndarray]]:
        """
        Tek bir frame'i işler ve eşleşen öğrenci ID'sini döndürür
        """
        # Yüz tespiti yap
        face_image = self.detect_face(frame)
        if face_image is None:
            return None, None

        # Yüz encoding'i oluştur
        face_encoding = self.get_face_encoding(face_image)
        if face_encoding is None:
            return None, None

        # Eşleşen öğrenciyi bul
        student_id = self.find_matching_student(face_encoding)
        
        return student_id, face_image

    def start_recognition(self, video_source: int = 0) -> Optional[UUID]:
        """
        Webcam'den sürekli görüntü alıp yüz tanıma yapar
        """
        cap = cv2.VideoCapture(video_source)
        if not cap.isOpened():
            raise ValueError("Kamera açılamadı")

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # Frame'i işle
                student_id, face_image = self.process_frame(frame)

                # Sonucu görselleştir
                if face_image is not None:
                    cv2.imshow('Yüz Tanıma', face_image)
                    
                    if student_id is not None:
                        print(f"Yüz tanındı! Öğrenci ID: {student_id}")
                        return student_id

                # 'q' tuşuna basılırsa çık
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        finally:
            cap.release()
            cv2.destroyAllWindows()

        return None 