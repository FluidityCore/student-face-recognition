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


@router.post("/debug-similarity")
async def debug_similarity(
        image1: UploadFile = File(...),
        image2: UploadFile = File(...),
):
    """
    Endpoint mejorado para debuggear similitud entre dos imágenes
    """
    temp_path1 = None
    temp_path2 = None

    try:
        # Validar ambas imágenes
        if not image_processor.is_valid_image(image1):
            raise HTTPException(status_code=400, detail="Imagen 1 no válida")

        if not image_processor.is_valid_image(image2):
            raise HTTPException(status_code=400, detail="Imagen 2 no válida")

        # Guardar ambas imágenes temporalmente
        temp_path1 = await image_processor.save_image(image1, "test")
        temp_path2 = await image_processor.save_image(image2, "test")

        # Información adicional sobre las imágenes
        image1_info = image_processor.get_image_info(temp_path1)
        image2_info = image_processor.get_image_info(temp_path2)

        # Debuggear comparación
        debug_result = await face_service.debug_encoding_comparison(temp_path1, temp_path2)

        # Limpiar cualquier valor numpy que pueda quedar
        def clean_numpy_values(obj):
            """Convertir valores numpy a tipos Python nativos recursivamente"""
            if isinstance(obj, dict):
                return {k: clean_numpy_values(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_numpy_values(item) for item in obj]
            elif hasattr(obj, 'item'):  # numpy scalar
                return obj.item()
            elif hasattr(obj, 'tolist'):  # numpy array
                return obj.tolist()
            else:
                return obj

        # Limpiar todos los valores
        debug_result = clean_numpy_values(debug_result)
        image1_info = clean_numpy_values(image1_info)
        image2_info = clean_numpy_values(image2_info)

        # Agregar información adicional
        final_result = {
            **debug_result,
            "image1_info": image1_info,
            "image2_info": image2_info,
            "images": {
                "image1_name": str(image1.filename),
                "image2_name": str(image2.filename),
                "temp_path1": str(temp_path1),
                "temp_path2": str(temp_path2)
            }
        }

        return final_result

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc(),
            "debug_info": {
                "endpoint": "debug_similarity",
                "temp_paths": {
                    "path1": str(temp_path1) if temp_path1 else None,
                    "path2": str(temp_path2) if temp_path2 else None
                }
            }
        }
    finally:
        # Limpiar archivos temporales
        for path in [temp_path1, temp_path2]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass  # Ignorar errores de limpieza
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


@router.get("/debug-system")
async def debug_system():
    """
    Endpoint para verificar el estado del sistema de reconocimiento
    """
    try:
        import face_recognition
        import sys
        import numpy as np

        # Información del sistema (todo convertido a tipos nativos)
        system_info = {
            "python_version": str(sys.version),
            "face_recognition_available": True,
            "face_recognition_version": str(getattr(face_recognition, '__version__', 'unknown')),
            "numpy_version": str(np.__version__),
        }

        # Verificar si mediapipe está presente
        try:
            import mediapipe
            system_info["mediapipe_present"] = True
            system_info["mediapipe_version"] = str(mediapipe.__version__)
            system_info["warning"] = "MediaPipe detectado - podría causar conflictos"
        except ImportError:
            system_info["mediapipe_present"] = False

        # Verificar dlib
        try:
            import dlib
            system_info["dlib_available"] = True
            system_info["dlib_version"] = str(dlib.version)
        except ImportError:
            system_info["dlib_available"] = False
            system_info["dlib_error"] = "dlib no disponible"

        # Probar encoding simple
        try:
            # Crear imagen de prueba
            test_image = np.zeros((200, 200, 3), dtype=np.uint8)

            # Intentar detectar (debería fallar, pero nos dice si la librería funciona)
            face_locations = face_recognition.face_locations(test_image)

            system_info["face_recognition_test"] = {
                "test_passed": True,
                "faces_detected": int(len(face_locations)),
                "note": "Test con imagen sintética (sin rostro real)"
            }

        except Exception as e:
            system_info["face_recognition_test"] = {
                "test_passed": False,
                "error": str(e)
            }

        # Información del servicio
        service_info = {
            "recognition_threshold": float(face_service.recognition_threshold),
            "model": str(face_service.model),
            "num_jitters": int(face_service.num_jitters)
        }

        return {
            "status": "ok",
            "system_info": system_info,
            "service_info": service_info,
            "recommendations": {
                "if_encodings_44d": "Desinstalar mediapipe: pip uninstall mediapipe",
                "if_encodings_128d": "Sistema funcionando correctamente",
                "if_dlib_missing": "Instalar dlib: pip install dlib"
            }
        }

    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }