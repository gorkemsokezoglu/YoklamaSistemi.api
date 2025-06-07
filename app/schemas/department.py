from pydantic import BaseModel
from typing import Optional

class DepartmentBase(BaseModel):
    name: str
    faculty_id: int

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentUpdate(DepartmentBase):
    name: Optional[str] = None
    faculty_id: Optional[int] = None

class DepartmentInDB(DepartmentBase):
    id: int

    class Config:
        from_attributes = True

class Department(DepartmentInDB):
    pass 