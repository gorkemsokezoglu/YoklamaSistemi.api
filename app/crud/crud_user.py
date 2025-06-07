from sqlalchemy.orm import Session
from app.models.models import User
from app.schemas.user import UserCreate
import uuid

def create_user(db: Session, user: UserCreate):
    db_user = User(
        id=uuid.uuid4(),
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        password=user.password,  # Şifre hash'lenmeden kaydediliyor
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: uuid.UUID):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_users(db: Session):
    return db.query(User).all()

def delete_user(db: Session, user_id: uuid.UUID):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
    return user
