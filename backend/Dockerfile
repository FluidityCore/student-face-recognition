# ==========================================
# DOCKERFILE PARA RAILWAY + RECONOCIMIENTO FACIAL ACADÉMICO
# ==========================================

FROM python:3.9-slim

# Configurar variables de entorno
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8000

# Instalar dependencias del sistema para dlib y OpenCV
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    libboost-python-dev \
    libopencv-dev \
    python3-opencv \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar requirements primero para aprovechar el cache de Docker
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Crear directorios necesarios
RUN mkdir -p dlib_models models temp_uploads

# Descargar modelos dlib automáticamente
RUN python setup_dlib_models.py

# Configurar permisos
RUN chmod +x app.py

# Exponer puerto
EXPOSE $PORT

# Comando de inicio para Railway
CMD ["python", "app.py"]