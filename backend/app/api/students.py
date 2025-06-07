from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import os

from ..models.database import get_db
from ..models.schemas import StudentCreate, StudentResponse, StudentUpdate
from ..services.database_service import StudentService
from ..services.face_recognition import FaceRecognitionService
from ..utils.image_processing import ImageProcessor

router = APIRouter(prefix="/api/students", tags=["students"])

# Servicios
student_service = StudentService()
face_service = FaceRecognitionService()
image_processor = ImageProcessor()


@router.post("/", response_model=StudentResponse)
async def create_student(
        nombre: str = Form(...),
        apellidos: str = Form(...),
        codigo: str = Form(...),
        correo: str = Form(...),
        requisitoriado: bool = Form(False),
        image: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    """
    Crear un nuevo estudiante con su imagen de referencia
    """
    try:
        # Validar formato de imagen
        if not image_processor.is_valid_image(image):
            raise HTTPException(status_code=400, detail="Formato de imagen no válido")

        # Verificar que el código no exista
        existing_student = student_service.get_student_by_codigo(db, codigo)
        if existing_student:
            raise HTTPException(status_code=400, detail="El código de estudiante ya existe")

        # Procesar imagen y extraer características faciales
        image_path = await image_processor.save_image(image, "reference")
        face_encoding = await face_service.extract_face_encoding(image_path)

        if face_encoding is None:
            # Limpiar archivo si no se detectó rostro
            os.remove(image_path)
            raise HTTPException(status_code=400, detail="No se detectó un rostro en la imagen")

        # Crear estudiante en la base de datos
        student_data = StudentCreate(
            nombre=nombre,
            apellidos=apellidos,
            codigo=codigo,
            correo=correo,
            requisitoriado=requisitoriado,
            imagen_path=image_path,
            face_encoding=face_encoding.tolist()  # Convertir numpy array a lista
        )

        student = student_service.create_student(db, student_data)
        return student

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear estudiante: {str(e)}")


@router.get("/", response_model=List[StudentResponse])
def get_all_students(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)
):
    """
    Obtener lista de todos los estudiantes
    """
    students = student_service.get_students(db, skip=skip, limit=limit)
    return students


@router.get("/{student_id}", response_model=StudentResponse)
def get_student(student_id: int, db: Session = Depends(get_db)):
    """
    Obtener un estudiante por ID
    """
    student = student_service.get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    return student


@router.get("/codigo/{codigo}", response_model=StudentResponse)
def get_student_by_codigo(codigo: str, db: Session = Depends(get_db)):
    """
    Obtener un estudiante por código
    """
    student = student_service.get_student_by_codigo(db, codigo)
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    return student


@router.put("/{student_id}", response_model=StudentResponse)
async def update_student(
        student_id: int,
        nombre: Optional[str] = Form(None),
        apellidos: Optional[str] = Form(None),
        codigo: Optional[str] = Form(None),
        correo: Optional[str] = Form(None),
        requisitoriado: Optional[bool] = Form(None),
        image: Optional[UploadFile] = File(None),
        db: Session = Depends(get_db)
):
    """
    Actualizar datos de un estudiante
    """
    try:
        # Verificar que el estudiante existe
        student = student_service.get_student(db, student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")

        # Preparar datos de actualización
        update_data = {}
        if nombre is not None:
            update_data["nombre"] = nombre
        if apellidos is not None:
            update_data["apellidos"] = apellidos
        if codigo is not None:
            # Verificar que el nuevo código no exista
            existing = student_service.get_student_by_codigo(db, codigo)
            if existing and existing.id != student_id:
                raise HTTPException(status_code=400, detail="El código ya existe")
            update_data["codigo"] = codigo
        if correo is not None:
            update_data["correo"] = correo
        if requisitoriado is not None:
            update_data["requisitoriado"] = requisitoriado

        # Si hay nueva imagen, procesarla
        if image:
            if not image_processor.is_valid_image(image):
                raise HTTPException(status_code=400, detail="Formato de imagen no válido")

            # Eliminar imagen anterior
            if student.imagen_path and os.path.exists(student.imagen_path):
                os.remove(student.imagen_path)

            # Procesar nueva imagen
            image_path = await image_processor.save_image(image, "reference")
            face_encoding = await face_service.extract_face_encoding(image_path)

            if face_encoding is None:
                os.remove(image_path)
                raise HTTPException(status_code=400, detail="No se detectó un rostro en la nueva imagen")

            update_data["imagen_path"] = image_path
            update_data["face_encoding"] = face_encoding.tolist()

        student_update = StudentUpdate(**update_data)
        updated_student = student_service.update_student(db, student_id, student_update)
        return updated_student

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar estudiante: {str(e)}")


@router.delete("/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    """
    Eliminar un estudiante
    """
    try:
        student = student_service.get_student(db, student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")

        # Eliminar imagen física
        if student.imagen_path and os.path.exists(student.imagen_path):
            os.remove(student.imagen_path)

        # Eliminar de la base de datos
        success = student_service.delete_student(db, student_id)
        if success:
            return {"message": "Estudiante eliminado correctamente"}
        else:
            raise HTTPException(status_code=500, detail="Error al eliminar estudiante")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar estudiante: {str(e)}")


@router.get("/{student_id}/image")
def get_student_image(student_id: int, db: Session = Depends(get_db)):
    """
    Obtener la imagen de un estudiante
    """
    from fastapi.responses import FileResponse

    student = student_service.get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    if not student.imagen_path or not os.path.exists(student.imagen_path):
        raise HTTPException(status_code=404, detail="Imagen no encontrada")

    return FileResponse(student.imagen_path)