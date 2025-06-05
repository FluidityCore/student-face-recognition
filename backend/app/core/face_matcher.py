# app/core/face_matcher.py
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import logging
from config import SIMILARITY_THRESHOLD

logger = logging.getLogger(__name__)


class FaceMatcher:
    """Comparador de rostros usando similitud coseno"""

    @staticmethod
    def find_best_match(test_encoding, known_encodings, students_data, threshold=SIMILARITY_THRESHOLD):
        """Encontrar la mejor coincidencia"""
        try:
            if len(known_encodings) == 0:
                return None, 0.0

            # Calcular similitudes coseno
            similarities = cosine_similarity([test_encoding], known_encodings)[0]

            # Encontrar la mejor coincidencia
            best_match_index = np.argmax(similarities)
            best_similarity = similarities[best_match_index]

            if best_similarity >= threshold:
                best_match = students_data[best_match_index]
                return best_match, best_similarity

            return None, best_similarity

        except Exception as e:
            logger.error(f"Error encontrando coincidencia: {e}")
            return None, 0.0