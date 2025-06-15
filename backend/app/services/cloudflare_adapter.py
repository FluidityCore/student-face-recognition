import os
import logging
from typing import Dict, Any, List, Optional, Union
from sqlalchemy.orm import Session
from fastapi import UploadFile

from .cloudflare_d1 import CloudflareD1Service
from .cloudflare_r2 import CloudflareR2Service
from .mysql_service import MySQLService
from ..models.database import Student, RecognitionLogModel, SessionLocal

logger = logging.getLogger(__name__)


class CloudflareAdapter:
    """Adaptador unificado con métodos async - FIX"""

    def __init__(self):
        """Inicializar adaptador"""
        self.use_d1 = os.getenv("USE_CLOUDFLARE_D1", "false").lower() == "true"
        self.use_r2 = os.getenv("USE_CLOUDFLARE_R2", "false").lower() == "true"

        # Inicializar servicios
        self.d1_service = CloudflareD1Service() if self.use_d1 else None
        self.r2_service = CloudflareR2Service() if self.use_r2 else None
        self.mysql_service = MySQLService() if not self.use_d1 else None

        # Verificar disponibilidad
        self.d1_available = self.d1_service and self.d1_service.enabled
        self.r2_available = self.r2_service and self.r2_service.is_available()
        self.mysql_available = self.mysql_service and self.mysql_service.enabled

        if self.d1_available:
            self._initialize_d1()
        elif self.mysql_available:
            logger.info("💾 Using MySQL as main database")

    def _initialize_d1(self) -> bool:
        """Inicializar base de datos D1"""
        try:
            if self.d1_service.test_connection():
                self.d1_service.initialize_database()
                logger.info("✅ Cloudflare D1 initialized")
                return True
            else:
                logger.error("❌ Could not connect to D1")
                return False
        except Exception as e:
            logger.error(f"❌ Error initializing D1: {e}")
            return False

    # ==========================================
    # ✅ FIX: MÉTODOS ASYNC PARA ESTUDIANTES
    # ==========================================

    async def create_student_async(self, db: Session, student_data: Dict[str, Any], image_file: UploadFile = None) -> Dict[str, Any]:
        """✅ FIX: Método async para crear estudiante"""
        try:
            # Subir imagen si se proporciona
            image_url = None
            if image_file:
                if self.r2_available:
                    image_url = await self.r2_service.upload_image(image_file, "students")
                else:
                    from ..utils.image_processing import ImageProcessor
                    image_processor = ImageProcessor()
                    image_url = await image_processor.save_image(image_file, "reference")

                student_data["imagen_path"] = image_url

            # Crear estudiante en base de datos
            if self.d1_available:
                student_id = self.d1_service.create_student(student_data)
                student = self.d1_service.get_student_by_id(student_id)

                if student is None:
                    raise Exception(f"Could not retrieve created student with ID {student_id}")

                return self._format_student_response(student)

            elif self.mysql_available:
                student_id = self.mysql_service.create_student(student_data)
                student = self.mysql_service.get_student_by_id(student_id)

                if student is None:
                    raise Exception(f"Could not retrieve created student with ID {student_id}")

                return self._format_student_response(student)

            else:
                raise Exception("No database service available")

        except Exception as e:
            logger.error(f"❌ Error creating student: {e}")
            # Cleanup image if error
            if image_url:
                if self.r2_available:
                    self.r2_service.delete_file(image_url)
                else:
                    try:
                        os.remove(image_url)
                    except:
                        pass
            raise

    async def get_all_students_async(self, db: Session) -> List[Dict[str, Any]]:
        """✅ FIX: Método async para obtener todos los estudiantes"""
        try:
            if self.d1_available:
                students_raw = self.d1_service.get_all_students()
                students = []
                for student_data in students_raw:
                    try:
                        formatted = self._format_student_response(student_data)
                        if formatted:
                            students.append(formatted)
                    except Exception as e:
                        logger.error(f"❌ Error formatting student {student_data}: {e}")
                        continue

                return students

            elif self.mysql_available:
                students_raw = self.mysql_service.get_all_students()
                students = []
                for student_data in students_raw:
                    try:
                        formatted = self._format_student_response(student_data)
                        if formatted:
                            students.append(formatted)
                    except Exception as e:
                        logger.error(f"❌ Error formatting student {student_data}: {e}")
                        continue

                return students

            else:
                logger.error("❌ No database service available")
                return []

        except Exception as e:
            logger.error(f"❌ Error getting students: {e}")
            return []

    async def get_student_by_id_async(self, db: Session, student_id: int) -> Optional[Dict[str, Any]]:
        """✅ FIX: Método async para obtener estudiante por ID"""
        try:
            if self.d1_available:
                student = self.d1_service.get_student_by_id(student_id)
                if student is None:
                    return None
                return self._format_student_response(student)

            elif self.mysql_available:
                student = self.mysql_service.get_student_by_id(student_id)
                if student is None:
                    return None
                return self._format_student_response(student)

            else:
                logger.error("❌ No database service available")
                return None

        except Exception as e:
            logger.error(f"❌ Error getting student {student_id}: {e}")
            return None

    async def get_student_by_codigo_async(self, db: Session, codigo: str) -> Optional[Dict[str, Any]]:
        """✅ FIX: Método async para obtener estudiante por código"""
        try:
            if self.d1_available:
                student = self.d1_service.get_student_by_codigo(codigo)
                if student is None:
                    return None
                return self._format_student_response(student)

            elif self.mysql_available:
                student = self.mysql_service.get_student_by_codigo(codigo)
                if student is None:
                    return None
                return self._format_student_response(student)

            else:
                logger.error("❌ No database service available")
                return None

        except Exception as e:
            logger.error(f"❌ Error getting student by codigo {codigo}: {e}")
            return None

    async def update_student_async(self, db: Session, student_id: int, update_data: Dict[str, Any], image_file: UploadFile = None) -> Optional[Dict[str, Any]]:
        """✅ FIX: Método async para actualizar estudiante"""
        try:
            # Obtener estudiante actual
            current_student = await self.get_student_by_id_async(db, student_id)
            if not current_student:
                return None

            # Actualizar imagen si se proporciona
            if image_file:
                # Eliminar imagen anterior
                old_image = current_student.get("imagen_path")
                if old_image:
                    if self.r2_available:
                        self.r2_service.delete_file(old_image)
                    else:
                        try:
                            os.remove(old_image)
                        except:
                            pass

                # Subir nueva imagen
                if self.r2_available:
                    new_image = await self.r2_service.upload_image(image_file, "students")
                else:
                    from ..utils.image_processing import ImageProcessor
                    image_processor = ImageProcessor()
                    new_image = await image_processor.save_image(image_file, "reference")

                update_data["imagen_path"] = new_image

            # Actualizar en base de datos
            if self.d1_available:
                success = self.d1_service.update_student(student_id, update_data)
                if success:
                    student = self.d1_service.get_student_by_id(student_id)
                    if student is None:
                        logger.error(f"❌ Could not retrieve updated student {student_id}")
                        return None
                    return self._format_student_response(student)
                return None

            elif self.mysql_available:
                success = self.mysql_service.update_student(student_id, update_data)
                if success:
                    student = self.mysql_service.get_student_by_id(student_id)
                    if student is None:
                        logger.error(f"❌ Could not retrieve updated student {student_id}")
                        return None
                    return self._format_student_response(student)
                return None

            else:
                logger.error("❌ No database service available")
                return None

        except Exception as e:
            logger.error(f"❌ Error updating student {student_id}: {e}")
            raise

    async def delete_student_async(self, db: Session, student_id: int) -> bool:
        """✅ FIX: Método async para eliminar estudiante"""
        try:
            # Obtener estudiante para eliminar imagen
            student = await self.get_student_by_id_async(db, student_id)

            # Eliminar de base de datos
            if self.d1_available:
                success = self.d1_service.delete_student(student_id)
            elif self.mysql_available:
                success = self.mysql_service.delete_student(student_id)
            else:
                logger.error("❌ No database service available")
                return False

            # Eliminar imagen si el estudiante fue eliminado exitosamente
            if success and student and student.get("imagen_path"):
                if self.r2_available:
                    self.r2_service.delete_file(student["imagen_path"])
                else:
                    try:
                        os.remove(student["imagen_path"])
                    except:
                        pass

            return success

        except Exception as e:
            logger.error(f"❌ Error deleting student {student_id}: {e}")
            return False

    # ==========================================
    # MÉTODOS SÍNCRONOS ORIGINALES (mantener compatibilidad)
    # ==========================================

    def get_all_students(self, db: Session) -> List[Dict[str, Any]]:
        """Método síncrono original - mantener para compatibilidad"""
        import asyncio
        return asyncio.run(self.get_all_students_async(db))

    def get_student_by_id(self, db: Session, student_id: int) -> Optional[Dict[str, Any]]:
        """Método síncrono original - mantener para compatibilidad"""
        import asyncio
        return asyncio.run(self.get_student_by_id_async(db, student_id))

    def get_student_by_codigo(self, db: Session, codigo: str) -> Optional[Dict[str, Any]]:
        """Método síncrono original - mantener para compatibilidad"""
        import asyncio
        return asyncio.run(self.get_student_by_codigo_async(db, codigo))

    # ==========================================
    # MÉTODOS PARA LOGS DE RECONOCIMIENTO
    # ==========================================

    def create_recognition_log(self, db: Session, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crear log de reconocimiento"""
        try:
            if self.d1_available:
                log_id = self.d1_service.create_recognition_log(log_data)
                return {"id": log_id, "success": True}
            elif self.mysql_available:
                log_id = self.mysql_service.create_recognition_log(log_data)
                return {"id": log_id, "success": True}
            else:
                logger.error("❌ No database service available")
                return {"success": False, "error": "No database service available"}

        except Exception as e:
            logger.error(f"❌ Error creating log: {e}")
            return {"success": False, "error": str(e)}

    def get_recognition_stats(self, db: Session) -> Dict[str, Any]:
        """Obtener estadísticas de reconocimiento"""
        try:
            if self.d1_available:
                return self.d1_service.get_recognition_stats()
            elif self.mysql_available:
                return self.mysql_service.get_recognition_stats()
            else:
                return {
                    "total_recognitions": 0,
                    "successful_recognitions": 0,
                    "failed_recognitions": 0,
                    "success_rate": 0,
                    "average_processing_time": 0
                }
        except Exception as e:
            logger.error(f"❌ Error getting stats: {e}")
            return {
                "total_recognitions": 0,
                "successful_recognitions": 0,
                "failed_recognitions": 0,
                "success_rate": 0,
                "average_processing_time": 0
            }

    # ==========================================
    # MÉTODOS AUXILIARES
    # ==========================================

    def _format_student_response(self, student_data: Union[Dict, Any]) -> Optional[Dict[str, Any]]:
        """Formatear respuesta de estudiante - FIX EMAIL VALIDATION"""
        if student_data is None:
            logger.warning("⚠️ _format_student_response received None")
            return None

        # Verificar que tenemos datos válidos
        if isinstance(student_data, dict):
            data = student_data.copy()
        elif hasattr(student_data, '__dict__'):
            data = student_data.__dict__.copy()
        else:
            logger.error(f"❌ Invalid data type for student: {type(student_data)}")
            return None

        # Verificar campos obligatorios
        required_fields = ['id', 'nombre', 'apellidos', 'codigo']
        missing_fields = [field for field in required_fields if field not in data or data[field] is None]

        if missing_fields:
            logger.error(f"❌ Missing required fields in student: {missing_fields}")
            return None

        # ✅ FIX: Limpiar email antes de validation
        correo = data.get('correo')
        if correo and '@' not in str(correo):
            # Si no es un email válido, convertir a None
            data['correo'] = None
        elif correo:
            # Si es válido, normalizar
            data['correo'] = str(correo).strip().lower()

        # Parsear face_encoding si es string JSON
        if isinstance(data.get("face_encoding"), str):
            try:
                import json
                data["face_encoding"] = json.loads(data["face_encoding"])
            except Exception as e:
                logger.warning(f"⚠️ Error parsing face_encoding: {e}")
                data["face_encoding"] = None

        # Asegurar tipos correctos
        try:
            # Convertir fechas si son strings
            for date_field in ['created_at', 'updated_at']:
                if date_field in data and isinstance(data[date_field], str):
                    try:
                        from datetime import datetime
                        data[date_field] = datetime.fromisoformat(data[date_field].replace('Z', '+00:00'))
                    except:
                        from datetime import datetime
                        data[date_field] = datetime.utcnow()

            # Asegurar valores por defecto
            data.setdefault('active', True)
            data.setdefault('requisitoriado', False)
            data.setdefault('correo', None)
            data.setdefault('imagen_path', None)

            return data

        except Exception as e:
            logger.error(f"❌ Error formatting student data: {e}")
            return None
        
    def get_system_status(self) -> Dict[str, Any]:
        """Obtener estado del sistema"""
        return {
            "d1_enabled": self.use_d1,
            "d1_available": self.d1_available,
            "r2_enabled": self.use_r2,
            "r2_available": self.r2_available,
            "mysql_enabled": not self.use_d1,
            "mysql_available": self.mysql_available,
            "fallback_mode": not (self.d1_available or self.mysql_available),
            "services": {
                "database": "Cloudflare D1" if self.d1_available else "MySQL Local" if self.mysql_available else "None",
                "storage": "Cloudflare R2" if self.r2_available else "Local Storage"
            }
        }