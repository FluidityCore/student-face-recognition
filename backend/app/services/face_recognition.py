import cv2
import numpy as np
import mediapipe as mp
from typing import Optional, List, Dict, Any, Tuple
import os
from sklearn.metrics.pairwise import cosine_similarity
import logging

from ..models.database import Student

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FaceRecognitionService:
    """Servicio de reconocimiento facial usando MediaPipe"""

    def __init__(self):
        """Inicializar MediaPipe Face Detection y Face Mesh"""
        try:
            self.mp_face_detection = mp.solutions.face_detection
            self.mp_face_mesh = mp.solutions.face_mesh
            self.mp_drawing = mp.solutions.drawing_utils

            # Configurar detectores
            self.face_detection = self.mp_face_detection.FaceDetection(
                model_selection=1,  # 0 para imágenes cercanas, 1 para imágenes lejanas
                min_detection_confidence=0.7
            )

            self.face_mesh = self.mp_face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.7,
                min_tracking_confidence=0.5
            )

            # Umbral de reconocimiento (se puede configurar desde .env)
            self.recognition_threshold = float(os.getenv("RECOGNITION_THRESHOLD", "0.8"))

            logger.info("✅ MediaPipe Face Recognition Service inicializado correctamente")

        except Exception as e:
            logger.error(f"❌ Error al inicializar MediaPipe: {e}")
            raise

    async def extract_face_encoding(self, image_path: str) -> Optional[np.ndarray]:
        """
        Extraer características faciales de una imagen
        """
        try:
            # Leer imagen
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"No se pudo cargar la imagen: {image_path}")
                return None

            # Convertir de BGR a RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            # Detectar rostro primero
            detection_results = self.face_detection.process(rgb_image)

            if not detection_results.detections:
                logger.warning(f"No se detectó rostro en: {image_path}")
                return None

            # Obtener landmarks faciales
            mesh_results = self.face_mesh.process(rgb_image)

            if not mesh_results.multi_face_landmarks:
                logger.warning(f"No se detectaron landmarks en: {image_path}")
                return None

            # Extraer características del primer rostro detectado
            face_landmarks = mesh_results.multi_face_landmarks[0]

            # Convertir landmarks a vector de características
            encoding = self._landmarks_to_encoding(face_landmarks, rgb_image.shape)

            logger.info(f"✅ Características extraídas exitosamente de: {image_path}")
            return encoding

        except Exception as e:
            logger.error(f"❌ Error al extraer características de {image_path}: {e}")
            return None

    def _landmarks_to_encoding(self, landmarks, image_shape: Tuple[int, int, int]) -> np.ndarray:
        """
        Convertir landmarks de MediaPipe a vector de características
        """
        try:
            height, width = image_shape[:2]

            # Extraer coordenadas normalizadas de landmarks importantes
            # MediaPipe FaceMesh tiene 468 puntos, seleccionamos los más relevantes
            important_landmarks = [
                # Contorno facial
                10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288,
                # Ojos
                33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246,
                # Nariz
                19, 20, 94, 125, 141, 235, 236, 3, 51, 48, 115, 131, 134, 102, 49, 220,
                # Boca
                61, 84, 17, 314, 405, 320, 307, 375, 321, 308, 324, 318,
                # Cejas
                70, 63, 105, 66, 107, 55, 65, 52, 53, 46
            ]

            # Extraer coordenadas de landmarks importantes
            encoding_points = []
            for idx in important_landmarks:
                if idx < len(landmarks.landmark):
                    landmark = landmarks.landmark[idx]
                    # Normalizar coordenadas
                    x = landmark.x * width
                    y = landmark.y * height
                    z = landmark.z if hasattr(landmark, 'z') else 0
                    encoding_points.extend([x, y, z])

            # Convertir a numpy array
            encoding = np.array(encoding_points, dtype=np.float32)

            # Normalizar el vector
            if np.linalg.norm(encoding) > 0:
                encoding = encoding / np.linalg.norm(encoding)

            return encoding

        except Exception as e:
            logger.error(f"❌ Error al convertir landmarks a encoding: {e}")
            return np.array([])

    async def recognize_face(self, face_encoding: np.ndarray, students: List[Student]) -> Dict[str, Any]:
        """
        Reconocer rostro comparando con estudiantes registrados
        """
        try:
            if len(students) == 0:
                return {
                    "found": False,
                    "message": "No hay estudiantes registrados",
                    "similarity": 0.0,
                    "confidence": "Baja"
                }

            best_match = None
            best_similarity = 0.0
            similarities = []

            # Comparar con cada estudiante
            for student in students:
                if not student.face_encoding:
                    continue

                try:
                    # Convertir encoding de la BD a numpy array
                    student_encoding = np.array(student.face_encoding, dtype=np.float32)

                    # Calcular similitud coseno
                    similarity = self._calculate_similarity(face_encoding, student_encoding)
                    similarities.append(similarity)

                    # Verificar si es la mejor coincidencia
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = student

                except Exception as e:
                    logger.warning(f"Error al comparar con estudiante {student.id}: {e}")
                    continue

            # Determinar si hay coincidencia
            if best_similarity >= self.recognition_threshold:
                confidence = self._get_confidence_level(best_similarity)

                return {
                    "found": True,
                    "student": {
                        "id": best_match.id,
                        "nombre": best_match.nombre,
                        "apellidos": best_match.apellidos,
                        "codigo": best_match.codigo,
                        "correo": best_match.correo,
                        "requisitoriado": best_match.requisitoriado,
                        "imagen_path": best_match.imagen_path,
                        "created_at": best_match.created_at,
                        "updated_at": best_match.updated_at,
                        "active": best_match.active
                    },
                    "similarity": best_similarity,
                    "confidence": confidence,
                    "message": f"Estudiante identificado con {confidence.lower()} confianza"
                }
            else:
                return {
                    "found": False,
                    "message": "No se encontró coincidencia suficiente",
                    "best_similarity": best_similarity,
                    "similarity": best_similarity,
                    "confidence": "Baja"
                }

        except Exception as e:
            logger.error(f"❌ Error en reconocimiento facial: {e}")
            return {
                "found": False,
                "message": f"Error en el procesamiento: {str(e)}",
                "similarity": 0.0,
                "confidence": "Baja"
            }

    def _calculate_similarity(self, encoding1: np.ndarray, encoding2: np.ndarray) -> float:
        """
        Calcular similitud entre dos encodings faciales
        """
        try:
            # Verificar que ambos arrays tengan datos
            if len(encoding1) == 0 or len(encoding2) == 0:
                return 0.0

            # Asegurar que tengan la misma dimensión
            if len(encoding1) != len(encoding2):
                logger.warning(f"Dimensiones diferentes: {len(encoding1)} vs {len(encoding2)}")
                return 0.0

            # Reshapear para sklearn
            enc1 = encoding1.reshape(1, -1)
            enc2 = encoding2.reshape(1, -1)

            # Calcular similitud coseno
            similarity = cosine_similarity(enc1, enc2)[0][0]

            # Convertir de rango [-1, 1] a [0, 1]
            similarity = (similarity + 1) / 2

            return float(similarity)

        except Exception as e:
            logger.error(f"❌ Error al calcular similitud: {e}")
            return 0.0

    def _get_confidence_level(self, similarity: float) -> str:
        """
        Determinar nivel de confianza basado en similitud
        """
        if similarity >= 0.95:
            return "Alta"
        elif similarity >= 0.85:
            return "Media"
        else:
            return "Baja"

    def verify_face_quality(self, image_path: str) -> Dict[str, Any]:
        """
        Verificar calidad de la imagen para reconocimiento facial
        """
        try:
            image = cv2.imread(image_path)
            if image is None:
                return {"valid": False, "reason": "No se pudo cargar la imagen"}

            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = self.face_detection.process(rgb_image)

            if not results.detections:
                return {"valid": False, "reason": "No se detectó rostro"}

            detection = results.detections[0]
            confidence = detection.score[0]

            # Verificar tamaño de la imagen
            height, width = image.shape[:2]
            if width < 200 or height < 200:
                return {"valid": False, "reason": "Imagen muy pequeña"}

            # Verificar confianza de detección
            if confidence < 0.8:
                return {"valid": False, "reason": "Calidad de rostro insuficiente"}

            return {
                "valid": True,
                "confidence": float(confidence),
                "resolution": f"{width}x{height}",
                "face_area": self._calculate_face_area(detection, width, height)
            }

        except Exception as e:
            return {"valid": False, "reason": f"Error al verificar calidad: {str(e)}"}

    def _calculate_face_area(self, detection, image_width: int, image_height: int) -> float:
        """
        Calcular área relativa del rostro en la imagen
        """
        try:
            bbox = detection.location_data.relative_bounding_box
            face_width = bbox.width * image_width
            face_height = bbox.height * image_height
            face_area = face_width * face_height
            total_area = image_width * image_height

            return face_area / total_area

        except Exception:
            return 0.0

    def cleanup_resources(self):
        """
        Limpiar recursos de MediaPipe
        """
        try:
            if hasattr(self, 'face_detection'):
                self.face_detection.close()
            if hasattr(self, 'face_mesh'):
                self.face_mesh.close()

            logger.info("✅ Recursos de MediaPipe liberados")

        except Exception as e:
            logger.error(f"❌ Error al liberar recursos: {e}")

    def __del__(self):
        """Destructor para limpiar recursos automáticamente"""
        self.cleanup_resources()