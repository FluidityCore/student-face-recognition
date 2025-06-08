import os
import uuid
import cv2
import numpy as np
from PIL import Image, ImageOps, ExifTags
from fastapi import UploadFile, HTTPException
from typing import Tuple, Optional, List, Union
import logging
from datetime import datetime
import hashlib
import tempfile
import time
import shutil

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImageProcessor:
    """Utilidades para procesamiento de imágenes - Railway + Cloudflare R2"""

    def __init__(self):
        """Inicializar configuración de procesamiento de imágenes"""
        self.max_image_size = int(os.getenv("MAX_IMAGE_SIZE", "10485760"))  # 10MB
        self.allowed_formats = os.getenv("ALLOWED_IMAGE_FORMATS", "jpg,jpeg,png,bmp").split(",")
        self.upload_dir = os.getenv("UPLOAD_DIR", "temp_uploads")

        # En Railway, usamos directorios temporales principalmente
        self.use_r2 = os.getenv("USE_CLOUDFLARE_R2", "false").lower() == "true"

        # Crear directorios si no existen (solo para fallback local)
        self._create_directories()

        logger.info(f"✅ ImageProcessor inicializado - Formatos: {self.allowed_formats}")
        logger.info(f"☁️ Cloudflare R2: {'Habilitado' if self.use_r2 else 'Deshabilitado'}")

    def _create_directories(self):
        """Crear directorios necesarios para almacenamiento temporal"""
        try:
            directories = [
                self.upload_dir,
                os.path.join(self.upload_dir, "reference"),
                os.path.join(self.upload_dir, "recognition"),
                os.path.join(self.upload_dir, "test"),
                os.path.join(self.upload_dir, "temp")
            ]

            for directory in directories:
                os.makedirs(directory, exist_ok=True)

            logger.info("✅ Directorios de imágenes creados")

        except Exception as e:
            logger.error(f"❌ Error al crear directorios: {e}")
            # En Railway, no es crítico si no se pueden crear directorios
            logger.warning("⚠️ Continuando sin directorios locales (solo R2)")

    def is_valid_image(self, file: UploadFile) -> bool:
        """Validar si el archivo es una imagen válida"""
        try:
            # Verificar tamaño
            if hasattr(file, 'size') and file.size and file.size > self.max_image_size:
                logger.warning(f"Imagen muy grande: {file.size} bytes")
                return False

            # Verificar formato por extensión
            if not file.filename:
                logger.warning("Archivo sin nombre")
                return False

            file_extension = file.filename.lower().split('.')[-1]
            if file_extension not in self.allowed_formats:
                logger.warning(f"Formato no permitido: {file_extension}")
                return False

            # Verificar content-type
            valid_content_types = [
                "image/jpeg", "image/jpg", "image/png",
                "image/bmp", "image/webp"
            ]

            if hasattr(file, 'content_type') and file.content_type:
                if file.content_type not in valid_content_types:
                    logger.warning(f"Content-type no válido: {file.content_type}")
                    return False

            return True

        except Exception as e:
            logger.error(f"❌ Error al validar imagen: {e}")
            return False

    async def save_image(self, file: UploadFile, category: str = "temp") -> str:
        """
        Guardar imagen usando Cloudflare R2 o almacenamiento local
        category: 'reference', 'recognition', 'test', 'temp'
        """
        try:
            logger.info(f"📤 Guardando imagen en categoría: {category}")

            if self.use_r2:
                # Usar Cloudflare R2
                try:
                    from ..services.cloudflare_r2 import CloudflareR2Service
                    r2_service = CloudflareR2Service()

                    if r2_service.is_available():
                        logger.info(f"☁️ Subiendo imagen a Cloudflare R2: {category}")
                        return await r2_service.upload_image(file, category)
                    else:
                        logger.warning("⚠️ R2 no disponible, usando almacenamiento temporal")

                except ImportError as e:
                    logger.warning(f"⚠️ Servicio R2 no importable: {e}")
                except Exception as e:
                    logger.error(f"❌ Error con R2: {e}")

            # Fallback: almacenamiento temporal local
            return await self._save_image_temp(file, category)

        except Exception as e:
            logger.error(f"❌ Error al guardar imagen: {e}")
            raise

    async def _save_image_temp(self, file: UploadFile, category: str = "temp") -> str:
        """Guardar imagen en almacenamiento temporal (para Railway)"""
        try:
            # Leer contenido del archivo
            content = await file.read()

            if len(content) == 0:
                raise ValueError("Archivo de imagen vacío")

            # Generar nombre único con timestamp
            file_extension = file.filename.lower().split('.')[-1] if file.filename else "jpg"
            unique_filename = f"{category}_{int(time.time())}_{uuid.uuid4().hex[:8]}.{file_extension}"

            # Crear archivo temporal
            temp_dir = tempfile.gettempdir()
            file_path = os.path.join(temp_dir, unique_filename)

            # Guardar archivo
            with open(file_path, "wb") as buffer:
                buffer.write(content)

            # Procesar imagen si es necesario
            processed_path = await self._process_image(file_path, category)

            logger.info(f"✅ Imagen guardada temporalmente: {processed_path}")
            return processed_path

        except Exception as e:
            logger.error(f"❌ Error al guardar imagen temporal: {e}")
            # Limpiar archivo si existe
            if 'file_path' in locals() and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
            raise

    async def save_image_from_path(self, file_path: str, subfolder: str = "uploads") -> str:
        """
        Subir imagen desde un archivo local a Cloudflare R2

        Args:
            file_path: Ruta del archivo local
            subfolder: Subcarpeta en R2 (uploads, reference, recognition, etc.)

        Returns:
            URL pública de la imagen en Cloudflare R2
        """
        try:
            logger.info(f"📤 Subiendo imagen desde: {file_path}")

            # Verificar que el archivo existe
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Archivo no encontrado: {file_path}")

            # Si Cloudflare R2 está habilitado
            if self.use_r2:
                try:
                    from ..services.cloudflare_r2 import CloudflareR2Service
                    r2_service = CloudflareR2Service()

                    if r2_service.is_available():
                        # Subir desde archivo local
                        image_url = r2_service.upload_image_from_path(file_path, subfolder)
                        logger.info(f"✅ Imagen subida a R2: {image_url}")
                        return image_url
                    else:
                        logger.warning("⚠️ R2 no disponible")

                except ImportError as e:
                    logger.warning(f"⚠️ R2 service no disponible: {e}")
                except Exception as e:
                    logger.error(f"❌ Error al subir a R2: {e}")

            # Fallback: copiar a almacenamiento local temporal
            return await self._save_locally_from_path(file_path, subfolder)

        except Exception as e:
            logger.error(f"❌ Error al procesar imagen desde {file_path}: {e}")
            raise

    async def _save_locally_from_path(self, file_path: str, subfolder: str) -> str:
        """
        Copiar archivo a almacenamiento local temporal (fallback para Railway)
        """
        try:
            # En Railway, usar directorio temporal del sistema
            temp_dir = tempfile.gettempdir()
            dest_dir = os.path.join(temp_dir, "railway_images", subfolder)
            os.makedirs(dest_dir, exist_ok=True)

            # Generar nombre único
            file_extension = os.path.splitext(file_path)[1]
            unique_filename = f"railway_{int(time.time())}_{uuid.uuid4().hex[:8]}{file_extension}"
            dest_path = os.path.join(dest_dir, unique_filename)

            # Copiar archivo
            shutil.copy2(file_path, dest_path)

            logger.info(f"📁 Imagen copiada temporalmente: {dest_path}")
            return dest_path

        except Exception as e:
            logger.error(f"❌ Error al copiar archivo localmente: {e}")
            raise

    async def _process_image(self, image_path: str, category: str) -> str:
        """Procesar y optimizar imagen para Railway"""
        try:
            # Verificar si la imagen es válida antes de procesarla
            if not os.path.exists(image_path):
                logger.error(f"❌ Archivo no existe: {image_path}")
                return image_path

            # Intentar abrir imagen con PIL
            try:
                image = Image.open(image_path)
            except Exception as e:
                logger.warning(f"⚠️ No se pudo procesar imagen: {e}")
                return image_path  # Retornar original si no se puede procesar

            # Corregir orientación basada en EXIF
            image = self._fix_image_orientation(image)

            # Optimizar según categoría (más agresivo en Railway para ahorrar espacio)
            if category == "reference":
                image = self._optimize_for_reference(image)
            elif category == "recognition":
                image = self._optimize_for_recognition(image)
            else:
                image = self._optimize_general(image)

            # Convertir a RGB si es necesario
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")

            # Guardar imagen procesada con mayor compresión para Railway
            quality = 75 if category in ["temp", "test"] else 85
            image.save(image_path, "JPEG", quality=quality, optimize=True)

            logger.info(f"✅ Imagen procesada: {image_path}")
            return image_path

        except Exception as e:
            logger.warning(f"⚠️ Error al procesar imagen: {e}")
            return image_path  # Retornar original si falla el procesamiento

    def _fix_image_orientation(self, image: Image.Image) -> Image.Image:
        """Corregir orientación de imagen basada en datos EXIF"""
        try:
            # Usar ExifTags para obtener orientación
            exif = image.getexif()
            if exif:
                for tag_id, value in exif.items():
                    tag = ExifTags.TAGS.get(tag_id, tag_id)
                    if tag == 'Orientation':
                        if value == 3:
                            image = image.rotate(180, expand=True)
                        elif value == 6:
                            image = image.rotate(270, expand=True)
                        elif value == 8:
                            image = image.rotate(90, expand=True)
                        break

            return image

        except Exception as e:
            logger.warning(f"⚠️ Error corrigiendo orientación: {e}")
            return image  # Retornar original si falla

    def _optimize_for_reference(self, image: Image.Image) -> Image.Image:
        """Optimizar imagen para referencia (alta calidad pero optimizada para Railway)"""
        try:
            # Redimensionar para Railway - mantener calidad pero optimizar tamaño
            width, height = image.size
            max_dimension = max(width, height)

            # En Railway, ser más agresivo con el tamaño para ahorrar memoria
            if max_dimension > 1024:
                scale_factor = 1024 / max_dimension
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            elif width < 300 or height < 300:
                # Asegurar tamaño mínimo para face recognition
                min_dimension = min(width, height)
                if min_dimension < 300:
                    scale_factor = 300 / min_dimension
                    new_width = int(width * scale_factor)
                    new_height = int(height * scale_factor)
                    image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Mejorar contraste ligeramente
            image = ImageOps.autocontrast(image, cutoff=1)

            return image

        except Exception as e:
            logger.warning(f"⚠️ Error al optimizar imagen de referencia: {e}")
            return image

    def _optimize_for_recognition(self, image: Image.Image) -> Image.Image:
        """Optimizar imagen para reconocimiento (equilibrio calidad/velocidad en Railway)"""
        try:
            # Redimensionar para reconocimiento eficiente en Railway
            width, height = image.size
            max_side = max(width, height)

            # Ser más conservador en Railway para mejor performance
            if max_side > 600:
                scale_factor = 600 / max_side
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Normalizar contraste
            image = ImageOps.autocontrast(image, cutoff=2)

            return image

        except Exception as e:
            logger.warning(f"⚠️ Error al optimizar imagen de reconocimiento: {e}")
            return image

    def _optimize_general(self, image: Image.Image) -> Image.Image:
        """Optimización general para Railway (más agresiva para ahorrar recursos)"""
        try:
            # Redimensionar más agresivamente en Railway
            width, height = image.size
            if width > 800 or height > 800:
                image.thumbnail((800, 800), Image.Resampling.LANCZOS)

            return image

        except Exception as e:
            logger.warning(f"⚠️ Error en optimización general: {e}")
            return image

    def get_image_info(self, image_path: str) -> dict:
        """Obtener información de la imagen (compatible con URLs de R2)"""
        try:
            # Verificar si es URL de R2 o archivo local
            if image_path.startswith("http"):
                # Es una URL de R2
                if self.use_r2:
                    try:
                        from ..services.cloudflare_r2 import CloudflareR2Service
                        r2_service = CloudflareR2Service()
                        if r2_service.is_available():
                            r2_info = r2_service.get_file_info(image_path)
                            if r2_info:
                                return r2_info
                    except ImportError:
                        pass

                # Fallback para URLs - info básica
                return {
                    "filename": os.path.basename(image_path),
                    "url": image_path,
                    "type": "remote_url",
                    "storage": "cloudflare_r2"
                }

            # Es un archivo local
            if not os.path.exists(image_path):
                return {"error": "Archivo no encontrado", "path": image_path}

            try:
                image = Image.open(image_path)
                file_size = os.path.getsize(image_path)

                # Información básica
                info = {
                    "filename": os.path.basename(image_path),
                    "format": image.format,
                    "mode": image.mode,
                    "size": image.size,
                    "width": image.width,
                    "height": image.height,
                    "file_size": file_size,
                    "file_size_mb": round(file_size / (1024 * 1024), 2),
                    "type": "local_file",
                    "storage": "temporary"
                }

                # Calcular hash para verificar duplicados (solo para archivos pequeños)
                if file_size < 5 * 1024 * 1024:  # Solo para archivos < 5MB
                    try:
                        with open(image_path, "rb") as f:
                            file_hash = hashlib.md5(f.read()).hexdigest()
                        info["hash"] = file_hash
                    except:
                        info["hash"] = "unavailable"

                return info

            except Exception as e:
                return {"error": f"Error procesando imagen: {e}", "path": image_path}

        except Exception as e:
            logger.error(f"❌ Error al obtener info de imagen: {e}")
            return {"error": str(e)}

    def convert_to_opencv(self, image_path: str) -> Optional[np.ndarray]:
        """Convertir imagen a formato OpenCV (compatible con URLs)"""
        try:
            # Verificar si es URL o archivo local
            if image_path.startswith("http"):
                # Para URLs, descargar la imagen
                import requests
                response = requests.get(image_path, timeout=30)
                if response.status_code == 200:
                    # Convertir bytes a numpy array
                    image_array = np.frombuffer(response.content, np.uint8)
                    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
                else:
                    logger.error(f"❌ Error descargando imagen: {response.status_code}")
                    return None
            else:
                # Archivo local
                if not os.path.exists(image_path):
                    logger.error(f"❌ Archivo no encontrado: {image_path}")
                    return None
                image = cv2.imread(image_path)

            if image is None:
                logger.error(f"❌ No se pudo cargar imagen: {image_path}")
                return None

            # OpenCV usa BGR, convertir a RGB para compatibilidad
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            return rgb_image

        except Exception as e:
            logger.error(f"❌ Error al convertir a OpenCV: {e}")
            return None

    def cleanup_temp_files(self, max_age_hours: int = 1):
        """Limpiar archivos temporales (optimizado para Railway)"""
        try:
            deleted_count = 0

            # Si estamos usando R2, limpiar archivos temporales en R2
            if self.use_r2:
                try:
                    from ..services.cloudflare_r2 import CloudflareR2Service
                    r2_service = CloudflareR2Service()
                    if r2_service.is_available():
                        # En Railway, limpiar más frecuentemente
                        max_age_days = max(1, max_age_hours // 24)
                        r2_deleted = r2_service.cleanup_old_files("temp", max_age_days)
                        deleted_count += r2_deleted
                        logger.info(f"✅ Limpieza R2 completada: {r2_deleted} archivos eliminados")
                except ImportError:
                    pass
                except Exception as e:
                    logger.warning(f"⚠️ Error en limpieza R2: {e}")

            # Limpiar archivos temporales locales (Railway)
            temp_dirs = [
                tempfile.gettempdir(),
                os.path.join(tempfile.gettempdir(), "railway_images")
            ]

            current_time = time.time()
            max_age_seconds = max_age_hours * 3600

            for temp_dir in temp_dirs:
                if not os.path.exists(temp_dir):
                    continue

                try:
                    for root, dirs, files in os.walk(temp_dir):
                        for filename in files:
                            # Solo limpiar archivos de imagen
                            if any(filename.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.bmp']):
                                file_path = os.path.join(root, filename)
                                try:
                                    file_age = current_time - os.path.getmtime(file_path)
                                    if file_age > max_age_seconds:
                                        os.remove(file_path)
                                        deleted_count += 1
                                except:
                                    pass  # Ignorar errores de archivos individuales
                except Exception as e:
                    logger.warning(f"⚠️ Error limpiando {temp_dir}: {e}")

            logger.info(f"✅ Limpieza temporal completada: {deleted_count} archivos eliminados")
            return deleted_count

        except Exception as e:
            logger.error(f"❌ Error en limpieza de archivos: {e}")
            return 0

    def delete_image(self, image_path: str) -> bool:
        """Eliminar imagen de forma segura (compatible con R2 y local)"""
        try:
            # Verificar si es URL de R2 o archivo local
            if image_path.startswith("http"):
                # Es una URL de R2
                if self.use_r2:
                    try:
                        from ..services.cloudflare_r2 import CloudflareR2Service
                        r2_service = CloudflareR2Service()
                        if r2_service.is_available():
                            success = r2_service.delete_file(image_path)
                            if success:
                                logger.info(f"✅ Imagen eliminada de R2: {image_path}")
                            return success
                    except ImportError:
                        logger.warning("⚠️ Servicio R2 no disponible para eliminar imagen")
                        return False
                return False
            else:
                # Es un archivo local
                if os.path.exists(image_path):
                    os.remove(image_path)
                    logger.info(f"✅ Imagen eliminada localmente: {image_path}")
                    return True
                return False

        except Exception as e:
            logger.error(f"❌ Error al eliminar imagen: {e}")
            return False

    def get_directory_stats(self) -> dict:
        """Obtener estadísticas de almacenamiento (Railway optimizado)"""
        try:
            # Si estamos usando R2, obtener stats de R2
            if self.use_r2:
                try:
                    from ..services.cloudflare_r2 import CloudflareR2Service
                    r2_service = CloudflareR2Service()
                    if r2_service.is_available():
                        r2_stats = r2_service.get_bucket_stats()
                        r2_stats["type"] = "cloudflare_r2"
                        return r2_stats
                except ImportError:
                    pass
                except Exception as e:
                    logger.warning(f"⚠️ Error obteniendo stats R2: {e}")

            # Stats temporales locales (Railway)
            stats = {}
            total_files = 0
            total_size = 0

            temp_dirs = [
                tempfile.gettempdir(),
                os.path.join(tempfile.gettempdir(), "railway_images")
            ]

            for temp_dir in temp_dirs:
                if os.path.exists(temp_dir):
                    try:
                        files = [f for f in os.listdir(temp_dir)
                                 if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
                        dir_size = sum(
                            os.path.getsize(os.path.join(temp_dir, f))
                            for f in files if os.path.isfile(os.path.join(temp_dir, f))
                        )

                        total_files += len(files)
                        total_size += dir_size

                    except Exception as e:
                        logger.warning(f"⚠️ Error obteniendo stats de {temp_dir}: {e}")

            return {
                "type": "railway_temporary",
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "storage_location": "temporary_directories",
                "note": "Railway uses temporary storage for processing"
            }

        except Exception as e:
            logger.error(f"❌ Error al obtener estadísticas: {e}")
            return {"type": "unknown", "error": str(e)}

    def get_storage_type(self) -> str:
        """Obtener tipo de almacenamiento actual"""
        if self.use_r2:
            return "Cloudflare R2 + Railway Temporary"
        else:
            return "Railway Temporary Storage"

    async def download_from_url(self, url: str, category: str = "temp") -> str:
        """Descargar imagen desde URL y guardarla temporalmente en Railway"""
        try:
            import requests

            logger.info(f"📥 Descargando imagen desde: {url}")

            # Descargar imagen con timeout
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            if len(response.content) == 0:
                raise ValueError("Contenido de imagen vacío")

            # Generar nombre único
            filename = f"downloaded_{category}_{int(time.time())}_{uuid.uuid4().hex[:8]}.jpg"

            # Usar directorio temporal del sistema
            temp_dir = tempfile.gettempdir()
            file_path = os.path.join(temp_dir, filename)

            # Guardar imagen
            with open(file_path, "wb") as f:
                f.write(response.content)

            logger.info(f"✅ Imagen descargada: {url} → {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"❌ Error descargando imagen: {e}")
            raise

    def create_temp_file(self, content: bytes, extension: str = "jpg") -> str:
        """Crear archivo temporal con contenido específico"""
        try:
            # Generar nombre único
            filename = f"temp_{int(time.time())}_{uuid.uuid4().hex[:8]}.{extension}"

            # Usar directorio temporal del sistema
            temp_dir = tempfile.gettempdir()
            file_path = os.path.join(temp_dir, filename)

            # Escribir contenido
            with open(file_path, "wb") as f:
                f.write(content)

            logger.info(f"📄 Archivo temporal creado: {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"❌ Error creando archivo temporal: {e}")
            raise