#!/usr/bin/env python3
"""
Entry point principal para Railway deployment
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

    # Railway siempre proporciona PORT, pero por seguridad
    if not port_str or port_str.strip() == '':
        logger.warning("⚠️ PORT variable empty, using default 8000")
        return 8000

    try:
        port = int(port_str)
        logger.info(f"✅ Using Railway port: {port}")
        return port
    except ValueError:
        logger.warning(f"⚠️ Invalid PORT value: {port_str}, using default 8000")
        return 8000


try:
    # Importar la aplicación FastAPI
    from app.main import app

    logger.info("✅ Aplicación FastAPI importada correctamente")
    logger.info(f"🌍 Entorno: PRODUCCIÓN Railway")
    logger.info(f"☁️ Cloudflare D1: {'✅' if os.getenv('USE_CLOUDFLARE_D1') == 'true' else '❌'}")
    logger.info(f"☁️ Cloudflare R2: {'✅' if os.getenv('USE_CLOUDFLARE_R2') == 'true' else '❌'}")

    # Verificar configuración crítica
    required_vars = [
        "CLOUDFLARE_ACCOUNT_ID",
        "CLOUDFLARE_API_TOKEN",
        "CLOUDFLARE_D1_DATABASE_ID",
        "CLOUDFLARE_R2_ACCESS_KEY"
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"❌ Variables críticas faltantes: {missing_vars}")
        logger.error("💡 Configura las variables de entorno en Railway")
    else:
        logger.info("✅ Variables de entorno Railway configuradas")

    # Exponer la aplicación para Railway
    application = app

except ImportError as e:
    logger.error(f"❌ Error al importar la aplicación: {e}")
    sys.exit(1)
except Exception as e:
    logger.error(f"❌ Error inesperado: {e}")
    sys.exit(1)

# Para ejecución directa (Railway automático)
if __name__ == "__main__":
    import uvicorn

    # Configuración para Railway
    port = get_port()
    host = "0.0.0.0"  # Railway requiere 0.0.0.0

    logger.info(f"🚀 Iniciando servidor Railway en {host}:{port}")

    uvicorn.run(
        "app:application",
        host=host,
        port=port,
        reload=False,  # Nunca reload en producción
        log_level="info",
        workers=1  # Railway funciona mejor con 1 worker
    )