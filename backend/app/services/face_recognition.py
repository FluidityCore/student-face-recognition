import face_recognition
import numpy as np
from typing import Optional, List, Dict, Any, Union
import os
import logging
import requests
import tempfile
from PIL import Image
import io

from ..models.database import Student

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FaceRecognitionService:
    """Servicio de reconocimiento facial usando face_recognition library para Railway"""

    def __init__(self):
        """Inicializar servicio de reconocimiento facial"""
        try:
            # Umbral de reconocimiento (se puede configurar desde .env)
            self.recognition_threshold = float(os.getenv("RECOGNITION_THRESHOLD", "0.6"))

            # Configuración para face_recognition
            self.model = "large"  # 'large' para mayor precisión, 'small' para velocidad
            self.num_jitters = 1  # Número de re-muestreos para encoding (1 para velocidad)

            logger.info("✅ FaceRecognition Service inicializado correctamente")
            logger.info(f"📊 Umbral de reconocimiento: {self.recognition_threshold}")
            logger.info(f"🎯 Modelo: {self.model}")

        except Exception as e:
            logger.error(f"❌ Error al inicializar FaceRecognition Service: {e}")
            raise

    async def extract_face_encoding(self, image_source: Union[str, bytes, np.ndarray]) -> Optional[np.ndarray]:
        """
        Extraer encoding facial de una imagen

        Args:
            image_source: Puede ser:
                - str: ruta de archivo local o URL de Cloudflare R2
                - bytes: datos de imagen en bytes
                - np.ndarray: array de imagen ya cargado
        """
        temp_file_path = None

        try:
            # Determinar el tipo de fuente y preparar para procesamiento
            if isinstance(image_source, str):
                if image_source.startswith('http'):
                    # Es una URL de Cloudflare R2 - descargar primero
                    logger.info(f"📥 Descargando imagen desde R2: {image_source}")
                    image_array = await self._download_image_from_url(image_source)
                else:
                    # Es un archivo local
                    logger.info(f"📁 Cargando imagen local: {image_source}")
                    if not os.path.exists(image_source):
                        raise FileNotFoundError(f"Archivo no encontrado: {image_source}")
                    image_array = face_recognition.load_image_file(image_source)

            elif isinstance(image_source, bytes):
                # Son bytes de imagen - convertir a array numpy
                logger.info("🔄 Procesando imagen desde bytes")
                image_pil = Image.open(io.BytesIO(image_source))
                image_array = np.array(image_pil)

            elif isinstance(image_source, np.ndarray):
                # Ya es un array numpy
                logger.info("🔄 Procesando array numpy directo")
                image_array = image_source

            else:
                raise ValueError(f"Tipo de imagen no soportado: {type(image_source)}")

            # Verificar que tenemos una imagen válida
            if image_array is None or image_array.size == 0:
                logger.error("❌ Array de imagen vacío o inválido")
                return None

            logger.info(f"🖼️ Imagen cargada: {image_array.shape}")

            # Detectar ubicaciones de rostros
            logger.info("🔍 Detectando rostros...")
            face_locations = face_recognition.face_locations(image_array, model="hog")

            if not face_locations:
                logger.warning(f"❌ No se detectó rostro en la imagen")
                return None

            if len(face_locations) > 1:
                logger.warning(f"⚠️ Se detectaron {len(face_locations)} rostros, usando el primero")

            logger.info(f"✅ Se detectaron {len(face_locations)} rostro(s)")

            # Extraer encodings faciales
            logger.info("🤖 Extrayendo characteristics faciales...")
            face_encodings = face_recognition.face_encodings(
                image_array,
                face_locations,
                num_jitters=self.num_jitters,
                model=self.model
            )

            if not face_encodings:
                logger.warning(f"❌ No se pudo extraer encoding facial")
                return None

            encoding = face_encodings[0]
            logger.info(f"✅ Encoding extraído exitosamente: {len(encoding)} características")

            return encoding

        except Exception as e:
            logger.error(f"❌ Error al extraer encoding: {e}")
            return None

        finally:
            # Limpiar archivo temporal si se creó
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                    logger.info(f"🧹 Archivo temporal eliminado: {temp_file_path}")
                except:
                    pass

    async def _download_image_from_url(self, url: str) -> np.ndarray:
        """
        Descargar imagen desde URL de Cloudflare R2 y convertir a array numpy
        """
        try:
            logger.info(f"📥 Descargando imagen desde: {url}")

            response = requests.get(url, timeout=30)
            response.raise_for_status()

            if response.status_code != 200:
                raise Exception(f"Error al descargar imagen: HTTP {response.status_code}")

            # Convertir bytes a imagen PIL y luego a numpy array
            image_pil = Image.open(io.BytesIO(response.content))

            # Convertir a RGB si es necesario
            if image_pil.mode != 'RGB':
                image_pil = image_pil.convert('RGB')

            image_array = np.array(image_pil)

            logger.info(f"✅ Imagen descargada y convertida: {image_array.shape}")
            return image_array

        except Exception as e:
            logger.error(f"❌ Error al descargar imagen desde {url}: {e}")
            raise

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

            logger.info(f"🔍 Comparando contra {len(students)} estudiantes")
            logger.info(f"📏 Encoding de entrada: {len(face_encoding)} dimensiones")

            # Preparar encodings de estudiantes para comparación
            known_encodings = []
            known_students = []
            incompatible_count = 0

            for student in students:
                if student.face_encoding:
                    try:
                        # Convertir encoding de la BD a numpy array
                        student_encoding = np.array(student.face_encoding, dtype=np.float64)

                        # VERIFICAR COMPATIBILIDAD DE DIMENSIONES
                        if len(student_encoding) != len(face_encoding):
                            logger.warning(
                                f"⚠️ Encoding incompatible para {student.nombre} {student.apellidos}: "
                                f"{len(student_encoding)} vs {len(face_encoding)} dimensiones"
                            )
                            incompatible_count += 1
                            continue

                        known_encodings.append(student_encoding)
                        known_students.append(student)

                    except Exception as e:
                        logger.warning(f"Error al procesar encoding del estudiante {student.id}: {e}")
                        continue

            # Reportar estadísticas
            logger.info(f"✅ Encodings compatibles: {len(known_encodings)}")
            logger.info(f"⚠️ Encodings incompatibles: {incompatible_count}")

            if not known_encodings:
                return {
                    "found": False,
                    "message": f"No hay encodings compatibles para comparar. "
                               f"Encontrados {incompatible_count} encodings incompatibles. "
                               f"Posiblemente necesites regenerar los encodings de los estudiantes.",
                    "similarity": 0.0,
                    "confidence": "Baja",
                    "debug_info": {
                        "total_students": len(students),
                        "incompatible_encodings": incompatible_count,
                        "expected_dimensions": len(face_encoding)
                    }
                }

            # Calcular distancias faciales
            face_distances = face_recognition.face_distance(known_encodings, face_encoding)

            # Encontrar la mejor coincidencia
            best_match_index = np.argmin(face_distances)
            best_distance = face_distances[best_match_index]
            best_student = known_students[best_match_index]

            # Convertir distancia a similitud (0-1)
            similarity = max(0.0, 1.0 - best_distance)

            logger.info(f"📊 Mejor coincidencia: {best_student.nombre} {best_student.apellidos}")
            logger.info(f"📏 Distancia: {best_distance:.4f}")
            logger.info(f"📈 Similitud: {similarity:.4f}")
            logger.info(f"🎯 Umbral: {self.recognition_threshold}")

            # Usar comparación con umbral personalizado
            matches = face_recognition.compare_faces(
                known_encodings,
                face_encoding,
                tolerance=1.0 - self.recognition_threshold
            )

            # Determinar si hay coincidencia
            if matches[best_match_index] and similarity >= self.recognition_threshold:
                confidence = self._get_confidence_level(similarity)

                # Verificar que no hay múltiples coincidencias muy cercanas
                close_matches = [d for d in face_distances if d <= best_distance + 0.1]
                if len(close_matches) > 1:
                    logger.warning(f"⚠️ Múltiples coincidencias cercanas detectadas: {len(close_matches)}")
                    if similarity < 0.8:
                        return {
                            "found": False,
                            "message": "Múltiples candidatos similares detectados",
                            "similarity": similarity,
                            "confidence": "Baja",
                            "debug_info": {
                                "close_matches_count": len(close_matches),
                                "best_similarity": similarity
                            }
                        }

                return {
                    "found": True,
                    "student": {
                        "id": best_student.id,
                        "nombre": best_student.nombre,
                        "apellidos": best_student.apellidos,
                        "codigo": best_student.codigo,
                        "correo": best_student.correo,
                        "requisitoriado": best_student.requisitoriado,
                        "imagen_path": best_student.imagen_path,
                        "created_at": best_student.created_at,
                        "updated_at": best_student.updated_at,
                        "active": best_student.active
                    },
                    "similarity": similarity,
                    "confidence": confidence,
                    "message": f"Estudiante identificado con {confidence.lower()} confianza",
                    "debug_info": {
                        "compatible_encodings": len(known_encodings),
                        "incompatible_encodings": incompatible_count,
                        "encoding_dimensions": len(face_encoding)
                    }
                }
            else:
                return {
                    "found": False,
                    "message": "No se encontró coincidencia suficiente",
                    "best_similarity": similarity,
                    "similarity": similarity,
                    "confidence": self._get_confidence_level(similarity),
                    "debug_info": {
                        "compatible_encodings": len(known_encodings),
                        "incompatible_encodings": incompatible_count,
                        "threshold": self.recognition_threshold,
                        "best_distance": best_distance
                    }
                }

        except Exception as e:
            logger.error(f"❌ Error en reconocimiento facial: {e}")
            import traceback
            logger.error(f"📍 Traceback: {traceback.format_exc()}")

            return {
                "found": False,
                "message": f"Error en el procesamiento: {str(e)}",
                "similarity": 0.0,
                "confidence": "Baja",
                "debug_info": {
                    "error": str(e),
                    "input_encoding_dimensions": len(face_encoding) if face_encoding is not None else None
                }
            }

    def _get_confidence_level(self, similarity: float) -> str:
        """
        Determinar nivel de confianza basado en similitud
        """
        if similarity >= 0.85:
            return "Alta"
        elif similarity >= 0.70:
            return "Media"
        else:
            return "Baja"

    async def debug_encoding_comparison(self, image_path1: str, image_path2: str) -> Dict[str, Any]:
        """
        Método de debugging mejorado para comparar dos imágenes paso a paso
        """
        try:
            logger.info(f"🔍 Comparando {image_path1} vs {image_path2}")

            # Extraer encodings
            encoding1 = await self.extract_face_encoding(image_path1)
            encoding2 = await self.extract_face_encoding(image_path2)

            if encoding1 is None or encoding2 is None:
                return {"error": "No se pudo extraer encoding de una o ambas imágenes"}

            # Información detallada de debugging
            import numpy as np

            # Calcular estadísticas de los encodings (CONVERTIR TODO A PYTHON NATIVO)
            encoding1_stats = {
                "length": int(len(encoding1)),
                "mean": float(np.mean(encoding1)),
                "std": float(np.std(encoding1)),
                "min": float(np.min(encoding1)),
                "max": float(np.max(encoding1)),
                "variance": float(np.var(encoding1))
            }

            encoding2_stats = {
                "length": int(len(encoding2)),
                "mean": float(np.mean(encoding2)),
                "std": float(np.std(encoding2)),
                "min": float(np.min(encoding2)),
                "max": float(np.max(encoding2)),
                "variance": float(np.var(encoding2))
            }

            # Calcular distancia y similitud usando face_recognition
            distance = face_recognition.face_distance([encoding1], encoding2)[0]
            similarity = max(0.0, 1.0 - distance)

            # Comparar con umbral
            matches = face_recognition.compare_faces([encoding1], encoding2, tolerance=1.0 - self.recognition_threshold)

            # Información de la librería utilizada
            library_info = {
                "face_recognition_version": getattr(face_recognition, '__version__', 'unknown'),
                "model_used": self.model,
                "num_jitters": self.num_jitters,
                "recognition_threshold": float(self.recognition_threshold)
            }

            logger.info(f"📏 Distancia facial: {distance:.4f}")
            logger.info(f"📈 Similitud: {similarity:.4f}")
            logger.info(f"✅ Coincidencia: {matches[0]}")
            logger.info(f"📊 Encoding 1 length: {len(encoding1)}")
            logger.info(f"📊 Encoding 2 length: {len(encoding2)}")

            # CONVERTIR TODOS LOS VALORES A TIPOS PYTHON NATIVOS
            return {
                "similarity": float(similarity),
                "distance": float(distance),
                "encoding1_length": int(len(encoding1)),
                "encoding2_length": int(len(encoding2)),
                "encoding1_stats": encoding1_stats,
                "encoding2_stats": encoding2_stats,
                "threshold": float(self.recognition_threshold),
                "would_match": bool(matches[0]),  # CONVERTIR numpy.bool_ a bool nativo
                "confidence": self._get_confidence_level(similarity),
                "library_info": library_info,
                "debug_info": {
                    "encodings_are_128d": bool(len(encoding1) == 128 and len(encoding2) == 128),
                    "expected_face_recognition": True,
                    "actual_library": "face_recognition" if len(encoding1) == 128 else "possibly_mediapipe_or_other",
                    "encoding1_dimensions": int(len(encoding1)),
                    "encoding2_dimensions": int(len(encoding2))
                }
            }

        except Exception as e:
            logger.error(f"Error en debug: {e}")
            import traceback
            return {
                "error": str(e),
                "traceback": traceback.format_exc(),
                "debug_info": {
                    "error_occurred": True,
                    "function": "debug_encoding_comparison"
                }
            }

    def verify_face_quality(self, image_source: Union[str, bytes, np.ndarray]) -> Dict[str, Any]:
        """
        Verificar calidad de la imagen para reconocimiento facial
        """
        try:
            # Cargar imagen según el tipo de fuente
            if isinstance(image_source, str):
                if image_source.startswith('http'):
                    # Es URL - usar método async (simplificado para sync)
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    image = loop.run_until_complete(self._download_image_from_url(image_source))
                else:
                    image = face_recognition.load_image_file(image_source)
            elif isinstance(image_source, bytes):
                image_pil = Image.open(io.BytesIO(image_source))
                image = np.array(image_pil)
            else:
                image = image_source

            face_locations = face_recognition.face_locations(image)

            if not face_locations:
                return {"valid": False, "reason": "No se detectó rostro"}

            if len(face_locations) > 1:
                return {
                    "valid": True,
                    "reason": f"Se detectaron {len(face_locations)} rostros, se usará el primero",
                    "face_count": len(face_locations)
                }

            # Verificar tamaño de la imagen
            height, width = image.shape[:2]
            if width < 200 or height < 200:
                return {"valid": False, "reason": "Imagen muy pequeña"}

            return {
                "valid": True,
                "face_count": len(face_locations),
                "resolution": f"{width}x{height}",
                "face_locations": face_locations
            }

        except Exception as e:
            return {"valid": False, "reason": f"Error al verificar calidad: {str(e)}"}

    def cleanup_resources(self):
        """
        Limpiar recursos (face_recognition no requiere limpieza específica)
        """
        logger.info("✅ Recursos de face_recognition liberados")

    def __del__(self):
        """Destructor para limpiar recursos automáticamente"""
        self.cleanup_resources()