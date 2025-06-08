from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import os
import logging

from ..models.database import Student, RecognitionLogModel, SystemConfig, is_d1_enabled
from ..models.schemas import StudentCreate, StudentUpdate, RecognitionLog

logger = logging.getLogger(__name__)


class StudentService:
    """Servicio para operaciones CRUD de estudiantes - Compatible con D1 y SQLite"""

    def __init__(self):
        self.use_d1 = is_d1_enabled()

    def create_student(self, db: Session, student_data: StudentCreate) -> Student:
        """Crear un nuevo estudiante"""
        try:
            if self.use_d1:
                return self._create_student_d1(student_data)
            else:
                return self._create_student_sqlite(db, student_data)
        except Exception as e:
            if not self.use_d1:
                db.rollback()
            raise e

    def _create_student_d1(self, student_data: StudentCreate) -> Student:
        """Crear estudiante en Cloudflare D1"""
        try:
            from ..services.cloudflare_d1 import CloudflareD1Service
            d1_service = CloudflareD1Service()

            # Convertir datos a formato D1
            student_dict = {
                "nombre": student_data.nombre,
                "apellidos": student_data.apellidos,
                "codigo": student_data.codigo,
                "correo": student_data.correo,
                "requisitoriado": student_data.requisitoriado,
                "imagen_path": student_data.imagen_path,
                "face_encoding": student_data.face_encoding
            }

            student_id = d1_service.create_student(student_dict)

            # Crear objeto Student para retornar (compatible con el resto del código)
            student = Student(
                id=student_id,
                nombre=student_data.nombre,
                apellidos=student_data.apellidos,
                codigo=student_data.codigo,
                correo=student_data.correo,
                requisitoriado=student_data.requisitoriado,
                imagen_path=student_data.imagen_path,
                face_encoding=student_data.face_encoding,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                active=True
            )

            return student

        except Exception as e:
            logger.error(f"Error creando estudiante en D1: {e}")
            raise

    def _create_student_sqlite(self, db: Session, student_data: StudentCreate) -> Student:
        """Crear estudiante en SQLite"""
        face_encoding = student_data.face_encoding
        if isinstance(face_encoding, list):
            face_encoding = face_encoding

        db_student = Student(
            nombre=student_data.nombre,
            apellidos=student_data.apellidos,
            codigo=student_data.codigo,
            correo=student_data.correo,
            requisitoriado=student_data.requisitoriado,
            imagen_path=student_data.imagen_path,
            face_encoding=face_encoding
        )

        db.add(db_student)
        db.commit()
        db.refresh(db_student)
        return db_student

    def get_student(self, db: Session, student_id: int) -> Optional[Student]:
        """Obtener estudiante por ID"""
        try:
            if self.use_d1:
                return self._get_student_d1(student_id)
            else:
                return db.query(Student).filter(
                    Student.id == student_id,
                    Student.active == True
                ).first()
        except Exception as e:
            logger.error(f"Error obteniendo estudiante {student_id}: {e}")
            return None

    def _get_student_d1(self, student_id: int) -> Optional[Student]:
        """Obtener estudiante desde D1"""
        try:
            from ..services.cloudflare_d1 import CloudflareD1Service
            d1_service = CloudflareD1Service()

            student_data = d1_service.get_student_by_id(student_id)
            if student_data:
                return self._dict_to_student(student_data)
            return None

        except Exception as e:
            logger.error(f"Error obteniendo estudiante D1 {student_id}: {e}")
            return None

    def get_student_by_codigo(self, db: Session, codigo: str) -> Optional[Student]:
        """Obtener estudiante por código"""
        try:
            if self.use_d1:
                return self._get_student_by_codigo_d1(codigo)
            else:
                return db.query(Student).filter(
                    Student.codigo == codigo,
                    Student.active == True
                ).first()
        except Exception as e:
            logger.error(f"Error obteniendo estudiante por código {codigo}: {e}")
            return None

    def _get_student_by_codigo_d1(self, codigo: str) -> Optional[Student]:
        """Obtener estudiante por código desde D1"""
        try:
            from ..services.cloudflare_d1 import CloudflareD1Service
            d1_service = CloudflareD1Service()

            student_data = d1_service.get_student_by_codigo(codigo)
            if student_data:
                return self._dict_to_student(student_data)
            return None

        except Exception as e:
            logger.error(f"Error obteniendo estudiante D1 por código {codigo}: {e}")
            return None

    def get_students(self, db: Session, skip: int = 0, limit: int = 100) -> List[Student]:
        """Obtener lista de estudiantes con paginación"""
        try:
            if self.use_d1:
                return self._get_students_d1(skip, limit)
            else:
                return db.query(Student).filter(
                    Student.active == True
                ).offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Error obteniendo estudiantes: {e}")
            return []

    def _get_students_d1(self, skip: int = 0, limit: int = 100) -> List[Student]:
        """Obtener estudiantes desde D1"""
        try:
            from ..services.cloudflare_d1 import CloudflareD1Service
            d1_service = CloudflareD1Service()

            students_data = d1_service.get_all_students()
            students = [self._dict_to_student(data) for data in students_data]

            # Aplicar paginación manual
            return students[skip:skip + limit]

        except Exception as e:
            logger.error(f"Error obteniendo estudiantes D1: {e}")
            return []

    def get_all_students(self, db: Session) -> List[Student]:
        """Obtener todos los estudiantes activos (para reconocimiento)"""
        try:
            if self.use_d1:
                return self._get_all_students_d1()
            else:
                return db.query(Student).filter(
                    Student.active == True,
                    Student.face_encoding.isnot(None)
                ).all()
        except Exception as e:
            logger.error(f"Error obteniendo todos los estudiantes: {e}")
            return []

    def _get_all_students_d1(self) -> List[Student]:
        """Obtener todos los estudiantes desde D1"""
        try:
            from ..services.cloudflare_d1 import CloudflareD1Service
            d1_service = CloudflareD1Service()

            students_data = d1_service.get_all_students()
            return [self._dict_to_student(data) for data in students_data if data.get('face_encoding')]

        except Exception as e:
            logger.error(f"Error obteniendo todos los estudiantes D1: {e}")
            return []

    def _dict_to_student(self, data: dict) -> Student:
        """Convertir diccionario de D1 a objeto Student"""
        import json

        # Convertir face_encoding de JSON string a lista
        face_encoding = data.get('face_encoding')
        if isinstance(face_encoding, str):
            try:
                face_encoding = json.loads(face_encoding)
            except:
                face_encoding = None

        # Convertir fechas
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except:
                created_at = datetime.utcnow()

        updated_at = data.get('updated_at')
        if isinstance(updated_at, str):
            try:
                updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            except:
                updated_at = datetime.utcnow()

        return Student(
            id=data.get('id'),
            nombre=data.get('nombre'),
            apellidos=data.get('apellidos'),
            codigo=data.get('codigo'),
            correo=data.get('correo'),
            requisitoriado=bool(data.get('requisitoriado', False)),
            imagen_path=data.get('imagen_path'),
            face_encoding=face_encoding,
            created_at=created_at,
            updated_at=updated_at,
            active=bool(data.get('active', True))
        )

    def update_student(self, db: Session, student_id: int, student_data: StudentUpdate) -> Optional[Student]:
        """Actualizar datos de estudiante"""
        try:
            if self.use_d1:
                return self._update_student_d1(student_id, student_data)
            else:
                return self._update_student_sqlite(db, student_id, student_data)
        except Exception as e:
            if not self.use_d1:
                db.rollback()
            raise e

    def _update_student_d1(self, student_id: int, student_data: StudentUpdate) -> Optional[Student]:
        """Actualizar estudiante en D1"""
        try:
            from ..services.cloudflare_d1 import CloudflareD1Service
            d1_service = CloudflareD1Service()

            update_data = student_data.dict(exclude_unset=True)
            success = d1_service.update_student(student_id, update_data)

            if success:
                return self._get_student_d1(student_id)
            return None

        except Exception as e:
            logger.error(f"Error actualizando estudiante D1 {student_id}: {e}")
            return None

    def _update_student_sqlite(self, db: Session, student_id: int, student_data: StudentUpdate) -> Optional[Student]:
        """Actualizar estudiante en SQLite"""
        db_student = self.get_student(db, student_id)
        if not db_student:
            return None

        update_data = student_data.dict(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_student, field):
                setattr(db_student, field, value)

        db_student.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(db_student)
        return db_student

    def delete_student(self, db: Session, student_id: int) -> bool:
        """Eliminar estudiante (soft delete)"""
        try:
            if self.use_d1:
                from ..services.cloudflare_d1 import CloudflareD1Service
                d1_service = CloudflareD1Service()
                return d1_service.delete_student(student_id)
            else:
                db_student = self.get_student(db, student_id)
                if not db_student:
                    return False

                db_student.active = False
                db_student.updated_at = datetime.utcnow()
                db.commit()
                return True

        except Exception as e:
            if not self.use_d1:
                db.rollback()
            raise e

    def count_students(self, db: Session) -> Dict[str, int]:
        """Contar estudiantes por categorías"""
        try:
            if self.use_d1:
                students = self._get_all_students_d1()
                total = len(students)
                requisitoriados = sum(1 for s in students if s.requisitoriado)

                return {
                    "total": total,
                    "activos": total,
                    "requisitoriados": requisitoriados,
                    "regulares": total - requisitoriados
                }
            else:
                total = db.query(Student).filter(Student.active == True).count()
                requisitoriados = db.query(Student).filter(
                    Student.active == True,
                    Student.requisitoriado == True
                ).count()

                return {
                    "total": total,
                    "activos": total,
                    "requisitoriados": requisitoriados,
                    "regulares": total - requisitoriados
                }
        except Exception as e:
            logger.error(f"Error contando estudiantes: {e}")
            return {"total": 0, "activos": 0, "requisitoriados": 0, "regulares": 0}


class LogService:
    """Servicio para logs de reconocimiento - Compatible con D1 y SQLite"""

    def __init__(self):
        self.use_d1 = is_d1_enabled()

    def create_recognition_log(self, db: Session, log_data: RecognitionLog) -> RecognitionLogModel:
        """Crear log de reconocimiento"""
        try:
            if self.use_d1:
                return self._create_log_d1(log_data)
            else:
                return self._create_log_sqlite(db, log_data)
        except Exception as e:
            if not self.use_d1:
                db.rollback()
            raise e

    def _create_log_d1(self, log_data: RecognitionLog) -> RecognitionLogModel:
        """Crear log en D1"""
        try:
            from ..services.cloudflare_d1 import CloudflareD1Service
            d1_service = CloudflareD1Service()

            log_dict = {
                "found": log_data.found,
                "student_id": log_data.student_id,
                "similarity": log_data.similarity,
                "confidence": log_data.confidence,
                "processing_time": log_data.processing_time,
                "image_path": log_data.image_path,
                "ip_address": log_data.ip_address,
                "user_agent": log_data.user_agent
            }

            log_id = d1_service.create_recognition_log(log_dict)

            # Crear objeto para retornar
            return RecognitionLogModel(
                id=log_id,
                found=log_data.found,
                student_id=log_data.student_id,
                similarity=log_data.similarity,
                confidence=log_data.confidence,
                processing_time=log_data.processing_time,
                image_path=log_data.image_path,
                timestamp=datetime.utcnow(),
                ip_address=log_data.ip_address,
                user_agent=log_data.user_agent
            )

        except Exception as e:
            logger.error(f"Error creando log D1: {e}")
            raise

    def _create_log_sqlite(self, db: Session, log_data: RecognitionLog) -> RecognitionLogModel:
        """Crear log en SQLite"""
        db_log = RecognitionLogModel(
            found=log_data.found,
            student_id=log_data.student_id,
            similarity=log_data.similarity,
            confidence=log_data.confidence,
            processing_time=log_data.processing_time,
            image_path=log_data.image_path,
            ip_address=log_data.ip_address,
            user_agent=log_data.user_agent
        )

        db.add(db_log)
        db.commit()
        db.refresh(db_log)
        return db_log

    def get_recognition_stats(self, db: Session) -> Dict[str, Any]:
        """Obtener estadísticas de reconocimiento"""
        try:
            if self.use_d1:
                from ..services.cloudflare_d1 import CloudflareD1Service
                d1_service = CloudflareD1Service()
                return d1_service.get_recognition_stats()
            else:
                # SQLite original
                total_logs = db.query(RecognitionLogModel).count()
                successful = db.query(RecognitionLogModel).filter(
                    RecognitionLogModel.found == True
                ).count()
                failed = total_logs - successful

                avg_time = db.query(func.avg(RecognitionLogModel.processing_time)).scalar() or 0.0

                return {
                    "total_recognitions": total_logs,
                    "successful_recognitions": successful,
                    "failed_recognitions": failed,
                    "success_rate": round((successful / total_logs * 100) if total_logs > 0 else 0, 2),
                    "average_processing_time": round(avg_time, 2)
                }
        except Exception as e:
            logger.error(f"Error obteniendo stats: {e}")
            return {
                "total_recognitions": 0,
                "successful_recognitions": 0,
                "failed_recognitions": 0,
                "success_rate": 0,
                "average_processing_time": 0
            }


class ConfigService:
    """Servicio para configuración del sistema - Compatible con D1 y SQLite"""

    def __init__(self):
        self.use_d1 = is_d1_enabled()

    def get_recognition_threshold(self, db: Session = None) -> float:
        """Obtener umbral de reconocimiento"""
        try:
            if self.use_d1:
                # Para D1, usar variables de entorno
                return float(os.getenv("RECOGNITION_THRESHOLD", "0.8"))
            else:
                # Para SQLite, intentar usar system_config
                if db:
                    config = db.query(SystemConfig).filter(
                        SystemConfig.key == "recognition_threshold"
                    ).first()
                    if config:
                        return float(config.value)
                return float(os.getenv("RECOGNITION_THRESHOLD", "0.8"))
        except Exception as e:
            logger.warning(f"Error obteniendo recognition_threshold: {e}")
            return 0.8

    def get_max_image_size(self, db: Session = None) -> int:
        """Obtener tamaño máximo de imagen"""
        try:
            if self.use_d1:
                return int(os.getenv("MAX_IMAGE_SIZE", "10485760"))
            else:
                if db:
                    config = db.query(SystemConfig).filter(
                        SystemConfig.key == "max_image_size"
                    ).first()
                    if config:
                        return int(config.value)
                return int(os.getenv("MAX_IMAGE_SIZE", "10485760"))
        except Exception as e:
            logger.warning(f"Error obteniendo max_image_size: {e}")
            return 10485760

    def get_allowed_formats(self, db: Session = None) -> List[str]:
        """Obtener formatos permitidos"""
        try:
            if self.use_d1:
                formats_str = os.getenv("ALLOWED_IMAGE_FORMATS", "jpg,jpeg,png,bmp")
                return formats_str.split(",")
            else:
                if db:
                    config = db.query(SystemConfig).filter(
                        SystemConfig.key == "allowed_formats"
                    ).first()
                    if config:
                        return config.value.split(",")
                formats_str = os.getenv("ALLOWED_IMAGE_FORMATS", "jpg,jpeg,png,bmp")
                return formats_str.split(",")
        except Exception as e:
            logger.warning(f"Error obteniendo allowed_formats: {e}")
            return ["jpg", "jpeg", "png", "bmp"]