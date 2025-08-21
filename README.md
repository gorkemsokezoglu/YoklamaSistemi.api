## Yüz Tanıma Yoklama Sistemi API

Bu depo, yüz tanıma destekli yoklama sisteminin backend API'sidir. FastAPI ile geliştirilmiştir; PostgreSQL + SQLAlchemy kullanır, JWT tabanlı kimlik doğrulama ve rol bazlı yetkilendirme içerir. Yüz tanıma için OpenCV ve face_recognition kullanılmaktadır.

### 🚀 Özellikler

- Modern, hızlı FastAPI REST API
- PostgreSQL + SQLAlchemy ORM
- Alembic ile veritabanı migrasyonları
- JWT ile kimlik doğrulama, rol bazlı yetkilendirme (öğrenci/akademisyen)
- Yüz tanıma ile otomatik yoklama
- PDF yoklama raporu üretimi (WeasyPrint + Jinja2)
- Otomatik yoklama oluşturucu zamanlayıcı (APScheduler)
- Swagger/OpenAPI dokümantasyonu

## 🗺️ Mimari Genel Bakış

- `app/main.py`: Uygulama başlatma, CORS, router bağlama, zamanlayıcıyı başlatma/durdurma
- `app/api/v1/endpoints/`: Tüm işlevsel endpoint’ler
  - `auth.py`: Giriş, kayıt, e-posta doğrulama, şifre sıfırlama
  - `students.py`, `academicians.py`, `users.py`: Kullanıcı/öğrenci/akademisyen işlemleri
  - `courses.py`, `course_schedules.py`: Ders ve ders programları
  - `attendances.py`, `face_recognition.py`: Yoklama ve yüz tanıma akışı
  - `course_selections_student.py`, `course_selections_academician.py`: Ders seçim süreçleri
  - `faculties.py`, `departments.py`: Fakülte/bölüm listeleme
  - `reports.py`: PDF yoklama raporu
- `app/models/models.py`: Tüm veri modelleri (User, Student, Academician, Course, Attendance, FaceData, vb.)
- `app/crud/`: Veritabanı CRUD işlemleri
- `app/schemas/`: İstek/cevap Pydantic şemaları
- `app/services/`: E-posta, yüz tanıma, performans, rapor ve zamanlayıcı servisleri
- `app/utils/auth.py`: JWT, parola, rol ve endpoint bazlı izin kontrolü
- `app/database.py`: SQLAlchemy engine/Session ve `Base`

## 🛠️ Kurulum

### 1) Gereksinimler

- Python 3.8+
- PostgreSQL 12+
- Windows için yüz tanıma bağımlılıkları (dlib/face_recognition) nedeniyle C++ Build Tools ve CMake gerekebilir.
  - Visual Studio Build Tools ve CMake kurulu değilse kurun ve sonra tekrar `pip install` deneyin.

### 2) Sanal ortam ve bağımlılıklar

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

pip install --upgrade pip
pip install -r requirements.txt
```

Not: `dlib`/`face_recognition` kurulumu Windows’ta derleme gerektirebilir. Gerekirse CMake ve C++ Build Tools kurun veya uyumlu hazır wheel dosyalarını kullanın.

### 3) Veritabanı ayarı

- Varsayılan bağlantı: `app/database.py` içinde `postgresql://admin:01230123@localhost:5432/db_yuzTanima`
- Kendi PostgreSQL bilginize göre bu değeri düzenleyin veya yeni bir veritabanı oluşturun:

```sql
CREATE DATABASE db_yuzTanima;
```

### 4) Ortam değişkenleri

Uygulama bazı değerleri ortam değişkenlerinden okur (bkz. `app/core/config.py`). `.env` kullanabilirsiniz.

- `DATABASE_URL` (opsiyonel; fiili kullanım `app/database.py` içinden gelir)
- `SECRET_KEY` (JWT için)
- `EMAIL_ADDRESS`, `EMAIL_PASSWORD` (Gmail uygulama şifresi önerilir)
- `BACKEND_URL` (e-posta linkleri)
- `ACCESS_TOKEN_EXPIRE_MINUTES` (varsayılan 30)

Örnek `.env` (opsiyonel):

```env
DATABASE_URL=postgresql://admin:pass@localhost:5432/db_yuzTanima
SECRET_KEY=super-secret-key
EMAIL_ADDRESS=example@gmail.com
EMAIL_PASSWORD=xxxxxxxxxxxxxxxx
BACKEND_URL=http://localhost:8000
```

### 5) Şema oluşturma / migrasyon

Projede iki yol vardır:

- Uygulama başlangıcında `Base.metadata.create_all` tabloları oluşturur (hızlı başlangıç).
- Alembic ile versiyonlu migrasyon:

```bash
alembic upgrade head
```

### 6) Uygulamayı çalıştırma

```bash
uvicorn app.main:app --reload
```

### 7) API dokümantasyonu

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🔐 Kimlik Doğrulama ve Yetkilendirme

- JWT Bearer kullanılır.
- Roller: `student`, `academician`.
- Öğrencilerin erişebileceği endpoint/metodları sınırlayan kontrol `app/utils/auth.py` içindedir.

Giriş örneği:

```http
POST /api/v1/auth/token
Content-Type: application/json

{
  "email": "ogrenci@ogr.iuc.edu.tr",
  "password": "parola123"
}
```

Cevapta `access_token` döner. Sonraki isteklerde `Authorization: Bearer <token>` başlığını gönderin.

## 📌 Önemli Endpoint’ler (Özet)

- Auth: `/api/v1/auth/token`, `/api/v1/auth/register`, `/api/v1/auth/verify-code`, `/api/v1/auth/forgot-password`, `/api/v1/auth/reset-password`, `/api/v1/auth/logout`
- Öğrenci: `/api/v1/students/me`, `/api/v1/students/{id}`, `PUT /api/v1/students/me`
- Dersler: `GET /api/v1/courses`, `GET /api/v1/courses/{id}`, `GET /api/v1/courses/my-courses`
- Ders Programı: `GET /api/v1/course-schedules`, `GET /api/v1/course-schedules/course/{course_id}`
- Yoklama: `GET /api/v1/attendances`, `GET /api/v1/attendances/myAttendances`
- Yüz Tanıma: `POST /api/v1/face-recognition/identify/{course_id}` (öğrenci giriş yapmış olmalı, kamera açılır)
- Ders Seçimi (Öğrenci): `POST /api/v1/course-selections-student`, `GET /api/v1/course-selections-student/my-selections`
- Ders Seçimi (Akademisyen): `POST/GET/PUT/DELETE /api/v1/course-selections-academicians`
- Fakülte/Bölüm: `GET /api/v1/faculties`, `GET /api/v1/departments`, `GET /api/v1/departments/faculty/{faculty_id}`
- Raporlar: `GET /api/v1/reports/attendance/{course_id}/{date}` → PDF indirir

Örnek: Yüz tanıma ile yoklama

```http
POST /api/v1/face-recognition/identify/{course_id}
Authorization: Bearer <token>
```

Başarılı tespit sonrası, ders saatleri uygunsa yoklama oluşturulur/güncellenir ve öğrencinin derse katılım oranı hesaplanır.

## 🧠 Yüz Tanıma ve Yoklama Akışı

1. Kayıt sırasında öğrencinin yüz verileri encoding’e çevrilip `face_data` tablosuna kaydedilir.
2. Öğrenci, dersteyken `identify/{course_id}` çağrısı ile kamerayı açar ve yüz tanıma yapılır.
3. Tanınan öğrenci giriş yapan kullanıcı ile eşleşmezse işlem reddedilir.
4. O an dersin programı (`course_schedules`) içinde ise:
   - Bugüne ait yoklama yoksa yeni kayıt oluşturulur (`status=True`).
   - Kayıt var ve `status=False` ise `True` olarak güncellenir.
5. Her başarılı yoklama sonrası `PerformanceCalculator` ilgili ders için devam oranını günceller.

### ⏱️ Otomatik Yoklama Kayıtları (Scheduler)

- `AttendanceScheduler` her 5 dakikada bir aktif ders başlangıçlarını kontrol eder ve o derslere kayıtlı/ onaylı öğrenciler için günün yoklama kayıtlarını (başlangıçta `status=False`) oluşturur.
- Öğrenci yüz tanıma yaptığında bu kayıt `True` olur.

## 🧾 PDF Yoklama Raporu

- `GET /api/v1/reports/attendance/{course_id}/{date}` çağrısı PDF döner.
- Sadece akademisyenler kendi dersleri için rapor üretebilir.

## 🧩 Sık Karşılaşılan Notlar

- Windows’ta `dlib` derleme sorunlarında CMake ve C++ Build Tools kurulu olduğundan emin olun.
- Gmail ile e-posta gönderimi için “Uygulama Şifresi” kullanın ve `.env`’de saklayın.
- Öğrenci e-postası doğrulanmadan girişe izin verilmez.

## 🗂️ Proje Yapısı (Özet)

```
YoklamaSistemi.api/
├── alembic/
├── app/
│   ├── api/v1/endpoints/
│   ├── core/
│   ├── crud/
│   ├── models/
│   ├── schemas/
│   └── services/
├── requirements.txt
└── alembic.ini
```

## 📝 Lisans

Bu proje MIT lisansı altındadır.
