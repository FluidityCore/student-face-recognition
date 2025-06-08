import os
import uuid
import cv2
import numpy as np
from PIL import Image, ImageOps, ExifTags
from fastapi import UploadFile, HTTPException
from typing import Tuple, Optional, List
import logging
from datetime import datetime
import hashlib

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImageProcessor:
    """Utilidades para procesamiento de imágenes"""

    def __init__(self):
        """Inicializar configuración de procesamiento de imágenes"""
        self.max_image_size = int(os.getenv("MAX_IMAGE_SIZE", "10485760"))  # 10MB
        self.allowed_formats = os.getenv("ALLOWED_IMAGE_FORMATS", "jpg,jpeg,png,bmp").split(",")
        self.upload_dir = os.getenv("UPLOAD_DIR", "uploads")

        # Crear directorios si no existen
        self._create_directories()

        logger.info(f"✅ ImageProcessor inicializado - Formatos: {self.allowed_formats}")

    def _create_directories(self):
        """Crear directorios necesarios"""
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
            raise

    def is_valid_image(self, file: UploadFile) -> bool:
        """Validar si el archivo es una imagen válida"""
        try:
            # Verificar tamaño
            if file.size > self.max_image_size:
                logger.warning(f"Imagen muy grande: {file.size} bytes")
                return False

            # Verificar formato por extensión
            if not file.filename:
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
            # Verificar si usar Cloudflare R2
            use_r2 = os.getenv("USE_CLOUDFLARE_R2", "false").lower() == "true"

            if use_r2:
                # Usar Cloudflare R2
                try:
                    from ..services.cloudflare_r2 import CloudflareR2Service
                    r2_service = CloudflareR2Service()

                    if r2_service.is_available():
                        logger.info(f"📤 Subiendo imagen a Cloudflare R2: {category}")
                        return await r2_service.upload_image(file, category)
                    else:
                        logger.warning("⚠️ R2 no disponible, usando almacenamiento local")
                except ImportError:
                    logger.warning("⚠️ Servicio R2 no disponible, usando almacenamiento local")

            # Fallback: almacenamiento local
            return await self._save_image_local(file, category)

        except Exception as e:
            logger.error(f"❌ Error al guardar imagen: {e}")
            raise

    async def _save_image_local(self, file: UploadFile, category: str = "temp") -> str:
        """Guardar imagen en almacenamiento local (método original)"""
        try:
            # Generar nombre único
            file_extension = file.filename.lower().split('.')[-1]
            unique_filename = f"{uuid.uuid4().hex}_{int(datetime.now().timestamp())}.{file_extension}"

            # Determinar directorio
            save_dir = os.path.join(self.upload_dir, category)
            file_path = os.path.join(save_dir, unique_filename)

            # Leer contenido del archivo
            content = await file.read()

            # Guardar archivo temporalmente
            with open(file_path, "wb") as buffer:
                buffer.write(content)

            # Procesar y optimizar imagen
            processed_path = await self._process_image(file_path, category)

            # Si se procesó correctamente, eliminar original si es diferente
            if processed_path != file_path and os.path.exists(file_path):
                os.remove(file_path)

            logger.info(f"✅ Imagen guardada localmente: {processed_path}")
            return processed_path

        except Exception as e:
            logger.error(f"❌ Error al guardar imagen local: {e}")
            # Limpiar archivo si existe
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            raise

    async def _process_image(self, image_path: str, category: str) -> str:
        """Procesar y optimizar imagen"""
        try:
            # Abrir imagen con PIL
            image = Image.open(image_path)

            # Corregir orientación basada en EXIF
            image = self._fix_image_orientation(image)

            # Optimizar según categoría
            if category == "reference":
                image = self._optimize_for_reference(image)
            elif category == "recognition":
                image = self._optimize_for_recognition(image)
            else:
                image = self._optimize_general(image)

            # Guardar imagen procesada
            processed_path = image_path.replace(".", "_processed.")

            # Convertir a RGB si es necesario
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")

            # Guardar con calidad optimizada
            image.save(processed_path, "JPEG", quality=85, optimize=True)

            return image_path

        except Exception as e:
            logger.error(f"❌ Error al procesar imagen: {e}")
            return image_path  # Retornar original si falla el procesamiento

    def _fix_image_orientation(self, image: Image.Image) -> Image.Image:
        """Corregir orientación de imagen basada en datos EXIF"""
        try:
            if hasattr(image, '_getexif'):
                exif = image._getexif()
                if exif is not None:
                    for tag, value in exif.items():
                        if tag in ExifTags.TAGS and ExifTags.TAGS[tag] == 'Orientation':
                            if value == 3:
                                image = image.rotate(180, expand=True)
                            elif value == 6:
                                image = image.rotate(270, expand=True)
                            elif value == 8:
                                image = image.rotate(90, expand=True)
                            break

            return image

        except Exception:
            return image  # Retornar original si falla

    def _optimize_for_reference(self, image: Image.Image) -> Image.Image:
        """Optimizar imagen para referencia (alta calidad)"""
        try:
            # Redimensionar manteniendo aspecto, mínimo 512px en el lado más corto
            width, height = image.size
            min_side = min(width, height)

            if min_side < 512:
                scale_factor = 512 / min_side
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            elif min_side > 1024:
                scale_factor = 1024 / min_side
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Mejorar contraste y nitidez ligeramente
            image = ImageOps.autocontrast(image, cutoff=1)

            return image

        except Exception as e:
            logger.warning(f"Error al optimizar imagen de referencia: {e}")
            return image

    def _optimize_for_recognition(self, image: Image.Image) -> Image.Image:
        """Optimizar imagen para reconocimiento (equilibrio calidad/velocidad)"""
        try:
            # Redimensionar para reconocimiento eficiente
            width, height = image.size
            max_side = max(width, height)

            if max_side > 800:
                scale_factor = 800 / max_side
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Normalizar contraste
            image = ImageOps.autocontrast(image, cutoff=2)

            return image

        except Exception as e:
            logger.warning(f"Error al optimizar imagen de reconocimiento: {e}")
            return image

    def _optimize_general(self, image: Image.Image) -> Image.Image:
        """Optimización general para otras categorías"""
        try:
            # Redimensionar si es muy grande
            width, height = image.size
            if width > 1200 or height > 1200:
                image.thumbnail((1200, 1200), Image.Resampling.LANCZOS)

            return image

        except Exception as e:
            logger.warning(f"Error en optimización general: {e}")
            return image

    def get_image_info(self, image_path: str) -> dict:
        """Obtener información de la imagen"""
        try:
            # Verificar si es URL de R2 o archivo local
            if image_path.startswith("http"):
                # Es una URL de R2, usar servicio R2 para obtener info
                try:
                    from ..services.cloudflare_r2 import CloudflareR2Service
                    r2_service = CloudflareR2Service()
                    if r2_service.is_available():
                        return r2_service.get_file_info(image_path) or {}
                except ImportError:
                    pass

                # Si no se puede obtener info de R2, retornar info básica
                return {
                    "filename": os.path.basename(image_path),
                    "url": image_path,
                    "type": "remote"
                }

            # Es un archivo local
            image = Image.open(image_path)

            # Información básica
            info = {
                "filename": os.path.basename(image_path),
                "format": image.format,
                "mode": image.mode,
                "size": image.size,
                "width": image.width,
                "height": image.height,
                "file_size": os.path.getsize(image_path),
                "type": "local"
            }

            # Calcular hash para verificar duplicados
            with open(image_path, "rb") as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            info["hash"] = file_hash

            return info

        except Exception as e:
            logger.error(f"❌ Error al obtener info de imagen: {e}")
            return {}

    def resize_image(self, image_path: str, target_size: Tuple[int, int],
                     maintain_aspect: bool = True) -> str:
        """Redimensionar imagen a tamaño específico"""
        try:
            image = Image.open(image_path)

            if maintain_aspect:
                image.thumbnail(target_size, Image.Resampling.LANCZOS)
            else:
                image = image.resize(target_size, Image.Resampling.LANCZOS)

            # Guardar imagen redimensionada
            resized_path = image_path.replace(".", "_resized.")
            image.save(resized_path, "JPEG", quality=85)

            return resized_path

        except Exception as e:
            logger.error(f"❌ Error al redimensionar imagen: {e}")
            raise

    def convert_to_opencv(self, image_path: str) -> Optional[np.ndarray]:
        """Convertir imagen a formato OpenCV"""
        try:
            # Verificar si es URL o archivo local
            if image_path.startswith("http"):
                # Para URLs, necesitamos descargar la imagen primero
                import requests
                response = requests.get(image_path)
                if response.status_code == 200:
                    # Convertir bytes a numpy array
                    image_array = np.frombuffer(response.content, np.uint8)
                    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
                else:
                    logger.error(f"Error descargando imagen: {response.status_code}")
                    return None
            else:
                # Archivo local
                image = cv2.imread(image_path)

            if image is None:
                return None

            # OpenCV usa BGR, convertir a RGB para compatibilidad
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            return rgb_image

        except Exception as e:
            logger.error(f"❌ Error al convertir a OpenCV: {e}")
            return None

    def cleanup_temp_files(self, max_age_hours: int = 24):
        """Limpiar archivos temporales antiguos"""
        try:
            # Si estamos usando R2, limpiar archivos temporales en R2
            use_r2 = os.getenv("USE_CLOUDFLARE_R2", "false").lower() == "true"

            if use_r2:
                try:
                    from ..services.cloudflare_r2 import CloudflareR2Service
                    r2_service = CloudflareR2Service()
                    if r2_service.is_available():
                        deleted_count = r2_service.cleanup_old_files("temp", max_age_hours // 24)
                        logger.info(f"✅ Limpieza R2 completada: {deleted_count} archivos eliminados")
                        return deleted_count
                except ImportError:
                    pass

            # Limpiar archivos locales
            temp_dir = os.path.join(self.upload_dir, "temp")
            current_time = datetime.now().timestamp()
            max_age_seconds = max_age_hours * 3600

            deleted_count = 0

            for filename in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age_seconds:
                        os.remove(file_path)
                        deleted_count += 1

            logger.info(f"✅ Limpieza local completada: {deleted_count} archivos eliminados")
            return deleted_count

        except Exception as e:
            logger.error(f"❌ Error en limpieza de archivos: {e}")
            return 0

    def delete_image(self, image_path: str) -> bool:
        """Eliminar imagen de forma segura"""
        try:
            # Verificar si es URL de R2 o archivo local
            if image_path.startswith("http"):
                # Es una URL de R2
                try:
                    from ..services.cloudflare_r2 import CloudflareR2Service
                    r2_service = CloudflareR2Service()
                    if r2_service.is_available():
                        success = r2_service.delete_file(image_path)
                        if success:
                            logger.info(f"✅ Imagen eliminada de R2: {image_path}")
                        return success
                except ImportError:
                    logger.warning("Servicio R2 no disponible para eliminar imagen")
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
        """Obtener estadísticas de directorios de imágenes"""
        try:
            # Si estamos usando R2, obtener stats de R2
            use_r2 = os.getenv("USE_CLOUDFLARE_R2", "false").lower() == "true"

            if use_r2:
                try:
                    from ..services.cloudflare_r2 import CloudflareR2Service
                    r2_service = CloudflareR2Service()
                    if r2_service.is_available():
                        return r2_service.get_bucket_stats()
                except ImportError:
                    pass

            # Stats locales
            stats = {}

            for category in ["reference", "recognition", "test", "temp"]:
                category_dir = os.path.join(self.upload_dir, category)
                if os.path.exists(category_dir):
                    files = os.listdir(category_dir)
                    total_size = sum(
                        os.path.getsize(os.path.join(category_dir, f))
                        for f in files if os.path.isfile(os.path.join(category_dir, f))
                    )

                    stats[category] = {
                        "file_count": len(files),
                        "total_size_bytes": total_size,
                        "total_size_mb": round(total_size / (1024 * 1024), 2)
                    }
                else:
                    stats[category] = {
                        "file_count": 0,
                        "total_size_bytes": 0,
                        "total_size_mb": 0.0
                    }

            return {
                "type": "local",
                "categories": stats,
                "total_files": sum(cat["file_count"] for cat in stats.values()),
                "total_size_mb": sum(cat["total_size_mb"] for cat in stats.values())
            }

        except Exception as e:
            logger.error(f"❌ Error al obtener estadísticas: {e}")
            return {}

    def get_storage_type(self) -> str:
        """Obtener tipo de almacenamiento actual"""
        use_r2 = os.getenv("USE_CLOUDFLARE_R2", "false").lower() == "true"
        return "Cloudflare R2" if use_r2 else "Local Storage"

    async def download_from_url(self, url: str, category: str = "temp") -> str:
        """Descargar imagen desde URL y guardarla localmente"""
        try:
            import requests

            # Descargar imagen
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Generar nombre único
            filename = f"downloaded_{uuid.uuid4().hex}.jpg"

            # Guardar en directorio local
            save_dir = os.path.join(self.upload_dir, category)
            file_path = os.path.join(save_dir, filename)

            with open(file_path, "wb") as f:
                f.write(response.content)

            logger.info(f"✅ Imagen descargada: {url} → {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"❌ Error descargando imagen: {e}")
            raise