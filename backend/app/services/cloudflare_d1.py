import os
import json
import requests
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CloudflareD1Service:
    """Servicio para interactuar con Cloudflare D1 - FIXED"""

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
            logger.warning("⚠️ Cloudflare D1 no configurado")

    def execute_query(self, sql: str, params: List[Any] = None) -> Dict[str, Any]:
        """Ejecutar query en D1 - VERSIÓN LIMPIA"""
        if not self.enabled:
            raise Exception("Cloudflare D1 no está configurado")

        try:
            payload = {
                "sql": sql,
                "params": params or []
            }

            # ✅ FIX: Solo log críticos, no debugging
            logger.debug(f"D1 Query: {sql[:50]}...")

            response = requests.post(
                f"{self.base_url}/query",
                headers=self.headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()

                if result.get("success"):
                    query_results = result.get("result", [])

                    if query_results and len(query_results) > 0:
                        first_result = query_results[0]

                        if isinstance(first_result, dict) and "results" in first_result:
                            actual_data = first_result["results"]
                            meta_data = first_result.get("meta", {})

                            return {
                                "results": actual_data,
                                "meta": meta_data,
                                "success": True
                            }
                        else:
                            return {
                                "results": [first_result] if first_result else [],
                                "meta": {},
                                "success": True
                            }
                    else:
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
            logger.error(f"❌ Error D1: {e}")
            raise

    def create_student(self, student_data: Dict[str, Any]) -> int:
        """Crear estudiante en D1"""
        sql = """INSERT INTO estudiantes (nombre, apellidos, codigo, correo, requisitoriado, imagen_path, face_encoding, created_at, updated_at, active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

        params = [
            student_data["nombre"],
            student_data["apellidos"],
            student_data["codigo"],
            student_data.get("correo"),
            "true" if student_data.get("requisitoriado", False) else "false",
            student_data.get("imagen_path"),
            json.dumps(student_data.get("face_encoding")) if student_data.get("face_encoding") else None,
            datetime.utcnow().isoformat(),
            datetime.utcnow().isoformat(),
            "true"
        ]

        result = self.execute_query(sql, params)
        return result.get("meta", {}).get("last_row_id")

    def get_all_students(self) -> List[Dict[str, Any]]:
        """Obtener todos los estudiantes de D1"""
        try:
            sql = 'SELECT * FROM estudiantes WHERE active = "true"'
            result = self.execute_query(sql)

            students = []
            if isinstance(result, dict):
                if "results" in result:
                    students = result["results"]
                elif "data" in result:
                    students = result["data"]
                else:
                    if "id" in result:
                        students = [result]

            # ✅ FIX: Solo log el conteo, no los datos
            logger.info(f"D1 students found: {len(students)}")
            return students

        except Exception as e:
            logger.error(f"❌ Error obteniendo estudiantes D1: {e}")
            return []

    def get_student_by_id(self, student_id: int) -> Optional[Dict[str, Any]]:
        """Obtener estudiante por ID"""
        sql = 'SELECT * FROM estudiantes WHERE id = ? AND active = "true"'
        result = self.execute_query(sql, [student_id])
        results = result.get("results", [])
        return results[0] if results else None

    def get_student_by_codigo(self, codigo: str) -> Optional[Dict[str, Any]]:
        """Obtener estudiante por código"""
        sql = 'SELECT * FROM estudiantes WHERE codigo = ? AND active = "true"'
        result = self.execute_query(sql, [codigo])
        results = result.get("results", [])
        return results[0] if results else None

    def update_student(self, student_id: int, update_data: Dict[str, Any]) -> bool:
        """Actualizar estudiante en D1"""
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
        """Eliminar estudiante (soft delete)"""
        sql = 'UPDATE estudiantes SET active = "false", updated_at = ? WHERE id = ?'
        params = [datetime.utcnow().isoformat(), student_id]

        result = self.execute_query(sql, params)
        return result.get("meta", {}).get("changes", 0) > 0

    def create_recognition_log(self, log_data: Dict[str, Any]) -> int:
        """Crear log de reconocimiento en D1"""
        sql = """INSERT INTO recognition_logs (found, student_id, similarity, confidence, processing_time, image_path, ip_address, user_agent, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""

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
            stats_sql = """SELECT COUNT(*) as total_recognitions, SUM(CASE WHEN found = 1 THEN 1 ELSE 0 END) as successful_recognitions, AVG(processing_time) as avg_processing_time, SUM(CASE WHEN confidence = 'Alta' THEN 1 ELSE 0 END) as high_confidence, SUM(CASE WHEN confidence = 'Media' THEN 1 ELSE 0 END) as medium_confidence, SUM(CASE WHEN confidence = 'Baja' THEN 1 ELSE 0 END) as low_confidence FROM recognition_logs"""

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
            logger.error(f"Error stats D1: {e}")
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
        """✅ FIX: Inicializar esquema con SQL limpio"""
        try:
            # ✅ FIX: SQL en una línea sin saltos problemáticos
            students_sql = """CREATE TABLE IF NOT EXISTS estudiantes (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, apellidos TEXT NOT NULL, codigo TEXT UNIQUE NOT NULL, correo TEXT, requisitoriado BOOLEAN DEFAULT FALSE, imagen_path TEXT, face_encoding TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, active BOOLEAN DEFAULT TRUE)"""

            logs_sql = """CREATE TABLE IF NOT EXISTS recognition_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, found BOOLEAN NOT NULL, student_id INTEGER, similarity REAL NOT NULL DEFAULT 0.0, confidence TEXT NOT NULL, processing_time REAL NOT NULL, image_path TEXT, ip_address TEXT, user_agent TEXT, timestamp TEXT NOT NULL)"""

            # ✅ FIX: Índices en una línea
            indexes_sql = [
                "CREATE INDEX IF NOT EXISTS idx_estudiantes_codigo ON estudiantes(codigo)",
                "CREATE INDEX IF NOT EXISTS idx_estudiantes_active ON estudiantes(active)",
                "CREATE INDEX IF NOT EXISTS idx_recognition_logs_timestamp ON recognition_logs(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_recognition_logs_found ON recognition_logs(found)"
            ]

            # Ejecutar con menos logs
            self.execute_query(students_sql)
            self.execute_query(logs_sql)

            for index_sql in indexes_sql:
                self.execute_query(index_sql)

            logger.info("✅ D1 database initialized")
            return True

        except Exception as e:
            logger.error(f"❌ Error init D1: {e}")
            return False

    def test_connection(self) -> bool:
        """Probar conexión con D1"""
        if not self.enabled:
            return False

        try:
            result = self.execute_query("SELECT 1 as test")
            if isinstance(result, dict):
                if "results" in result:
                    test_results = result["results"]
                    return len(test_results) > 0 and test_results[0].get("test") == 1
                else:
                    return result.get("test") == 1
            return False
        except Exception:
            return False