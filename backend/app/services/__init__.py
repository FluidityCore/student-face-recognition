# Inicialización del paquete services
from .database_service import StudentService, LogService, ConfigService
from .face_recognition import FaceRecognitionService
from .cloudflare_r2 import CloudflareR2Service
from .cloudflare_d1 import CloudflareD1Service
from .cloudflare_adapter import CloudflareAdapter

__all__ = [
    "StudentService",
    "LogService",
    "ConfigService",
    "FaceRecognitionService",
    "CloudflareR2Service",
    "CloudflareD1Service",
    "CloudflareAdapter"
]