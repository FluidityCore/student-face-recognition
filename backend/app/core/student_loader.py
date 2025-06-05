# app/core/student_loader.py
import numpy as np
import logging
from app.database.models import StudentModel

logger = logging.getLogger(__name__)

# Variables globales para almacenar datos en memoria
known_encodings = []
students_data = []
model_loaded = False


def load_students_from_db():
    """Cargar todos los estudiantes y sus características de la BD"""
    global known_encodings, students_data, model_loaded

    try:
        # Cargar estudiantes con características
        students = StudentModel.get_all_students_with_features()

        if not students:
            logger.warning("No se encontraron estudiantes con características")
            return False

        # Separar datos y características
        students_data = students
        encodings_list = [student['encoding'] for student in students]
        known_encodings = np.array(encodings_list)

        model_loaded = True

        logger.info(f"Cargados {len(students_data)} estudiantes de la BD")
        return True

    except Exception as e:
        logger.error(f"Error cargando estudiantes: {e}")
        model_loaded = False
        return False


def get_students_data():
    """Obtener datos de estudiantes cargados"""
    return students_data


def get_known_encodings():
    """Obtener características conocidas"""
    return known_encodings


def get_students_count():
    """Obtener número de estudiantes cargados"""
    return len(students_data)


def is_model_loaded():
    """Verificar si el modelo está cargado"""
    return model_loaded


def reload_students():
    """Recargar estudiantes de la BD"""
    return load_students_from_db()