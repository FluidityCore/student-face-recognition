from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from datetime import datetime


# Schemas para Estudiante
class StudentBase(BaseModel):
    """Schema base para estudiante"""
    nombre: str
    apellidos: str
    codigo: str
    correo: Optional[str] = None
    requisitoriado: bool = False

    @validator('nombre', 'apellidos')
    def validate_names(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('El nombre y apellidos deben tener al menos 2 caracteres')
        return v.strip().title()

    @validator('codigo')
    def validate_codigo(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError('El código debe tener al menos 3 caracteres')
        return v.strip().upper()

    @validator('correo')
    def validate_correo(cls, v):
        # ✅ FIX: Validación más flexible - permite None, vacío o email válido
        if not v or v.strip() == '':
            return None

        # Solo validar formato si tiene contenido
        if '@' not in v:
            # ✅ FIX: En lugar de error, normalizar valores inválidos
            return None  # O podrías retornar v si quieres mantener el valor original

        return v.strip().lower()


class StudentCreate(StudentBase):
    """Schema para crear estudiante"""
    imagen_path: Optional[str] = None
    face_encoding: Optional[List[float]] = None


class StudentUpdate(BaseModel):
    """Schema para actualizar estudiante"""
    nombre: Optional[str] = None
    apellidos: Optional[str] = None
    codigo: Optional[str] = None
    correo: Optional[str] = None
    requisitoriado: Optional[bool] = None
    imagen_path: Optional[str] = None
    face_encoding: Optional[List[float]] = None

    @validator('nombre', 'apellidos')
    def validate_names(cls, v):
        if v is not None and (not v or len(v.strip()) < 2):
            raise ValueError('El nombre y apellidos deben tener al menos 2 caracteres')
        return v.strip().title() if v else v

    @validator('codigo')
    def validate_codigo(cls, v):
        if v is not None and (not v or len(v.strip()) < 3):
            raise ValueError('El código debe tener al menos 3 caracteres')
        return v.strip().upper() if v else v

    @validator('correo')
    def validate_correo(cls, v):
        # ✅ FIX: Validación flexible para updates también
        if not v or v.strip() == '':
            return None
        if '@' not in v:
            return None
        return v.strip().lower()


class StudentResponse(StudentBase):
    """Schema para respuesta de estudiante - FIX VALIDATION"""
    id: int
    imagen_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    active: bool

    # ✅ FIX: Override validator para ser más permisivo en responses
    @validator('correo')
    def validate_correo_response(cls, v):
        # Para responses, ser muy permisivo
        if not v:
            return None
        # No validar formato en responses, solo limpiar
        return str(v).strip() if v else None

    class Config:
        from_attributes = True


# Schemas para Reconocimiento
class RecognitionResult(BaseModel):
    """Schema para resultado de reconocimiento"""
    found: bool
    student: Optional[StudentResponse] = None
    similarity: float = 0.0
    confidence: str = "Baja"  # Alta, Media, Baja
    processing_time: float = 0.0
    message: str = ""

    @validator('confidence')
    def validate_confidence(cls, v):
        valid_values = ["Alta", "Media", "Baja"]
        if v not in valid_values:
            raise ValueError(f'Confianza debe ser uno de: {valid_values}')
        return v

    @validator('similarity')
    def validate_similarity(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('La similitud debe estar entre 0.0 y 1.0')
        return round(v, 3)


class RecognitionLog(BaseModel):
    """Schema para log de reconocimiento"""
    found: bool
    student_id: Optional[int] = None
    similarity: float = 0.0
    confidence: str = "Baja"
    processing_time: float = 0.0
    image_path: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class RecognitionLogResponse(RecognitionLog):
    """Schema para respuesta de log de reconocimiento"""
    id: int
    timestamp: datetime
    student: Optional[StudentResponse] = None

    class Config:
        from_attributes = True


# Schemas para Estadísticas
class RecognitionStats(BaseModel):
    """Schema para estadísticas de reconocimiento"""
    total_recognitions: int = 0
    successful_recognitions: int = 0
    failed_recognitions: int = 0
    success_rate: float = 0.0
    average_processing_time: float = 0.0
    total_students: int = 0
    requisitoriados: int = 0

    # Estadísticas por confianza
    high_confidence: int = 0
    medium_confidence: int = 0
    low_confidence: int = 0

    # Estadísticas de tiempo
    last_recognition: Optional[datetime] = None
    recognitions_today: int = 0
    recognitions_this_week: int = 0


class SystemInfo(BaseModel):
    """Schema para información del sistema"""
    version: str = "1.0.0"
    status: str = "active"
    database_status: str = "connected"
    total_students: int = 0
    recognition_threshold: float = 0.8
    max_image_size: int = 10485760
    allowed_formats: List[str] = ["jpg", "jpeg", "png", "bmp"]
    uptime: str = "0 days"


# Schemas para Configuración
class SystemConfigBase(BaseModel):
    """Schema base para configuración del sistema"""
    key: str
    value: str
    description: Optional[str] = None

    @validator('key')
    def validate_key(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError('La clave debe tener al menos 3 caracteres')
        return v.strip().lower()


class SystemConfigCreate(SystemConfigBase):
    """Schema para crear configuración"""
    pass


class SystemConfigUpdate(BaseModel):
    """Schema para actualizar configuración"""
    value: Optional[str] = None
    description: Optional[str] = None


class SystemConfigResponse(SystemConfigBase):
    """Schema para respuesta de configuración"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Schemas para respuestas generales
class MessageResponse(BaseModel):
    """Schema para respuestas simples con mensaje"""
    message: str
    success: bool = True
    data: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Schema para respuestas de error"""
    error: str
    detail: Optional[str] = None
    code: Optional[int] = None


# Schemas para pruebas y desarrollo
class FaceDetectionTest(BaseModel):
    """Schema para prueba de detección facial"""
    face_detected: bool
    encoding_length: Optional[int] = None
    message: str
    confidence_score: Optional[float] = None


class HealthCheck(BaseModel):
    """Schema para health check"""
    status: str = "ok"
    message: str = "API funcionando correctamente"
    version: str = "1.0.0"
    timestamp: datetime = datetime.utcnow()
    database_connected: bool = True


# Esquemas para paginación
class PaginationParams(BaseModel):
    """Schema para parámetros de paginación"""
    skip: int = 0
    limit: int = 100

    @validator('skip')
    def validate_skip(cls, v):
        if v < 0:
            raise ValueError('Skip debe ser mayor o igual a 0')
        return v

    @validator('limit')
    def validate_limit(cls, v):
        if not 1 <= v <= 1000:
            raise ValueError('Limit debe estar entre 1 y 1000')
        return v


class PaginatedResponse(BaseModel):
    """Schema para respuestas paginadas"""
    items: List[Any]
    total: int
    skip: int
    limit: int
    has_next: bool
    has_previous: bool