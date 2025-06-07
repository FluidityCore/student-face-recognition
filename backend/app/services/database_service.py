from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ..models.database import Student, RecognitionLogModel, SystemConfig
from ..models.schemas import StudentCreate, StudentUpdate, RecognitionLog


class StudentService:
    """Servicio para operaciones CRUD de estudiantes"""

    def create_student(self, db: Session, student_data: StudentCreate) -> Student:
        """Crear un nuevo estudiante"""
        try:
            # Convertir face_encoding a formato JSON si es necesario
            face_encoding = student_data.face_encoding
            if isinstance(face_encoding, list):
                face_encoding = face_encoding  # Ya está en formato correcto

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

        except Exception as e:
            db.rollback()
            raise e

    def get_student(self, db: Session, student_id: int) -> Optional[Student]:
        """Obtener estudiante por ID"""
        return db.query(Student).filter(
            Student.id == student_id,
            Student.active == True
        ).first()

    def get_student_by_codigo(self, db: Session, codigo: str) -> Optional[Student]:
        """Obtener estudiante por código"""
        return db.query(Student).filter(
            Student.codigo == codigo,
            Student.active == True
        ).first()

    def get_students(self, db: Session, skip: int = 0, limit: int = 100) -> List[Student]:
        """Obtener lista de estudiantes con paginación"""
        return db.query(Student).filter(
            Student.active == True
        ).offset(skip).limit(limit).all()

    def get_all_students(self, db: Session) -> List[Student]:
        """Obtener todos los estudiantes activos (para reconocimiento)"""
        return db.query(Student).filter(
            Student.active == True,
            Student.face_encoding.isnot(None)
        ).all()

    def update_student(self, db: Session, student_id: int, student_data: StudentUpdate) -> Optional[Student]:
        """Actualizar datos de estudiante"""
        try:
            db_student = self.get_student(db, student_id)
            if not db_student:
                return None

            # Actualizar solo los campos proporcionados
            update_data = student_data.dict(exclude_unset=True)

            for field, value in update_data.items():
                if hasattr(db_student, field):
                    setattr(db_student, field, value)

            # Actualizar timestamp
            db_student.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(db_student)
            return db_student

        except Exception as e:
            db.rollback()
            raise e

    def delete_student(self, db: Session, student_id: int) -> bool:
        """Eliminar estudiante (soft delete)"""
        try:
            db_student = self.get_student(db, student_id)
            if not db_student:
                return False

            # Soft delete
            db_student.active = False
            db_student.updated_at = datetime.utcnow()

            db.commit()
            return True

        except Exception as e:
            db.rollback()
            raise e

    def search_students(self, db: Session, query: str, skip: int = 0, limit: int = 100) -> List[Student]:
        """Buscar estudiantes por nombre, apellido o código"""
        search_filter = or_(
            Student.nombre.contains(query),
            Student.apellidos.contains(query),
            Student.codigo.contains(query),
            Student.correo.contains(query) if query else False
        )

        return db.query(Student).filter(
            Student.active == True,
            search_filter
        ).offset(skip).limit(limit).all()

    def get_requisitoriados(self, db: Session) -> List[Student]:
        """Obtener estudiantes requisitoriados"""
        return db.query(Student).filter(
            Student.active == True,
            Student.requisitoriado == True
        ).all()

    def count_students(self, db: Session) -> Dict[str, int]:
        """Contar estudiantes por categorías"""
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


class LogService:
    """Servicio para logs de reconocimiento"""

    def create_recognition_log(self, db: Session, log_data: RecognitionLog) -> RecognitionLogModel:
        """Crear log de reconocimiento"""
        try:
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

        except Exception as e:
            db.rollback()
            raise e

    def get_recognition_logs(self, db: Session, skip: int = 0, limit: int = 50) -> List[RecognitionLogModel]:
        """Obtener logs de reconocimiento"""
        return db.query(RecognitionLogModel).order_by(
            desc(RecognitionLogModel.timestamp)
        ).offset(skip).limit(limit).all()

    def get_recognition_stats(self, db: Session) -> Dict[str, Any]:
        """Obtener estadísticas de reconocimiento"""
        try:
            # Estadísticas básicas
            total_logs = db.query(RecognitionLogModel).count()
            successful = db.query(RecognitionLogModel).filter(
                RecognitionLogModel.found == True
            ).count()
            failed = total_logs - successful

            # Promedio de tiempo de procesamiento
            avg_time = db.query(func.avg(RecognitionLogModel.processing_time)).scalar() or 0.0

            # Estadísticas por confianza
            high_confidence = db.query(RecognitionLogModel).filter(
                RecognitionLogModel.confidence == "Alta"
            ).count()
            medium_confidence = db.query(RecognitionLogModel).filter(
                RecognitionLogModel.confidence == "Media"
            ).count()
            low_confidence = db.query(RecognitionLogModel).filter(
                RecognitionLogModel.confidence == "Baja"
            ).count()

            # Estadísticas de tiempo
            today = datetime.utcnow().date()
            week_ago = datetime.utcnow() - timedelta(days=7)

            recognitions_today = db.query(RecognitionLogModel).filter(
                func.date(RecognitionLogModel.timestamp) == today
            ).count()

            recognitions_week = db.query(RecognitionLogModel).filter(
                RecognitionLogModel.timestamp >= week_ago
            ).count()

            # Último reconocimiento
            last_recognition = db.query(RecognitionLogModel).order_by(
                desc(RecognitionLogModel.timestamp)
            ).first()

            return {
                "total_recognitions": total_logs,
                "successful_recognitions": successful,
                "failed_recognitions": failed,
                "success_rate": round((successful / total_logs * 100) if total_logs > 0 else 0, 2),
                "average_processing_time": round(avg_time, 2),
                "high_confidence": high_confidence,
                "medium_confidence": medium_confidence,
                "low_confidence": low_confidence,
                "recognitions_today": recognitions_today,
                "recognitions_this_week": recognitions_week,
                "last_recognition": last_recognition.timestamp if last_recognition else None
            }

        except Exception as e:
            raise e

    def get_logs_by_student(self, db: Session, student_id: int, limit: int = 10) -> List[RecognitionLogModel]:
        """Obtener logs de un estudiante específico"""
        return db.query(RecognitionLogModel).filter(
            RecognitionLogModel.student_id == student_id
        ).order_by(desc(RecognitionLogModel.timestamp)).limit(limit).all()

    def get_recent_recognitions(self, db: Session, hours: int = 24) -> List[RecognitionLogModel]:
        """Obtener reconocimientos recientes"""
        time_threshold = datetime.utcnow() - timedelta(hours=hours)

        return db.query(RecognitionLogModel).filter(
            RecognitionLogModel.timestamp >= time_threshold
        ).order_by(desc(RecognitionLogModel.timestamp)).all()

    def cleanup_old_logs(self, db: Session, days: int = 30) -> int:
        """Limpiar logs antiguos"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            deleted_count = db.query(RecognitionLogModel).filter(
                RecognitionLogModel.timestamp < cutoff_date
            ).delete()

            db.commit()
            return deleted_count

        except Exception as e:
            db.rollback()
            raise e


class ConfigService:
    """Servicio para configuración del sistema"""

    def get_config(self, db: Session, key: str) -> Optional[SystemConfig]:
        """Obtener configuración por clave"""
        return db.query(SystemConfig).filter(SystemConfig.key == key).first()

    def get_all_configs(self, db: Session) -> List[SystemConfig]:
        """Obtener todas las configuraciones"""
        return db.query(SystemConfig).all()

    def set_config(self, db: Session, key: str, value: str, description: str = None) -> SystemConfig:
        """Establecer o actualizar configuración"""
        try:
            config = self.get_config(db, key)

            if config:
                # Actualizar existente
                config.value = value
                if description:
                    config.description = description
                config.updated_at = datetime.utcnow()
            else:
                # Crear nueva
                config = SystemConfig(
                    key=key,
                    value=value,
                    description=description
                )
                db.add(config)

            db.commit()
            db.refresh(config)
            return config

        except Exception as e:
            db.rollback()
            raise e

    def get_recognition_threshold(self, db: Session) -> float:
        """Obtener umbral de reconocimiento"""
        config = self.get_config(db, "recognition_threshold")
        return float(config.value) if config else 0.8

    def get_max_image_size(self, db: Session) -> int:
        """Obtener tamaño máximo de imagen"""
        config = self.get_config(db, "max_image_size")
        return int(config.value) if config else 10485760  # 10MB

    def get_allowed_formats(self, db: Session) -> List[str]:
        """Obtener formatos de imagen permitidos"""
        config = self.get_config(db, "allowed_formats")
        if config:
            return config.value.split(",")
        return ["jpg", "jpeg", "png", "bmp"]

    def delete_config(self, db: Session, key: str) -> bool:
        """Eliminar configuración"""
        try:
            config = self.get_config(db, key)
            if config:
                db.delete(config)
                db.commit()
                return True
            return False

        except Exception as e:
            db.rollback()
            raise e