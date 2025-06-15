from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import os
import time
import tempfile
import logging

from ..models.database import get_db
from ..models.schemas import StudentCreate, StudentResponse, StudentUpdate
from ..services.cloudflare_adapter import CloudflareAdapter
from ..services.face_recognition import FaceRecognitionService
from ..utils.image_processing import ImageProcessor

router = APIRouter(prefix="/api/students", tags=["students"])

adapter = CloudflareAdapter()
face_service = FaceRecognitionService()
image_processor = ImageProcessor()

logger = logging.getLogger(__name__)


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
    """Crear un nuevo estudiante con su imagen de referencia - FIX ASYNC"""
    temp_file_path = None

    try:
        logger.info(f"Creating student: {nombre} {apellidos} ({codigo})")

        # Validar formato de imagen
        if not image_processor.is_valid_image(image):
            raise HTTPException(status_code=400, detail="Formato de imagen no válido")

        # ✅ FIX: await para método async
        existing_student = await adapter.get_student_by_codigo_async(db, codigo)
        if existing_student:
            raise HTTPException(status_code=400, detail="El código de estudiante ya existe")

        # Leer imagen en memoria
        image_content = await image.read()

        if len(image_content) == 0:
            raise HTTPException(status_code=400, detail="Imagen vacía")

        file_size_mb = len(image_content) / (1024 * 1024)

        if file_size_mb > 10:
            raise HTTPException(status_code=400, detail="Imagen demasiado grande (máximo 10MB)")

        # Crear archivo temporal para face recognition
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{int(time.time())}.jpg") as temp_file:
            temp_file.write(image_content)
            temp_file_path = temp_file.name

        # Extraer encoding facial del archivo temporal
        face_encoding = await face_service.extract_face_encoding(temp_file_path)

        if face_encoding is None:
            raise HTTPException(status_code=400, detail="No se detectó un rostro en la imagen")

        # Subir imagen usando image_processor
        image_url = await image_processor.save_image_from_path(temp_file_path, "reference")

        # Crear estudiante usando adapter - ✅ FIX: await
        student_data = {
            "nombre": nombre,
            "apellidos": apellidos,
            "codigo": codigo,
            "correo": correo,
            "requisitoriado": requisitoriado,
            "imagen_path": image_url,
            "face_encoding": face_encoding.tolist()
        }

        # ✅ FIX: await para método async
        student = await adapter.create_student_async(db, student_data, None)

        logger.info(f"Student created successfully: ID {student.get('id', 'unknown')}")

        return StudentResponse(**student)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating student: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error al crear estudiante: {str(e)}")

    finally:
        # Limpiar archivo temporal
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception as e:
                logger.warning(f"Could not remove temp file {temp_file_path}: {e}")


@router.get("/", response_model=List[StudentResponse])
async def get_all_students(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)
):
    """Obtener lista de todos los estudiantes - FIX ASYNC"""
    # ✅ FIX: await para método async
    students_data = await adapter.get_all_students_async(db)

    # Aplicar paginación manual
    paginated_students = students_data[skip:skip + limit]

    students = [StudentResponse(**student) for student in paginated_students]
    return students


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(student_id: int, db: Session = Depends(get_db)):
    """Obtener un estudiante por ID - FIX ASYNC"""
    # ✅ FIX: await para método async
    student_data = await adapter.get_student_by_id_async(db, student_id)
    if not student_data:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    return StudentResponse(**student_data)


@router.get("/codigo/{codigo}", response_model=StudentResponse)
async def get_student_by_codigo(codigo: str, db: Session = Depends(get_db)):
    """Obtener un estudiante por código - FIX ASYNC"""
    # ✅ FIX: await para método async
    student_data = await adapter.get_student_by_codigo_async(db, codigo)
    if not student_data:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    return StudentResponse(**student_data)


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
    """Actualizar datos de un estudiante - FIX ASYNC"""
    temp_file_path = None

    try:
        # ✅ FIX: await para verificar existencia
        student = await adapter.get_student_by_id_async(db, student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")

        # Preparar datos de actualización
        update_data = {}
        if nombre is not None:
            update_data["nombre"] = nombre
        if apellidos is not None:
            update_data["apellidos"] = apellidos
        if codigo is not None:
            # ✅ FIX: await para verificar código único
            existing = await adapter.get_student_by_codigo_async(db, codigo)
            if existing and existing.get('id') != student_id:
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

            # Leer imagen en memoria
            image_content = await image.read()

            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_update_{int(time.time())}.jpg") as temp_file:
                temp_file.write(image_content)
                temp_file_path = temp_file.name

            # Extraer nuevo encoding facial
            face_encoding = await face_service.extract_face_encoding(temp_file_path)

            if face_encoding is None:
                raise HTTPException(status_code=400, detail="No se detectó un rostro en la nueva imagen")

            # Subir nueva imagen
            new_image_url = await image_processor.save_image_from_path(temp_file_path, "reference")

            update_data["imagen_path"] = new_image_url
            update_data["face_encoding"] = face_encoding.tolist()

        # ✅ FIX: await para actualizar usando adapter
        updated_student = await adapter.update_student_async(db, student_id, update_data, image)

        if not updated_student:
            raise HTTPException(status_code=500, detail="Error al actualizar estudiante")

        return StudentResponse(**updated_student)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating student: {e}")
        raise HTTPException(status_code=500, detail=f"Error al actualizar estudiante: {str(e)}")

    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except:
                pass


@router.delete("/{student_id}")
async def delete_student(student_id: int, db: Session = Depends(get_db)):
    """Eliminar un estudiante - FIX ASYNC"""
    try:
        # ✅ FIX: await para verificar existencia y eliminar
        student = await adapter.get_student_by_id_async(db, student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")

        # ✅ FIX: await para eliminar
        success = await adapter.delete_student_async(db, student_id)

        if success:
            return {"message": "Estudiante eliminado correctamente"}
        else:
            raise HTTPException(status_code=500, detail="Error al eliminar estudiante")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting student: {e}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar estudiante: {str(e)}")


@router.get("/{student_id}/image")
async def get_student_image(student_id: int, db: Session = Depends(get_db)):
    """Obtener la imagen de un estudiante - FIX ASYNC"""
    from fastapi.responses import RedirectResponse

    # ✅ FIX: await
    student = await adapter.get_student_by_id_async(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    imagen_path = student.get("imagen_path")
    if not imagen_path:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")

    if imagen_path.startswith('http'):
        return RedirectResponse(url=imagen_path)
    else:
        raise HTTPException(status_code=404, detail="Imagen no accesible")


@router.post("/batch")
async def create_students_batch(
        students_data: List[dict],
        db: Session = Depends(get_db)
):
    """Crear múltiples estudiantes en lote - FIX ASYNC"""
    try:
        created_students = []
        errors = []

        for i, student_data in enumerate(students_data):
            try:
                required_fields = ['nombre', 'apellidos', 'codigo', 'correo']
                missing_fields = [field for field in required_fields if field not in student_data]

                if missing_fields:
                    errors.append({
                        "index": i,
                        "error": f"Campos faltantes: {missing_fields}",
                        "data": student_data
                    })
                    continue

                # ✅ FIX: await para verificar código único
                existing = await adapter.get_student_by_codigo_async(db, student_data['codigo'])
                if existing:
                    errors.append({
                        "index": i,
                        "error": f"Código {student_data['codigo']} ya existe",
                        "data": student_data
                    })
                    continue

                student_create_data = {
                    "nombre": student_data['nombre'],
                    "apellidos": student_data['apellidos'],
                    "codigo": student_data['codigo'],
                    "correo": student_data['correo'],
                    "requisitoriado": student_data.get('requisitoriado', False),
                    "imagen_path": None,
                    "face_encoding": None
                }

                # ✅ FIX: await para crear estudiante
                student = await adapter.create_student_async(db, student_create_data, None)
                created_students.append(student)

            except Exception as e:
                errors.append({
                    "index": i,
                    "error": str(e),
                    "data": student_data
                })

        return {
            "created": len(created_students),
            "errors": len(errors),
            "students": created_students,
            "error_details": errors
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en creación por lotes: {str(e)}")


@router.get("/{student_id}/face-encoding")
async def get_student_face_encoding(student_id: int, db: Session = Depends(get_db)):
    """Obtener el encoding facial de un estudiante - FIX ASYNC"""
    # ✅ FIX: await
    student = await adapter.get_student_by_id_async(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    face_encoding = student.get("face_encoding")
    if not face_encoding:
        raise HTTPException(status_code=404, detail="Encoding facial no encontrado")

    return {
        "student_id": student.get("id"),
        "nombre": f"{student.get('nombre', '')} {student.get('apellidos', '')}",
        "codigo": student.get("codigo"),
        "encoding_length": len(face_encoding),
        "encoding_preview": face_encoding[:5],
        "has_image": bool(student.get("imagen_path"))
    }