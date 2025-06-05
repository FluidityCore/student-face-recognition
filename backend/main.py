# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.core.student_loader import load_students_from_db
from app.routers import recognition, students, admin
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="API Reconocimiento Facial - Estudiantes",
    description="API para reconocer estudiantes usando base de datos existente",
    version="1.0.0",
    docs_url="/docs"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(recognition.router, prefix="/api", tags=["Reconocimiento"])
app.include_router(students.router, prefix="/api/students", tags=["Estudiantes"])
app.include_router(admin.router, prefix="/api/admin", tags=["Administración"])


@app.on_event("startup")
async def startup_event():
    """Cargar datos al iniciar"""
    logger.info("🚀 Iniciando API de Reconocimiento de Estudiantes")
    if load_students_from_db():
        logger.info("✅ Datos de estudiantes cargados correctamente")
    else:
        logger.error("❌ Error cargando datos de estudiantes")


@app.get("/")
async def root():
    """Endpoint principal"""
    from app.core.student_loader import get_students_count

    return {
        "message": "API de Reconocimiento Facial - Estudiantes",
        "version": "1.0.0",
        "status": "activo",
        "students_loaded": get_students_count(),
        "docs": "/docs",
        "endpoints": {
            "reconocer": "/api/recognize",
            "estudiantes": "/api/students",
            "estadisticas": "/api/admin/stats"
        }
    }


@app.get("/health")
async def health_check():
    """Verificar estado del sistema"""
    from app.database.connection import get_db_connection
    from app.core.student_loader import get_students_count, is_model_loaded

    try:
        connection = get_db_connection()
        if connection:
            connection.close()
            db_status = "connected"
        else:
            db_status = "disconnected"

        return {
            "status": "healthy",
            "database": db_status,
            "students_loaded": get_students_count(),
            "model_status": "loaded" if is_model_loaded() else "not_loaded"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )