from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import time
import logging
import sys
from contextlib import asynccontextmanager

# Imports locales
from .api import students, recognition
from .models.database import create_tables, test_database_connection
from .services.face_recognition import FaceRecognitionService
from .utils.image_processing import ImageProcessor

# ✅ FIX: CONFIGURACIÓN DE LOGS REDUCIDA PARA RAILWAY
log_level = os.getenv("LOG_LEVEL", "WARNING").upper()  # WARNING por defecto
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(levelname)s - %(message)s',  # Formato más simple
    handlers=[logging.StreamHandler()]
)

# ✅ FIX: Reducir logs de librerías externas
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("boto3").setLevel(logging.WARNING)
logging.getLogger("botocore").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Variables globales para servicios
face_service = None
image_processor = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación - OPTIMIZADO"""
    global face_service, image_processor

    # Startup
    logger.info("🚀 Starting Face Recognition API...")

    try:
        # Verificar conexión a base de datos
        if not test_database_connection():
            logger.error("❌ Database connection failed")
            raise Exception("Database connection failed")

        # Crear tablas si no existen
        create_tables()

        # Inicializar servicios (con menos logs)
        face_service = FaceRecognitionService()
        image_processor = ImageProcessor()

        # Limpiar archivos temporales (solo en producción)
        if os.getenv("DEBUG", "False") != "True":
            deleted_count = image_processor.cleanup_temp_files(max_age_hours=1)
            if deleted_count > 0:
                logger.info(f"🧹 Cleaned {deleted_count} temp files")

        logger.info("✅ API started successfully")

    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
        raise

    yield

    # Shutdown
    logger.info("🔄 Shutting down API...")
    if face_service:
        face_service.cleanup_resources()
    logger.info("✅ API shutdown complete")


# Crear aplicación FastAPI
app = FastAPI(
    title="Student Face Recognition API",
    description="Sistema de reconocimiento facial para estudiantes - Railway Deploy",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """✅ FIX: Middleware con logs mínimos"""
    start_time = time.time()

    # Solo log para errores o requests lentos
    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        # Solo log si hay error o request muy lento
        if response.status_code >= 400:
            logger.warning(f"❌ {request.method} {request.url.path} - Status: {response.status_code}")
        elif process_time > 10.0:  # Solo requests muy lentos
            logger.warning(f"⏱️ SLOW: {request.method} {request.url.path} - {process_time:.1f}s")

        # Headers básicos
        response.headers["X-Process-Time"] = str(round(process_time, 2))
        response.headers["X-Server"] = "Railway"

        return response

    except Exception as e:
        logger.error(f"❌ {request.method} {request.url.path} - Error: {str(e)}")
        raise


# CORS simplificado
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Simplificado para Railway
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# Incluir routers
app.include_router(students.router)
app.include_router(recognition.router)


@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "Student Face Recognition API",
        "version": "1.0.0",
        "status": "active",
        "server": "Railway",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """✅ FIX: Health check simplificado"""
    try:
        db_status = "connected" if test_database_connection() else "disconnected"

        services_ok = all([
            face_service is not None,
            image_processor is not None,
            db_status == "connected"
        ])

        return {
            "status": "healthy" if services_ok else "unhealthy",
            "database": db_status,
            "services": services_ok,
            "version": "1.0.0"
        }

    except Exception as e:
        logger.error(f"❌ Health check error: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@app.get("/info")
async def system_info():
    """✅ FIX: Info simplificado"""
    try:
        from .models.database import get_database_stats, is_d1_enabled

        db_stats = get_database_stats()

        return {
            "version": "1.0.0",
            "server": "Railway",
            "database": {
                **db_stats,
                "d1_enabled": is_d1_enabled()
            },
            "configuration": {
                "r2_enabled": os.getenv("USE_CLOUDFLARE_R2", "false").lower() == "true",
                "threshold": float(os.getenv("RECOGNITION_THRESHOLD", "0.5"))
            }
        }

    except Exception as e:
        return {
            "version": "1.0.0",
            "server": "Railway",
            "error": str(e)
        }


# ✅ FIX: Exception handlers simplificados
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"❌ Global error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "path": str(request.url.path)}
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "path": str(request.url.path)}
    )


# Configuración para Railway
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    host = "0.0.0.0"

    logger.info(f"🚀 Starting server on {host}:{port}")

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=False,
        log_level="warning",  # ✅ FIX: Warning level
        workers=1,
        access_log=False  # ✅ FIX: Disable access log
    )