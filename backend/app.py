#!/usr/bin/env python3
"""
Entry point principal para Railway deployment - FIX ASGI ERROR
"""

import os
import sys
import logging
from pathlib import Path

# Configurar path para imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Configurar logging mínimo
logging.basicConfig(
    level=logging.WARNING,  # Solo warnings y errores
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_port():
    """Obtiene el puerto de forma robusta para Railway"""
    port_str = os.environ.get('PORT', '8000')

    if not port_str or port_str.strip() == '':
        logger.warning("PORT variable empty, using default 8000")
        return 8000

    try:
        port = int(port_str)
        logger.info(f"Using Railway port: {port}")
        return port
    except ValueError:
        logger.warning(f"Invalid PORT value: {port_str}, using default 8000")
        return 8000


try:
    # ✅ FIX: Importar la aplicación FastAPI
    from app.main import app

    # ✅ FIX: Crear variable 'application' que Railway/uvicorn espera
    application = app

    logger.info("✅ FastAPI app imported successfully")
    logger.info("✅ ASGI application variable created")

    # Log mínimo de configuración
    if os.getenv('USE_CLOUDFLARE_D1') == 'true':
        logger.info("☁️ Cloudflare D1 enabled")
    if os.getenv('USE_CLOUDFLARE_R2') == 'true':
        logger.info("☁️ Cloudflare R2 enabled")

except ImportError as e:
    logger.error(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    logger.error(f"❌ Unexpected error: {e}")
    sys.exit(1)

# Para ejecución directa (Railway automático)
if __name__ == "__main__":
    import uvicorn

    port = get_port()
    host = "0.0.0.0"

    logger.info(f"🚀 Starting Railway server on {host}:{port}")

    # ✅ FIX: Usar la variable 'app' directamente, no 'application'
    uvicorn.run(
        app,  # Pasar el objeto app directamente
        host=host,
        port=port,
        reload=False,
        log_level="warning",
        workers=1,
        access_log=False
    )