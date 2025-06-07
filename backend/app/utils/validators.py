import re
import os
from typing import Optional, List
from fastapi import HTTPException


class Validators:
    """Validadores para diferentes tipos de datos"""

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validar formato de email"""
        if not email:
            return False

        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def validate_student_code(code: str) -> bool:
        """Validar código de estudiante"""
        if not code:
            return False

        # Código debe tener entre 3 y 20 caracteres, solo alfanuméricos
        pattern = r'^[A-Za-z0-9]{3,20}$'
        return re.match(pattern, code) is not None

    @staticmethod
    def validate_name(name: str) -> bool:
        """Validar nombre/apellido"""
        if not name or len(name.strip()) < 2:
            return False

        # Solo letras, espacios, acentos y guiones
        pattern = r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s\-]+$'
        return re.match(pattern, name.strip()) is not None

    @staticmethod
    def validate_file_path(file_path: str) -> bool:
        """Validar que el archivo existe y es accesible"""
        try:
            return os.path.exists(file_path) and os.path.isfile(file_path)
        except Exception:
            return False

    @staticmethod
    def validate_image_size(file_size: int, max_size: int = 10485760) -> bool:
        """Validar tamaño de imagen (default 10MB)"""
        return 0 < file_size <= max_size

    @staticmethod
    def validate_confidence_level(confidence: str) -> bool:
        """Validar nivel de confianza"""
        valid_levels = ["Alta", "Media", "Baja"]
        return confidence in valid_levels

    @staticmethod
    def validate_similarity(similarity: float) -> bool:
        """Validar valor de similitud"""
        return 0.0 <= similarity <= 1.0

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitizar nombre de archivo"""
        if not filename:
            return "unnamed"

        # Eliminar caracteres peligrosos
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)

        # Limitar longitud
        if len(filename) > 100:
            name, ext = os.path.splitext(filename)
            filename = name[:90] + ext

        return filename or "unnamed"

    @staticmethod
    def validate_pagination(skip: int, limit: int) -> tuple:
        """Validar parámetros de paginación"""
        skip = max(0, skip)
        limit = max(1, min(1000, limit))
        return skip, limit


class SecurityValidator:
    """Validadores de seguridad"""

    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        """Validar dirección IP"""
        if not ip:
            return False

        # IPv4
        ipv4_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'

        # IPv6 básico
        ipv6_pattern = r'^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'

        return re.match(ipv4_pattern, ip) or re.match(ipv6_pattern, ip)

    @staticmethod
    def validate_user_agent(user_agent: str) -> bool:
        """Validar user agent (básico)"""
        if not user_agent:
            return True  # Permitir vacío

        # Verificar longitud razonable
        return len(user_agent) <= 500

    @staticmethod
    def is_safe_path(path: str, base_dir: str) -> bool:
        """Verificar que el path está dentro del directorio base (prevenir path traversal)"""
        try:
            real_path = os.path.realpath(path)
            real_base = os.path.realpath(base_dir)
            return real_path.startswith(real_base)
        except Exception:
            return False


class APIValidator:
    """Validadores específicos para API"""

    @staticmethod
    def validate_recognition_threshold(threshold: float) -> bool:
        """Validar umbral de reconocimiento"""
        return 0.1 <= threshold <= 1.0

    @staticmethod
    def validate_processing_time(time: float) -> bool:
        """Validar tiempo de procesamiento"""
        return 0.0 <= time <= 300.0  # Máximo 5 minutos

    @staticmethod
    def validate_encoding_length(encoding: List[float]) -> bool:
        """Validar longitud de encoding facial"""
        # Longitud esperada depende del modelo usado
        expected_lengths = [128, 256, 512, 768]  # Longitudes comunes
        return len(encoding) in expected_lengths

    @staticmethod
    def raise_validation_error(message: str, field: str = None):
        """Lanzar error de validación"""
        detail = f"Error de validación en {field}: {message}" if field else message
        raise HTTPException(status_code=422, detail=detail)


def validate_student_data(nombre: str, apellidos: str, codigo: str, correo: Optional[str] = None):
    """Validar datos completos de estudiante"""
    validators = Validators()

    if not validators.validate_name(nombre):
        APIValidator.raise_validation_error("Nombre inválido", "nombre")

    if not validators.validate_name(apellidos):
        APIValidator.raise_validation_error("Apellidos inválidos", "apellidos")

    if not validators.validate_student_code(codigo):
        APIValidator.raise_validation_error("Código de estudiante inválido", "codigo")

    if correo and not validators.validate_email(correo):
        APIValidator.raise_validation_error("Email inválido", "correo")


def validate_recognition_data(similarity: float, confidence: str, processing_time: float):
    """Validar datos de reconocimiento"""
    validators = Validators()
    api_validator = APIValidator()

    if not validators.validate_similarity(similarity):
        api_validator.raise_validation_error("Similitud debe estar entre 0.0 y 1.0", "similarity")

    if not validators.validate_confidence_level(confidence):
        api_validator.raise_validation_error("Nivel de confianza inválido", "confidence")

    if not api_validator.validate_processing_time(processing_time):
        api_validator.raise_validation_error("Tiempo de procesamiento inválido", "processing_time")