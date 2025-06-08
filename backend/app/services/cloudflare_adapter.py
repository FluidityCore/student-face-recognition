import os
import logging
from typing import Dict, Any, List, Optional, Union
from sqlalchemy.orm import Session
from fastapi import UploadFile

from .cloudflare_d1 import CloudflareD1Service
from .cloudflare_r2 import CloudflareR2Service
from ..models.database import Student, RecognitionLogModel, SessionLocal
from ..services.database_service import StudentService, LogService

logger = logging.getLogger(__name__)


class CloudflareAdapter:
    """Adaptador unificado para usar Cloudflare D1 + R2 o SQLite + Local"""

    def __init__(self):
        """Inicializar adaptador"""
        self.use_d1 = os.getenv("USE_CLOUDFLARE_D1", "false").lower() == "true"
        self.use_r2 = os.getenv("USE_CLOUDFLARE_R2", "false").lower() == "true"

        # Inicializar servicios
        self.d1_service = CloudflareD1Service() if self.use_d1 else None
        self.r2_service = CloudflareR2Service() if self.use_r2 else None

        # Servicios de fallback (SQLite + Local)
        self.student_service = StudentService()
        self.log_service = LogService()

        # Verificar disponibilidad
        self.d1_available = self.d1_service and self.d1_service.enabled
        self.r2_available = self.r2_service and self.r2_service.is_available()

        # Log de configuración
        logger.info(f"🔧 Cloudflare D1: {'✅ Habilitado' if self.d1_available else '❌ Deshabilitado'}")
        logger.info(f"🔧 Cloudflare R2: {'✅ Habilitado' if self.r2_available else '❌ Deshabilitado'}")

        if self.d1_available:
            self._initialize_d1()

    def _initialize_d1(self) -> bool:
        """Inicializar base de datos D1"""
        try:
            if self.d1_service.test_connection():
                self.d1_service.initialize_database()
                logger.info("✅ Cloudflare D1 inicializado")
                return True
            else:
                logger.error("❌ No se pudo conectar a D1")
                return False
        except Exception as e:
            logger.error(f"❌ Error inicializando D1: {e}")
            return False

    # ==========================================
    # MÉTODOS PARA ESTUDIANTES
    # ==========================================

    def create_student(self, db: Session, student_data: Dict[str, Any], image_file: UploadFile = None) -> Dict[
        str, Any]:
        """Crear estudiante usando D1 + R2 o SQLite + Local"""
        try:
            # 1. Subir imagen si se proporciona
            image_url = None
            if image_file:
                if self.r2_available:
                    # Subir a R2
                    image_url = self.r2_service.upload_image(image_file, "students")
                else:
                    # Guardar localmente
                    from ..utils.image_processing import ImageProcessor
                    image_processor = ImageProcessor()
                    image_url = image_processor.save_image(image_file, "reference")

                student_data["imagen_path"] = image_url

            # 2. Crear estudiante en base de datos
            if self.d1_available:
                # Usar D1
                student_id = self.d1_service.create_student(student_data)
                student = self.d1_service.get_student_by_id(student_id)
                return self._format_student_response(student)
            else:
                # Usar SQLite local
                from ..models.schemas import StudentCreate
                student_create = StudentCreate(**student_data)
                student = self.student_service.create_student(db, student_create)
                return self._format_student_response(student.__dict__)

        except Exception as e:
            logger.error(f"❌ Error creando estudiante: {e}")
            # Limpiar imagen si hubo error
            if image_url:
                if self.r2_available:
                    self.r2_service.delete_file(image_url)
                else:
                    try:
                        os.remove(image_url)
                    except:
                        pass
            raise

    def get_all_students(self, db: Session) -> List[Dict[str, Any]]:
        """Obtener todos los estudiantes"""
        try:
            if self.d1_available:
                students = self.d1_service.get_all_students()
                return [self._format_student_response(s) for s in students]
            else:
                students = self.student_service.get_all_students(db)
                return [self._format_student_response(s.__dict__) for s in students]
        except Exception as e:
            logger.error(f"❌ Error obteniendo estudiantes: {e}")
            return []

    def get_student_by_id(self, db: Session, student_id: int) -> Optional[Dict[str, Any]]:
        """Obtener estudiante por ID"""
        try:
            if self.d1_available:
                student = self.d1_service.get_student_by_id(student_id)
                return self._format_student_response(student) if student else None
            else:
                student = self.student_service.get_student(db, student_id)
                return self._format_student_response(student.__dict__) if student else None
        except Exception as e:
            logger.error(f"❌ Error obteniendo estudiante {student_id}: {e}")
            return None

    def get_student_by_codigo(self, db: Session, codigo: str) -> Optional[Dict[str, Any]]:
        """Obtener estudiante por código"""
        try:
            if self.d1_available:
                student = self.d1_service.get_student_by_codigo(codigo)
                return self._format_student_response(student) if student else None
            else:
                student = self.student_service.get_student_by_codigo(db, codigo)
                return self._format_student_response(student.__dict__) if student else None
        except Exception as e:
            logger.error(f"❌ Error obteniendo estudiante {codigo}: {e}")
            return None

    def update_student(self, db: Session, student_id: int, update_data: Dict[str, Any],
                       image_file: UploadFile = None) -> Optional[Dict[str, Any]]:
        """Actualizar estudiante"""
        try:
            # Obtener estudiante actual
            current_student = self.get_student_by_id(db, student_id)
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
                    new_image = self.r2_service.upload_image(image_file, "students")
                else:
                    from ..utils.image_processing import ImageProcessor
                    image_processor = ImageProcessor()
                    new_image = image_processor.save_image(image_file, "reference")
                
                update_data["imagen_path"] = new_image

            # Actualizar en base de datos
            if self.d1_available:
                success = self.d1_service.update_student(student_id, update_data)
                if success:
                    student = self.d1_service.get_student_by_id(student_id)
                    return self._format_student_response(student)
                return None
            else:
                from ..models.schemas import StudentUpdate
                student_update = StudentUpdate(**update_data)
                student = self.student_service.update_student(db, student_id, student_update)
                return self._format_student_response(student.__dict__) if student else None

        except Exception as e:
            logger.error(f"❌ Error actualizando estudiante {student_id}: {e}")
            raise

    def delete_student(self, db: Session, student_id: int) -> bool:
        """Eliminar estudiante"""
        try:
            # Obtener estudiante para eliminar imagen
            student = self.get_student_by_id(db, student_id)

            # Eliminar de base de datos
            if self.d1_available:
                success = self.d1_service.delete_student(student_id)
            else:
                success = self.student_service.delete_student(db, student_id)

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
            logger.error(f"❌ Error eliminando estudiante {student_id}: {e}")
            return False

    # ==========================================
    # MÉTODOS PARA LOGS DE RECONOCIMIENTO
    # ==========================================

    def create_recognition_log(self, db: Session, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crear log de reconocimiento"""
        try:
            if self.d1_available:
                log_id = self.d1_service.create_recognition_log(log_data)
                return {"id": log_id, "success": True}
            else:
                from ..models.schemas import RecognitionLog
                recognition_log = RecognitionLog(**log_data)
                log = self.log_service.create_recognition_log(db, recognition_log)
                return {"id": log.id, "success": True}
        except Exception as e:
            logger.error(f"❌ Error creando log: {e}")
            return {"success": False, "error": str(e)}

    def get_recognition_stats(self, db: Session) -> Dict[str, Any]:
        """Obtener estadísticas de reconocimiento"""
        try:
            if self.d1_available:
                return self.d1_service.get_recognition_stats()
            else:
                return self.log_service.get_recognition_stats(db)
        except Exception as e:
            logger.error(f"❌ Error obteniendo stats: {e}")
            return {
                "total_recognitions": 0,
                "successful_recognitions": 0,
                "failed_recognitions": 0,
                "success_rate": 0,
                "average_processing_time": 0
            }

    # ==========================================
    # MÉTODOS PARA ALMACENAMIENTO DE IMÁGENES
    # ==========================================

    async def save_recognition_image(self, file: UploadFile) -> str:
        """Guardar imagen de reconocimiento temporal"""
        try:
            if self.r2_available:
                return await self.r2_service.upload_image(file, "recognition")
            else:
                from ..utils.image_processing import ImageProcessor
                image_processor = ImageProcessor()
                return await image_processor.save_image(file, "recognition")
        except Exception as e:
            logger.error(f"❌ Error guardando imagen de reconocimiento: {e}")
            raise

    def delete_temp_image(self, image_path: str) -> bool:
        """Eliminar imagen temporal"""
        try:
            if self.r2_available and image_path.startswith("http"):
                return self.r2_service.delete_file(image_path)
            else:
                try:
                    os.remove(image_path)
                    return True
                except:
                    return False
        except Exception as e:
            logger.error(f"❌ Error eliminando imagen temporal: {e}")
            return False

    def get_storage_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de almacenamiento"""
        try:
            if self.r2_available:
                return self.r2_service.get_bucket_stats()
            else:
                from ..utils.image_processing import ImageProcessor
                image_processor = ImageProcessor()
                return image_processor.get_directory_stats()
        except Exception as e:
            logger.error(f"❌ Error obteniendo stats de almacenamiento: {e}")
            return {}

    # ==========================================
    # MÉTODOS DE MIGRACIÓN
    # ==========================================

    def migrate_to_cloudflare(self, db: Session) -> Dict[str, Any]:
        """Migrar datos desde SQLite local a Cloudflare D1"""
        if not self.d1_available:
            raise Exception("Cloudflare D1 no está disponible")

        try:
            # Obtener datos de SQLite
            students = self.student_service.get_all_students(db)
            logs = self.log_service.get_recognition_logs(db, skip=0, limit=10000)

            # Convertir a diccionarios
            students_data = [self._student_to_dict(s) for s in students]
            logs_data = [self._log_to_dict(l) for l in logs]

            # Migrar a D1
            result = self.d1_service.migrate_from_sqlite(students_data, logs_data)

            logger.info(f"✅ Migración completada: {result}")
            return result

        except Exception as e:
            logger.error(f"❌ Error en migración: {e}")
            raise

    def migrate_images_to_r2(self) -> Dict[str, Any]:
        """Migrar imágenes locales a Cloudflare R2"""
        if not self.r2_available:
            raise Exception("Cloudflare R2 no está disponible")

        try:
            migrated_count = 0
            error_count = 0

            # Obtener todas las imágenes locales
            from ..utils.image_processing import ImageProcessor
            image_processor = ImageProcessor()

            upload_dir = os.getenv("UPLOAD_DIR", "uploads")

            for category in ["reference", "recognition"]:
                category_dir = os.path.join(upload_dir, category)
                if os.path.exists(category_dir):
                    for filename in os.listdir(category_dir):
                        file_path = os.path.join(category_dir, filename)
                        if os.path.isfile(file_path):
                            try:
                                # Leer archivo
                                with open(file_path, 'rb') as f:
                                    content = f.read()

                                # Subir a R2
                                r2_url = self.r2_service.upload_file(content, filename, category)
                                migrated_count += 1

                                logger.info(f"✅ Migrado: {file_path} → {r2_url}")

                            except Exception as e:
                                logger.error(f"❌ Error migrando {file_path}: {e}")
                                error_count += 1

            return {
                "migrated": migrated_count,
                "errors": error_count,
                "success": error_count == 0
            }

        except Exception as e:
            logger.error(f"❌ Error en migración de imágenes: {e}")
            raise

    # ==========================================
    # MÉTODOS AUXILIARES
    # ==========================================

    def _format_student_response(self, student_data: Union[Dict, Any]) -> Dict[str, Any]:
        """Formatear respuesta de estudiante"""
        if isinstance(student_data, dict):
            data = student_data.copy()
        else:
            data = student_data

        # Parsear face_encoding si es string JSON
        if isinstance(data.get("face_encoding"), str):
            try:
                import json
                data["face_encoding"] = json.loads(data["face_encoding"])
            except:
                data["face_encoding"] = None

        return data

    def _student_to_dict(self, student: Student) -> Dict[str, Any]:
        """Convertir modelo Student a diccionario"""
        return {
            "nombre": student.nombre,
            "apellidos": student.apellidos,
            "codigo": student.codigo,
            "correo": student.correo,
            "requisitoriado": student.requisitoriado,
            "imagen_path": student.imagen_path,
            "face_encoding": student.face_encoding,
            "created_at": student.created_at.isoformat() if student.created_at else None,
            "updated_at": student.updated_at.isoformat() if student.updated_at else None,
            "active": student.active
        }

    def _log_to_dict(self, log: RecognitionLogModel) -> Dict[str, Any]:
        """Convertir modelo RecognitionLog a diccionario"""
        return {
            "found": log.found,
            "student_id": log.student_id,
            "similarity": log.similarity,
            "confidence": log.confidence,
            "processing_time": log.processing_time,
            "image_path": log.image_path,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None
        }

    def cleanup_temp_files(self, max_age_hours: int = 24) -> int:
        """Limpiar archivos temporales"""
        try:
            if self.r2_available:
                return self.r2_service.cleanup_old_files("temp", max_age_hours // 24)
            else:
                from ..utils.image_processing import ImageProcessor
                image_processor = ImageProcessor()
                return image_processor.cleanup_temp_files(max_age_hours)
        except Exception as e:
            logger.error(f"❌ Error limpiando archivos: {e}")
            return 0

    def get_system_status(self) -> Dict[str, Any]:
        """Obtener estado del sistema Cloudflare"""
        return {
            "d1_enabled": self.use_d1,
            "d1_available": self.d1_available,
            "r2_enabled": self.use_r2,
            "r2_available": self.r2_available,
            "fallback_mode": not (self.d1_available and self.r2_available),
            "services": {
                "database": "Cloudflare D1" if self.d1_available else "SQLite Local",
                "storage": "Cloudflare R2" if self.r2_available else "Local Storage"
            }
        }