from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import time
import logging
from contextlib import asynccontextmanager

# Imports locales
from .api import students, recognition
from .models.database import create_tables, test_database_connection
from .services.face_recognition import FaceRecognitionService
from .utils.image_processing import ImageProcessor

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Variables globales para servicios
face_service = None
image_processor = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    global face_service, image_processor

    # Startup
    logger.info("🚀 Iniciando API de Reconocimiento Facial...")

    try:
        # Verificar conexión a base de datos
        if not test_database_connection():
            logger.error("❌ No se pudo conectar a la base de datos")
            raise Exception("Database connection failed")

        # Crear tablas si no existen
        create_tables()

        # Inicializar servicios
        face_service = FaceRecognitionService()
        image_processor = ImageProcessor()

        # Limpiar archivos temporales al inicio
        image_processor.cleanup_temp_files(max_age_hours=1)

        logger.info("✅ API iniciada correctamente")

    except Exception as e:
        logger.error(f"❌ Error al iniciar la aplicación: {e}")
        raise

    yield

    # Shutdown
    logger.info("🔄 Cerrando API...")

    if face_service:
        face_service.cleanup_resources()

    logger.info("✅ API cerrada correctamente")


# Crear aplicación FastAPI
app = FastAPI(
    title="API de Reconocimiento Facial de Estudiantes",
    description="""
    Sistema de reconocimiento facial para identificación de estudiantes.

    ## Características principales:
    - Reconocimiento facial con MediaPipe
    - Gestión completa de estudiantes (CRUD)
    - Logs y estadísticas de reconocimiento
    - Umbral de reconocimiento configurable (80%)
    - Procesamiento optimizado de imágenes

    ## Endpoints principales:
    - `/api/recognize` - Reconocer estudiante por imagen
    - `/api/students` - Gestión de estudiantes
    - `/api/recognition/stats` - Estadísticas del sistema
    """,
    version="1.0.0",
    contact={
        "name": "Sistema de Reconocimiento Facial",
        "email": "admin@universidad.edu"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React frontend
        "http://10.0.2.2:8000",  # Android emulator
        "http://localhost:8000",  # Local development
        os.getenv("FRONTEND_URL", "http://localhost:3000"),
        os.getenv("MOBILE_APP_URL", "http://10.0.2.2:8000")
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Middleware de hosts confiables
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # En producción, especificar hosts específicos
)


# Middleware personalizado para logging y métricas
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware para logging de requests"""
    start_time = time.time()

    # Log request
    logger.info(f"📥 {request.method} {request.url.path} - IP: {request.client.host}")

    try:
        response = await call_next(request)

        # Calcular tiempo de procesamiento
        process_time = time.time() - start_time

        # Log response
        logger.info(
            f"📤 {request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.2f}s"
        )

        # Agregar header de tiempo de procesamiento
        response.headers["X-Process-Time"] = str(process_time)

        return response

    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"❌ {request.method} {request.url.path} - Error: {str(e)} - Time: {process_time:.2f}s")
        raise


# Incluir routers
app.include_router(students.router)
app.include_router(recognition.router)


# Endpoints raíz
@app.get("/")
async def root():
    """Endpoint raíz con información de la API"""
    return {
        "message": "API de Reconocimiento Facial de Estudiantes",
        "version": "1.0.0",
        "status": "active",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "health": "/health",
            "students": "/api/students",
            "recognize": "/api/recognize",
            "stats": "/api/recognition/stats"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Verificar base de datos
        db_status = "connected" if test_database_connection() else "disconnected"

        # Verificar servicios
        services_status = {
            "face_recognition": face_service is not None,
            "image_processor": image_processor is not None,
            "database": db_status == "connected"
        }

        overall_status = "healthy" if all(services_status.values()) else "unhealthy"

        return {
            "status": overall_status,
            "timestamp": time.time(),
            "services": services_status,
            "database": db_status,
            "version": "1.0.0"
        }

    except Exception as e:
        logger.error(f"❌ Error en health check: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }


@app.get("/info")
async def system_info():
    """Información del sistema"""
    try:
        from .models.database import get_database_stats
        from .services.database_service import ConfigService
        from .models.database import SessionLocal

        # Obtener estadísticas
        db_stats = get_database_stats()

        # Obtener configuración
        db = SessionLocal()
        config_service = ConfigService()

        recognition_threshold = config_service.get_recognition_threshold(db)
        max_image_size = config_service.get_max_image_size(db)
        allowed_formats = config_service.get_allowed_formats(db)

        db.close()

        # Estadísticas de almacenamiento
        storage_stats = image_processor.get_directory_stats() if image_processor else {}

        return {
            "system": {
                "version": "1.0.0",
                "status": "active",
                "recognition_threshold": recognition_threshold,
                "max_image_size_mb": round(max_image_size / (1024 * 1024), 2),
                "allowed_formats": allowed_formats
            },
            "database": db_stats,
            "storage": storage_stats,
            "configuration": {
                "debug": os.getenv("DEBUG", "False") == "True",
                "api_host": os.getenv("API_HOST", "0.0.0.0"),
                "api_port": os.getenv("API_PORT", "8000")
            }
        }

    except Exception as e:
        logger.error(f"❌ Error al obtener info del sistema: {e}")
        raise HTTPException(status_code=500, detail=f"Error del sistema: {str(e)}")


@app.get("/admin/cleanup")
async def cleanup_temp_files(max_age_hours: int = 24):
    """Endpoint administrativo para limpiar archivos temporales"""
    try:
        if not image_processor:
            raise HTTPException(status_code=503, detail="Image processor no disponible")

        deleted_count = image_processor.cleanup_temp_files(max_age_hours)

        return {
            "message": "Limpieza completada",
            "deleted_files": deleted_count,
            "max_age_hours": max_age_hours
        }

    except Exception as e:
        logger.error(f"❌ Error en limpieza: {e}")
        raise HTTPException(status_code=500, detail=f"Error en limpieza: {str(e)}")


# Manejo global de excepciones
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Manejo global de excepciones"""
    logger.error(f"❌ Excepción no manejada: {str(exc)} - URL: {request.url}")

    return JSONResponse(
        status_code=500,
        content={
            "error": "Error interno del servidor",
            "detail": "Ha ocurrido un error inesperado",
            "path": str(request.url.path),
            "method": request.method
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Manejo de HTTPExceptions"""
    logger.warning(f"⚠️ HTTP Exception: {exc.status_code} - {exc.detail} - URL: {request.url}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url.path),
            "method": request.method
        }
    )


# Montar archivos estáticos (opcional, para servir imágenes)
if os.path.exists("uploads"):
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

if __name__ == "__main__":
    import uvicorn

    # Configuración para desarrollo
    uvicorn.run(
        "app.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=os.getenv("DEBUG", "True") == "True",
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )