# Yoklama Sistemi API

Bu proje, yoklama sisteminin backend API'sini içermektedir. FastAPI framework'ü kullanılarak geliştirilmiştir.

## 🚀 Özellikler

- FastAPI tabanlı modern REST API
- SQLAlchemy ORM ile veritabanı yönetimi
- Alembic ile veritabanı migrasyon desteği
- JWT tabanlı kimlik doğrulama
- Swagger/OpenAPI dokümantasyonu

## 🛠️ Kurulum

1. Python 3.8 veya daha yüksek bir sürümün yüklü olduğundan emin olun.

2. Sanal ortam oluşturun ve aktif edin:

```bash
python -m venv .venv
# Windows için
.venv\Scripts\activate
# Linux/Mac için
source .venv/bin/activate
```

3. Gerekli paketleri yükleyin:

```bash
pip install -r requirements.txt
```

4. Veritabanı migrasyonlarını çalıştırın:

```bash
alembic upgrade head
```

5. API'yi başlatın:

```bash
uvicorn app.main:app --reload
```

## 📚 API Dokümantasyonu

API çalışır durumdayken aşağıdaki URL'lerden dokümantasyona erişebilirsiniz:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🗄️ Proje Yapısı

```
yoklamasistemi.api/
├── alembic/              # Veritabanı migrasyon dosyaları
├── app/                  # Ana uygulama kodları
│   ├── api/             # API endpoint'leri
│   ├── core/            # Çekirdek yapılandırmalar
│   ├── crud/            # Veritabanı işlemleri
│   ├── models/          # Veritabanı modelleri
│   └── schemas/         # Pydantic modelleri
├── alembic.ini          # Alembic yapılandırması
└── requirements.txt     # Proje bağımlılıkları
```

## 🔐 Ortam Değişkenleri

Projeyi çalıştırmadan önce aşağıdaki ortam değişkenlerini ayarlamanız gerekmektedir:

- `DATABASE_URL`: Veritabanı bağlantı URL'i
- `SECRET_KEY`: JWT token'ları için gizli anahtar
- `ALGORITHM`: JWT algoritması (varsayılan: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token geçerlilik süresi

## 📝 Lisans

Bu proje [MIT](LICENSE) lisansı altında lisanslanmıştır.
