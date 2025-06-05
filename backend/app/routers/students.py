# app/routers/students.py
from fastapi import APIRouter, HTTPException
import logging
from app.database.models import StudentModel
from app.core.student_loader import reload_students

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def list_students():
    """Listar todos los estudiantes registrados"""
    try:
        students = StudentModel.get_all_students()
        return {
            "total": len(students),
            "students": students
        }
    except Exception as e:
        logger.error(f"Error listando estudiantes: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo lista de estudiantes")


@router.get("/{student_id}")
async def get_student(student_id: int):
    """Obtener información específica de un estudiante"""
    try:
        student = StudentModel.get_student_by_id(student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")

        return student

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo estudiante: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/{student_id}/toggle-requisitoriado")
async def toggle_requisitoriado(student_id: int):
    """Cambiar estado de requisitoriado de un estudiante"""
    try:
        new_status = StudentModel.toggle_requisitoriado(student_id)

        if new_status is None:
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")

        # Recargar datos en memoria
        reload_students()

        return {
            "message": "Estado actualizado",
            "student_id": student_id,
            "requisitoriado": new_status
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cambiando estado: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")