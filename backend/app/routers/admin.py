# app/routers/admin.py
from fastapi import APIRouter, HTTPException
import logging
from app.database.models import StudentModel
from app.core.student_loader import reload_students, get_students_count
from config import DB_CONFIG

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/stats")
async def get_stats():
    """Obtener estadísticas del sistema"""
    try:
        db_stats = StudentModel.get_stats()

        return {
            "system": {
                "name": "API Reconocimiento Facial - Estudiantes",
                "version": "1.0.0",
                "status": "activo"
            },
            "database": {
                "name": DB_CONFIG['database'],
                "host": f"{DB_CONFIG['host']}:{DB_CONFIG['port']}",
                "status": "connected"
            },
            "statistics": {
                **db_stats,
                "students_loaded_memory": get_students_count()
            }
        }

    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/reload-students")
async def reload_students_endpoint():
    """Recargar estudiantes de la base de datos"""
    try:
        if reload_students():
            return {
                "message": "Estudiantes recargados exitosamente",
                "students_loaded": get_students_count()
            }
        else:
            raise HTTPException(status_code=500, detail="Error recargando estudiantes")
    except Exception as e:
        logger.error(f"Error recargando estudiantes: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/health")
async def admin_health_check():
    """Verificación detallada de salud del sistema"""
    from app.database.connection import get_db_connection
    from app.core.student_loader import is_model_loaded

    try:
        connection = get_db_connection()
        if connection:
            connection.close()
            db_status = "connected"
        else:
            db_status = "disconnected"

        return {
            "status": "healthy" if db_status == "connected" else "degraded",
            "components": {
                "database": db_status,
                "students_model": "loaded" if is_model_loaded() else "not_loaded",
                "facial_recognition": "active"
            },
            "students_in_memory": get_students_count()
        }

    except Exception as e:
        logger.error(f"Error en health check: {e}")
        raise HTTPException(status_code=500, detail="Error verificando estado del sistema")