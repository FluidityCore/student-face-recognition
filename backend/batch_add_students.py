#!/usr/bin/env python3
"""
Script para agregar estudiantes en masa basado en nombres de archivos
Formato esperado: apellido1_apellido2_nombre1_nombre2_codigo_email.jpg
Ejemplo: HERRERA_ANGULO_JOSE_MIGUEL_000245501_jherreraa6.jpg
"""

import os
import sys
import asyncio
import random
import requests
import logging
from pathlib import Path
from typing import List, Dict, Any
import time

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BatchStudentLoader:
    """Cargador masivo de estudiantes desde archivos de imagen"""

    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url.rstrip('/')
        self.results = {
            'success': [],
            'failed': [],
            'skipped': []
        }

    def parse_filename(self, filename: str) -> Dict[str, str]:
        """
        Parsear nombre de archivo según formato:
        apellido1_apellido2_nombre1_nombre2_codigo_email.jpg

        Ejemplo: HERRERA_ANGULO_JOSE_MIGUEL_000245501_jherreraa6.jpg
        """
        try:
            # Remover extensión
            name_without_ext = filename.rsplit('.', 1)[0]

            # Dividir por guiones bajos
            parts = name_without_ext.split('_')

            if len(parts) < 6:
                raise ValueError(f"Formato incorrecto. Se esperan al menos 6 partes, se encontraron {len(parts)}")

            # Identificar partes por posición
            apellido1 = parts[0].title()
            apellido2 = parts[1].title()

            # Los nombres pueden ser múltiples palabras
            # Buscar dónde empiezan los códigos (números)
            codigo_index = None
            for i in range(2, len(parts)):
                if parts[i].isdigit() or parts[i].startswith('0'):
                    codigo_index = i
                    break

            if codigo_index is None:
                raise ValueError("No se encontró código numérico en el nombre del archivo")

            # Extraer nombres (entre apellidos y código)
            nombres_parts = parts[2:codigo_index]
            nombres = ' '.join([name.title() for name in nombres_parts])

            # Extraer código y email
            codigo = parts[codigo_index]
            email_part = parts[codigo_index + 1] if codigo_index + 1 < len(parts) else codigo.lower()

            # Construir datos del estudiante
            student_data = {
                'nombres': nombres,
                'apellidos': f"{apellido1} {apellido2}",
                'codigo': codigo,
                'email': f"{email_part}@upao.edu.pe",
                'requisitoriado': random.choice([True, False])  # Aleatorio
            }

            logger.info(
                f"📄 Parseado: {student_data['apellidos']}, {student_data['nombres']} ({student_data['codigo']})")

            return student_data

        except Exception as e:
            logger.error(f"❌ Error parseando '{filename}': {e}")
            raise

    def find_image_files(self, directory: str) -> List[str]:
        """Encontrar todos los archivos de imagen en el directorio"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
        image_files = []

        directory_path = Path(directory)

        if not directory_path.exists():
            raise FileNotFoundError(f"Directorio no encontrado: {directory}")

        for file_path in directory_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                image_files.append(str(file_path))

        logger.info(f"📁 Encontrados {len(image_files)} archivos de imagen en {directory}")
        return sorted(image_files)

    def test_api_connection(self) -> bool:
        """Probar conexión con la API"""
        try:
            response = requests.get(f"{self.api_base_url}/health", timeout=10)
            if response.status_code == 200:
                logger.info(f"✅ API conectada: {self.api_base_url}")
                return True
            else:
                logger.error(f"❌ API responde con error: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Error conectando con API: {e}")
            return False

    async def create_student(self, student_data: Dict[str, str], image_path: str) -> Dict[str, Any]:
        """Crear un estudiante usando la API"""
        try:
            # Preparar datos para multipart form
            files = {
                'image': ('image.jpg', open(image_path, 'rb'), 'image/jpeg')
            }

            data = {
                'nombre': student_data['nombres'],
                'apellidos': student_data['apellidos'],
                'codigo': student_data['codigo'],
                'correo': student_data['email'],
                'requisitoriado': student_data['requisitoriado']
            }

            logger.info(f"📤 Creando estudiante: {student_data['apellidos']}, {student_data['nombres']}")

            # Realizar request
            response = requests.post(
                f"{self.api_base_url}/api/students/",
                files=files,
                data=data,
                timeout=60
            )

            # Cerrar archivo
            files['image'][1].close()

            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Estudiante creado: {result.get('codigo', 'N/A')} - ID: {result.get('id', 'N/A')}")

                return {
                    'status': 'success',
                    'student_data': student_data,
                    'api_response': result,
                    'image_path': image_path
                }
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"❌ Error creando estudiante: {error_msg}")

                return {
                    'status': 'failed',
                    'student_data': student_data,
                    'error': error_msg,
                    'image_path': image_path
                }

        except Exception as e:
            logger.error(f"❌ Excepción creando estudiante: {e}")
            return {
                'status': 'failed',
                'student_data': student_data,
                'error': str(e),
                'image_path': image_path
            }

    async def process_images_batch(self, image_files: List[str], batch_size: int = 5, delay: float = 1.0):
        """Procesar imágenes en lotes para evitar sobrecargar la API"""
        total_files = len(image_files)

        logger.info(f"🚀 Iniciando procesamiento de {total_files} imágenes en lotes de {batch_size}")

        for i in range(0, total_files, batch_size):
            batch = image_files[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_files + batch_size - 1) // batch_size

            logger.info(f"📦 Procesando lote {batch_num}/{total_batches} ({len(batch)} imágenes)")

            # Procesar lote
            batch_tasks = []
            for image_path in batch:
                try:
                    # Parsear nombre de archivo
                    filename = os.path.basename(image_path)
                    student_data = self.parse_filename(filename)

                    # Crear tarea asíncrona
                    task = self.create_student(student_data, image_path)
                    batch_tasks.append(task)

                except Exception as e:
                    logger.error(f"❌ Error procesando {image_path}: {e}")
                    self.results['skipped'].append({
                        'image_path': image_path,
                        'error': str(e)
                    })

            # Ejecutar lote de tareas
            if batch_tasks:
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

                # Procesar resultados
                for result in batch_results:
                    if isinstance(result, Exception):
                        logger.error(f"❌ Excepción en lote: {result}")
                        continue

                    if result['status'] == 'success':
                        self.results['success'].append(result)
                    else:
                        self.results['failed'].append(result)

            # Delay entre lotes para no sobrecargar
            if i + batch_size < total_files:
                logger.info(f"⏸️ Esperando {delay}s antes del siguiente lote...")
                await asyncio.sleep(delay)

        logger.info("✅ Procesamiento de lotes completado")

    def generate_report(self) -> Dict[str, Any]:
        """Generar reporte final del procesamiento"""
        total_processed = len(self.results['success']) + len(self.results['failed']) + len(self.results['skipped'])

        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total_images': total_processed,
                'successful': len(self.results['success']),
                'failed': len(self.results['failed']),
                'skipped': len(self.results['skipped']),
                'success_rate': round(
                    (len(self.results['success']) / total_processed * 100) if total_processed > 0 else 0, 2)
            },
            'details': self.results
        }

        return report

    def print_report(self):
        """Imprimir reporte en consola"""
        report = self.generate_report()
        summary = report['summary']

        logger.info("\n" + "=" * 60)
        logger.info("📊 REPORTE FINAL DE CARGA MASIVA")
        logger.info("=" * 60)
        logger.info(f"📄 Total de imágenes procesadas: {summary['total_images']}")
        logger.info(f"✅ Estudiantes creados exitosamente: {summary['successful']}")
        logger.info(f"❌ Errores de creación: {summary['failed']}")
        logger.info(f"⚠️ Archivos omitidos: {summary['skipped']}")
        logger.info(f"📈 Tasa de éxito: {summary['success_rate']}%")

        # Mostrar errores si los hay
        if self.results['failed']:
            logger.info("\n❌ ERRORES ENCONTRADOS:")
            for i, failed in enumerate(self.results['failed'][:5], 1):  # Mostrar solo primeros 5
                student = failed['student_data']
                logger.info(f"   {i}. {student['apellidos']}, {student['nombres']} - {failed['error'][:100]}")

            if len(self.results['failed']) > 5:
                logger.info(f"   ... y {len(self.results['failed']) - 5} errores más")

        if self.results['skipped']:
            logger.info("\n⚠️ ARCHIVOS OMITIDOS:")
            for i, skipped in enumerate(self.results['skipped'][:3], 1):  # Mostrar solo primeros 3
                logger.info(f"   {i}. {os.path.basename(skipped['image_path'])} - {skipped['error']}")

        logger.info("=" * 60)

    async def run_batch_load(self, images_directory: str, batch_size: int = 5, delay: float = 1.0):
        """Ejecutar carga masiva completa"""
        logger.info("🚀 INICIANDO CARGA MASIVA DE ESTUDIANTES")
        logger.info("=" * 50)

        try:
            # 1. Verificar conexión API
            if not self.test_api_connection():
                logger.error("❌ No se puede conectar con la API")
                return False

            # 2. Encontrar archivos de imagen
            image_files = self.find_image_files(images_directory)

            if not image_files:
                logger.error(f"❌ No se encontraron imágenes en {images_directory}")
                return False

            # 3. Mostrar preview de algunos archivos
            logger.info("🔍 Preview de archivos a procesar:")
            for i, img_file in enumerate(image_files[:3]):
                try:
                    filename = os.path.basename(img_file)
                    student_data = self.parse_filename(filename)
                    logger.info(
                        f"   {i + 1}. {student_data['apellidos']}, {student_data['nombres']} ({student_data['codigo']})")
                except Exception as e:
                    logger.info(f"   {i + 1}. {filename} - ERROR: {e}")

            if len(image_files) > 3:
                logger.info(f"   ... y {len(image_files) - 3} archivos más")

            # 4. Confirmar procesamiento
            response = input(f"\n¿Procesar {len(image_files)} imágenes? (y/N): ")
            if response.lower() != 'y':
                logger.info("❌ Procesamiento cancelado por el usuario")
                return False

            # 5. Procesar en lotes
            await self.process_images_batch(image_files, batch_size, delay)

            # 6. Generar reporte
            self.print_report()

            return len(self.results['success']) > 0

        except Exception as e:
            logger.error(f"❌ Error en carga masiva: {e}")
            return False


async def main():
    """Función principal"""
    import argparse

    parser = argparse.ArgumentParser(description="Carga masiva de estudiantes desde imágenes")
    parser.add_argument(
        "directory",
        help="Directorio con las imágenes de estudiantes"
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="URL base de la API (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="Tamaño del lote para procesamiento (default: 5)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay en segundos entre lotes (default: 1.0)"
    )

    args = parser.parse_args()

    # Crear cargador
    loader = BatchStudentLoader(args.api_url)

    # Ejecutar carga masiva
    success = await loader.run_batch_load(
        args.directory,
        args.batch_size,
        args.delay
    )

    if success:
        logger.info("🎉 Carga masiva completada exitosamente")
        return 0
    else:
        logger.error("❌ Carga masiva falló")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())