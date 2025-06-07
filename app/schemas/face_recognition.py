from pydantic import BaseModel
from typing import Optional

class FaceRecognitionRequest(BaseModel):
    student_id: int
    course_id: int 