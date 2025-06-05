from pydantic import BaseModel
from typing import List, Optional

class Student(BaseModel):
    id: int
    nombre: str
    apellidos: str
    correo: Optional[str] = None
    requisitoriado: bool = False
    kp: List[float]  # Los embeddings PCA

class StudentsResponse(BaseModel):
    count: int
    students: List[Student]