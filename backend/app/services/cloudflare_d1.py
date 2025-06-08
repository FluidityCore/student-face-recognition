import os
import json
import requests
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CloudflareD1Service:
    """Servicio para interactuar con Cloudflare D1"""

    def __init__(self):
        """Inicializar servicio D1"""
        self.account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        self.api_token = os.getenv("CLOUDFLARE_API_TOKEN")
        self.database_id = os.getenv("CLOUDFLARE_D1_DATABASE_ID")
        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/d1/database/{self.database_id}"

        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

        self.enabled = all([self.account_id, self.api_token, self.database_id])

        if self.enabled:
            logger.info("✅ Cloudflare D1 configurado")
        else:
            logger.warning("⚠️ Cloudflare D1 no configurado - usando SQLite local")

    def execute_query(self, sql: str, params: List[Any] = None) -> Dict[str, Any]:
        """Ejecutar query en D1 - VERSIÓN CORREGIDA"""
        if not self.enabled:
            raise Exception("Cloudflare D1 no está configurado")

        try:
            payload = {
                "sql": sql,
                "params": params or []
            }

            logger.info(f"🔍 Ejecutando query D1: {sql}")
            if params:
                logger.info(f"📊 Parámetros: {params}")

            response = requests.post(
                f"{self.base_url}/query",
                headers=self.headers,
                json=payload,
                timeout=30
            )

            logger.info(f"📡 Response status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                logger.info(f"📊 Full response structure: {result}")

                if result.get("success"):
                    # ✅ FIX CRÍTICO: Extraer datos correctamente de la estructura anidada
                    query_results = result.get("result", [])
                    logger.info(f"📊 query_results length: {len(query_results)}")

                    if query_results and len(query_results) > 0:
                        # La estructura real es: result[0].results
                        first_result = query_results[0]
                        logger.info(f"📊 first_result structure: {first_result}")

                        if isinstance(first_result, dict) and "results" in first_result:
                            actual_data = first_result["results"]
                            meta_data = first_result.get("meta", {})

                            logger.info(
                                f"✅ Extracted data: {len(actual_data) if isinstance(actual_data, list) else 'not list'} items")
                            logger.info(
                                f"📊 Sample data: {actual_data[:2] if isinstance(actual_data, list) else actual_data}")

                            # Retornar en formato consistente
                            return {
                                "results": actual_data,
                                "meta": meta_data,
                                "success": True
                            }
                        else:
                            # Fallback si la estructura es diferente
                            logger.warning(f"⚠️ Estructura inesperada en first_result: {type(first_result)}")
                            return {
                                "results": [first_result] if first_result else [],
                                "meta": {},
                                "success": True
                            }
                    else:
                        # Sin resultados
                        logger.info("📊 No query results found")
                        return {
                            "results": [],
                            "meta": {},
                            "success": True
                        }
                else:
                    raise Exception(f"D1 Error: {result.get('errors', 'Unknown error')}")
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")

        except Exception as e:
            logger.error(f"❌ Error ejecutando query D1: {e}")
            raise

    def create_student(self, student_data: Dict[str, Any]) -> int:
        """Crear estudiante en D1 - FIX con string booleans"""
        sql = """
              INSERT INTO estudiantes (nombre, apellidos, codigo, correo, requisitoriado, imagen_path, face_encoding,
                                       created_at, updated_at, active)
              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
              """

        params = [
            student_data["nombre"],
            student_data["apellidos"],
            student_data["codigo"],
            student_data.get("correo"),
            "true" if student_data.get("requisitoriado", False) else "false",  # ✅ FIX: String boolean
            student_data.get("imagen_path"),
            json.dumps(student_data.get("face_encoding")) if student_data.get("face_encoding") else None,
            datetime.utcnow().isoformat(),
            datetime.utcnow().isoformat(),
            "true"  # ✅ FIX: String boolean
        ]

        result = self.execute_query(sql, params)
        return result.get("meta", {}).get("last_row_id")

    def get_all_students(self) -> List[Dict[str, Any]]:
        """
        ✅ FIX FINAL: Obtener todos los estudiantes de D1 con tipos correctos
        """
        try:
            # ✅ FIX: D1 guarda booleanos como strings "true"/"false"
            sql = 'SELECT * FROM estudiantes WHERE active = "true"'
            logger.info("🔍 Ejecutando get_all_students en D1 con string boolean...")

            result = self.execute_query(sql)

            # ✅ FIX: Verificar la estructura de respuesta
            logger.info(f"📊 Raw D1 response: {result}")

            students = []

            if isinstance(result, dict):
                if "results" in result:
                    students = result["results"]
                elif "data" in result:
                    students = result["data"]
                else:
                    # Si result tiene datos directamente
                    if "id" in result:  # Es un solo estudiante
                        students = [result]
                    else:
                        students = []
            elif isinstance(result, list):
                students = result
            else:
                logger.warning(f"⚠️ Formato de respuesta D1 no reconocido: {type(result)}")
                students = []

            logger.info(f"✅ Estudiantes obtenidos de D1: {len(students)}")

            # ✅ FIX: Log de muestra para debugging
            if students:
                logger.info(f"📊 Muestra de estudiante: {students[0]}")
            else:
                logger.warning("⚠️ No se encontraron estudiantes en D1")

                # ✅ FIX: Verificar diferentes queries si falló
                try:
                    # Probar sin filtro active
                    count_result = self.execute_query("SELECT COUNT(*) as count FROM estudiantes")
                    total_count = count_result.get("results", [{}])[0].get("count", 0)
                    logger.info(f"📊 Total estudiantes en tabla: {total_count}")

                    if total_count > 0:
                        # Probar con active=1 (numérico)
                        logger.info("🔄 Probando active=1 (numérico)...")
                        numeric_result = self.execute_query("SELECT * FROM estudiantes WHERE active = 1 LIMIT 3")
                        logger.info(f"📊 Query numérica: {numeric_result}")

                        # Probar sin filtro active
                        logger.info("🔄 Probando sin filtro active...")
                        all_result = self.execute_query("SELECT * FROM estudiantes LIMIT 3")
                        logger.info(f"📊 Query sin filtro: {all_result}")

                        # Si encontramos datos sin filtro, los retornamos
                        if isinstance(all_result, dict) and "results" in all_result:
                            students = all_result["results"]
                            logger.info(f"✅ Datos encontrados sin filtro: {len(students)}")

                except Exception as e:
                    logger.error(f"❌ Error verificando tabla: {e}")

            return students

        except Exception as e:
            logger.error(f"❌ Error al obtener estudiantes de D1: {e}")
            return []

    def get_student_by_id(self, student_id: int) -> Optional[Dict[str, Any]]:
        """Obtener estudiante por ID - FIX con string boolean"""
        sql = 'SELECT * FROM estudiantes WHERE id = ? AND active = "true"'
        result = self.execute_query(sql, [student_id])
        results = result.get("results", [])
        return results[0] if results else None

    def get_student_by_codigo(self, codigo: str) -> Optional[Dict[str, Any]]:
        """Obtener estudiante por código - FIX con string boolean"""
        sql = 'SELECT * FROM estudiantes WHERE codigo = ? AND active = "true"'
        result = self.execute_query(sql, [codigo])
        results = result.get("results", [])
        return results[0] if results else None

    def update_student(self, student_id: int, update_data: Dict[str, Any]) -> bool:
        """Actualizar estudiante en D1"""
        # Construir query dinámicamente
        fields = []
        params = []

        for field, value in update_data.items():
            if field == "face_encoding" and value:
                fields.append("face_encoding = ?")
                params.append(json.dumps(value))
            elif value is not None:
                fields.append(f"{field} = ?")
                params.append(value)

        fields.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())
        params.append(student_id)

        sql = f"UPDATE estudiantes SET {', '.join(fields)} WHERE id = ?"

        result = self.execute_query(sql, params)
        return result.get("meta", {}).get("changes", 0) > 0

    def delete_student(self, student_id: int) -> bool:
        """Eliminar estudiante (soft delete) - FIX con string boolean"""
        sql = 'UPDATE estudiantes SET active = "false", updated_at = ? WHERE id = ?'  # ✅ FIX: String boolean
        params = [datetime.utcnow().isoformat(), student_id]

        result = self.execute_query(sql, params)
        return result.get("meta", {}).get("changes", 0) > 0

    def create_recognition_log(self, log_data: Dict[str, Any]) -> int:
        """Crear log de reconocimiento en D1"""
        sql = """
              INSERT INTO recognition_logs (found, student_id, similarity, confidence, processing_time, image_path,
                                            ip_address, user_agent, timestamp)
              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
              """

        params = [
            log_data["found"],
            log_data.get("student_id"),
            log_data["similarity"],
            log_data["confidence"],
            log_data["processing_time"],
            log_data.get("image_path"),
            log_data.get("ip_address"),
            log_data.get("user_agent"),
            datetime.utcnow().isoformat()
        ]

        result = self.execute_query(sql, params)
        return result.get("meta", {}).get("last_row_id")

    def get_recognition_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de reconocimiento"""
        try:
            # Query para estadísticas básicas
            stats_sql = """
                        SELECT COUNT(*)                                              as total_recognitions,
                               SUM(CASE WHEN found = 1 THEN 1 ELSE 0 END)            as successful_recognitions,
                               AVG(processing_time)                                  as avg_processing_time,
                               SUM(CASE WHEN confidence = 'Alta' THEN 1 ELSE 0 END)  as high_confidence,
                               SUM(CASE WHEN confidence = 'Media' THEN 1 ELSE 0 END) as medium_confidence,
                               SUM(CASE WHEN confidence = 'Baja' THEN 1 ELSE 0 END)  as low_confidence
                        FROM recognition_logs
                        """

            result = self.execute_query(stats_sql)
            stats = result.get("results", [{}])[0]

            total = stats.get("total_recognitions", 0)
            successful = stats.get("successful_recognitions", 0)

            return {
                "total_recognitions": total,
                "successful_recognitions": successful,
                "failed_recognitions": total - successful,
                "success_rate": round((successful / total * 100) if total > 0 else 0, 2),
                "average_processing_time": round(stats.get("avg_processing_time", 0) or 0, 2),
                "high_confidence": stats.get("high_confidence", 0),
                "medium_confidence": stats.get("medium_confidence", 0),
                "low_confidence": stats.get("low_confidence", 0)
            }

        except Exception as e:
            logger.error(f"Error obteniendo stats de D1: {e}")
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

    def initialize_database(self) -> bool:
        """Inicializar esquema de base de datos en D1"""
        try:
            # Crear tabla de estudiantes
            students_sql = """
                           CREATE TABLE IF NOT EXISTS estudiantes
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               nombre
                               TEXT
                               NOT
                               NULL,
                               apellidos
                               TEXT
                               NOT
                               NULL,
                               codigo
                               TEXT
                               UNIQUE
                               NOT
                               NULL,
                               correo
                               TEXT,
                               requisitoriado
                               BOOLEAN
                               DEFAULT
                               FALSE,
                               imagen_path
                               TEXT,
                               face_encoding
                               TEXT,
                               created_at
                               TEXT
                               NOT
                               NULL,
                               updated_at
                               TEXT
                               NOT
                               NULL,
                               active
                               BOOLEAN
                               DEFAULT
                               TRUE
                           )
                           """

            # Crear tabla de logs
            logs_sql = """
                       CREATE TABLE IF NOT EXISTS recognition_logs
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           found
                           BOOLEAN
                           NOT
                           NULL,
                           student_id
                           INTEGER,
                           similarity
                           REAL
                           NOT
                           NULL
                           DEFAULT
                           0.0,
                           confidence
                           TEXT
                           NOT
                           NULL,
                           processing_time
                           REAL
                           NOT
                           NULL,
                           image_path
                           TEXT,
                           ip_address
                           TEXT,
                           user_agent
                           TEXT,
                           timestamp
                           TEXT
                           NOT
                           NULL
                       )
                       """

            # Crear índices
            indexes_sql = [
                "CREATE INDEX IF NOT EXISTS idx_estudiantes_codigo ON estudiantes(codigo)",
                "CREATE INDEX IF NOT EXISTS idx_estudiantes_active ON estudiantes(active)",
                "CREATE INDEX IF NOT EXISTS idx_recognition_logs_timestamp ON recognition_logs(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_recognition_logs_found ON recognition_logs(found)"
            ]

            # Ejecutar todas las queries
            self.execute_query(students_sql)
            self.execute_query(logs_sql)

            for index_sql in indexes_sql:
                self.execute_query(index_sql)

            logger.info("✅ Base de datos D1 inicializada")
            return True

        except Exception as e:
            logger.error(f"❌ Error inicializando D1: {e}")
            return False

    def test_connection(self) -> bool:
        """Probar conexión con D1"""
        if not self.enabled:
            return False

        try:
            result = self.execute_query("SELECT 1 as test")
            # ✅ FIX: Verificar respuesta correctamente
            if isinstance(result, dict):
                if "results" in result:
                    test_results = result["results"]
                    return len(test_results) > 0 and test_results[0].get("test") == 1
                else:
                    return result.get("test") == 1
            return False
        except Exception as e:
            logger.error(f"❌ Error en test_connection: {e}")
            return False

    def migrate_from_sqlite(self, sqlite_students: List[Dict], sqlite_logs: List[Dict]) -> Dict[str, int]:
        """Migrar datos desde SQLite local a D1"""
        try:
            migrated_students = 0
            migrated_logs = 0

            # Migrar estudiantes
            for student in sqlite_students:
                try:
                    self.create_student(student)
                    migrated_students += 1
                except Exception as e:
                    logger.error(f"Error migrando estudiante {student.get('codigo')}: {e}")

            # Migrar logs
            for log in sqlite_logs:
                try:
                    self.create_recognition_log(log)
                    migrated_logs += 1
                except Exception as e:
                    logger.error(f"Error migrando log: {e}")

            logger.info(f"✅ Migración completada: {migrated_students} estudiantes, {migrated_logs} logs")

            return {
                "students": migrated_students,
                "logs": migrated_logs
            }

        except Exception as e:
            logger.error(f"❌ Error en migración: {e}")
            raise