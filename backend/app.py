#!/usr/bin/env python3
"""
Entry point principal para Railway deployment
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


def get_port():
    """Obtiene el puerto de forma robusta para Railway"""
    port_str = os.environ.get('PORT', '8000')

    # Log para debugging
    logger.info(f"🔍 PORT environment variable: '{port_str}'")

    # Si es una cadena vacía o None, usar 8000
    if not port_str or port_str.strip() == '':
        logger.warning("⚠️ PORT variable empty, using default 8000")
        return 8000

    # Si contiene variables no expandidas, usar 8000
    if '$' in port_str:
        logger.warning(f"⚠️ PORT variable not expanded: {port_str}, using default 8000")
        return 8000

    try:
        port = int(port_str)
        logger.info(f"✅ Using port: {port}")
        return port
    except ValueError:
        logger.warning(f"⚠️ Invalid PORT value: {port_str}, using default 8000")
        return 8000


try:
    # Importar la aplicación FastAPI
    from app.main import app

    logger.info("✅ Aplicación FastAPI importada correctamente")
    logger.info(f"🌍 Entorno: {'PRODUCCIÓN' if os.getenv('DEBUG', 'False') != 'True' else 'DESARROLLO'}")

    # Log del puerto para Railway
    port = get_port()
    logger.info(f"🔗 Puerto configurado: {port}")

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

# Para ejecución directa (desarrollo local)
if __name__ == "__main__":
    import uvicorn

    # Configuración para Railway
    port = get_port()
    host = os.getenv("API_HOST", "0.0.0.0")

    logger.info(f"🚀 Ejecutando en Railway: {host}:{port}")
    logger.info(f"🔧 Debug mode: {os.getenv('DEBUG', 'False') == 'True'}")

    uvicorn.run(
        "app:application",
        host=host,
        port=port,
        reload=os.getenv("DEBUG", "False") == "True",
        log_level="info"
    )