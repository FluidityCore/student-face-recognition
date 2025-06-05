from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from database import get_all_students, get_student_by_id
from models.student import StudentsResponse

app = FastAPI(title="Student Recognition API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Student Recognition API is running!"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# ✅ ORDEN CORRECTO: rutas específicas ANTES que rutas con parámetros
@app.get("/students/count")
def get_students_count():
    """Obtener solo el número de estudiantes registrados"""
    students = get_all_students()
    return {"count": len(students)}

@app.get("/students", response_model=StudentsResponse)
def get_students():
    """Obtener todos los estudiantes con sus embeddings"""
    try:
        students = get_all_students()
        return StudentsResponse(
            count=len(students),
            students=students
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener estudiantes: {str(e)}")

@app.get("/students/{student_id}")
def get_student(student_id: int):
    """Obtener un estudiante específico"""
    student = get_student_by_id(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    return student

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)