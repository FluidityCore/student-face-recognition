from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import time
import logging
import sys
import traceback
from contextlib import asynccontextmanager

# Imports locales
from .api import students, recognition
from .models.database import create_tables, test_database_connection
from .services.face_recognition import FaceRecognitionService
from .utils.image_processing import ImageProcessor

# Configurar logging para servidor
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Para logs en consola (Railway)
    ]
)
logger = logging.getLogger(__name__)

# Variables globales para servicios
face_service = None
image_processor = None

# Intentar importar psutil, si no está disponible, continuar sin él
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("⚠️ psutil no disponible, continuando sin monitoring de memoria")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    global face_service, image_processor

    # Startup
    logger.info("🚀 Iniciando API de Reconocimiento Facial en SERVIDOR...")
    logger.info(f"🌍 Entorno: {'PRODUCCIÓN' if not os.getenv('DEBUG', 'False') == 'True' else 'DESARROLLO'}")
    logger.info(f"🗄️ Base de datos: {os.getenv('DATABASE_URL', 'SQLite local')[:50]}...")

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

        # Limpiar archivos temporales al inicio (solo en servidor)
        if not os.getenv("DEBUG", "False") == "True":
            deleted_count = image_processor.cleanup_temp_files(max_age_hours=1)
            logger.info(f"🧹 Archivos temporales limpiados: {deleted_count}")

        # Verificar configuración de Cloudflare (si está habilitado)
        if os.getenv("USE_CLOUDFLARE_R2", "false").lower() == "true":
            logger.info("☁️ Cloudflare R2 configurado para almacenamiento")
        else:
            logger.info("💾 Almacenamiento local configurado")

        logger.info("✅ API iniciada correctamente en servidor")

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

    **🚀 Versión para Servidor - Railway + Cloudflare**

    ## Características principales:
    - Reconocimiento facial con face_recognition library
    - Gestión completa de estudiantes (CRUD)
    - Logs y estadísticas de reconocimiento
    - Umbral de reconocimiento configurable (80%)
    - Procesamiento optimizado de imágenes
    - Almacenamiento en Cloudflare R2
    - Base de datos SQLite + Cloudflare D1

    ## Endpoints principales:
    - `/api/recognize` - Reconocer estudiante por imagen
    - `/api/students` - Gestión de estudiantes
    - `/api/recognition/stats` - Estadísticas del sistema
    - `/health` - Health check del servidor
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
    lifespan=lifespan,
    # Configuración para servidor
    docs_url="/docs" if os.getenv("DEBUG", "False") == "True" else "/docs",
    redoc_url="/redoc" if os.getenv("DEBUG", "False") == "True" else "/redoc"
)


# ========================================
# DEBUG MIDDLEWARE PARA RAILWAY - DEBE IR PRIMERO
# ========================================

@app.middleware("http")
async def railway_debug_middleware(request: Request, call_next):
    """Debug middleware específico para Railway - DEBE IR PRIMERO"""
    try:
        # Log básico del request
        print(f"🔍 RAILWAY DEBUG: {request.method} {request.url.path}")
        print(f"🔍 Client: {request.client.host if request.client else 'unknown'}")
        print(f"🔍 User-Agent: {request.headers.get('user-agent', 'unknown')}")
        sys.stdout.flush()  # Forzar flush de stdout

        # Memoria antes del request (si psutil está disponible)
        if PSUTIL_AVAILABLE:
            try:
                memory_before = psutil.virtual_memory().percent
                print(f"🧠 Memory before: {memory_before}%")
            except Exception as mem_error:
                print(f"🧠 Memory check error: {mem_error}")

        # Log antes de procesar
        print(f"⏳ Processing request...")
        sys.stdout.flush()

        # Procesar request
        response = await call_next(request)

        # Log de éxito
        print(f"✅ RAILWAY DEBUG: Response {response.status_code}")
        print(f"✅ Response headers: {dict(response.headers)}")
        sys.stdout.flush()

        return response

    except Exception as e:
        # Log detallado del error
        print(f"❌ RAILWAY ERROR: {str(e)}")
        print(f"❌ ERROR TYPE: {type(e).__name__}")
        print(f"❌ ERROR ARGS: {e.args}")
        print(f"❌ TRACEBACK:")
        traceback.print_exc()
        sys.stdout.flush()

        # Devolver error JSON
        return JSONResponse(
            status_code=500,
            content={
                "error": "Railway Debug Error",
                "detail": str(e),
                "type": type(e).__name__,
                "path": str(request.url.path),
                "method": request.method
            }
        )


# ========================================
# FIN DEBUG MIDDLEWARE
# ========================================

# CONFIGURAR CORS PARA SERVIDOR
allowed_origins = [
    "http://localhost:3000",  # React frontend local
    "http://10.0.2.2:8000",  # Android emulator
    "http://localhost:8000",  # Local development
    "https://*.onrender.com",  # Cualquier subdominio de Render
    "https://*.vercel.app",  # Cualquier frontend en Vercel
    "https://*.netlify.app",  # Cualquier frontend en Netlify
]

# Agregar URLs específicas desde variables de entorno
if os.getenv("FRONTEND_URL"):
    allowed_origins.append(os.getenv("FRONTEND_URL"))
if os.getenv("MOBILE_APP_URL"):
    allowed_origins.append(os.getenv("MOBILE_APP_URL"))
if os.getenv("RENDER_EXTERNAL_URL"):
    allowed_origins.append(os.getenv("RENDER_EXTERNAL_URL"))

# Si estamos en desarrollo, permitir todos los orígenes
if os.getenv("DEBUG", "False") == "True":
    allowed_origins.append("*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# CONFIGURAR TRUSTED HOSTS PARA RAILWAY
# Permitir todos los hosts en Railway (más simple y seguro)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Permitir todos los dominios de Railway
)

# COMENTADO TEMPORALMENTE - Middleware original
# @app.middleware("http")
# async def log_requests(request: Request, call_next):
#     """Middleware para logging de requests en servidor"""
#     start_time = time.time()
#
#     # Obtener IP real (considerando proxies de Railway)
#     client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
#     if "," in client_ip:
#         client_ip = client_ip.split(",")[0].strip()
#
#     # Log request (más detallado en desarrollo)
#     if os.getenv("DEBUG", "False") == "True":
#         logger.info(f"📥 {request.method} {request.url.path} - IP: {client_ip}")
#     else:
#         # En producción, log más simple
#         logger.info(f"{request.method} {request.url.path}")
#
#     try:
#         response = await call_next(request)
#
#         # Calcular tiempo de procesamiento
#         process_time = time.time() - start_time
#
#         # Log response
#         if process_time > 5.0:  # Solo log si tarda más de 5 segundos
#             logger.warning(
#                 f"⏱️ SLOW REQUEST: {request.method} {request.url.path} - "
#                 f"Time: {process_time:.2f}s - Status: {response.status_code}"
#             )
#         elif os.getenv("DEBUG", "False") == "True":
#             logger.info(
#                 f"📤 {request.method} {request.url.path} - "
#                 f"Status: {response.status_code} - Time: {process_time:.2f}s"
#             )
#
#         # Agregar headers para servidor
#         response.headers["X-Process-Time"] = str(round(process_time, 2))
#         response.headers["X-Server"] = "Railway"
#         response.headers["X-API-Version"] = "1.0.0"
#
#         return response
#
#     except Exception as e:
#         process_time = time.time() - start_time
#         logger.error(f"❌ {request.method} {request.url.path} - Error: {str(e)} - Time: {process_time:.2f}s")
#         raise

# Incluir routers
app.include_router(students.router)
app.include_router(recognition.router)


# Endpoint ultra-simple para testing
@app.get("/railway-test")
async def railway_test():
    """Endpoint súper simple para debug"""
    try:
        print("🧪 RAILWAY TEST: Endpoint called")
        sys.stdout.flush()

        # Test básico de imports
        import os
        import time

        result = {
            "status": "ok",
            "message": "Railway test successful",
            "server": "Railway",
            "timestamp": time.time(),
            "env_port": os.getenv("PORT", "not_set"),
            "python_version": sys.version
        }

        if PSUTIL_AVAILABLE:
            try:
                result["memory_percent"] = psutil.virtual_memory().percent
                result["cpu_percent"] = psutil.cpu_percent()
            except:
                result["system_info"] = "psutil error"

        print(f"🧪 Returning: {result}")
        sys.stdout.flush()

        return result

    except Exception as e:
        print(f"❌ RAILWAY TEST ERROR: {e}")
        print(f"❌ TRACEBACK:")
        traceback.print_exc()
        sys.stdout.flush()
        raise


# ENDPOINTS ESPECÍFICOS PARA SERVIDOR
@app.get("/")
async def root():
    """Endpoint raíz con información de la API para servidor"""
    return {
        "message": "API de Reconocimiento Facial de Estudiantes",
        "version": "1.0.0",
        "environment": "production" if os.getenv("DEBUG", "False") != "True" else "development",
        "server": "Railway",
        "database": "SQLite + Cloudflare D1",
        "storage": "Cloudflare R2" if os.getenv("USE_CLOUDFLARE_R2", "false").lower() == "true" else "Local",
        "status": "active",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "health": "/health",
            "students": "/api/students",
            "recognize": "/api/recognize",
            "stats": "/api/recognition/stats",
            "railway_test": "/railway-test"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint optimizado para servidor"""
    try:
        # Verificar base de datos
        db_status = "connected" if test_database_connection() else "disconnected"

        # Verificar servicios
        services_status = {
            "face_recognition": face_service is not None,
            "image_processor": image_processor is not None,
            "database": db_status == "connected",
            "cloudflare_r2": os.getenv("USE_CLOUDFLARE_R2", "false").lower() == "true"
        }

        overall_status = "healthy" if all([
            services_status["face_recognition"],
            services_status["image_processor"],
            services_status["database"]
        ]) else "unhealthy"

        return {
            "status": overall_status,
            "timestamp": time.time(),
            "server": "Railway",
            "environment": "production" if os.getenv("DEBUG", "False") != "True" else "development",
            "services": services_status,
            "database": {
                "status": db_status,
                "type": "SQLite"
            },
            "version": "1.0.0",
            "uptime": "Available"  # Railway maneja el uptime
        }

    except Exception as e:
        logger.error(f"❌ Error en health check: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time(),
            "server": "Railway"
        }


@app.get("/info")
async def system_info():
    """Información del sistema optimizada para Railway + D1"""
    try:
        from .models.database import get_database_stats, is_d1_enabled, get_database_type

        # Obtener estadísticas de base de datos
        db_stats = get_database_stats()

        # Configuración por defecto (sin depender de system_config)
        default_config = {
            "recognition_threshold": float(os.getenv("RECOGNITION_THRESHOLD", "0.8")),
            "max_image_size_mb": round(int(os.getenv("MAX_IMAGE_SIZE", "10485760")) / (1024 * 1024), 2),
            "allowed_formats": os.getenv("ALLOWED_IMAGE_FORMATS", "jpg,jpeg,png,bmp").split(",")
        }

        # Estadísticas de almacenamiento
        storage_stats = {}
        if os.getenv("USE_CLOUDFLARE_R2", "false").lower() != "true" and image_processor:
            try:
                storage_stats = image_processor.get_directory_stats()
            except:
                storage_stats = {"error": "No disponible"}

        return {
            "system": {
                "version": "1.0.0",
                "status": "active",
                "server": "Railway",
                "environment": "production" if os.getenv("DEBUG", "False") != "True" else "development",
                **default_config
            },
            "database": {
                **db_stats,
                "type": get_database_type(),
                "cloudflare_d1_ready": is_d1_enabled(),
                "d1_enabled": is_d1_enabled()
            },
            "storage": {
                "type": "Cloudflare R2" if os.getenv("USE_CLOUDFLARE_R2", "false").lower() == "true" else "Local",
                "stats": storage_stats
            },
            "configuration": {
                "debug": os.getenv("DEBUG", "False") == "True",
                "api_host": os.getenv("API_HOST", "0.0.0.0"),
                "api_port": os.getenv("API_PORT", "10000"),
                "use_cloudflare_r2": os.getenv("USE_CLOUDFLARE_R2", "false").lower() == "true",
                "use_cloudflare_d1": os.getenv("USE_CLOUDFLARE_D1", "false").lower() == "true"
            }
        }

    except Exception as e:
        logger.error(f"❌ Error al obtener info del sistema: {e}")

        # Fallback con información básica
        return {
            "system": {
                "version": "1.0.0",
                "status": "active",
                "server": "Railway",
                "environment": "production",
                "recognition_threshold": 0.8,
                "max_image_size_mb": 10.0,
                "allowed_formats": ["jpg", "jpeg", "png", "bmp"]
            },
            "database": {
                "type": "Cloudflare D1" if os.getenv("USE_CLOUDFLARE_D1", "false").lower() == "true" else "SQLite",
                "status": "unknown",
                "error": str(e)
            },
            "storage": {
                "type": "Cloudflare R2" if os.getenv("USE_CLOUDFLARE_R2", "false").lower() == "true" else "Local"
            },
            "configuration": {
                "debug": os.getenv("DEBUG", "False") == "True",
                "use_cloudflare_r2": os.getenv("USE_CLOUDFLARE_R2", "false").lower() == "true",
                "use_cloudflare_d1": os.getenv("USE_CLOUDFLARE_D1", "false").lower() == "true"
            }
        }


@app.get("/server-status")
async def server_status():
    """Estado específico del servidor Railway"""
    try:
        import platform
    except ImportError:
        platform = None

    status = {
        "server": "Railway",
        "api_version": "1.0.0",
        "python_version": platform.python_version() if platform else "Unknown",
        "environment": {
            "debug": os.getenv("DEBUG", "False") == "True",
            "port": os.getenv("PORT", os.getenv("API_PORT", "10000")),
            "host": os.getenv("API_HOST", "0.0.0.0")
        },
        "features": {
            "face_recognition": True,
            "cloudflare_r2": os.getenv("USE_CLOUDFLARE_R2", "false").lower() == "true",
            "cloudflare_d1": os.getenv("USE_CLOUDFLARE_D1", "false").lower() == "true",
            "sqlite": True,
            "psutil": PSUTIL_AVAILABLE
        }
    }

    if PSUTIL_AVAILABLE:
        try:
            status["system"] = {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent
            }
        except:
            pass

    return status


@app.get("/admin/cleanup")
async def cleanup_temp_files(max_age_hours: int = 24):
    """Endpoint administrativo para limpiar archivos temporales en servidor"""
    try:
        if not image_processor:
            raise HTTPException(status_code=503, detail="Image processor no disponible")

        # En servidor, ser más agresivo con la limpieza
        deleted_count = image_processor.cleanup_temp_files(max_age_hours)

        return {
            "message": "Limpieza completada",
            "deleted_files": deleted_count,
            "max_age_hours": max_age_hours,
            "server": "Railway"
        }

    except Exception as e:
        logger.error(f"❌ Error en limpieza: {e}")
        raise HTTPException(status_code=500, detail=f"Error en limpieza: {str(e)}")


# Manejo global de excepciones para servidor
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Manejo global de excepciones en servidor"""
    logger.error(f"❌ Excepción no manejada: {str(exc)} - URL: {request.url}")

    return JSONResponse(
        status_code=500,
        content={
            "error": "Error interno del servidor",
            "detail": "Ha ocurrido un error inesperado",
            "path": str(request.url.path),
            "method": request.method,
            "server": "Railway",
            "timestamp": time.time()
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Manejo de HTTPExceptions en servidor"""
    logger.warning(f"⚠️ HTTP Exception: {exc.status_code} - {exc.detail} - URL: {request.url}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url.path),
            "method": request.method,
            "server": "Railway",
            "timestamp": time.time()
        }
    )


# NO montar archivos estáticos en servidor (usar Cloudflare R2)
# En servidor, las imágenes se sirven desde Cloudflare R2
if os.getenv("USE_CLOUDFLARE_R2", "false").lower() != "true" and os.path.exists("uploads"):
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
    logger.info("📁 Archivos estáticos montados (desarrollo)")

# Configuración para ejecutar en servidor
if __name__ == "__main__":
    import uvicorn

    # Configuración para servidor
    port = int(os.getenv("PORT", os.getenv("API_PORT", "10000")))
    host = os.getenv("API_HOST", "0.0.0.0")

    logger.info(f"🚀 Iniciando servidor en {host}:{port}")

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=os.getenv("DEBUG", "False") == "True",
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
        # Configuración específica para servidor
        workers=1,  # Railway Free tier funciona mejor con 1 worker
        access_log=os.getenv("DEBUG", "False") == "True"
    )