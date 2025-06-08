from typing import Optional, Dict, Any, List
import os
import boto3
import uuid
import logging
from datetime import datetime
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.config import Config
from fastapi import UploadFile
import mimetypes


logger = logging.getLogger(__name__)


class CloudflareR2Service:
    """Servicio para interactuar con Cloudflare R2 Storage"""

    def __init__(self):
        """Inicializar servicio R2"""
        self.account_id = os.getenv("CLOUDFLARE_R2_ACCOUNT_ID") or os.getenv("CLOUDFLARE_ACCOUNT_ID")
        self.access_key = os.getenv("CLOUDFLARE_R2_ACCESS_KEY")
        self.secret_key = os.getenv("CLOUDFLARE_R2_SECRET_KEY")
        self.bucket_name = os.getenv("CLOUDFLARE_R2_BUCKET_NAME", "student-images")
        self.endpoint_url = os.getenv("CLOUDFLARE_R2_ENDPOINT")
        self.public_url = os.getenv("CLOUDFLARE_R2_PUBLIC_URL")

        self.enabled = all([
            self.account_id, self.access_key, self.secret_key,
            self.endpoint_url, self.public_url
        ])

        if self.enabled:
            try:
                # Configurar cliente S3 compatible
                self.s3_client = boto3.client(
                    's3',
                    endpoint_url=self.endpoint_url,
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                    region_name='auto',  # Cloudflare usa 'auto'
                    config=Config(
                        signature_version='v4',
                        retries={'max_attempts': 3}
                    )
                )

                # Probar conexión
                self._test_connection()
                logger.info("✅ Cloudflare R2 configurado y conectado")

            except Exception as e:
                logger.error(f"❌ Error configurando R2: {e}")
                self.enabled = False
        else:
            logger.warning("⚠️ Cloudflare R2 no configurado - usando almacenamiento local")
            self.s3_client = None

    def _test_connection(self) -> bool:
        """Probar conexión con R2"""
        try:
            # Intentar listar objetos del bucket
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.error(f"❌ Bucket '{self.bucket_name}' no existe")
            elif error_code == '403':
                logger.error("❌ Sin permisos para acceder al bucket")
            else:
                logger.error(f"❌ Error de conexión R2: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Error inesperado en R2: {e}")
            raise

    def _generate_filename(self, original_filename: str, category: str = "students") -> str:
        """Generar nombre único para archivo"""
        # Obtener extensión
        _, ext = os.path.splitext(original_filename)
        if not ext:
            ext = '.jpg'  # Default

        # Generar nombre único
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        unique_id = uuid.uuid4().hex[:8]

        return f"{category}/{timestamp}_{unique_id}{ext}"

    def upload_file(self, file_content: bytes, filename: str, category: str = "students") -> str:
        """Subir archivo a R2"""
        if not self.enabled:
            raise Exception("Cloudflare R2 no está configurado")

        try:
            # Generar nombre único
            key = self._generate_filename(filename, category)

            # Detectar content type
            content_type = mimetypes.guess_type(filename)[0] or 'image/jpeg'

            # Configurar metadatos
            metadata = {
                'original-filename': filename,
                'upload-timestamp': datetime.utcnow().isoformat(),
                'category': category
            }

            # Subir archivo
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=file_content,
                ContentType=content_type,
                Metadata=metadata,
                # Configurar cache
                CacheControl='public, max-age=31536000'  # 1 año
            )

            # Retornar URL pública
            public_url = f"{self.public_url.rstrip('/')}/{key}"

            logger.info(f"✅ Archivo subido a R2: {key}")
            return public_url

        except ClientError as e:
            logger.error(f"❌ Error subiendo a R2: {e}")
            raise Exception(f"Error de almacenamiento: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Error inesperado subiendo a R2: {e}")
            raise

    async def upload_image(self, file: UploadFile, category: str = "students") -> str:
        """Subir imagen desde UploadFile a R2"""
        try:
            # Leer contenido del archivo
            content = await file.read()

            # Validar tamaño
            max_size = int(os.getenv("MAX_IMAGE_SIZE", "10485760"))  # 10MB
            if len(content) > max_size:
                raise Exception(f"Archivo muy grande: {len(content)} bytes (máximo: {max_size})")

            # Validar tipo de archivo
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/bmp']
            if file.content_type not in allowed_types:
                raise Exception(f"Tipo de archivo no permitido: {file.content_type}")

            # Subir archivo
            return self.upload_file(content, file.filename or "unknown.jpg", category)

        except Exception as e:
            logger.error(f"❌ Error subiendo imagen: {e}")
            raise

    def delete_file(self, file_url: str) -> bool:
        """Eliminar archivo de R2"""
        if not self.enabled:
            return False

        try:
            # Extraer key desde URL
            if file_url.startswith(self.public_url):
                key = file_url.replace(self.public_url.rstrip('/') + '/', '')
            else:
                logger.warning(f"URL no corresponde a R2: {file_url}")
                return False

            # Eliminar archivo
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)

            logger.info(f"✅ Archivo eliminado de R2: {key}")
            return True

        except ClientError as e:
            logger.error(f"❌ Error eliminando de R2: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error inesperado eliminando de R2: {e}")
            return False

    def get_file_info(self, file_url: str) -> Optional[Dict[str, Any]]:
        """Obtener información de archivo en R2"""
        if not self.enabled:
            return None

        try:
            # Extraer key desde URL
            if file_url.startswith(self.public_url):
                key = file_url.replace(self.public_url.rstrip('/') + '/', '')
            else:
                return None

            # Obtener metadatos
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=key)

            return {
                "key": key,
                "size": response.get('ContentLength', 0),
                "content_type": response.get('ContentType', ''),
                "last_modified": response.get('LastModified'),
                "metadata": response.get('Metadata', {}),
                "public_url": file_url
            }

        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.warning(f"Archivo no encontrado en R2: {file_url}")
            else:
                logger.error(f"Error obteniendo info de R2: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado obteniendo info de R2: {e}")
            return None

    def list_files(self, category: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Listar archivos en R2"""
        if not self.enabled:
            return []

        try:
            # Configurar parámetros de búsqueda
            params = {
                'Bucket': self.bucket_name,
                'MaxKeys': limit
            }

            if category:
                params['Prefix'] = f"{category}/"

            # Listar objetos
            response = self.s3_client.list_objects_v2(**params)

            files = []
            for obj in response.get('Contents', []):
                files.append({
                    "key": obj['Key'],
                    "size": obj['Size'],
                    "last_modified": obj['LastModified'],
                    "public_url": f"{self.public_url.rstrip('/')}/{obj['Key']}"
                })

            return files

        except Exception as e:
            logger.error(f"❌ Error listando archivos R2: {e}")
            return []

    def get_bucket_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del bucket"""
        if not self.enabled:
            return {"enabled": False}

        try:
            # Listar todos los objetos para estadísticas
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)

            total_files = response.get('KeyCount', 0)
            total_size = sum(obj['Size'] for obj in response.get('Contents', []))

            # Estadísticas por categoría
            categories = {}
            for obj in response.get('Contents', []):
                key = obj['Key']
                category = key.split('/')[0] if '/' in key else 'root'

                if category not in categories:
                    categories[category] = {"count": 0, "size": 0}

                categories[category]["count"] += 1
                categories[category]["size"] += obj['Size']

            return {
                "enabled": True,
                "bucket_name": self.bucket_name,
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "categories": categories,
                "public_url": self.public_url
            }

        except Exception as e:
            logger.error(f"❌ Error obteniendo stats de R2: {e}")
            return {
                "enabled": True,
                "error": str(e)
            }

    def cleanup_old_files(self, category: str = "temp", days: int = 7) -> int:
        """Limpiar archivos antiguos de una categoría"""
        if not self.enabled:
            return 0

        try:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Listar archivos de la categoría
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=f"{category}/"
            )

            deleted_count = 0
            for obj in response.get('Contents', []):
                if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                    try:
                        self.s3_client.delete_object(Bucket=self.bucket_name, Key=obj['Key'])
                        deleted_count += 1
                    except Exception as e:
                        logger.error(f"Error eliminando {obj['Key']}: {e}")

            logger.info(f"✅ Limpieza R2 completada: {deleted_count} archivos eliminados")
            return deleted_count

        except Exception as e:
            logger.error(f"❌ Error en limpieza R2: {e}")
            return 0

    def is_available(self) -> bool:
        """Verificar si R2 está disponible"""
        return self.enabled and self.s3_client is not None