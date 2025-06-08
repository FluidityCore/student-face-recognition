from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import os
import logging
from dotenv import load_dotenv
from sqlalchemy import text

# Cargar variables de entorno
load_dotenv()

logger = logging.getLogger(__name__)


# CONFIGURACIÓN INTELIGENTE: SQLite O CLOUDFLARE D1
def get_database_configuration():
    """Determinar configuración de base de datos según variables de entorno"""

    # Verificar si Cloudflare D1 está habilitado
    use_d1 = os.getenv("USE_CLOUDFLARE_D1", "false").lower() == "true"

    # Verificar credenciales de D1
    d1_configured = all([
        os.getenv("CLOUDFLARE_ACCOUNT_ID"),
        os.getenv("CLOUDFLARE_API_TOKEN"),
        os.getenv("CLOUDFLARE_D1_DATABASE_ID")
    ])

    if use_d1 and d1_configured:
        logger.info("🌍 Configurando Cloudflare D1 como base de datos principal")
        return {
            "type": "cloudflare_d1",
            "url": "cloudflare://d1",
            "use_d1": True
        }
    else:
        # Fallback a SQLite
        sqlite_url = os.getenv("DATABASE_URL", "sqlite:///./student_recognition.db")
        logger.info(f"💾 Configurando SQLite como base de datos: {sqlite_url}")
        return {
            "type": "sqlite",
            "url": sqlite_url,
            "use_d1": False
        }


# Obtener configuración
db_config = get_database_configuration()
DATABASE_URL = db_config["url"]
USE_CLOUDFLARE_D1 = db_config["use_d1"]

# Configurar engine según el tipo de base de datos
if USE_CLOUDFLARE_D1:
    # Para D1, usamos un engine dummy para SQLAlchemy (solo para modelos)
    # Las operaciones reales las maneja CloudflareD1Service
    engine = create_engine(
        "sqlite:///:memory:",  # Engine temporal para SQLAlchemy
        echo=False,
        connect_args={"check_same_thread": False}
    )
    logger.info("☁️ Engine configurado para Cloudflare D1")
else:
    # SQLite tradicional
    if "sqlite" in DATABASE_URL:
        engine = create_engine(
            DATABASE_URL,
            echo=False,
            connect_args={"check_same_thread": False}
        )
    else:
        engine = create_engine(
            DATABASE_URL,
            echo=False,
            pool_pre_ping=True,
            pool_recycle=300
        )
    logger.info(f"💾 Engine configurado para SQLite: {DATABASE_URL}")

# Crear SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para los modelos
Base = declarative_base()


# Modelo de Estudiante
class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(100), nullable=False, index=True)
    apellidos = Column(String(100), nullable=False, index=True)
    codigo = Column(String(20), unique=True, nullable=False, index=True)
    correo = Column(String(100), nullable=True, index=True)
    requisitoriado = Column(Boolean, default=False, nullable=False)

    # Datos de la imagen y reconocimiento facial
    imagen_path = Column(String(500), nullable=True)
    face_encoding = Column(JSON, nullable=True)  # Compatible con SQLite y D1

    # Metadatos
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    active = Column(Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<Student(id={self.id}, codigo='{self.codigo}', nombre='{self.nombre} {self.apellidos}')>"


# Modelo de Logs de Reconocimiento
class RecognitionLogModel(Base):
    __tablename__ = "recognition_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    found = Column(Boolean, nullable=False)
    student_id = Column(Integer, nullable=True)
    similarity = Column(Float, nullable=False, default=0.0)
    confidence = Column(String(10), nullable=False)
    processing_time = Column(Float, nullable=False)

    # Datos de la imagen procesada
    image_path = Column(String(500), nullable=True)

    # Metadatos
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    def __repr__(self):
        status = "Encontrado" if self.found else "No encontrado"
        return f"<RecognitionLog(id={self.id}, {status}, similarity={self.similarity:.2f})>"


# Modelo de Configuración del Sistema
class SystemConfig(Base):
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    description = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<SystemConfig(key='{self.key}', value='{self.value}')>"


# Función para obtener sesión de base de datos
def get_db() -> Session:
    """
    Dependency para obtener sesión de base de datos
    NOTA: Si usas D1, la lógica de datos debe usar CloudflareD1Service directamente
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Función para crear todas las tablas
def create_tables():
    """
    Crear todas las tablas en la base de datos
    """
    try:
        if USE_CLOUDFLARE_D1:
            # Para D1, usar el servicio específico
            logger.info("🌍 Inicializando tablas en Cloudflare D1...")
            try:
                from ..services.cloudflare_d1 import CloudflareD1Service
                d1_service = CloudflareD1Service()
                if d1_service.enabled:
                    success = d1_service.initialize_database()
                    if success:
                        logger.info("✅ Tablas D1 creadas exitosamente")
                    else:
                        logger.error("❌ Error creando tablas en D1")
                        raise Exception("Error inicializando D1")
                else:
                    logger.error("❌ D1 no está configurado correctamente")
                    raise Exception("D1 no configurado")
            except ImportError:
                logger.error("❌ CloudflareD1Service no disponible")
                raise Exception("D1 Service no disponible")
        else:
            # SQLite tradicional
            logger.info("💾 Creando tablas en SQLite...")
            Base.metadata.create_all(bind=engine)
            logger.info("✅ Tablas SQLite creadas exitosamente")

        # Insertar configuraciones por defecto (solo para SQLite)
        if not USE_CLOUDFLARE_D1:
            _insert_default_configs()

    except Exception as e:
        logger.error(f"❌ Error al crear tablas: {e}")
        raise


def _insert_default_configs():
    """Insertar configuraciones por defecto (solo SQLite)"""
    try:
        db = SessionLocal()
        try:
            # Verificar si ya existen configuraciones
            existing_config = db.query(SystemConfig).first()
            if not existing_config:
                default_configs = [
                    SystemConfig(
                        key="recognition_threshold",
                        value="0.8",
                        description="Umbral de similitud para reconocimiento facial"
                    ),
                    SystemConfig(
                        key="max_image_size",
                        value="10485760",
                        description="Tamaño máximo de imagen en bytes (10MB)"
                    ),
                    SystemConfig(
                        key="allowed_formats",
                        value="jpg,jpeg,png,bmp",
                        description="Formatos de imagen permitidos"
                    ),
                ]

                for config in default_configs:
                    db.add(config)

                db.commit()
                logger.info("✅ Configuraciones por defecto insertadas")
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"⚠️ Error insertando configs por defecto: {e}")


# Función para verificar conexión a la base de datos
def test_database_connection():
    """
    Probar la conexión a la base de datos
    """
    try:
        if USE_CLOUDFLARE_D1:
            # Probar conexión D1
            try:
                from ..services.cloudflare_d1 import CloudflareD1Service
                d1_service = CloudflareD1Service()
                if d1_service.enabled and d1_service.test_connection():
                    logger.info("✅ Conexión a Cloudflare D1 exitosa")
                    return True
                else:
                    logger.error("❌ Error de conexión a Cloudflare D1")
                    return False
            except ImportError:
                logger.error("❌ CloudflareD1Service no disponible")
                return False
        else:
            # Probar conexión SQLite
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db.close()
            logger.info("✅ Conexión a SQLite exitosa")
            return True

    except Exception as e:
        logger.error(f"❌ Error de conexión a la base de datos: {e}")
        return False


# Función para obtener estadísticas de la base de datos
def get_database_stats():
    """
    Obtener estadísticas básicas de la base de datos
    """
    try:
        if USE_CLOUDFLARE_D1:
            # Usar D1 Service para estadísticas
            try:
                from ..services.cloudflare_d1 import CloudflareD1Service
                d1_service = CloudflareD1Service()
                if d1_service.enabled:
                    # Obtener estadísticas desde D1
                    students = d1_service.get_all_students()
                    recognition_stats = d1_service.get_recognition_stats()

                    total_students = len(students)
                    requisitoriados = sum(1 for s in students if s.get('requisitoriado', False))

                    return {
                        "total_students": total_students,
                        "requisitoriados": requisitoriados,
                        "total_recognitions": recognition_stats.get("total_recognitions", 0),
                        "successful_recognitions": recognition_stats.get("successful_recognitions", 0),
                        "success_rate": recognition_stats.get("success_rate", 0)
                    }
                else:
                    return {"error": "D1 no configurado"}
            except ImportError:
                return {"error": "D1 Service no disponible"}
        else:
            # SQLite tradicional
            db = SessionLocal()

            total_students = db.query(Student).filter(Student.active == True).count()
            requisitoriados = db.query(Student).filter(
                Student.active == True,
                Student.requisitoriado == True
            ).count()

            total_recognitions = db.query(RecognitionLogModel).count()
            successful_recognitions = db.query(RecognitionLogModel).filter(
                RecognitionLogModel.found == True
            ).count()

            db.close()

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
        logger.error(f"❌ Error al obtener estadísticas: {e}")
        return {
            "total_students": 0,
            "requisitoriados": 0,
            "total_recognitions": 0,
            "successful_recognitions": 0,
            "success_rate": 0
        }


def get_database_info():
    """
    Obtener información detallada de la base de datos
    """
    try:
        if USE_CLOUDFLARE_D1:
            return {
                "database_type": "Cloudflare D1",
                "database_url": "Cloudflare Edge Database",
                "connection_status": "Connected to D1" if test_database_connection() else "D1 Connection Failed",
                "ready_for_production": True,
                "global_distribution": True,
                "storage_type": "Edge Database"
            }
        else:
            db_url = str(engine.url)
            return {
                "database_type": "SQLite",
                "database_url": db_url.split("///")[-1] if "sqlite" in db_url else "Remote DB",
                "connection_status": "Connected" if test_database_connection() else "Connection Failed",
                "ready_for_production": False,
                "global_distribution": False,
                "storage_type": "Local File"
            }

    except Exception as e:
        return {
            "database_type": "Unknown",
            "connection_status": f"Error: {str(e)}",
            "ready_for_production": False
        }


# Función para obtener tipo de base de datos actual
def get_database_type():
    """Retornar el tipo de base de datos en uso"""
    return "Cloudflare D1" if USE_CLOUDFLARE_D1 else "SQLite"


# Función para verificar si D1 está habilitado
def is_d1_enabled():
    """Verificar si Cloudflare D1 está habilitado"""
    return USE_CLOUDFLARE_D1


if __name__ == "__main__":
    # Script para configurar base de datos
    print("🗄️ Configurador de Base de Datos para Railway + Cloudflare")
    print("=" * 70)

    # Mostrar información
    db_info = get_database_info()
    print(f"📊 Tipo de BD: {db_info['database_type']}")
    print(f"📍 Ubicación: {db_info['database_url']}")
    print(f"🔗 Estado: {db_info['connection_status']}")
    print(f"🌍 Producción: {'✅' if db_info['ready_for_production'] else '❌'}")

    print("\n🔄 Probando conexión...")
    if test_database_connection():
        print("🔄 Creando/verificando tablas...")
        create_tables()

        print(f"\n🎉 ¡Base de datos lista!")
        print(f"📋 Configuración actual:")
        print(f"   - Tipo: {get_database_type()}")
        print(f"   - D1 Habilitado: {'✅' if is_d1_enabled() else '❌'}")
        print(f"   - Estado: Funcionando")
    else:
        print("❌ Error de conexión")