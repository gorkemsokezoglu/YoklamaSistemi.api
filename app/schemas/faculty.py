from pydantic import BaseModel
from typing import Optional, List

class FacultyBase(BaseModel):
    name: str

class FacultyCreate(FacultyBase):
    pass

class FacultyUpdate(FacultyBase):
    name: Optional[str] = None

class FacultyInDB(FacultyBase):
    id: int

    class Config:
        from_attributes = True

class Faculty(FacultyInDB):
    pass 