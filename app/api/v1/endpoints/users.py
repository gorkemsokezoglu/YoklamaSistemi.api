from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserResponse
from app.crud.crud_user import create_user, get_user, get_users, delete_user
from app.database import SessionLocal

router = APIRouter(
    prefix="/api/v1/users",
    tags=["users"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/{user_id}", response_model=UserResponse)
def read_user(user_id: str, db: Session = Depends(get_db)):
    db_user = get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.get("/", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db)):
    users = get_users(db)
    return users

@router.delete("/{user_id}")
def remove_user(user_id: str, db: Session = Depends(get_db)):
    deleted_user = delete_user(db, user_id)
    if not deleted_user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"ok": True}
