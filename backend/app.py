#!/usr/bin/env python3
"""
Entry point principal para Render deployment
Este archivo simplifica el acceso a la aplicación FastAPI
"""

import os
import sys
import logging
from pathlib import Path

# Configurar path para imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Configurar logging temprano
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    # Importar la aplicación FastAPI
    from app.main import app

    logger.info("✅ Aplicación FastAPI importada correctamente")
    logger.info(f"🌍 Entorno: {'PRODUCCIÓN' if os.getenv('DEBUG', 'False') != 'True' else 'DESARROLLO'}")
    logger.info(f"🔗 Puerto configurado: {os.getenv('PORT', os.getenv('API_PORT', '10000'))}")

    # Verificar configuración crítica
    required_vars = ["DATABASE_URL"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.warning(f"⚠️ Variables faltantes: {missing_vars}")
    else:
        logger.info("✅ Variables de entorno configuradas")

    # Exponer la aplicación para gunicorn
    application = app

except ImportError as e:
    logger.error(f"❌ Error al importar la aplicación: {e}")
    logger.error("📍 Verifica que la estructura de carpetas sea correcta")
    sys.exit(1)
except Exception as e:
    logger.error(f"❌ Error inesperado: {e}")
    sys.exit(1)

# Para ejecución directa (desarrollo)
if __name__ == "__main__":
    import uvicorn

    # Configuración para servidor (Railway)
    port = int(os.getenv("PORT", "8000"))  # Railway usa PORT
    host = os.getenv("API_HOST", "0.0.0.0")

    logger.info(f"🚀 Ejecutando en servidor: {host}:{port}")

    uvicorn.run(
        "app:application",
        host=host,
        port=port,
        reload=os.getenv("DEBUG", "False") == "True",
        log_level="info"
    )