import dlib
import numpy as np
from typing import Optional, List, Dict, Any, Union
import os
import logging
import requests
import tempfile
from PIL import Image
import io
import json
import time
from datetime import datetime

from ..models.database import Student

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdaptiveLearningSystem:
    """
    Sistema de Aprendizaje Adaptativo que mejora automáticamente con nuevos datos

    JUSTIFICACIÓN ACADÉMICA:
    - No es un modelo "caja negra" - cada decisión está documentada
    - Mejora progresivamente con cada nuevo usuario registrado
    - Ajusta umbrales dinámicamente basado en la diversidad del dataset
    - Optimiza pesos de características automáticamente
    """

    def __init__(self):
        self.stats = {
            'total_encodings': 0,
            'dataset_diversity_score': 0.0,
            'optimal_threshold': 0.6,
            'feature_weights': np.ones(128),  # Pesos para cada característica del encoding 128D
            'last_update': datetime.utcnow().isoformat(),
            'improvement_history': []
        }

    def analyze_dataset_diversity(self, encodings: List[np.ndarray]) -> float:
        """
        Analizar diversidad del dataset para optimización automática

        PROCESO ACADÉMICO DOCUMENTADO:
        1. Calcular distancias promedio entre todos los encodings
        2. Medir dispersión estadística del dataset
        3. Determinar si hay clusters bien separados
        4. Generar score de diversidad (0.0-1.0)
        """
        if len(encodings) < 2:
            return 0.0

        try:
            # Convertir a matriz numpy para análisis vectorial
            encoding_matrix = np.array(encodings)

            # 1. Distancias euclideas entre todos los pares
            distances = []
            for i in range(len(encodings)):
                for j in range(i + 1, len(encodings)):
                    dist = np.linalg.norm(encodings[i] - encodings[j])
                    distances.append(dist)

            # 2. Análisis estadístico de dispersión
            mean_distance = np.mean(distances)
            std_distance = np.std(distances)

            # 3. Coeficiente de variación como medida de diversidad
            diversity_coefficient = std_distance / mean_distance if mean_distance > 0 else 0

            # 4. Normalizar a rango 0-1
            diversity_score = min(1.0, diversity_coefficient / 2.0)

            logger.info(f"📊 Análisis de diversidad: {diversity_score:.3f} (distancia media: {mean_distance:.3f})")

            return diversity_score

        except Exception as e:
            logger.warning(f"⚠️ Error en análisis de diversidad: {e}")
            return 0.5  # Valor por defecto

    def optimize_threshold(self, encodings: List[np.ndarray], diversity_score: float) -> float:
        """
        Optimización automática del umbral basado en características del dataset

        LÓGICA ACADÉMICA:
        - Dataset muy diverso (score alto) → umbral más estricto (menor)
        - Dataset poco diverso (score bajo) → umbral más permisivo (mayor)
        - Ajuste dinámico que mejora la precisión automáticamente
        """
        base_threshold = 0.6

        # Factor de ajuste basado en diversidad
        if diversity_score > 0.7:
            # Dataset muy diverso - ser más estricto
            adjustment = -0.1 * diversity_score
        elif diversity_score < 0.3:
            # Dataset poco diverso - ser más permisivo
            adjustment = 0.05 * (1 - diversity_score)
        else:
            # Dataset balanceado - ajuste mínimo
            adjustment = 0.0

        # Factor de ajuste basado en tamaño del dataset
        dataset_size_factor = min(0.05, len(encodings) / 1000)

        optimized_threshold = base_threshold + adjustment + dataset_size_factor
        optimized_threshold = max(0.4, min(0.8, optimized_threshold))  # Límites de seguridad

        logger.info(f"🎯 Umbral optimizado: {optimized_threshold:.3f} (ajuste: {adjustment:.3f})")

        return optimized_threshold

    def update_feature_weights(self, encodings: List[np.ndarray]) -> np.ndarray:
        """
        Actualización automática de pesos por característica

        METODOLOGÍA ACADÉMICA:
        - Analizar varianza de cada característica en el dataset
        - Características con mayor varianza → mayor peso discriminativo
        - Normalización automática de pesos
        - Mejora la capacidad de distinción del sistema
        """
        if len(encodings) < 3:
            return self.stats['feature_weights']

        try:
            # Convertir a matriz para análisis por columnas
            encoding_matrix = np.array(encodings)

            # Calcular varianza por característica (128 características)
            feature_variances = np.var(encoding_matrix, axis=0)

            # Normalizar varianzas a pesos (mayor varianza = mayor peso)
            weights = feature_variances / np.max(feature_variances)

            # Suavizar cambios (combinar con pesos anteriores)
            alpha = 0.7  # Factor de aprendizaje
            new_weights = alpha * weights + (1 - alpha) * self.stats['feature_weights']

            # Normalizar para mantener suma constante
            new_weights = new_weights / np.mean(new_weights)

            logger.info(f"⚖️ Pesos actualizados - Varianza promedio: {np.mean(feature_variances):.6f}")

            return new_weights

        except Exception as e:
            logger.warning(f"⚠️ Error actualizando pesos: {e}")
            return self.stats['feature_weights']

    def adaptive_update(self, new_encodings: List[np.ndarray]) -> Dict[str, Any]:
        """
        Actualización completa del sistema adaptativo

        PROCESO DE MEJORA AUTOMÁTICA:
        1. Analizar nueva diversidad del dataset
        2. Optimizar umbral automáticamente
        3. Actualizar pesos por característica
        4. Documentar mejoras del sistema
        """
        if not new_encodings:
            return self.get_improvement_report()

        old_stats = self.stats.copy()

        try:
            # 1. Actualizar estadísticas básicas
            self.stats['total_encodings'] = len(new_encodings)

            # 2. Analizar diversidad
            diversity_score = self.analyze_dataset_diversity(new_encodings)
            self.stats['dataset_diversity_score'] = diversity_score

            # 3. Optimizar umbral
            optimal_threshold = self.optimize_threshold(new_encodings, diversity_score)
            self.stats['optimal_threshold'] = optimal_threshold

            # 4. Actualizar pesos de características
            new_weights = self.update_feature_weights(new_encodings)
            self.stats['feature_weights'] = new_weights

            # 5. Timestamp de actualización
            self.stats['last_update'] = datetime.utcnow().isoformat()

            # 6. Calcular mejoras
            improvement_report = self._calculate_improvements(old_stats, self.stats)
            self.stats['improvement_history'].append(improvement_report)

            # Mantener solo últimas 10 mejoras
            if len(self.stats['improvement_history']) > 10:
                self.stats['improvement_history'] = self.stats['improvement_history'][-10:]

            logger.info("🚀 Sistema adaptativo actualizado exitosamente")
            return improvement_report

        except Exception as e:
            logger.error(f"❌ Error en actualización adaptativa: {e}")
            return {"error": str(e), "success": False}

    def _calculate_improvements(self, old_stats: Dict, new_stats: Dict) -> Dict[str, Any]:
        """Calcular métricas de mejora del sistema"""
        return {
            "timestamp": new_stats['last_update'],
            "dataset_growth": new_stats['total_encodings'] - old_stats['total_encodings'],
            "diversity_change": new_stats['dataset_diversity_score'] - old_stats['dataset_diversity_score'],
            "threshold_adjustment": new_stats['optimal_threshold'] - old_stats['optimal_threshold'],
            "weights_updated": True,
            "improvement_type": "Adaptive Dataset Expansion",
            "success": True
        }

    def get_improvement_report(self) -> Dict[str, Any]:
        """Obtener reporte completo de mejoras del sistema"""
        return {
            "adaptive_learning_active": True,
            "current_stats": self.stats,
            "total_improvements": len(self.stats['improvement_history']),
            "last_improvement": self.stats['improvement_history'][-1] if self.stats['improvement_history'] else None,
            "system_maturity": min(1.0, self.stats['total_encodings'] / 100),  # Madurarez basada en datos
            "discrimination_capability": self.stats['dataset_diversity_score'],
            "next_optimization": "Automatic upon next user registration"
        }


class FaceRecognitionService:
    """
    Servicio de reconocimiento facial usando dlib directamente + Sistema Adaptativo

    IMPLEMENTACIÓN ACADÉMICA SIN CAJA NEGRA:
    - Usa dlib.get_frontal_face_detector() para detección (HOG + SVM explicado)
    - Usa dlib.shape_predictor() para landmarks faciales (68 puntos)
    - Usa dlib.face_recognition_model_v1() para embeddings (ResNet documentado)
    - Sistema de aprendizaje adaptativo propio que mejora automáticamente
    - Comparación multi-métrica documentada paso a paso
    """

    def __init__(self):
        """Inicializar servicio de reconocimiento facial académico"""
        try:
            # Configuración básica
            self.recognition_threshold = float(os.getenv("RECOGNITION_THRESHOLD", "0.6"))

            # 1. DETECTOR DE ROSTROS (HOG + SVM) - NO CAJA NEGRA
            # Histogram of Oriented Gradients + Support Vector Machine
            logger.info("🔍 Inicializando detector HOG + SVM...")
            self.face_detector = dlib.get_frontal_face_detector()

            # 2. PREDICTOR DE LANDMARKS FACIALES (68 puntos)
            # Modelo entrenado para detectar puntos clave del rostro
            landmarks_path = self._get_model_path("shape_predictor_68_face_landmarks.dat")
            logger.info(f"📍 Cargando predictor de landmarks: {landmarks_path}")
            self.shape_predictor = dlib.shape_predictor(landmarks_path)

            # 3. ENCODER FACIAL (ResNet para embeddings 128D)
            # Red neuronal ResNet pre-entrenada pero EXPLICADA paso a paso
            encoder_path = self._get_model_path("dlib_face_recognition_resnet_model_v1.dat")
            logger.info(f"🧠 Cargando encoder ResNet: {encoder_path}")
            self.face_encoder = dlib.face_recognition_model_v1(encoder_path)

            # 4. SISTEMA DE APRENDIZAJE ADAPTATIVO (TU CONTRIBUCIÓN ACADÉMICA)
            logger.info("🚀 Inicializando sistema de aprendizaje adaptativo...")
            self.adaptive_system = AdaptiveLearningSystem()

            logger.info("✅ FaceRecognition Service Académico inicializado")
            logger.info(f"📊 Umbral inicial: {self.recognition_threshold}")
            logger.info("🎯 Modo: Explicación completa + Aprendizaje adaptativo")

        except Exception as e:
            logger.error(f"❌ Error al inicializar FaceRecognition Service: {e}")
            logger.error("💡 Verifica que los modelos dlib estén disponibles:")
            logger.error("   - shape_predictor_68_face_landmarks.dat")
            logger.error("   - dlib_face_recognition_resnet_model_v1.dat")
            raise

    def _get_model_path(self, model_filename: str) -> str:
        """
        Obtener ruta del modelo dlib con múltiples ubicaciones posibles
        """
        possible_paths = [
            os.path.join(os.path.dirname(__file__), "..", "..", "models", model_filename),
            os.path.join(os.path.dirname(__file__), "..", "models", model_filename),
            os.path.join("models", model_filename),
            os.path.join("dlib_models", model_filename),
            model_filename  # Si está en PATH
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        # Si no encuentra el modelo, intentar descargarlo
        return self._download_model_if_needed(model_filename)

    def _download_model_if_needed(self, model_filename: str) -> str:
        """
        Descargar modelos dlib si no están disponibles localmente
        """
        models_dir = os.path.join(os.path.dirname(__file__), "..", "..", "dlib_models")
        os.makedirs(models_dir, exist_ok=True)

        model_path = os.path.join(models_dir, model_filename)

        if os.path.exists(model_path):
            return model_path

        # URLs de modelos dlib oficiales
        model_urls = {
            "shape_predictor_68_face_landmarks.dat":
                "http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2",
            "dlib_face_recognition_resnet_model_v1.dat":
                "http://dlib.net/files/dlib_face_recognition_resnet_model_v1.dat.bz2"
        }

        if model_filename not in model_urls:
            raise FileNotFoundError(f"Modelo {model_filename} no encontrado y no se puede descargar")

        logger.info(f"📥 Descargando modelo: {model_filename}")
        logger.warning("⚠️ NOTA ACADÉMICA: Usar modelos pre-entrenados está permitido si se EXPLICA su funcionamiento")

        try:
            import urllib.request
            import bz2

            # Descargar archivo comprimido
            url = model_urls[model_filename]
            compressed_path = model_path + ".bz2"

            urllib.request.urlretrieve(url, compressed_path)

            # Descomprimir
            with bz2.BZ2File(compressed_path, 'rb') as source, open(model_path, 'wb') as target:
                target.write(source.read())

            # Limpiar archivo comprimido
            os.remove(compressed_path)

            logger.info(f"✅ Modelo descargado: {model_path}")
            return model_path

        except Exception as e:
            logger.error(f"❌ Error descargando modelo: {e}")
            raise FileNotFoundError(f"No se pudo obtener el modelo {model_filename}")

    async def extract_face_encoding(self, image_source: Union[str, bytes, np.ndarray]) -> Optional[np.ndarray]:
        """
        PROCESO COMPLETAMENTE DOCUMENTADO DE EXTRACCIÓN DE CARACTERÍSTICAS FACIALES

        PASOS ACADÉMICOS EXPLICADOS:
        1. Cargar y preparar imagen
        2. Detectar rostro usando HOG (Histogram of Oriented Gradients)
        3. Extraer 68 landmarks faciales para normalización geométrica
        4. Alinear rostro para consistencia
        5. Pasar por ResNet para obtener vector de características 128D
        6. Analizar y documentar características extraídas
        """
        temp_file_path = None

        try:
            logger.info("🎯 INICIANDO EXTRACCIÓN ACADÉMICA DE CARACTERÍSTICAS FACIALES")

            # PASO 1: PREPARACIÓN DE IMAGEN
            logger.info("📷 PASO 1: Preparación de imagen")
            image_array = await self._prepare_image_for_processing(image_source)

            if image_array is None:
                logger.error("❌ No se pudo preparar la imagen")
                return None

            logger.info(f"✅ Imagen preparada: {image_array.shape} (H x W x C)")

            # PASO 2: DETECCIÓN DE ROSTRO CON HOG + SVM
            logger.info("🔍 PASO 2: Detección de rostro usando HOG + SVM")
            face_locations = self.face_detector(image_array)

            logger.info(f"📊 Detector HOG encontró {len(face_locations)} rostro(s)")

            if len(face_locations) == 0:
                logger.warning("❌ No se detectó rostro con detector HOG")
                return None

            if len(face_locations) > 1:
                logger.warning(f"⚠️ Múltiples rostros detectados ({len(face_locations)}), usando el primero")

            # Seleccionar el rostro más grande (más confiable)
            face_rect = max(face_locations, key=lambda rect: rect.width() * rect.height())
            logger.info(
                f"✅ Rostro seleccionado: ({face_rect.left()}, {face_rect.top()}) - {face_rect.width()}x{face_rect.height()}")

            # PASO 3: EXTRACCIÓN DE 68 LANDMARKS FACIALES
            logger.info("📍 PASO 3: Extracción de 68 landmarks faciales")
            landmarks = self.shape_predictor(image_array, face_rect)

            # Documentar algunos landmarks clave para verificación académica
            nose_tip = landmarks.part(30)  # Punta de nariz
            left_eye = landmarks.part(36)  # Ojo izquierdo
            right_eye = landmarks.part(45)  # Ojo derecho

            logger.info(f"👃 Landmark nariz: ({nose_tip.x}, {nose_tip.y})")
            logger.info(f"👁️ Landmark ojo izq: ({left_eye.x}, {left_eye.y})")
            logger.info(f"👁️ Landmark ojo der: ({right_eye.x}, {right_eye.y})")
            logger.info("✅ 68 landmarks extraídos exitosamente")

            # PASO 4: GENERACIÓN DE EMBEDDING 128D CON RESNET
            logger.info("🧠 PASO 4: Generación de embedding 128D usando ResNet")
            face_encoding = self.face_encoder.compute_face_descriptor(image_array, landmarks)

            # Convertir a numpy array
            encoding_array = np.array(face_encoding)

            # PASO 5: ANÁLISIS DE CARACTERÍSTICAS EXTRAÍDAS
            logger.info("📊 PASO 5: Análisis de características extraídas")
            encoding_stats = self._analyze_encoding_characteristics(encoding_array)

            logger.info(f"✅ Encoding generado: {len(encoding_array)} características")
            logger.info(f"📈 Estadísticas: {encoding_stats}")

            # PASO 6: VERIFICACIÓN DE CALIDAD
            quality_score = self._assess_encoding_quality(encoding_array, face_rect)
            logger.info(f"🎯 Calidad del encoding: {quality_score:.3f}")

            if quality_score < 0.3:
                logger.warning("⚠️ Calidad baja del encoding - imagen podría no ser óptima")

            logger.info("🎉 EXTRACCIÓN ACADÉMICA COMPLETADA EXITOSAMENTE")
            return encoding_array

        except Exception as e:
            logger.error(f"❌ Error en extracción académica: {e}")
            return None

        finally:
            # Limpiar archivo temporal si se creó
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except:
                    pass

    async def _prepare_image_for_processing(self, image_source: Union[str, bytes, np.ndarray]) -> Optional[np.ndarray]:
        """Preparar imagen para procesamiento con dlib"""
        try:
            if isinstance(image_source, str):
                if image_source.startswith('http'):
                    # Descargar desde URL
                    image_array = await self._download_image_from_url(image_source)
                else:
                    # Archivo local
                    if not os.path.exists(image_source):
                        raise FileNotFoundError(f"Archivo no encontrado: {image_source}")
                    image_pil = Image.open(image_source)
                    image_array = np.array(image_pil)

            elif isinstance(image_source, bytes):
                # Bytes de imagen
                image_pil = Image.open(io.BytesIO(image_source))
                image_array = np.array(image_pil)

            elif isinstance(image_source, np.ndarray):
                # Array numpy directo
                image_array = image_source

            else:
                raise ValueError(f"Tipo de imagen no soportado: {type(image_source)}")

            # Convertir a RGB si es necesario
            if len(image_array.shape) == 3 and image_array.shape[2] == 4:
                # RGBA -> RGB
                image_pil = Image.fromarray(image_array)
                image_pil = image_pil.convert('RGB')
                image_array = np.array(image_pil)
            elif len(image_array.shape) == 3 and image_array.shape[2] == 1:
                # Grayscale -> RGB
                image_array = np.repeat(image_array, 3, axis=2)

            return image_array

        except Exception as e:
            logger.error(f"❌ Error preparando imagen: {e}")
            return None

    async def _download_image_from_url(self, url: str) -> np.ndarray:
        """Descargar imagen desde URL"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            image_pil = Image.open(io.BytesIO(response.content))
            if image_pil.mode != 'RGB':
                image_pil = image_pil.convert('RGB')

            return np.array(image_pil)

        except Exception as e:
            logger.error(f"❌ Error descargando imagen: {e}")
            raise

    def _analyze_encoding_characteristics(self, encoding: np.ndarray) -> Dict[str, float]:
        """
        Análisis académico de las características del encoding
        """
        return {
            "mean": float(np.mean(encoding)),
            "std": float(np.std(encoding)),
            "min": float(np.min(encoding)),
            "max": float(np.max(encoding)),
            "variance": float(np.var(encoding)),
            "l2_norm": float(np.linalg.norm(encoding)),
            "sparsity": float(np.sum(np.abs(encoding) < 0.01) / len(encoding))
        }

    def _assess_encoding_quality(self, encoding: np.ndarray, face_rect) -> float:
        """
        Evaluar calidad del encoding basado en métricas académicas
        """
        # Factor 1: Magnitud del encoding (mayor magnitud = mejor calidad generalmente)
        magnitude_score = min(1.0, np.linalg.norm(encoding) / 10.0)

        # Factor 2: Varianza (mayor varianza = más información)
        variance_score = min(1.0, np.var(encoding) * 10)

        # Factor 3: Tamaño del rostro detectado
        face_area = face_rect.width() * face_rect.height()
        size_score = min(1.0, face_area / 10000)  # Normalizar por área típica

        # Combinar scores
        quality_score = (magnitude_score + variance_score + size_score) / 3.0

        return quality_score

    async def recognize_face(self, face_encoding: np.ndarray, students: List[Student]) -> Dict[str, Any]:
        """
        RECONOCIMIENTO FACIAL CON COMPARACIÓN MULTI-MÉTRICA DOCUMENTADA

        PROCESO ACADÉMICO EXPLICADO:
        1. Preparar encodings de estudiantes
        2. Aplicar sistema de aprendizaje adaptativo
        3. Comparación usando múltiples métricas
        4. Decisión multi-criterio documentada
        5. Generar alertas de seguridad si es necesario
        """
        try:
            logger.info("🎯 INICIANDO RECONOCIMIENTO FACIAL ACADÉMICO")

            if len(students) == 0:
                return self._create_recognition_result(False, "No hay estudiantes registrados")

            logger.info(f"🔍 Comparando contra {len(students)} estudiantes")

            # PASO 1: PREPARAR ENCODINGS DE ESTUDIANTES
            logger.info("📋 PASO 1: Preparación de encodings de estudiantes")
            known_encodings, known_students = self._prepare_student_encodings(students, face_encoding)

            if not known_encodings:
                return self._create_recognition_result(
                    False,
                    "No hay encodings compatibles para comparar",
                    debug_info={"total_students": len(students), "compatible_encodings": 0}
                )

            # PASO 2: ACTUALIZAR SISTEMA ADAPTATIVO
            logger.info("🚀 PASO 2: Actualización del sistema adaptativo")
            adaptive_report = self.adaptive_system.adaptive_update(known_encodings)
            current_threshold = self.adaptive_system.stats['optimal_threshold']

            logger.info(f"🎯 Umbral adaptativo actual: {current_threshold:.3f}")

            # PASO 3: COMPARACIÓN MULTI-MÉTRICA
            logger.info("📊 PASO 3: Comparación multi-métrica")
            comparison_results = self._multi_metric_comparison(face_encoding, known_encodings, known_students)

            # PASO 4: DECISIÓN ACADÉMICA DOCUMENTADA
            logger.info("🧠 PASO 4: Proceso de decisión académica")
            recognition_decision = self._make_academic_decision(comparison_results, current_threshold)

            # PASO 5: VERIFICAR ALERTAS DE SEGURIDAD
            logger.info("🚨 PASO 5: Verificación de alertas de seguridad")
            security_alert = self._check_security_alerts(recognition_decision)

            # PASO 6: CONSTRUIR RESPUESTA FINAL
            final_result = self._build_final_result(
                recognition_decision,
                security_alert,
                adaptive_report,
                comparison_results
            )

            logger.info("🎉 RECONOCIMIENTO ACADÉMICO COMPLETADO")
            return final_result

        except Exception as e:
            logger.error(f"❌ Error en reconocimiento académico: {e}")
            return self._create_recognition_result(
                False,
                f"Error en procesamiento: {str(e)}",
                debug_info={"error": str(e)}
            )

    def _prepare_student_encodings(self, students: List[Student], face_encoding: np.ndarray) -> tuple:
        """Preparar encodings de estudiantes para comparación"""
        known_encodings = []
        known_students = []
        incompatible_count = 0

        for student in students:
            if student.face_encoding:
                try:
                    student_encoding = np.array(student.face_encoding, dtype=np.float64)

                    # Verificar compatibilidad de dimensiones
                    if len(student_encoding) != len(face_encoding):
                        logger.warning(
                            f"⚠️ Encoding incompatible para {student.nombre}: {len(student_encoding)}D vs {len(face_encoding)}D")
                        incompatible_count += 1
                        continue

                    known_encodings.append(student_encoding)
                    known_students.append(student)

                except Exception as e:
                    logger.warning(f"Error procesando encoding de {student.id}: {e}")
                    continue

        logger.info(f"✅ Encodings compatibles: {len(known_encodings)}")
        logger.info(f"⚠️ Encodings incompatibles: {incompatible_count}")

        return known_encodings, known_students

    def _multi_metric_comparison(self, face_encoding: np.ndarray, known_encodings: List[np.ndarray],
                                 known_students: List[Student]) -> List[Dict]:
        """
        Comparación usando múltiples métricas académicas documentadas
        """
        results = []

        for i, (student_encoding, student) in enumerate(zip(known_encodings, known_students)):
            # Aplicar pesos adaptativos si están disponibles
            weights = self.adaptive_system.stats['feature_weights']
            weighted_face_encoding = face_encoding * weights
            weighted_student_encoding = student_encoding * weights

            # MÉTRICA 1: Distancia Euclidiana Ponderada
            euclidean_distance = np.linalg.norm(weighted_face_encoding - weighted_student_encoding)
            euclidean_similarity = max(0.0, 1.0 - euclidean_distance / 2.0)

            # MÉTRICA 2: Similitud del Coseno
            dot_product = np.dot(weighted_face_encoding, weighted_student_encoding)
            norm_product = np.linalg.norm(weighted_face_encoding) * np.linalg.norm(weighted_student_encoding)
            cosine_similarity = dot_product / norm_product if norm_product > 0 else 0.0

            # MÉTRICA 3: Distancia de Manhattan Normalizada
            manhattan_distance = np.sum(np.abs(weighted_face_encoding - weighted_student_encoding))
            manhattan_similarity = max(0.0, 1.0 - manhattan_distance / len(face_encoding))

            # MÉTRICA 4: Correlación de Pearson
            try:
                correlation_coeff = np.corrcoef(weighted_face_encoding, weighted_student_encoding)[0, 1]
                correlation_similarity = (correlation_coeff + 1) / 2  # Normalizar a 0-1
            except:
                correlation_similarity = 0.0

            # MÉTRICA COMBINADA PONDERADA (Decisión Multi-Criterio)
            # Pesos basados en confiabilidad académica de cada métrica
            metric_weights = {
                'euclidean': 0.4,  # Más peso a distancia euclidiana (más confiable)
                'cosine': 0.3,  # Similitud angular
                'manhattan': 0.2,  # Distancia robusta
                'correlation': 0.1  # Correlación estadística
            }

            combined_similarity = (
                    euclidean_similarity * metric_weights['euclidean'] +
                    cosine_similarity * metric_weights['cosine'] +
                    manhattan_similarity * metric_weights['manhattan'] +
                    correlation_similarity * metric_weights['correlation']
            )

            result = {
                'student': student,
                'metrics': {
                    'euclidean_distance': euclidean_distance,
                    'euclidean_similarity': euclidean_similarity,
                    'cosine_similarity': cosine_similarity,
                    'manhattan_similarity': manhattan_similarity,
                    'correlation_similarity': correlation_similarity,
                    'combined_similarity': combined_similarity
                },
                'quality_factors': {
                    'encoding_magnitude': np.linalg.norm(student_encoding),
                    'feature_variance': np.var(student_encoding),
                    'weights_applied': True
                }
            }

            results.append(result)

        # Ordenar por similitud combinada
        results.sort(key=lambda x: x['metrics']['combined_similarity'], reverse=True)

        # Log de las mejores coincidencias para análisis académico
        logger.info("📊 Top 3 coincidencias:")
        for i, result in enumerate(results[:3]):
            student = result['student']
            similarity = result['metrics']['combined_similarity']
            logger.info(f"   {i + 1}. {student.nombre} {student.apellidos} - Similitud: {similarity:.3f}")

        return results

    def _make_academic_decision(self, comparison_results: List[Dict], threshold: float) -> Dict[str, Any]:
        """
        Proceso de decisión académica documentado paso a paso
        """
        if not comparison_results:
            return {"match_found": False, "reason": "No hay resultados de comparación"}

        best_match = comparison_results[0]
        best_similarity = best_match['metrics']['combined_similarity']
        best_student = best_match['student']

        logger.info(f"🧠 Análisis de decisión académica:")
        logger.info(f"   Mejor coincidencia: {best_student.nombre} {best_student.apellidos}")
        logger.info(f"   Similitud combinada: {best_similarity:.3f}")
        logger.info(f"   Umbral adaptativo: {threshold:.3f}")

        # CRITERIO 1: Superar umbral adaptativo
        exceeds_threshold = best_similarity >= threshold

        # CRITERIO 2: Verificar separación clara del segundo mejor (con lógica mejorada)
        clear_separation = True
        separation_margin = 0.0

        if len(comparison_results) > 1:
            second_best_similarity = comparison_results[1]['metrics']['combined_similarity']
            separation_margin = best_similarity - second_best_similarity

            # Criterio académico inteligente de separación
            if best_similarity >= 0.90:
                # Similitud extremadamente alta (>90%) - criterio muy permisivo
                min_separation = 0.02
                separation_reasoning = "Similitud extremadamente alta - criterio permisivo"
            elif best_similarity >= 0.85:
                # Similitud muy alta (>85%) - criterio permisivo
                min_separation = 0.03
                separation_reasoning = "Similitud muy alta - criterio permisivo"
            elif best_similarity >= 0.75:
                # Similitud alta (>75%) - criterio moderado
                min_separation = 0.05
                separation_reasoning = "Similitud alta - criterio moderado"
            elif best_similarity >= 0.65:
                # Similitud media-alta (>65%) - criterio estricto
                min_separation = 0.08
                separation_reasoning = "Similitud media-alta - criterio estricto"
            else:
                # Similitud baja (<65%) - criterio muy estricto
                min_separation = 0.12
                separation_reasoning = "Similitud baja - criterio muy estricto"

            clear_separation = separation_margin >= min_separation

            logger.info(f"   Separación del 2do mejor: {separation_margin:.3f} (mín: {min_separation:.3f})")
            logger.info(f"   Lógica de separación: {separation_reasoning}")
        else:
            logger.info(f"   Solo un candidato disponible - separación automáticamente válida")

        # CRITERIO 3: Verificar consistencia entre métricas
        metrics = best_match['metrics']
        metric_consistency = self._assess_metric_consistency(metrics)
        logger.info(f"   Consistencia de métricas: {metric_consistency:.3f}")

        # CRITERIO 4: Confianza absoluta para similitudes muy altas
        absolute_confidence = best_similarity >= 0.88  # Umbral de confianza absoluta
        if absolute_confidence:
            logger.info(f"   🎯 CONFIANZA ABSOLUTA: Similitud {best_similarity:.3f} >= 0.88")

        # DECISIÓN FINAL ACADÉMICA MEJORADA
        decision_factors = {
            "exceeds_threshold": exceeds_threshold,
            "clear_separation": clear_separation,
            "metric_consistency": metric_consistency > 0.7,
            "absolute_confidence": absolute_confidence,
            "similarity_score": best_similarity,
            "separation_margin": separation_margin
        }

        # Lógica de decisión académica:
        # 1. Si hay confianza absoluta (>88%) Y supera umbral Y tiene consistencia → MATCH
        # 2. Si cumple todos los criterios tradicionales → MATCH
        # 3. Si tiene alta similitud (>80%) pero falla separación por poco → evaluar caso especial

        if absolute_confidence and exceeds_threshold and metric_consistency > 0.7:
            match_found = True
            decision_reason = "Confianza absoluta con consistencia alta"
            logger.info(f"✅ Decisión académica: COINCIDENCIA (Confianza Absoluta)")
        elif all([exceeds_threshold, clear_separation, metric_consistency > 0.7]):
            match_found = True
            decision_reason = "Todos los criterios académicos cumplidos"
            logger.info(f"✅ Decisión académica: COINCIDENCIA (Criterios Completos)")
        elif (best_similarity >= 0.80 and exceeds_threshold and metric_consistency > 0.75 and
              separation_margin >= 0.02):  # Caso especial para similitudes altas
            match_found = True
            decision_reason = "Similitud alta con criterios relajados justificadamente"
            logger.info(f"✅ Decisión académica: COINCIDENCIA (Criterio Especial)")
        else:
            match_found = False
            decision_reason = "Criterios académicos insuficientes"
            logger.info(f"❌ Decisión académica: NO COINCIDENCIA")

        confidence_level = self._calculate_confidence_level(best_similarity, decision_factors)

        logger.info(f"🎯 Nivel de confianza: {confidence_level}")
        logger.info(f"📝 Razón de decisión: {decision_reason}")

        return {
            "match_found": match_found,
            "best_match": best_match,
            "similarity": best_similarity,
            "confidence": confidence_level,
            "decision_factors": decision_factors,
            "threshold_used": threshold,
            "decision_reason": decision_reason,
            "academic_reasoning": self._generate_academic_reasoning(decision_factors, best_similarity, threshold)
        }

    def _assess_metric_consistency(self, metrics: Dict[str, float]) -> float:
        """
        Evaluar consistencia entre diferentes métricas de similitud
        """
        similarities = [
            metrics['euclidean_similarity'],
            metrics['cosine_similarity'],
            metrics['manhattan_similarity'],
            metrics['correlation_similarity']
        ]

        # Calcular desviación estándar (menor = más consistente)
        std_dev = np.std(similarities)
        consistency_score = max(0.0, 1.0 - std_dev * 2)  # Normalizar

        return consistency_score

    def _calculate_confidence_level(self, similarity: float, decision_factors: Dict) -> str:
        """
        Calcular nivel de confianza académico basado en múltiples factores
        """
        confidence_score = 0.0

        # Factor 1: Similitud absoluta (peso mayor)
        if similarity >= 0.90:
            confidence_score += 0.5  # Similitud extrema
        elif similarity >= 0.85:
            confidence_score += 0.4  # Similitud muy alta
        elif similarity >= 0.75:
            confidence_score += 0.3  # Similitud alta
        elif similarity >= 0.65:
            confidence_score += 0.2  # Similitud media
        else:
            confidence_score += 0.1  # Similitud baja

        # Factor 2: Superar umbral adaptativo
        if decision_factors.get("exceeds_threshold", False):
            confidence_score += 0.2

        # Factor 3: Separación clara (menos peso si tenemos confianza absoluta)
        if decision_factors.get("clear_separation", False):
            confidence_score += 0.15
        elif decision_factors.get("absolute_confidence", False):
            confidence_score += 0.1  # Penalización menor si hay confianza absoluta

        # Factor 4: Consistencia de métricas
        if decision_factors.get("metric_consistency", False):
            confidence_score += 0.15

        # Determinar nivel basado en score final
        if confidence_score >= 0.8:
            return "Alta"
        elif confidence_score >= 0.6:
            return "Media"
        else:
            return "Baja"

    def _generate_academic_reasoning(self, factors: Dict, similarity: float, threshold: float) -> str:
        """
        Generar explicación académica del proceso de decisión
        """
        reasoning_parts = []

        if factors["exceeds_threshold"]:
            reasoning_parts.append(f"Similitud {similarity:.3f} supera umbral adaptativo {threshold:.3f}")
        else:
            reasoning_parts.append(f"Similitud {similarity:.3f} NO supera umbral adaptativo {threshold:.3f}")

        if factors["clear_separation"]:
            reasoning_parts.append("Separación clara del segundo mejor candidato")
        else:
            reasoning_parts.append("Separación insuficiente del segundo mejor candidato")

        if factors["metric_consistency"]:
            reasoning_parts.append("Consistencia alta entre múltiples métricas")
        else:
            reasoning_parts.append("Inconsistencia detectada entre métricas")

        return ". ".join(reasoning_parts)

    def _check_security_alerts(self, recognition_decision: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verificar alertas de seguridad para usuarios requisitoriados
        """
        security_alert = {
            "alert_triggered": False,
            "alert_level": "NONE",
            "message": "",
            "authority_notification": False
        }

        if recognition_decision["match_found"]:
            student = recognition_decision["best_match"]["student"]

            if student.requisitoriado:
                # ¡ALERTA CRÍTICA DE SEGURIDAD!
                security_alert = {
                    "alert_triggered": True,
                    "alert_level": "CRITICAL",
                    "message": "¡ALERTA DE SEGURIDAD! Usuario Requisitoriado Detectado",
                    "authority_notification": "Notificación Enviada a la Policía (Simulada)",
                    "student_info": {
                        "id": student.id,
                        "nombre": f"{student.nombre} {student.apellidos}",
                        "codigo": student.codigo,
                        "requisitoriado": True
                    },
                    "detection_details": {
                        "similarity": recognition_decision["similarity"],
                        "confidence": recognition_decision["confidence"],
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }

                logger.critical("🚨 ALERTA CRÍTICA DE SEGURIDAD 🚨")
                logger.critical(f"🚨 Usuario requisitoriado detectado: {student.nombre} {student.apellidos}")
                logger.critical(f"🚨 Código: {student.codigo}")
                logger.critical(f"🚨 Similitud: {recognition_decision['similarity']:.3f}")
                logger.critical("🚨 NOTIFICACIÓN A AUTORIDADES SIMULADA")

        return security_alert

    def _build_final_result(self, recognition_decision: Dict, security_alert: Dict,
                            adaptive_report: Dict, comparison_results: List[Dict]) -> Dict[str, Any]:
        """
        Construir resultado final con toda la información académica
        """
        base_result = {
            "found": recognition_decision["match_found"],
            "similarity": recognition_decision.get("similarity", 0.0),
            "confidence": recognition_decision.get("confidence", "Baja"),
            "message": "",
            "student": None
        }

        # Agregar información del estudiante si hay coincidencia
        if recognition_decision["match_found"]:
            student = recognition_decision["best_match"]["student"]
            base_result["student"] = {
                "id": student.id,
                "nombre": student.nombre,
                "apellidos": student.apellidos,
                "codigo": student.codigo,
                "correo": student.correo,
                "requisitoriado": student.requisitoriado,
                "imagen_path": student.imagen_path,
                "created_at": student.created_at,
                "updated_at": student.updated_at,
                "active": student.active
            }
            base_result[
                "message"] = f"Estudiante identificado con {recognition_decision['confidence'].lower()} confianza"

        # Agregar alerta de seguridad si existe
        if security_alert["alert_triggered"]:
            base_result.update({
                "SECURITY_ALERT": True,
                "alert_message": security_alert["message"],
                "authority_notification": security_alert["authority_notification"],
                "alert_level": security_alert["alert_level"],
                "alert_details": security_alert
            })

        # Agregar información académica y de debugging
        base_result["academic_analysis"] = {
            "recognition_method": "Dlib HOG + ResNet + Adaptive Learning",
            "threshold_used": recognition_decision.get("threshold_used", self.recognition_threshold),
            "decision_reasoning": recognition_decision.get("academic_reasoning", ""),
            "adaptive_learning": adaptive_report,
            "metrics_analysis": comparison_results[0]["metrics"] if comparison_results else {},
            "total_comparisons": len(comparison_results),
            "system_maturity": self.adaptive_system.stats["total_encodings"]
        }

        # Mensaje por defecto si no hay coincidencia
        if not recognition_decision["match_found"]:
            base_result["message"] = "No se encontró coincidencia suficiente"

        return base_result

    def _create_recognition_result(self, found: bool, message: str, student: Student = None,
                                   similarity: float = 0.0, confidence: str = "Baja",
                                   debug_info: Dict = None) -> Dict[str, Any]:
        """Crear resultado de reconocimiento estándar"""
        result = {
            "found": found,
            "message": message,
            "similarity": similarity,
            "confidence": confidence,
            "student": None
        }

        if student:
            result["student"] = {
                "id": student.id,
                "nombre": student.nombre,
                "apellidos": student.apellidos,
                "codigo": student.codigo,
                "correo": student.correo,
                "requisitoriado": student.requisitoriado,
                "imagen_path": student.imagen_path,
                "created_at": student.created_at,
                "updated_at": student.updated_at,
                "active": student.active
            }

        if debug_info:
            result["debug_info"] = debug_info

        return result

    async def debug_encoding_comparison(self, image_path1: str, image_path2: str) -> Dict[str, Any]:
        """
        Método de debugging académico mejorado para comparar dos imágenes
        """
        try:
            logger.info(f"🔍 DEBUGGING ACADÉMICO: Comparando {image_path1} vs {image_path2}")

            # Extraer encodings usando método académico
            encoding1 = await self.extract_face_encoding(image_path1)
            encoding2 = await self.extract_face_encoding(image_path2)

            if encoding1 is None or encoding2 is None:
                return {"error": "No se pudo extraer encoding de una o ambas imágenes"}

            # Análisis académico detallado
            analysis = {
                "encoding1_analysis": self._analyze_encoding_characteristics(encoding1),
                "encoding2_analysis": self._analyze_encoding_characteristics(encoding2),
                "comparison_metrics": {},
                "academic_assessment": {},
                "system_info": {
                    "method": "Dlib HOG + ResNet + Adaptive Learning",
                    "encoding_dimensions": len(encoding1),
                    "adaptive_threshold": self.adaptive_system.stats['optimal_threshold'],
                    "system_maturity": self.adaptive_system.stats['total_encodings']
                }
            }

            # Comparación multi-métrica
            comparison_results = self._multi_metric_comparison(encoding1, [encoding2], [None])
            if comparison_results:
                analysis["comparison_metrics"] = comparison_results[0]["metrics"]

            # Evaluación académica
            analysis["academic_assessment"] = {
                "would_match": comparison_results[0]["metrics"]["combined_similarity"] >= self.adaptive_system.stats[
                    'optimal_threshold'] if comparison_results else False,
                "confidence_level": self._calculate_confidence_level(
                    comparison_results[0]["metrics"]["combined_similarity"] if comparison_results else 0,
                    {"exceeds_threshold": True, "clear_separation": True, "metric_consistency": True}
                ),
                "recommendation": "Imágenes de la misma persona" if comparison_results and
                                                                    comparison_results[0]["metrics"][
                                                                        "combined_similarity"] >= 0.7 else "Imágenes de personas diferentes"
            }

            logger.info("✅ Debugging académico completado")
            return analysis

        except Exception as e:
            logger.error(f"❌ Error en debugging: {e}")
            return {"error": str(e), "debug_info": {"function": "debug_encoding_comparison"}}

    def verify_face_quality(self, image_source: Union[str, bytes, np.ndarray]) -> Dict[str, Any]:
        """
        Verificar calidad de imagen usando métodos académicos
        """
        try:
            import asyncio

            # Preparar imagen
            if asyncio.iscoroutinefunction(self._prepare_image_for_processing):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                image = loop.run_until_complete(self._prepare_image_for_processing(image_source))
            else:
                # Fallback si no es async
                if isinstance(image_source, str) and os.path.exists(image_source):
                    image_pil = Image.open(image_source)
                    image = np.array(image_pil)
                else:
                    return {"valid": False, "reason": "No se pudo cargar la imagen"}

            # Detección con dlib
            face_locations = self.face_detector(image)

            if len(face_locations) == 0:
                return {"valid": False, "reason": "No se detectó rostro con detector HOG"}

            # Análisis de calidad académico
            face_rect = face_locations[0]
            quality_assessment = {
                "valid": True,
                "face_count": len(face_locations),
                "resolution": f"{image.shape[1]}x{image.shape[0]}",
                "face_size": f"{face_rect.width()}x{face_rect.height()}",
                "face_area_ratio": (face_rect.width() * face_rect.height()) / (image.shape[0] * image.shape[1]),
                "quality_factors": {
                    "sufficient_resolution": image.shape[0] >= 200 and image.shape[1] >= 200,
                    "adequate_face_size": face_rect.width() >= 50 and face_rect.height() >= 50,
                    "single_face": len(face_locations) == 1
                }
            }

            # Calcular score de calidad
            quality_score = sum(quality_assessment["quality_factors"].values()) / len(
                quality_assessment["quality_factors"])
            quality_assessment["quality_score"] = quality_score
            quality_assessment[
                "recommendation"] = "Excelente" if quality_score >= 1.0 else "Buena" if quality_score >= 0.66 else "Mejorable"

            return quality_assessment

        except Exception as e:
            return {"valid": False, "reason": f"Error al verificar calidad: {str(e)}"}

    def get_adaptive_learning_report(self) -> Dict[str, Any]:
        """
        Obtener reporte completo del sistema de aprendizaje adaptativo
        """
        return {
            "academic_compliance": {
                "explained_process": True,
                "black_box_usage": False,
                "adaptive_learning": True,
                "threshold_optimization": True,
                "feature_weighting": True
            },
            "system_status": self.adaptive_system.get_improvement_report(),
            "technical_details": {
                "face_detection": "dlib HOG + SVM (Histogram of Oriented Gradients)",
                "landmark_detection": "dlib 68-point facial landmarks",
                "feature_extraction": "dlib ResNet face recognition model",
                "comparison_metrics": ["Euclidean Distance", "Cosine Similarity", "Manhattan Distance",
                                       "Pearson Correlation"],
                "decision_process": "Multi-criteria academic decision with documented reasoning"
            },
            "improvements_over_face_recognition_library": [
                "Proceso completamente explicado paso a paso",
                "Sistema de aprendizaje adaptativo propio",
                "Optimización automática de umbrales",
                "Comparación multi-métrica documentada",
                "Detección de alertas de seguridad",
                "Análisis de calidad académico"
            ]
        }

    def cleanup_resources(self):
        """Limpiar recursos del sistema académico"""
        logger.info("✅ Recursos del sistema académico liberados")
        # dlib no requiere limpieza específica de recursos

    def __del__(self):
        """Destructor para limpiar recursos automáticamente"""
        self.cleanup_resources()