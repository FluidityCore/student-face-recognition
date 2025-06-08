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

# Logger
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
    """
    Crear un nuevo estudiante con su imagen de referencia
    Flujo optimizado para Railway + Cloudflare R2
    """
    temp_file_path = None

    try:
        logger.info(f"Creando estudiante: {nombre} {apellidos} ({codigo})")

        # Validar formato de imagen
        if not image_processor.is_valid_image(image):
            raise HTTPException(status_code=400, detail="Formato de imagen no válido")

        # Verificar que el código no exista usando adapter
        existing_student = adapter.get_student_by_codigo(db, codigo)
        if existing_student:
            raise HTTPException(status_code=400, detail="El código de estudiante ya existe")

        # Leer imagen en memoria
        logger.info("Leyendo imagen en memoria...")
        image_content = await image.read()

        if len(image_content) == 0:
            raise HTTPException(status_code=400, detail="Imagen vacía")

        file_size_mb = len(image_content) / (1024 * 1024)
        logger.info(f"Tamaño de imagen: {file_size_mb:.2f}MB")

        if file_size_mb > 10:  # Límite de 10MB
            raise HTTPException(status_code=400, detail="Imagen demasiado grande (máximo 10MB)")

        # Crear archivo temporal para face recognition
        logger.info("Creando archivo temporal...")
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{int(time.time())}.jpg") as temp_file:
            temp_file.write(image_content)
            temp_file_path = temp_file.name

        logger.info(f"Archivo temporal creado: {temp_file_path}")

        # Extraer encoding facial del archivo temporal
        logger.info("Extrayendo encoding facial...")
        face_encoding = await face_service.extract_face_encoding(temp_file_path)

        if face_encoding is None:
            raise HTTPException(status_code=400, detail="No se detectó un rostro en la imagen")

        logger.info(f"Encoding facial extraído: {len(face_encoding)} características")

        # Subir imagen a Cloudflare R2
        logger.info("Subiendo imagen a Cloudflare R2...")
        try:
            # Usar el image_processor para subir desde el archivo temporal
            image_url = await image_processor.save_image_from_path(temp_file_path, "reference")
            logger.info(f"Imagen subida a R2: {image_url}")
        except Exception as e:
            logger.error(f"Error al subir a R2: {e}")
            raise HTTPException(status_code=500, detail=f"Error al subir imagen: {str(e)}")

        # Crear estudiante usando adapter
        logger.info("Guardando estudiante usando CloudflareAdapter...")
        student_data = {
            "nombre": nombre,
            "apellidos": apellidos,
            "codigo": codigo,
            "correo": correo,
            "requisitoriado": requisitoriado,
            "imagen_path": image_url,  # URL de Cloudflare R2
            "face_encoding": face_encoding.tolist()  # Convertir numpy array a lista
        }

        student = adapter.create_student(db, student_data, None)  # None porque ya procesamos la imagen

        logger.info(f"Estudiante creado exitosamente: ID {student.get('id', 'unknown')}")

        # Convertir a formato de respuesta
        return StudentResponse(**student)

    except HTTPException:
        # Re-lanzar HTTPExceptions sin modificar
        raise
    except Exception as e:
        logger.error(f"Error inesperado al crear estudiante: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error al crear estudiante: {str(e)}")

    finally:
        # Limpiar archivo temporal
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                logger.info(f"Archivo temporal eliminado: {temp_file_path}")
            except Exception as e:
                logger.warning(f"No se pudo eliminar archivo temporal {temp_file_path}: {e}")


@router.get("/", response_model=List[StudentResponse])
def get_all_students(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db)
):
    """
    Obtener lista de todos los estudiantes
    """
    # Usar adapter en lugar de servicio directo
    students_data = adapter.get_all_students(db)

    # Aplicar paginación manual (ya que get_all_students no tiene skip/limit)
    paginated_students = students_data[skip:skip + limit]

    # Convertir a formato de respuesta
    students = [StudentResponse(**student) for student in paginated_students]
    return students


@router.get("/{student_id}", response_model=StudentResponse)
def get_student(student_id: int, db: Session = Depends(get_db)):
    """
    Obtener un estudiante por ID
    """
    student_data = adapter.get_student_by_id(db, student_id)
    if not student_data:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    return StudentResponse(**student_data)


@router.get("/codigo/{codigo}", response_model=StudentResponse)
def get_student_by_codigo(codigo: str, db: Session = Depends(get_db)):
    """
    Obtener un estudiante por código
    """
    student_data = adapter.get_student_by_codigo(db, codigo)
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
    """
    Actualizar datos de un estudiante
    """
    temp_file_path = None

    try:
        # Verificar que el estudiante existe usando adapter
        student = adapter.get_student_by_id(db, student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")

        # Preparar datos de actualización
        update_data = {}
        if nombre is not None:
            update_data["nombre"] = nombre
        if apellidos is not None:
            update_data["apellidos"] = apellidos
        if codigo is not None:
            # Verificar que el nuevo código no exista usando adapter
            existing = adapter.get_student_by_codigo(db, codigo)
            if existing and existing.get('id') != student_id:
                raise HTTPException(status_code=400, detail="El código ya existe")
            update_data["codigo"] = codigo
        if correo is not None:
            update_data["correo"] = correo
        if requisitoriado is not None:
            update_data["requisitoriado"] = requisitoriado

        # Si hay nueva imagen, procesarla
        if image:
            logger.info(f"Actualizando imagen para estudiante {student_id}")

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

            # Subir nueva imagen a R2
            new_image_url = await image_processor.save_image_from_path(temp_file_path, "reference")

            update_data["imagen_path"] = new_image_url
            update_data["face_encoding"] = face_encoding.tolist()

            logger.info(f"Nueva imagen procesada y subida: {new_image_url}")

        # Actualizar usando adapter
        updated_student = adapter.update_student(db, student_id, update_data, image)

        if not updated_student:
            raise HTTPException(status_code=500, detail="Error al actualizar estudiante")

        return StudentResponse(**updated_student)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al actualizar estudiante: {e}")
        raise HTTPException(status_code=500, detail=f"Error al actualizar estudiante: {str(e)}")

    finally:
        # Limpiar archivo temporal
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                logger.info(f"Archivo temporal eliminado: {temp_file_path}")
            except:
                pass


@router.delete("/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    """
    Eliminar un estudiante
    """
    try:
        # Verificar existencia y eliminar usando adapter
        student = adapter.get_student_by_id(db, student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")

        logger.info(f"Eliminando estudiante {student_id} usando CloudflareAdapter")

        # Eliminar usando adapter (maneja tanto D1 como SQLite)
        success = adapter.delete_student(db, student_id)

        if success:
            return {"message": "Estudiante eliminado correctamente"}
        else:
            raise HTTPException(status_code=500, detail="Error al eliminar estudiante")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al eliminar estudiante: {e}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar estudiante: {str(e)}")


@router.get("/{student_id}/image")
def get_student_image(student_id: int, db: Session = Depends(get_db)):
    """
    Obtener la imagen de un estudiante (redirect a Cloudflare R2)
    """
    from fastapi.responses import RedirectResponse

    student = adapter.get_student_by_id(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    imagen_path = student.get("imagen_path")
    if not imagen_path:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")

    # En Railway + Cloudflare R2, redirigir a la URL pública
    if imagen_path.startswith('http'):
        return RedirectResponse(url=imagen_path)
    else:
        # Fallback para imágenes locales (no debería pasar en producción)
        raise HTTPException(status_code=404, detail="Imagen no accesible")


@router.post("/batch")
async def create_students_batch(
        students_data: List[dict],
        db: Session = Depends(get_db)
):
    """
    Crear múltiples estudiantes en lote (sin imágenes)
    Útil para importar datos masivos
    """
    try:
        created_students = []
        errors = []

        for i, student_data in enumerate(students_data):
            try:
                # Validar campos requeridos
                required_fields = ['nombre', 'apellidos', 'codigo', 'correo']
                missing_fields = [field for field in required_fields if field not in student_data]

                if missing_fields:
                    errors.append({
                        "index": i,
                        "error": f"Campos faltantes: {missing_fields}",
                        "data": student_data
                    })
                    continue

                # Verificar código único usando adapter
                existing = adapter.get_student_by_codigo(db, student_data['codigo'])
                if existing:
                    errors.append({
                        "index": i,
                        "error": f"Código {student_data['codigo']} ya existe",
                        "data": student_data
                    })
                    continue

                # Crear estudiante usando adapter
                student_create_data = {
                    "nombre": student_data['nombre'],
                    "apellidos": student_data['apellidos'],
                    "codigo": student_data['codigo'],
                    "correo": student_data['correo'],
                    "requisitoriado": student_data.get('requisitoriado', False),
                    "imagen_path": None,
                    "face_encoding": None
                }

                student = adapter.create_student(db, student_create_data, None)
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
def get_student_face_encoding(student_id: int, db: Session = Depends(get_db)):
    """
    Obtener el encoding facial de un estudiante (para debugging)
    """
    student = adapter.get_student_by_id(db, student_id)
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
        "encoding_preview": face_encoding[:5],  # Solo primeros 5 valores
        "has_image": bool(student.get("imagen_path"))
    }