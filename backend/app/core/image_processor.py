# app/core/image_processor.py
import cv2
import numpy as np
import logging
from config import IMG_SIZE

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Procesador de imágenes (igual que tu script original)"""

    @staticmethod
    def preprocess_image(image_array):
        """Preprocesar imagen (igual que tu script original)"""
        try:
            # Convertir a escala de grises si es necesario
            if len(image_array.shape) == 3:
                img = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)
            else:
                img = image_array

            # Redimensionar al tamaño estándar
            img = cv2.resize(img, IMG_SIZE)
            return img
        except Exception as e:
            logger.error(f"Error preprocesando imagen: {e}")
            return None

    @staticmethod
    def extract_features_single(image, known_encodings):
        """Extraer características de una sola imagen"""
        try:
            # Aplanar la imagen
            flattened_image = image.flatten()

            # Normalizar
            feature_vector = flattened_image.astype(float) / 255.0

            # Hacer compatible con las características guardadas
            if len(known_encodings) > 0:
                target_size = len(known_encodings[0])
                if len(feature_vector) > target_size:
                    feature_vector = feature_vector[:target_size]
                elif len(feature_vector) < target_size:
                    feature_vector = np.pad(feature_vector, (0, target_size - len(feature_vector)))

            return feature_vector

        except Exception as e:
            logger.error(f"Error extrayendo características: {e}")
            return None