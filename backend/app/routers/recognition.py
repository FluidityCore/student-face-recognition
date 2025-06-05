# app/routers/recognition.py
from fastapi import APIRouter, HTTPException, UploadFile, File
import cv2
import numpy as np
import logging
from app.core.image_processor import ImageProcessor
from app.core.face_matcher import FaceMatcher
from app.core.student_loader import get_students_data, get_known_encodings, get_students_count

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/recognize")
async def recognize_student(image: UploadFile = File(...)):
    """Reconocer estudiante desde imagen enviada por app móvil"""
    try:
        # Validaciones
        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Debe ser una imagen")

        if get_students_count() == 0:
            raise HTTPException(status_code=500, detail="No hay estudiantes cargados en el sistema")

        # Leer imagen
        image_content = await image.read()

        # Convertir bytes a array de numpy
        nparr = np.frombuffer(image_content, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            raise HTTPException(status_code=400, detail="No se pudo procesar la imagen")

        # Preprocesar imagen
        processed_img = ImageProcessor.preprocess_image(img)
        if processed_img is None:
            raise HTTPException(status_code=400, detail="Error preprocesando imagen")

        # Extraer características
        known_encodings = get_known_encodings()
        test_encoding = ImageProcessor.extract_features_single(processed_img, known_encodings)
        if test_encoding is None:
            raise HTTPException(status_code=400, detail="Error extrayendo características")

        # Buscar coincidencia
        students_data = get_students_data()
        best_match, similarity = FaceMatcher.find_best_match(test_encoding, known_encodings, students_data)

        if best_match:
            result = {
                "found": True,
                "student": {
                    "id": best_match['id'],
                    "nombre": best_match['nombre'],
                    "apellidos": best_match['apellidos'],
                    "correo": best_match['correo'],
                    "requisitoriado": best_match['requisitoriado']
                },
                "similarity": round(float(similarity), 4),
                "confidence": "Alta" if similarity > 0.8 else "Media" if similarity > 0.7 else "Baja"
            }
        else:
            result = {
                "found": False,
                "message": "No se encontró coincidencia",
                "best_similarity": round(float(similarity), 4),
                "threshold": 0.7
            }

        logger.info(f"Reconocimiento: {'Encontrado' if best_match else 'No encontrado'} - Similitud: {similarity:.4f}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en reconocimiento: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")
