import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import pymysql.cursors
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class MySQLService:
    """Servicio para interactuar con MySQL como fallback local"""

    def __init__(self):
        """Inicializar servicio MySQL"""
        self.host = os.getenv("MYSQL_HOST", "localhost")
        self.port = int(os.getenv("MYSQL_PORT", "3307"))
        self.user = os.getenv("MYSQL_USER", "root")
        self.password = os.getenv("MYSQL_PASSWORD", "root")
        self.database = os.getenv("MYSQL_DATABASE", "face_recognition_db")

        # Configuración de conexión
        self.connection_config = {
            'host': self.host,
            'port': self.port,
            'user': self.user,
            'password': self.password,
            'database': self.database,
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor,
            'autocommit': False
        }

        self.enabled = self._test_connection()

        if self.enabled:
            logger.info("✅ MySQL configurado y conectado")
            self._initialize_database()
        else:
            logger.warning("⚠️ MySQL no está disponible")

    def _test_connection(self) -> bool:
        """Probar conexión con MySQL"""
        try:
            with self._get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1 as test")
                    result = cursor.fetchone()
                    return result and result.get('test') == 1
        except Exception as e:
            logger.error(f"❌ Error conectando a MySQL: {e}")
            return False

    @contextmanager
    def _get_connection(self):
        """Context manager para conexiones MySQL"""
        connection = None
        try:
            connection = pymysql.connect(**self.connection_config)
            yield connection
        except Exception as e:
            if connection:
                connection.rollback()
            logger.error(f"❌ Error en conexión MySQL: {e}")
            raise
        finally:
            if connection:
                connection.close()

    def _initialize_database(self) -> bool:
        """Inicializar esquema de base de datos MySQL"""
        try:
            with self._get_connection() as connection:
                with connection.cursor() as cursor:
                    # Crear tabla de estudiantes
                    students_sql = """
                                   CREATE TABLE IF NOT EXISTS estudiantes \
                                   ( \
                                       id \
                                       INT \
                                       AUTO_INCREMENT \
                                       PRIMARY \
                                       KEY, \
                                       nombre \
                                       VARCHAR \
                                   ( \
                                       100 \
                                   ) NOT NULL,
                                       apellidos VARCHAR \
                                   ( \
                                       100 \
                                   ) NOT NULL,
                                       codigo VARCHAR \
                                   ( \
                                       20 \
                                   ) UNIQUE NOT NULL,
                                       correo VARCHAR \
                                   ( \
                                       100 \
                                   ),
                                       requisitoriado BOOLEAN DEFAULT FALSE,
                                       imagen_path VARCHAR \
                                   ( \
                                       500 \
                                   ),
                                       face_encoding JSON,
                                       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                       updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                                       active BOOLEAN DEFAULT TRUE, \
                                       INDEX idx_codigo \
                                   ( \
                                       codigo \
                                   ),
                                       INDEX idx_active \
                                   ( \
                                       active \
                                   ),
                                       INDEX idx_requisitoriado \
                                   ( \
                                       requisitoriado \
                                   )
                                       ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE =utf8mb4_unicode_ci \
                                   """

                    # Crear tabla de logs
                    logs_sql = """
                               CREATE TABLE IF NOT EXISTS recognition_logs \
                               ( \
                                   id \
                                   INT \
                                   AUTO_INCREMENT \
                                   PRIMARY \
                                   KEY, \
                                   found \
                                   BOOLEAN \
                                   NOT \
                                   NULL, \
                                   student_id \
                                   INT, \
                                   similarity \
                                   FLOAT \
                                   NOT \
                                   NULL \
                                   DEFAULT \
                                   0.0, \
                                   confidence \
                                   VARCHAR \
                               ( \
                                   10 \
                               ) NOT NULL,
                                   processing_time FLOAT NOT NULL,
                                   image_path VARCHAR \
                               ( \
                                   500 \
                               ),
                                   ip_address VARCHAR \
                               ( \
                                   45 \
                               ),
                                   user_agent VARCHAR \
                               ( \
                                   500 \
                               ),
                                   timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, \
                                   INDEX idx_timestamp \
                               ( \
                                   timestamp \
                               ),
                                   INDEX idx_found \
                               ( \
                                   found \
                               ),
                                   INDEX idx_student_id \
                               ( \
                                   student_id \
                               ),
                                   FOREIGN KEY \
                               ( \
                                   student_id \
                               ) REFERENCES estudiantes \
                               ( \
                                   id \
                               ) ON DELETE SET NULL
                                   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE =utf8mb4_unicode_ci \
                               """

                    cursor.execute(students_sql)
                    cursor.execute(logs_sql)
                    connection.commit()

            logger.info("✅ Base de datos MySQL inicializada")
            return True

        except Exception as e:
            logger.error(f"❌ Error inicializando MySQL: {e}")
            return False

    def create_student(self, student_data: Dict[str, Any]) -> int:
        """Crear estudiante en MySQL"""
        try:
            with self._get_connection() as connection:
                with connection.cursor() as cursor:
                    sql = """
                          INSERT INTO estudiantes
                          (nombre, apellidos, codigo, correo, requisitoriado, imagen_path, face_encoding)
                          VALUES (%(nombre)s, %(apellidos)s, %(codigo)s, %(correo)s, %(requisitoriado)s, \
                                  %(imagen_path)s, %(face_encoding)s) \
                          """

                    # Preparar datos
                    data = {
                        'nombre': student_data['nombre'],
                        'apellidos': student_data['apellidos'],
                        'codigo': student_data['codigo'],
                        'correo': student_data.get('correo'),
                        'requisitoriado': student_data.get('requisitoriado', False),
                        'imagen_path': student_data.get('imagen_path'),
                        'face_encoding': json.dumps(student_data.get('face_encoding')) if student_data.get(
                            'face_encoding') else None
                    }

                    cursor.execute(sql, data)
                    connection.commit()

                    return cursor.lastrowid

        except Exception as e:
            logger.error(f"❌ Error creando estudiante en MySQL: {e}")
            raise

    def get_all_students(self) -> List[Dict[str, Any]]:
        """Obtener todos los estudiantes activos"""
        try:
            with self._get_connection() as connection:
                with connection.cursor() as cursor:
                    sql = "SELECT * FROM estudiantes WHERE active = TRUE ORDER BY created_at DESC"
                    cursor.execute(sql)
                    students = cursor.fetchall()

                    # Procesar face_encoding JSON
                    for student in students:
                        if student.get('face_encoding'):
                            try:
                                student['face_encoding'] = json.loads(student['face_encoding'])
                            except:
                                student['face_encoding'] = None

                    return students

        except Exception as e:
            logger.error(f"❌ Error obteniendo estudiantes de MySQL: {e}")
            return []

    def get_student_by_id(self, student_id: int) -> Optional[Dict[str, Any]]:
        """Obtener estudiante por ID"""
        try:
            with self._get_connection() as connection:
                with connection.cursor() as cursor:
                    sql = "SELECT * FROM estudiantes WHERE id = %s AND active = TRUE"
                    cursor.execute(sql, (student_id,))
                    student = cursor.fetchone()

                    if student and student.get('face_encoding'):
                        try:
                            student['face_encoding'] = json.loads(student['face_encoding'])
                        except:
                            student['face_encoding'] = None

                    return student

        except Exception as e:
            logger.error(f"❌ Error obteniendo estudiante {student_id} de MySQL: {e}")
            return None

    def get_student_by_codigo(self, codigo: str) -> Optional[Dict[str, Any]]:
        """Obtener estudiante por código"""
        try:
            with self._get_connection() as connection:
                with connection.cursor() as cursor:
                    sql = "SELECT * FROM estudiantes WHERE codigo = %s AND active = TRUE"
                    cursor.execute(sql, (codigo,))
                    student = cursor.fetchone()

                    if student and student.get('face_encoding'):
                        try:
                            student['face_encoding'] = json.loads(student['face_encoding'])
                        except:
                            student['face_encoding'] = None

                    return student

        except Exception as e:
            logger.error(f"❌ Error obteniendo estudiante por código {codigo} de MySQL: {e}")
            return None

    def update_student(self, student_id: int, update_data: Dict[str, Any]) -> bool:
        """Actualizar estudiante en MySQL"""
        try:
            with self._get_connection() as connection:
                with connection.cursor() as cursor:
                    # Construir query dinámicamente
                    fields = []
                    values = []

                    for field, value in update_data.items():
                        if field == 'face_encoding' and value:
                            fields.append("face_encoding = %s")
                            values.append(json.dumps(value))
                        elif value is not None:
                            fields.append(f"{field} = %s")
                            values.append(value)

                    if not fields:
                        return True  # No hay nada que actualizar

                    values.append(student_id)
                    sql = f"UPDATE estudiantes SET {', '.join(fields)} WHERE id = %s"

                    cursor.execute(sql, values)
                    connection.commit()

                    return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"❌ Error actualizando estudiante {student_id} en MySQL: {e}")
            return False

    def delete_student(self, student_id: int) -> bool:
        """Eliminar estudiante (soft delete)"""
        try:
            with self._get_connection() as connection:
                with connection.cursor() as cursor:
                    sql = "UPDATE estudiantes SET active = FALSE WHERE id = %s"
                    cursor.execute(sql, (student_id,))
                    connection.commit()

                    return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"❌ Error eliminando estudiante {student_id} de MySQL: {e}")
            return False

    def create_recognition_log(self, log_data: Dict[str, Any]) -> int:
        """Crear log de reconocimiento en MySQL"""
        try:
            with self._get_connection() as connection:
                with connection.cursor() as cursor:
                    sql = """
                          INSERT INTO recognition_logs
                          (found, student_id, similarity, confidence, processing_time, image_path, ip_address, \
                           user_agent)
                          VALUES (%(found)s, %(student_id)s, %(similarity)s, %(confidence)s, %(processing_time)s, \
                                  %(image_path)s, %(ip_address)s, %(user_agent)s) \
                          """

                    cursor.execute(sql, log_data)
                    connection.commit()

                    return cursor.lastrowid

        except Exception as e:
            logger.error(f"❌ Error creando log en MySQL: {e}")
            raise

    def get_recognition_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de reconocimiento"""
        try:
            with self._get_connection() as connection:
                with connection.cursor() as cursor:
                    stats_sql = """
                                SELECT COUNT(*)                                              as total_recognitions, \
                                       SUM(CASE WHEN found = 1 THEN 1 ELSE 0 END)            as successful_recognitions, \
                                       AVG(processing_time)                                  as avg_processing_time, \
                                       SUM(CASE WHEN confidence = 'Alta' THEN 1 ELSE 0 END)  as high_confidence, \
                                       SUM(CASE WHEN confidence = 'Media' THEN 1 ELSE 0 END) as medium_confidence, \
                                       SUM(CASE WHEN confidence = 'Baja' THEN 1 ELSE 0 END)  as low_confidence
                                FROM recognition_logs \
                                """

                    cursor.execute(stats_sql)
                    stats = cursor.fetchone() or {}

                    total = stats.get('total_recognitions', 0)
                    successful = stats.get('successful_recognitions', 0)

                    return {
                        "total_recognitions": total,
                        "successful_recognitions": successful,
                        "failed_recognitions": total - successful,
                        "success_rate": round((successful / total * 100) if total > 0 else 0, 2),
                        "average_processing_time": round(stats.get('avg_processing_time', 0) or 0, 2),
                        "high_confidence": stats.get('high_confidence', 0),
                        "medium_confidence": stats.get('medium_confidence', 0),
                        "low_confidence": stats.get('low_confidence', 0)
                    }

        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas de MySQL: {e}")
            return {
                "total_recognitions": 0,
                "successful_recognitions": 0,
                "failed_recognitions": 0,
                "success_rate": 0,
                "average_processing_time": 0,
                "high_confidence": 0,
                "medium_confidence": 0,
                "low_confidence": 0
            }

    def test_connection(self) -> bool:
        """Probar conexión con MySQL"""
        return self._test_connection()

    def get_database_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de la base de datos"""
        try:
            with self._get_connection() as connection:
                with connection.cursor() as cursor:
                    # Estadísticas de estudiantes
                    cursor.execute("SELECT COUNT(*) as total FROM estudiantes WHERE active = TRUE")
                    total_students = cursor.fetchone().get('total', 0)

                    cursor.execute(
                        "SELECT COUNT(*) as total FROM estudiantes WHERE active = TRUE AND requisitoriado = TRUE")
                    requisitoriados = cursor.fetchone().get('total', 0)

                    # Estadísticas de reconocimiento
                    cursor.execute("SELECT COUNT(*) as total FROM recognition_logs")
                    total_recognitions = cursor.fetchone().get('total', 0)

                    cursor.execute("SELECT COUNT(*) as total FROM recognition_logs WHERE found = TRUE")
                    successful_recognitions = cursor.fetchone().get('total', 0)

                    return {
                        "total_students": total_students,
                        "requisitoriados": requisitoriados,
                        "total_recognitions": total_recognitions,
                        "successful_recognitions": successful_recognitions,
                        "success_rate": round(
                            (successful_recognitions / total_recognitions * 100) if total_recognitions > 0 else 0,
                            2
                        )
                    }

        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas de base de datos: {e}")
            return {
                "total_students": 0,
                "requisitoriados": 0,
                "total_recognitions": 0,
                "successful_recognitions": 0,
                "success_rate": 0
            }