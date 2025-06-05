# app/database/models.py
import json
import logging
from typing import List, Dict, Any, Optional
from .connection import get_db_connection

logger = logging.getLogger(__name__)


class StudentModel:
    """Modelo para manejar datos de estudiantes"""

    @staticmethod
    def get_all_students_with_features() -> List[Dict[str, Any]]:
        """Obtener todos los estudiantes con características"""
        try:
            connection = get_db_connection()
            if not connection:
                return []

            cursor = connection.cursor()
            cursor.execute("""
                           SELECT id, nombre, apellidos, correo, requisitoriado, kp
                           FROM estudiantes
                           WHERE kp IS NOT NULL
                           """)

            results = cursor.fetchall()
            cursor.close()
            connection.close()

            students = []
            for result in results:
                students.append({
                    'id': result[0],
                    'nombre': result[1],
                    'apellidos': result[2],
                    'correo': result[3],
                    'requisitoriado': bool(result[4]),
                    'encoding': json.loads(result[5])
                })

            return students

        except Exception as e:
            logger.error(f"Error obteniendo estudiantes: {e}")
            return []

    @staticmethod
    def get_all_students() -> List[Dict[str, Any]]:
        """Obtener todos los estudiantes (sin características)"""
        try:
            connection = get_db_connection()
            if not connection:
                return []

            cursor = connection.cursor()
            cursor.execute("""
                           SELECT id, nombre, apellidos, correo, requisitoriado
                           FROM estudiantes
                           ORDER BY apellidos, nombre
                           """)

            results = cursor.fetchall()
            cursor.close()
            connection.close()

            students = []
            for result in results:
                students.append({
                    "id": result[0],
                    "nombre": result[1],
                    "apellidos": result[2],
                    "correo": result[3],
                    "requisitoriado": bool(result[4])
                })

            return students

        except Exception as e:
            logger.error(f"Error listando estudiantes: {e}")
            return []

    @staticmethod
    def get_student_by_id(student_id: int) -> Optional[Dict[str, Any]]:
        """Obtener estudiante por ID"""
        try:
            connection = get_db_connection()
            if not connection:
                return None

            cursor = connection.cursor()
            cursor.execute("""
                           SELECT id, nombre, apellidos, correo, requisitoriado
                           FROM estudiantes
                           WHERE id = %s
                           """, (student_id,))

            result = cursor.fetchone()
            cursor.close()
            connection.close()

            if result:
                return {
                    "id": result[0],
                    "nombre": result[1],
                    "apellidos": result[2],
                    "correo": result[3],
                    "requisitoriado": bool(result[4])
                }

            return None

        except Exception as e:
            logger.error(f"Error obteniendo estudiante: {e}")
            return None

    @staticmethod
    def toggle_requisitoriado(student_id: int) -> Optional[bool]:
        """Cambiar estado de requisitoriado"""
        try:
            connection = get_db_connection()
            if not connection:
                return None

            cursor = connection.cursor()

            # Obtener estado actual
            cursor.execute("SELECT requisitoriado FROM estudiantes WHERE id = %s", (student_id,))
            result = cursor.fetchone()

            if not result:
                cursor.close()
                connection.close()
                return None

            # Cambiar estado
            new_status = not bool(result[0])
            cursor.execute(
                "UPDATE estudiantes SET requisitoriado = %s WHERE id = %s",
                (new_status, student_id)
            )

            connection.commit()
            cursor.close()
            connection.close()

            return new_status

        except Exception as e:
            logger.error(f"Error cambiando estado: {e}")
            return None

    @staticmethod
    def get_stats() -> Dict[str, int]:
        """Obtener estadísticas de estudiantes"""
        try:
            connection = get_db_connection()
            if not connection:
                return {}

            cursor = connection.cursor()

            cursor.execute("SELECT COUNT(*) FROM estudiantes")
            total = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM estudiantes WHERE requisitoriado = TRUE")
            requisitoriados = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM estudiantes WHERE kp IS NOT NULL")
            with_features = cursor.fetchone()[0]

            cursor.close()
            connection.close()

            return {
                "total_students": total,
                "students_with_features": with_features,
                "requisitoriados": requisitoriados
            }

        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
