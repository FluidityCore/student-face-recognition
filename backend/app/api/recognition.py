from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Dict, Any
import os
import time

from ..models.database import get_db
from ..models.schemas import RecognitionResult, RecognitionLog
from ..services.database_service import StudentService, LogService
from ..services.face_recognition import FaceRecognitionService
from ..utils.image_processing import ImageProcessor

router = APIRouter(prefix="/api", tags=["recognition"])

# Servicios
student_service = StudentService()
face_service = FaceRecognitionService()
image_processor = ImageProcessor()
log_service = LogService()


@router.post("/recognize", response_model=RecognitionResult)
async def recognize_student(
        image: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    """
    Reconocer estudiante a partir de una imagen
    """
    start_time = time.time()
    temp_image_path = None

    try:
        # Validar formato de imagen
        if not image_processor.is_valid_image(image):
            raise HTTPException(status_code=400, detail="Formato de imagen no válido")

        # Guardar imagen temporalmente
        temp_image_path = await image_processor.save_image(image, "recognition")

        # Extraer características faciales de la imagen
        face_encoding = await face_service.extract_face_encoding(temp_image_path)

        if face_encoding is None:
            # Limpiar archivo temporal
            if temp_image_path and os.path.exists(temp_image_path):
                os.remove(temp_image_path)
            raise HTTPException(status_code=400, detail="No se detectó un rostro en la imagen")

        # Obtener todos los estudiantes para comparación
        students = student_service.get_all_students(db)

        if not students:
            raise HTTPException(status_code=404, detail="No hay estudiantes registrados en el sistema")

        # Realizar reconocimiento
        recognition_result = await face_service.recognize_face(face_encoding, students)

        # Calcular tiempo de procesamiento
        processing_time = time.time() - start_time

        # Registrar en logs
        log_data = RecognitionLog(
            found=recognition_result["found"],
            student_id=recognition_result.get("student", {}).get("id") if recognition_result["found"] else None,
            similarity=recognition_result.get("similarity", 0.0),
            confidence=recognition_result.get("confidence", "Baja"),
            processing_time=processing_time,
            image_path=temp_image_path
        )

        log_service.create_recognition_log(db, log_data)

        # Limpiar imagen temporal (opcional, se puede mantener para logs)
        # if temp_image_path and os.path.exists(temp_image_path):
        #     os.remove(temp_image_path)

        # Agregar información adicional al resultado
        result = RecognitionResult(
            found=recognition_result["found"],
            student=recognition_result.get("student"),
            similarity=recognition_result.get("similarity", 0.0),
            confidence=recognition_result.get("confidence", "Baja"),
            processing_time=round(processing_time, 2),
            message=recognition_result.get("message", "")
        )

        return result

    except HTTPException:
        # Re-lanzar HTTPException sin modificar
        if temp_image_path and os.path.exists(temp_image_path):
            os.remove(temp_image_path)
        raise
    except Exception as e:
        # Limpiar archivo temporal en caso de error
        if temp_image_path and os.path.exists(temp_image_path):
            os.remove(temp_image_path)
        raise HTTPException(status_code=500, detail=f"Error en el reconocimiento: {str(e)}")


@router.get("/recognition/stats")
def get_recognition_stats(db: Session = Depends(get_db)):
    """
    Obtener estadísticas de reconocimiento
    """
    try:
        stats = log_service.get_recognition_stats(db)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener estadísticas: {str(e)}")


@router.get("/recognition/logs")
def get_recognition_logs(
        skip: int = 0,
        limit: int = 50,
        db: Session = Depends(get_db)
):
    """
    Obtener logs de reconocimiento
    """
    try:
        logs = log_service.get_recognition_logs(db, skip=skip, limit=limit)
        return logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener logs: {str(e)}")


@router.post("/test-face-detection")
async def test_face_detection(image: UploadFile = File(...)):
    """
    Endpoint para probar detección facial sin comparación
    """
    temp_image_path = None

    try:
        # Validar formato
        if not image_processor.is_valid_image(image):
            raise HTTPException(status_code=400, detail="Formato de imagen no válido")

        # Guardar temporalmente
        temp_image_path = await image_processor.save_image(image, "test")

        # Solo detectar rostro
        face_encoding = await face_service.extract_face_encoding(temp_image_path)

        # Limpiar archivo temporal
        if temp_image_path and os.path.exists(temp_image_path):
            os.remove(temp_image_path)

        if face_encoding is not None:
            return {
                "face_detected": True,
                "encoding_length": len(face_encoding),
                "message": "Rostro detectado correctamente"
            }
        else:
            return {
                "face_detected": False,
                "message": "No se detectó ningún rostro en la imagen"
            }

    except Exception as e:
        if temp_image_path and os.path.exists(temp_image_path):
            os.remove(temp_image_path)
        raise HTTPException(status_code=500, detail=f"Error en la detección: {str(e)}")


@router.get("/health")
def health_check():
    """
    Endpoint para verificar que la API está funcionando
    """
    return {
        "status": "ok",
        "message": "API de reconocimiento facial funcionando correctamente",
        "version": "1.0.0"
    }