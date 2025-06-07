#!/usr/bin/env python3
"""
Script para ejecutar el servidor de desarrollo
"""

import os
import sys
import uvicorn
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


def main():
    """Función principal para ejecutar el servidor"""

    # Configuración del servidor
    config = {
        "app": "app.main:app",
        "host": os.getenv("API_HOST", "0.0.0.0"),
        "port": int(os.getenv("API_PORT", "8000")),
        "reload": os.getenv("DEBUG", "True").lower() == "true",
        "log_level": os.getenv("LOG_LEVEL", "info").lower(),
        "access_log": True,
        "reload_dirs": ["app"] if os.getenv("DEBUG", "True").lower() == "true" else None
    }

    print("🚀 Iniciando servidor de Reconocimiento Facial...")
    print(f"📍 Host: {config['host']}")
    print(f"🔗 Puerto: {config['port']}")
    print(f"🔄 Reload: {config['reload']}")
    print(f"📊 Log Level: {config['log_level']}")
    print(f"🌐 URL: http://{config['host']}:{config['port']}")
    print(f"📚 Docs: http://{config['host']}:{config['port']}/docs")
    print("-" * 50)

    try:
        uvicorn.run(**config)
    except KeyboardInterrupt:
        print("\n✋ Servidor detenido por el usuario")
    except Exception as e:
        print(f"\n❌ Error al iniciar el servidor: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()