from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Dict, Any
import os
import time

from ..models.database import get_db
from ..models.schemas import RecognitionResult, RecognitionLog
from ..services.cloudflare_adapter import CloudflareAdapter  # ✅ CAMBIO PRINCIPAL
from ..services.face_recognition import FaceRecognitionService
from ..utils.image_processing import ImageProcessor

router = APIRouter(prefix="/api", tags=["recognition"])

# ✅ USAR CLOUDFLARE ADAPTER EN LUGAR DE SERVICIOS DIRECTOS
adapter = CloudflareAdapter()
face_service = FaceRecognitionService()
image_processor = ImageProcessor()


@router.post("/recognize", response_model=RecognitionResult)
async def recognize_student(
        image: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    """
    Reconocer estudiante a partir de una imagen
    """
    start_time = time.time()
    temp_image_path = None

    try:
        # Validar formato de imagen
        if not image_processor.is_valid_image(image):
            raise HTTPException(status_code=400, detail="Formato de imagen no válido")

        # Guardar imagen temporalmente
        temp_image_path = await image_processor.save_image(image, "recognition")

        # Extraer características faciales de la imagen
        face_encoding = await face_service.extract_face_encoding(temp_image_path)

        if face_encoding is None:
            # Limpiar archivo temporal
            if temp_image_path and os.path.exists(temp_image_path):
                os.remove(temp_image_path)
            raise HTTPException(status_code=400, detail="No se detectó un rostro en la imagen")

        # ✅ USAR ADAPTER PARA OBTENER ESTUDIANTES
        students = adapter.get_all_students(db)

        if not students:
            raise HTTPException(status_code=404, detail="No hay estudiantes registrados en el sistema")

        # Convertir students dict a objetos Student para face_service
        from ..models.database import Student
        student_objects = []
        for student_data in students:
            # Crear objeto Student temporal para reconocimiento
            student_obj = Student(
                id=student_data['id'],
                nombre=student_data['nombre'],
                apellidos=student_data['apellidos'],
                codigo=student_data['codigo'],
                correo=student_data.get('correo'),
                requisitoriado=student_data.get('requisitoriado', False),
                imagen_path=student_data.get('imagen_path'),
                face_encoding=student_data.get('face_encoding'),
                created_at=student_data.get('created_at'),
                updated_at=student_data.get('updated_at'),
                active=student_data.get('active', True)
            )
            student_objects.append(student_obj)

        # Realizar reconocimiento
        recognition_result = await face_service.recognize_face(face_encoding, student_objects)

        # Calcular tiempo de procesamiento
        processing_time = time.time() - start_time

        # ✅ USAR ADAPTER PARA LOGS
        log_data = {
            "found": recognition_result["found"],
            "student_id": recognition_result.get("student", {}).get("id") if recognition_result["found"] else None,
            "similarity": recognition_result.get("similarity", 0.0),
            "confidence": recognition_result.get("confidence", "Baja"),
            "processing_time": processing_time,
            "image_path": temp_image_path
        }

        adapter.create_recognition_log(db, log_data)

        # Agregar información adicional al resultado
        result = RecognitionResult(
            found=recognition_result["found"],
            student=recognition_result.get("student"),
            similarity=recognition_result.get("similarity", 0.0),
            confidence=recognition_result.get("confidence", "Baja"),
            processing_time=round(processing_time, 2),
            message=recognition_result.get("message", "")
        )

        return result

    except HTTPException:
        # Re-lanzar HTTPException sin modificar
        if temp_image_path and os.path.exists(temp_image_path):
            os.remove(temp_image_path)
        raise
    except Exception as e:
        # Limpiar archivo temporal en caso de error
        if temp_image_path and os.path.exists(temp_image_path):
            os.remove(temp_image_path)
        raise HTTPException(status_code=500, detail=f"Error en el reconocimiento: {str(e)}")


@router.get("/recognition/stats")
def get_recognition_stats(db: Session = Depends(get_db)):
    """
    Obtener estadísticas de reconocimiento
    """
    try:
        # ✅ USAR ADAPTER PARA STATS
        stats = adapter.get_recognition_stats(db)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener estadísticas: {str(e)}")


@router.get("/recognition/logs")
def get_recognition_logs(
        skip: int = 0,
        limit: int = 50,
        db: Session = Depends(get_db)
):
    """
    Obtener logs de reconocimiento
    """
    try:
        # ✅ USAR SERVICIOS DESDE ADAPTER
        logs = adapter.log_service.get_recognition_logs(db, skip=skip, limit=limit)
        return logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener logs: {str(e)}")


# Los demás endpoints permanecen igual...
@router.post("/test-face-detection")
async def test_face_detection(image: UploadFile = File(...)):
    """
    Endpoint para probar detección facial sin comparación
    """
    temp_image_path = None

    try:
        # Validar formato
        if not image_processor.is_valid_image(image):
            raise HTTPException(status_code=400, detail="Formato de imagen no válido")

        # Guardar temporalmente
        temp_image_path = await image_processor.save_image(image, "test")

        # Solo detectar rostro
        face_encoding = await face_service.extract_face_encoding(temp_image_path)

        # Limpiar archivo temporal
        if temp_image_path and os.path.exists(temp_image_path):
            os.remove(temp_image_path)

        if face_encoding is not None:
            return {
                "face_detected": True,
                "encoding_length": len(face_encoding),
                "message": "Rostro detectado correctamente"
            }
        else:
            return {
                "face_detected": False,
                "message": "No se detectó ningún rostro en la imagen"
            }

    except Exception as e:
        if temp_image_path and os.path.exists(temp_image_path):
            os.remove(temp_image_path)
        raise HTTPException(status_code=500, detail=f"Error en la detección: {str(e)}")


@router.post("/debug-similarity")
async def debug_similarity(
        image1: UploadFile = File(...),
        image2: UploadFile = File(...),
):
    """
    Endpoint mejorado para debuggear similitud entre dos imágenes
    """
    temp_path1 = None
    temp_path2 = None

    try:
        # Validar ambas imágenes
        if not image_processor.is_valid_image(image1):
            raise HTTPException(status_code=400, detail="Imagen 1 no válida")

        if not image_processor.is_valid_image(image2):
            raise HTTPException(status_code=400, detail="Imagen 2 no válida")

        # Guardar ambas imágenes temporalmente
        temp_path1 = await image_processor.save_image(image1, "test")
        temp_path2 = await image_processor.save_image(image2, "test")

        # Información adicional sobre las imágenes
        image1_info = image_processor.get_image_info(temp_path1)
        image2_info = image_processor.get_image_info(temp_path2)

        # Debuggear comparación
        debug_result = await face_service.debug_encoding_comparison(temp_path1, temp_path2)

        # Limpiar cualquier valor numpy que pueda quedar
        def clean_numpy_values(obj):
            """Convertir valores numpy a tipos Python nativos recursivamente"""
            if isinstance(obj, dict):
                return {k: clean_numpy_values(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_numpy_values(item) for item in obj]
            elif hasattr(obj, 'item'):  # numpy scalar
                return obj.item()
            elif hasattr(obj, 'tolist'):  # numpy array
                return obj.tolist()
            else:
                return obj

        # Limpiar todos los valores
        debug_result = clean_numpy_values(debug_result)
        image1_info = clean_numpy_values(image1_info)
        image2_info = clean_numpy_values(image2_info)

        # Agregar información adicional
        final_result = {
            **debug_result,
            "image1_info": image1_info,
            "image2_info": image2_info,
            "images": {
                "image1_name": str(image1.filename),
                "image2_name": str(image2.filename),
                "temp_path1": str(temp_path1),
                "temp_path2": str(temp_path2)
            }
        }

        return final_result

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc(),
            "debug_info": {
                "endpoint": "debug_similarity",
                "temp_paths": {
                    "path1": str(temp_path1) if temp_path1 else None,
                    "path2": str(temp_path2) if temp_path2 else None
                }
            }
        }
    finally:
        # Limpiar archivos temporales
        for path in [temp_path1, temp_path2]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass  # Ignorar errores de limpieza


@router.get("/health")
def health_check():
    """
    Endpoint para verificar que la API está funcionando
    """
    return {
        "status": "ok",
        "message": "API de reconocimiento facial funcionando correctamente",
        "version": "1.0.0"
    }


@router.get("/debug-system")
async def debug_system():
    """
    Endpoint para verificar el estado del sistema de reconocimiento
    """
    try:
        import face_recognition
        import sys
        import numpy as np

        # Información del sistema (todo convertido a tipos nativos)
        system_info = {
            "python_version": str(sys.version),
            "face_recognition_available": True,
            "face_recognition_version": str(getattr(face_recognition, '__version__', 'unknown')),
            "numpy_version": str(np.__version__),
        }

        # Verificar si mediapipe está presente
        try:
            import mediapipe
            system_info["mediapipe_present"] = True
            system_info["mediapipe_version"] = str(mediapipe.__version__)
            system_info["warning"] = "MediaPipe detectado - podría causar conflictos"
        except ImportError:
            system_info["mediapipe_present"] = False

        # Verificar dlib
        try:
            import dlib
            system_info["dlib_available"] = True
            system_info["dlib_version"] = str(dlib.version)
        except ImportError:
            system_info["dlib_available"] = False
            system_info["dlib_error"] = "dlib no disponible"

        # Probar encoding simple
        try:
            # Crear imagen de prueba
            test_image = np.zeros((200, 200, 3), dtype=np.uint8)

            # Intentar detectar (debería fallar, pero nos dice si la librería funciona)
            face_locations = face_recognition.face_locations(test_image)

            system_info["face_recognition_test"] = {
                "test_passed": True,
                "faces_detected": int(len(face_locations)),
                "note": "Test con imagen sintética (sin rostro real)"
            }

        except Exception as e:
            system_info["face_recognition_test"] = {
                "test_passed": False,
                "error": str(e)
            }

        # Información del servicio
        service_info = {
            "recognition_threshold": float(face_service.recognition_threshold),
            "model": str(face_service.model),
            "num_jitters": int(face_service.num_jitters)
        }

        return {
            "status": "ok",
            "system_info": system_info,
            "service_info": service_info,
            "recommendations": {
                "if_encodings_44d": "Desinstalar mediapipe: pip uninstall mediapipe",
                "if_encodings_128d": "Sistema funcionando correctamente",
                "if_dlib_missing": "Instalar dlib: pip install dlib"
            }
        }

    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@router.get("/debug/system-check")
async def debug_system_check(db: Session = Depends(get_db)):
    """
    🔍 DEBUGGING ENDPOINT - Verificar todo el sistema paso a paso
    """
    debug_info = {}

    try:
        # 1. Verificar variables de entorno
        debug_info["environment"] = {
            "USE_CLOUDFLARE_D1": os.getenv("USE_CLOUDFLARE_D1", "not_set"),
            "CLOUDFLARE_ACCOUNT_ID": "***" + os.getenv("CLOUDFLARE_ACCOUNT_ID", "not_set")[-4:] if os.getenv(
                "CLOUDFLARE_ACCOUNT_ID") else "not_set",
            "CLOUDFLARE_API_TOKEN": "***" + os.getenv("CLOUDFLARE_API_TOKEN", "not_set")[-4:] if os.getenv(
                "CLOUDFLARE_API_TOKEN") else "not_set",
            "CLOUDFLARE_D1_DATABASE_ID": "***" + os.getenv("CLOUDFLARE_D1_DATABASE_ID", "not_set")[-4:] if os.getenv(
                "CLOUDFLARE_D1_DATABASE_ID") else "not_set"
        }

        # 2. Verificar CloudflareAdapter
        debug_info["cloudflare_adapter"] = {
            "adapter_created": adapter is not None,
            "d1_available": adapter.d1_available if adapter else False,
            "r2_available": adapter.r2_available if adapter else False,
            "use_d1": adapter.use_d1 if adapter else False,
            "use_r2": adapter.use_r2 if adapter else False
        }

        # 3. Verificar D1 Service directamente
        try:
            from ..services.cloudflare_d1 import CloudflareD1Service
            d1_service = CloudflareD1Service()

            debug_info["d1_service"] = {
                "service_enabled": d1_service.enabled,
                "test_connection": False,
                "connection_error": None
            }

            # Test de conexión
            try:
                connection_test = d1_service.test_connection()
                debug_info["d1_service"]["test_connection"] = connection_test

                # Si la conexión funciona, probar query básico
                if connection_test:
                    try:
                        result = d1_service.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
                        debug_info["d1_service"]["tables"] = result.get("results", [])
                    except Exception as e:
                        debug_info["d1_service"]["query_error"] = str(e)

            except Exception as e:
                debug_info["d1_service"]["connection_error"] = str(e)

        except ImportError as e:
            debug_info["d1_service"] = {"import_error": str(e)}

        # 4. Verificar datos directamente
        debug_info["data_check"] = {}

        # Usar adapter para obtener estudiantes
        try:
            students = adapter.get_all_students(db)
            debug_info["data_check"]["adapter_students_count"] = len(students)
            debug_info["data_check"]["adapter_students_sample"] = students[:2] if students else []
        except Exception as e:
            debug_info["data_check"]["adapter_error"] = str(e)

        # Usar service directo para comparar
        try:
            from ..services.database_service import StudentService
            student_service = StudentService()
            sqlite_students = student_service.get_all_students(db)
            debug_info["data_check"]["sqlite_students_count"] = len(sqlite_students)
        except Exception as e:
            debug_info["data_check"]["sqlite_error"] = str(e)

        # 5. Verificar database configuration
        try:
            from ..models.database import get_database_type, is_d1_enabled, get_database_configuration
            debug_info["database_config"] = {
                "database_type": get_database_type(),
                "d1_enabled": is_d1_enabled(),
                "config": get_database_configuration()
            }
        except Exception as e:
            debug_info["database_config"] = {"error": str(e)}

        return {
            "status": "debug_complete",
            "timestamp": time.time(),
            "debug_info": debug_info
        }

    except Exception as e:
        return {
            "status": "debug_error",
            "error": str(e),
            "partial_debug_info": debug_info
        }


@router.get("/debug/test-d1-direct")
async def debug_test_d1_direct():
    """
    🔍 DEBUGGING - Test directo de D1 sin adapter
    """
    try:
        from ..services.cloudflare_d1 import CloudflareD1Service
        d1_service = CloudflareD1Service()

        if not d1_service.enabled:
            return {
                "error": "D1 service not enabled",
                "account_id": bool(os.getenv("CLOUDFLARE_ACCOUNT_ID")),
                "api_token": bool(os.getenv("CLOUDFLARE_API_TOKEN")),
                "database_id": bool(os.getenv("CLOUDFLARE_D1_DATABASE_ID"))
            }

        # Test de conexión
        connection_ok = d1_service.test_connection()
        if not connection_ok:
            return {"error": "D1 connection failed"}

        # Listar tablas
        tables_result = d1_service.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row.get("name") for row in tables_result.get("results", [])]

        # Contar estudiantes en D1
        if "estudiantes" in tables:
            count_result = d1_service.execute_query("SELECT COUNT(*) as count FROM estudiantes")
            student_count = count_result.get("results", [{}])[0].get("count", 0)

            # Obtener sample de estudiantes
            sample_result = d1_service.execute_query("SELECT id, nombre, apellidos, codigo FROM estudiantes LIMIT 3")
            sample_students = sample_result.get("results", [])
        else:
            student_count = 0
            sample_students = []

        return {
            "status": "d1_direct_test_ok",
            "connection": connection_ok,
            "tables": tables,
            "student_count": student_count,
            "sample_students": sample_students
        }

    except Exception as e:
        import traceback
        return {
            "status": "d1_direct_test_error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@router.get("/debug/test-adapter-step-by-step")
async def debug_test_adapter_step_by_step(db: Session = Depends(get_db)):
    """
    🔍 DEBUGGING - Test del adapter paso a paso
    """
    debug_steps = {}

    try:
        # Paso 1: Crear adapter
        debug_steps["step1_create_adapter"] = "ok"

        # Paso 2: Verificar propiedades
        debug_steps["step2_adapter_properties"] = {
            "use_d1": adapter.use_d1,
            "use_r2": adapter.use_r2,
            "d1_available": adapter.d1_available,
            "r2_available": adapter.r2_available
        }

        # Paso 3: Test del método get_all_students
        try:
            students = adapter.get_all_students(db)
            debug_steps["step3_get_students"] = {
                "status": "ok",
                "count": len(students),
                "sample": students[:2] if students else []
            }
        except Exception as e:
            debug_steps["step3_get_students"] = {
                "status": "error",
                "error": str(e)
            }

        # Paso 4: Verificar qué servicio se está usando
        debug_steps["step4_service_check"] = {}

        if adapter.d1_available:
            debug_steps["step4_service_check"]["using"] = "cloudflare_d1"
            try:
                d1_students = adapter.d1_service.get_all_students()
                debug_steps["step4_service_check"]["d1_direct"] = {
                    "count": len(d1_students),
                    "sample": d1_students[:2] if d1_students else []
                }
            except Exception as e:
                debug_steps["step4_service_check"]["d1_error"] = str(e)
        else:
            debug_steps["step4_service_check"]["using"] = "sqlite_fallback"
            try:
                sqlite_students = adapter.student_service.get_all_students(db)
                debug_steps["step4_service_check"]["sqlite_direct"] = {
                    "count": len(sqlite_students),
                    "sample": [s.__dict__ for s in sqlite_students[:2]]
                }
            except Exception as e:
                debug_steps["step4_service_check"]["sqlite_error"] = str(e)

        return {
            "status": "adapter_debug_complete",
            "debug_steps": debug_steps
        }

    except Exception as e:
        import traceback
        return {
            "status": "adapter_debug_error",
            "error": str(e),
            "traceback": traceback.format_exc(),
            "completed_steps": debug_steps
        }


@router.post("/debug/create-test-student")
async def debug_create_test_student(db: Session = Depends(get_db)):
    """
    🔍 DEBUGGING - Crear estudiante de prueba para verificar funcionamiento
    """
    try:
        test_student_data = {
            "nombre": "Test",
            "apellidos": "Debug Student",
            "codigo": f"DEBUG{int(time.time())}",
            "correo": "debug@test.com",
            "requisitoriado": False,
            "imagen_path": None,
            "face_encoding": None
        }

        # Test usando adapter
        result = adapter.create_student(db, test_student_data, None)

        # Verificar que se creó
        verification = adapter.get_all_students(db)

        return {
            "status": "test_student_created",
            "created_student": result,
            "total_students_after": len(verification),
            "test_data": test_student_data
        }

    except Exception as e:
        import traceback
        return {
            "status": "test_student_error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@router.post("/admin/nuclear-cleanup")
async def nuclear_cleanup_all_data(
        confirm_delete_all: bool = False,
        confirm_password: str = "",
        db: Session = Depends(get_db)
):
    """
    🚨 NUCLEAR CLEANUP: Eliminar TODOS los datos de D1 y R2
    CUIDADO: Esta operación es IRREVERSIBLE
    """

    # Verificación de seguridad
    expected_password = "DELETE_ALL_DATA_2025"

    if not confirm_delete_all or confirm_password != expected_password:
        return {
            "error": "Operación cancelada por seguridad",
            "instructions": {
                "confirm_delete_all": "Debe ser true",
                "confirm_password": f"Debe ser exactamente: {expected_password}",
                "url_ejemplo": "/admin/nuclear-cleanup?confirm_delete_all=true&confirm_password=DELETE_ALL_DATA_2025"
            },
            "warning": "Esta operación eliminará TODOS los estudiantes y sus imágenes PERMANENTEMENTE"
        }

    try:
        cleanup_results = {
            "d1_cleanup": {},
            "r2_cleanup": {},
            "total_deleted": {},
            "warnings": []
        }

        # 1. LIMPIAR D1 (Base de datos)
        logger.info("🧹 Iniciando limpieza nuclear de D1...")

        try:
            if adapter.d1_available:
                # Contar estudiantes antes
                students_before = adapter.get_all_students(db)
                students_count = len(students_before)

                # DELETE ALL estudiantes
                delete_students_sql = "DELETE FROM estudiantes"
                result_students = adapter.d1_service.execute_query(delete_students_sql)

                # DELETE ALL logs de reconocimiento
                delete_logs_sql = "DELETE FROM recognition_logs"
                result_logs = adapter.d1_service.execute_query(delete_logs_sql)

                # Reset autoincrement counters
                reset_students_sql = "DELETE FROM sqlite_sequence WHERE name='estudiantes'"
                reset_logs_sql = "DELETE FROM sqlite_sequence WHERE name='recognition_logs'"
                adapter.d1_service.execute_query(reset_students_sql)
                adapter.d1_service.execute_query(reset_logs_sql)

                cleanup_results["d1_cleanup"] = {
                    "status": "success",
                    "students_deleted": students_count,
                    "logs_deleted": result_logs.get("meta", {}).get("changes", 0),
                    "counters_reset": True
                }

                logger.info(f"✅ D1 limpiado: {students_count} estudiantes eliminados")

            else:
                cleanup_results["d1_cleanup"] = {
                    "status": "skipped",
                    "reason": "D1 no disponible"
                }

        except Exception as e:
            cleanup_results["d1_cleanup"] = {
                "status": "error",
                "error": str(e)
            }
            logger.error(f"❌ Error limpiando D1: {e}")

        # 2. LIMPIAR R2 (Imágenes)
        logger.info("🧹 Iniciando limpieza nuclear de R2...")

        try:
            if adapter.r2_available:
                r2_service = adapter.r2_service

                # Obtener lista de archivos en ambas carpetas
                reference_files = r2_service.list_files("reference", limit=1000)
                recognition_files = r2_service.list_files("recognition", limit=1000)

                deleted_reference = 0
                deleted_recognition = 0

                # Eliminar archivos de reference/
                for file_info in reference_files:
                    try:
                        if r2_service.delete_file(file_info["public_url"]):
                            deleted_reference += 1
                    except Exception as e:
                        logger.warning(f"⚠️ Error eliminando {file_info['key']}: {e}")

                # Eliminar archivos de recognition/
                for file_info in recognition_files:
                    try:
                        if r2_service.delete_file(file_info["public_url"]):
                            deleted_recognition += 1
                    except Exception as e:
                        logger.warning(f"⚠️ Error eliminando {file_info['key']}: {e}")

                cleanup_results["r2_cleanup"] = {
                    "status": "success",
                    "reference_files_deleted": deleted_reference,
                    "recognition_files_deleted": deleted_recognition,
                    "total_files_deleted": deleted_reference + deleted_recognition
                }

                logger.info(f"✅ R2 limpiado: {deleted_reference + deleted_recognition} archivos eliminados")

            else:
                cleanup_results["r2_cleanup"] = {
                    "status": "skipped",
                    "reason": "R2 no disponible"
                }

        except Exception as e:
            cleanup_results["r2_cleanup"] = {
                "status": "error",
                "error": str(e)
            }
            logger.error(f"❌ Error limpiando R2: {e}")

        # 3. VERIFICACIÓN POST-LIMPIEZA
        try:
            # Verificar que D1 esté vacío
            remaining_students = adapter.get_all_students(db)

            cleanup_results["verification"] = {
                "d1_students_remaining": len(remaining_students),
                "cleanup_successful": len(remaining_students) == 0
            }

        except Exception as e:
            cleanup_results["verification"] = {
                "error": str(e)
            }

        # 4. RESUMEN FINAL
        total_students_deleted = cleanup_results["d1_cleanup"].get("students_deleted", 0)
        total_files_deleted = cleanup_results["r2_cleanup"].get("total_files_deleted", 0)

        cleanup_results["summary"] = {
            "operation": "NUCLEAR CLEANUP COMPLETED",
            "timestamp": time.time(),
            "total_students_deleted": total_students_deleted,
            "total_files_deleted": total_files_deleted,
            "d1_status": cleanup_results["d1_cleanup"]["status"],
            "r2_status": cleanup_results["r2_cleanup"]["status"],
            "ready_for_bulk_upload": cleanup_results.get("verification", {}).get("cleanup_successful", False)
        }

        return {
            "status": "NUCLEAR CLEANUP COMPLETED",
            "message": "🚨 TODOS los datos han sido eliminados permanentemente",
            "results": cleanup_results,
            "next_steps": {
                "1": "Verificar que D1 y R2 están vacíos",
                "2": "Ejecutar tu script bulk_upload_railway.py",
                "3": "Recargar todos los estudiantes con imágenes",
                "4": "El sistema estará 100% limpio y funcional"
            }
        }

    except Exception as e:
        return {
            "status": "NUCLEAR CLEANUP FAILED",
            "error": str(e),
            "partial_results": cleanup_results
        }


@router.get("/admin/verify-empty")
async def verify_system_empty(db: Session = Depends(get_db)):
    """
    🔍 Verificar que el sistema esté completamente vacío después de la limpieza
    """
    try:
        verification = {
            "d1_check": {},
            "r2_check": {},
            "summary": {}
        }

        # Verificar D1
        try:
            students = adapter.get_all_students(db)

            # También verificar conteo directo
            if adapter.d1_available:
                count_result = adapter.d1_service.execute_query("SELECT COUNT(*) as count FROM estudiantes")
                direct_count = count_result.get("results", [{}])[0].get("count", 0)

                logs_result = adapter.d1_service.execute_query("SELECT COUNT(*) as count FROM recognition_logs")
                logs_count = logs_result.get("results", [{}])[0].get("count", 0)
            else:
                direct_count = 0
                logs_count = 0

            verification["d1_check"] = {
                "students_via_adapter": len(students),
                "students_direct_count": direct_count,
                "recognition_logs_count": logs_count,
                "is_empty": len(students) == 0 and direct_count == 0
            }

        except Exception as e:
            verification["d1_check"] = {"error": str(e)}

        # Verificar R2
        try:
            if adapter.r2_available:
                reference_stats = adapter.r2_service.list_files("reference", limit=10)
                recognition_stats = adapter.r2_service.list_files("recognition", limit=10)

                verification["r2_check"] = {
                    "reference_files": len(reference_stats),
                    "recognition_files": len(recognition_stats),
                    "total_files": len(reference_stats) + len(recognition_stats),
                    "is_empty": len(reference_stats) == 0 and len(recognition_stats) == 0
                }
            else:
                verification["r2_check"] = {"status": "r2_not_available"}

        except Exception as e:
            verification["r2_check"] = {"error": str(e)}

        # Resumen
        d1_empty = verification["d1_check"].get("is_empty", False)
        r2_empty = verification["r2_check"].get("is_empty", True)  # True si R2 no disponible

        verification["summary"] = {
            "system_completely_empty": d1_empty and r2_empty,
            "d1_empty": d1_empty,
            "r2_empty": r2_empty,
            "ready_for_bulk_upload": d1_empty and r2_empty,
            "timestamp": time.time()
        }

        return verification

    except Exception as e:
        return {"error": str(e)}