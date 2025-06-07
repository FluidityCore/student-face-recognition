from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import os
from dotenv import load_dotenv
from sqlalchemy import text

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3307")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "root")
DB_NAME = os.getenv("DB_NAME", "student_recognition")

# URL de conexión
DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Crear engine de SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Cambiar a True para ver las queries SQL
    pool_pre_ping=True,  # Verificar conexión antes de usar
    pool_recycle=300  # Reciclar conexiones cada 5 minutos
)

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
    face_encoding = Column(JSON, nullable=True)  # Almacenar como JSON

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
    student_id = Column(Integer, nullable=True)  # FK a students, pero no forzado
    similarity = Column(Float, nullable=False, default=0.0)
    confidence = Column(String(10), nullable=False)  # "Alta", "Media", "Baja"
    processing_time = Column(Float, nullable=False)  # Tiempo en segundos

    # Datos de la imagen procesada
    image_path = Column(String(500), nullable=True)

    # Metadatos
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    ip_address = Column(String(45), nullable=True)  # IPv4 o IPv6
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
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas creadas exitosamente")

        # Insertar configuraciones por defecto
        db = SessionLocal()
        try:
            # Verificar si ya existen configuraciones
            existing_config = db.query(SystemConfig).first()
            if not existing_config:
                default_configs = [
                    SystemConfig(
                        key="recognition_threshold",
                        value="0.9",
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
                print("✅ Configuraciones por defecto insertadas")
        finally:
            db.close()

    except Exception as e:
        print(f"❌ Error al crear tablas: {e}")
        raise


# Función para verificar conexión a la base de datos
def test_database_connection():
    """
    Probar la conexión a la base de datos
    """
    try:
        db = SessionLocal()
        # Ejecutar una query simple
        db.execute(text("SELECT 1"))
        db.close()
        print("✅ Conexión a la base de datos exitosa")
        return True
    except Exception as e:
        print(f"❌ Error de conexión a la base de datos: {e}")
        return False

# Función para obtener estadísticas de la base de datos
def get_database_stats():
    """
    Obtener estadísticas básicas de la base de datos
    """
    try:
        db = SessionLocal()

        # Contar estudiantes
        total_students = db.query(Student).filter(Student.active == True).count()
        requisitoriados = db.query(Student).filter(
            Student.active == True,
            Student.requisitoriado == True
        ).count()

        # Contar logs de reconocimiento
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
        print(f"❌ Error al obtener estadísticas: {e}")
        return None


if __name__ == "__main__":
    # Script para crear tablas y probar conexión
    print("🔄 Probando conexión a la base de datos...")
    if test_database_connection():
        print("🔄 Creando tablas...")
        create_tables()
        print("✅ ¡Base de datos configurada correctamente!")
    else:
        print("❌ No se pudo conectar a la base de datos")