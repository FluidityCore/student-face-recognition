#!/usr/bin/env python3
"""
Script para agregar estudiantes en masa basándose en nombres de archivos de imágenes
Formato esperado: APELLIDO1_APELLIDO2_NOMBRE1_NOMBRE2_CODIGO_EMAIL.jpg
Ejemplo: HERRERA_ANGULO_JOSE_MIGUEL_000245501_jherreraa6.jpg
"""

import os
import sys
import asyncio
import random
import logging
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any, Tuple
import requests

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Agregar path del proyecto
sys.path.append(str(Path(__file__).parent))

try:
    from app.services.face_recognition import FaceRecognitionService
    from app.services.cloudflare_adapter import CloudflareAdapter
    from app.models.database import get_db, SessionLocal
    from app.utils.image_processing import ImageProcessor
    from app.utils.validators import validate_student_data
except ImportError as e:
    logger.error(f"❌ Error importando módulos: {e}")
    logger.error("💡 Ejecuta desde el directorio raíz del proyecto")
    sys.exit(1)


class BulkStudentAdder:
    """Agregador masivo de estudiantes desde archivos de imagen"""

    def __init__(self, images_folder: str = "estudiantes_fotos"):
        self.images_folder = Path(images_folder)
        self.face_service = None
        self.adapter = None
        self.image_processor = None
        self.results = {
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "errors": [],
            "students_added": []
        }

        # Configuración
        self.domain = "@upao.edu.pe"
        self.requisitoriado_probability = 0.15  # 15% chance de ser requisitoriado

    async def initialize_services(self):
        """Inicializar servicios necesarios"""
        logger.info("🚀 Inicializando servicios...")

        try:
            self.face_service = FaceRecognitionService()
            self.adapter = CloudflareAdapter()
            self.image_processor = ImageProcessor()

            logger.info("✅ Servicios inicializados correctamente")
            return True

        except Exception as e:
            logger.error(f"❌ Error inicializando servicios: {e}")
            return False

    def parse_filename(self, filename: str) -> Dict[str, str]:
        """
        Parsear nombre de archivo según formato:
        APELLIDO1_APELLIDO2_NOMBRE1_NOMBRE2_CODIGO_EMAIL.jpg

        Ejemplo: HERRERA_ANGULO_JOSE_MIGUEL_000245501_jherreraa6.jpg
        """
        try:
            # Remover extensión
            name_without_ext = Path(filename).stem

            # Split por underscores
            parts = name_without_ext.split('_')

            if len(parts) < 6:
                raise ValueError(f"Formato inválido. Se esperan al menos 6 partes, encontradas: {len(parts)}")

            # Extraer partes básicas
            apellido1 = parts[0].title()
            apellido2 = parts[1].title()
            nombre1 = parts[2].title()
            nombre2 = parts[3].title()
            codigo = parts[4]
            email_prefix = parts[5]

            # Manejar casos con más de 6 partes (nombres/apellidos compuestos)
            if len(parts) > 6:
                # Asumir que las partes extra son parte del email o nombres adicionales
                extra_parts = parts[6:]
                # Por ahora, ignorar partes extra o incluirlas en email_prefix
                email_prefix = "_".join([email_prefix] + extra_parts)

            # Construir datos del estudiante
            student_data = {
                "apellidos": f"{apellido1} {apellido2}",
                "nombre": f"{nombre1} {nombre2}",
                "codigo": codigo,
                "correo": f"{email_prefix}{self.domain}",
                "requisitoriado": random.random() < self.requisitoriado_probability
            }

            logger.info(f"📝 Parseado: {student_data['nombre']} {student_data['apellidos']} ({student_data['codigo']})")

            return student_data

        except Exception as e:
            logger.error(f"❌ Error parseando {filename}: {e}")
            raise

    def validate_image_files(self) -> List[Path]:
        """Validar y listar archivos de imagen en la carpeta"""
        logger.info(f"🔍 Buscando imágenes en: {self.images_folder}")

        if not self.images_folder.exists():
            logger.error(f"❌ Carpeta no encontrada: {self.images_folder}")
            return []

        # Extensiones de imagen válidas
        valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}

        image_files = []
        for file_path in self.images_folder.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in valid_extensions:
                image_files.append(file_path)

        logger.info(f"📂 Encontradas {len(image_files)} imágenes")

        # Mostrar primeros 5 archivos como ejemplo
        for i, file_path in enumerate(image_files[:5]):
            logger.info(f"   {i + 1}. {file_path.name}")

        if len(image_files) > 5:
            logger.info(f"   ... y {len(image_files) - 5} más")

        return image_files

    async def process_single_student(self, image_path: Path) -> Dict[str, Any]:
        """Procesar un solo estudiante"""
        try:
            logger.info(f"👤 Procesando: {image_path.name}")

            # 1. Parsear información del archivo
            student_data = self.parse_filename(image_path.name)

            # 2. Validar datos del estudiante
            validate_student_data(
                student_data["nombre"],
                student_data["apellidos"],
                student_data["codigo"],
                student_data["correo"]
            )

            # 3. Verificar que el código no exista
            db = SessionLocal()
            try:
                existing_student = self.adapter.get_student_by_codigo(db, student_data["codigo"])
                if existing_student:
                    raise ValueError(f"Código {student_data['codigo']} ya existe")
            finally:
                db.close()

            # 4. Verificar que la imagen sea válida y extraer encoding
            if not image_path.exists():
                raise FileNotFoundError(f"Imagen no encontrada: {image_path}")

            # 5. Extraer encoding facial
            logger.info(f"🧠 Extrayendo características faciales...")
            face_encoding = await self.face_service.extract_face_encoding(str(image_path))

            if face_encoding is None:
                raise ValueError("No se detectó rostro en la imagen")

            logger.info(f"✅ Características extraídas: {len(face_encoding)} dimensiones")

            # 6. Copiar imagen a ubicación temporal para el procesamiento
            temp_image_path = None
            try:
                # Crear archivo temporal con extensión correcta
                with tempfile.NamedTemporaryFile(delete=False, suffix=image_path.suffix) as temp_file:
                    temp_image_path = temp_file.name

                # Copiar imagen al archivo temporal
                shutil.copy2(image_path, temp_image_path)

                # 7. Preparar datos completos para el adapter
                complete_student_data = {
                    "nombre": student_data["nombre"],
                    "apellidos": student_data["apellidos"],
                    "codigo": student_data["codigo"],
                    "correo": student_data["correo"],
                    "requisitoriado": student_data["requisitoriado"],
                    "imagen_path": None,  # Se establecerá en create_student
                    "face_encoding": face_encoding.tolist()
                }

                # 8. Crear mock UploadFile para el adapter
                from fastapi import UploadFile
                import io

                # Leer imagen como bytes
                with open(image_path, 'rb') as img_file:
                    image_bytes = img_file.read()

                # Crear UploadFile mock
                upload_file = UploadFile(
                    filename=image_path.name,
                    file=io.BytesIO(image_bytes),
                    size=len(image_bytes),
                    headers={"content-type": "image/jpeg"}
                )

                # Resetear puntero del archivo
                await upload_file.seek(0)

                # 9. Crear estudiante usando el adapter
                db = SessionLocal()
                try:
                    created_student = await self.adapter.create_student(
                        db, complete_student_data, upload_file
                    )

                    logger.info(
                        f"✅ Estudiante creado: {created_student.get('nombre')} {created_student.get('apellidos')}")

                    return {
                        "success": True,
                        "student": created_student,
                        "original_file": str(image_path),
                        "face_encoding_length": len(face_encoding)
                    }

                finally:
                    db.close()

            finally:
                # Limpiar archivo temporal
                if temp_image_path and os.path.exists(temp_image_path):
                    try:
                        os.remove(temp_image_path)
                    except:
                        pass

        except Exception as e:
            logger.error(f"❌ Error procesando {image_path.name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "original_file": str(image_path)
            }

    async def process_all_students(self, max_students: int = None) -> Dict[str, Any]:
        """Procesar todos los estudiantes en la carpeta"""
        logger.info("🚀 INICIANDO PROCESAMIENTO MASIVO DE ESTUDIANTES")
        logger.info("=" * 60)

        # 1. Validar archivos de imagen
        image_files = self.validate_image_files()

        if not image_files:
            logger.error("❌ No se encontraron archivos de imagen válidos")
            return self.results

        # 2. Limitar número de estudiantes si se especifica
        if max_students and max_students < len(image_files):
            image_files = image_files[:max_students]
            logger.info(f"🔢 Limitando procesamiento a {max_students} estudiantes")

        # 3. Procesar cada estudiante
        for i, image_path in enumerate(image_files, 1):
            logger.info(f"\n📊 Progreso: {i}/{len(image_files)} ({i / len(image_files) * 100:.1f}%)")

            self.results["processed"] += 1

            # Procesar estudiante individual
            result = await self.process_single_student(image_path)

            if result["success"]:
                self.results["successful"] += 1
                self.results["students_added"].append(result["student"])

                # Log de éxito con información del requisitoriado
                student = result["student"]
                req_status = "🚨 REQUISITORIADO" if student.get("requisitoriado") else "✅ Normal"
                logger.info(f"✅ Agregado: {student.get('codigo')} - {req_status}")

            else:
                self.results["failed"] += 1
                self.results["errors"].append({
                    "file": result["original_file"],
                    "error": result["error"]
                })
                logger.error(f"❌ Falló: {result['original_file']}")

        # 4. Actualizar sistema adaptativo
        if self.results["successful"] > 0:
            logger.info("\n🧠 Actualizando sistema de aprendizaje adaptativo...")
            try:
                # Obtener todos los encodings para actualizar el sistema adaptativo
                db = SessionLocal()
                try:
                    all_students = self.adapter.get_all_students(db)
                    encodings = []

                    for student in all_students:
                        if student.get('face_encoding'):
                            encodings.append(student['face_encoding'])

                    if encodings:
                        import numpy as np
                        np_encodings = [np.array(enc) for enc in encodings]
                        adaptive_report = self.face_service.adaptive_system.adaptive_update(np_encodings)

                        logger.info(f"🚀 Sistema adaptativo actualizado:")
                        logger.info(f"   📊 Total encodings: {len(np_encodings)}")
                        logger.info(
                            f"   🎯 Nuevo umbral: {self.face_service.adaptive_system.stats['optimal_threshold']:.3f}")
                        logger.info(
                            f"   📈 Diversidad: {self.face_service.adaptive_system.stats['dataset_diversity_score']:.3f}")

                finally:
                    db.close()

            except Exception as e:
                logger.warning(f"⚠️ Error actualizando sistema adaptativo: {e}")

        return self.results

    def generate_summary_report(self) -> str:
        """Generar reporte resumen del procesamiento"""
        report_lines = [
            "\n🎉 REPORTE FINAL DE PROCESAMIENTO MASIVO",
            "=" * 50,
            f"📊 Estudiantes procesados: {self.results['processed']}",
            f"✅ Exitosos: {self.results['successful']}",
            f"❌ Fallidos: {self.results['failed']}",
            f"📈 Tasa de éxito: {(self.results['successful'] / self.results['processed'] * 100) if self.results['processed'] > 0 else 0:.1f}%"
        ]

        # Estadísticas de requisitoriados
        requisitoriados = sum(1 for s in self.results['students_added'] if s.get('requisitoriado'))
        if self.results['successful'] > 0:
            report_lines.extend([
                f"🚨 Requisitoriados: {requisitoriados}/{self.results['successful']} ({requisitoriados / self.results['successful'] * 100:.1f}%)",
            ])

        # Errores más comunes
        if self.results['errors']:
            report_lines.append("\n❌ ERRORES ENCONTRADOS:")
            error_types = {}
            for error in self.results['errors']:
                error_msg = error['error']
                if error_msg in error_types:
                    error_types[error_msg] += 1
                else:
                    error_types[error_msg] = 1

            for error_msg, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
                report_lines.append(f"   • {error_msg}: {count} casos")

        # Primeros estudiantes agregados
        if self.results['students_added']:
            report_lines.append("\n✅ PRIMEROS ESTUDIANTES AGREGADOS:")
            for i, student in enumerate(self.results['students_added'][:5]):
                req_mark = "🚨" if student.get('requisitoriado') else "✅"
                report_lines.append(
                    f"   {i + 1}. {student.get('codigo')} - {student.get('nombre')} {student.get('apellidos')} {req_mark}")

            if len(self.results['students_added']) > 5:
                report_lines.append(f"   ... y {len(self.results['students_added']) - 5} más")

        return "\n".join(report_lines)

    async def run(self, max_students: int = None, dry_run: bool = False):
        """Ejecutar el procesamiento completo"""
        if dry_run:
            logger.info("🔍 MODO DRY RUN - Solo validar archivos sin procesar")

            image_files = self.validate_image_files()
            logger.info(f"\n📋 ARCHIVOS ENCONTRADOS PARA PROCESAR:")

            for i, image_path in enumerate(image_files[:10]):  # Mostrar solo primeros 10
                try:
                    student_data = self.parse_filename(image_path.name)
                    req_mark = "🚨" if student_data["requisitoriado"] else "✅"
                    logger.info(
                        f"   {i + 1}. {student_data['codigo']} - {student_data['nombre']} {student_data['apellidos']} {req_mark}")
                except Exception as e:
                    logger.error(f"   {i + 1}. ❌ {image_path.name} - Error: {e}")

            if len(image_files) > 10:
                logger.info(f"   ... y {len(image_files) - 10} más")

            logger.info(f"\n📊 Total archivos válidos: {len(image_files)}")
            logger.info("💡 Ejecuta sin --dry-run para procesar realmente")
            return True

        # Inicializar servicios
        if not await self.initialize_services():
            return False

        # Procesar estudiantes
        results = await self.process_all_students(max_students)

        # Mostrar reporte
        print(self.generate_summary_report())

        return results["successful"] > 0


async def main():
    """Función principal"""
    import argparse

    parser = argparse.ArgumentParser(description="Agregar estudiantes en masa desde archivos de imagen")
    parser.add_argument("--folder", default="estudiantes_fotos",
                        help="Carpeta con las imágenes (default: estudiantes_fotos)")
    parser.add_argument("--max", type=int, help="Máximo número de estudiantes a procesar")
    parser.add_argument("--dry-run", action="store_true", help="Solo validar archivos sin procesar")

    args = parser.parse_args()

    logger.info("🎓 AGREGADOR MASIVO DE ESTUDIANTES ACADÉMICOS")
    logger.info("=" * 50)
    logger.info(f"📁 Carpeta: {args.folder}")
    logger.info(f"🎯 Máximo: {args.max if args.max else 'Sin límite'}")
    logger.info(f"🔍 Dry run: {'✅' if args.dry_run else '❌'}")
    logger.info(f"📧 Dominio email: @upao.edu.pe")
    logger.info(f"🚨 Probabilidad requisitoriado: 15%")

    adder = BulkStudentAdder(args.folder)
    success = await adder.run(args.max, args.dry_run)

    if success:
        logger.info("\n🎉 PROCESAMIENTO COMPLETADO EXITOSAMENTE")
        if not args.dry_run:
            logger.info("🚀 Próximos pasos:")
            logger.info("   1. python -m app.main  # Ejecutar API")
            logger.info("   2. POST /api/recognize  # Probar reconocimiento")
            logger.info("   3. GET /api/students    # Ver estudiantes agregados")
        return 0
    else:
        logger.error("❌ PROCESAMIENTO FALLÓ")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())