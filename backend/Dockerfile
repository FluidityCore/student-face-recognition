FROM python:3.9-slim

# Instalar dependencias del sistema incluyendo CMake
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    python3-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Verificar CMake
RUN cmake --version

WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# NO CMD - Railway usará el Procfile