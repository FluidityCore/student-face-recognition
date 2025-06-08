#!/usr/bin/env python3
"""
Script para probar conexión con Cloudflare D1 y R2
"""

import os
import sys
from dotenv import load_dotenv

# Asegura que 'app' esté en sys.path para los imports
APP_PATH = os.path.join(os.path.dirname(__file__), "app")
if APP_PATH not in sys.path:
    sys.path.insert(0, APP_PATH)

from app.services.cloudflare_d1 import CloudflareD1Service
from app.services.cloudflare_r2 import CloudflareR2Service
from app.services.cloudflare_adapter import CloudflareAdapter

# Cargar variables de entorno
load_dotenv()


def test_d1_connection():
    """Probar conexión con Cloudflare D1"""
    print("🗄️ Probando Cloudflare D1...")

    try:
        d1 = CloudflareD1Service()

        if not d1.enabled:
            print("❌ D1 no configurado - Verifica variables de entorno:")
            print(f"   CLOUDFLARE_ACCOUNT_ID: {'✅' if os.getenv('CLOUDFLARE_ACCOUNT_ID') else '❌'}")
            print(f"   CLOUDFLARE_API_TOKEN: {'✅' if os.getenv('CLOUDFLARE_API_TOKEN') else '❌'}")
            print(f"   CLOUDFLARE_D1_DATABASE_ID: {'✅' if os.getenv('CLOUDFLARE_D1_DATABASE_ID') else '❌'}")
            return False

        if d1.test_connection():
            print("✅ D1 conectado exitosamente")
            if d1.initialize_database():
                print("✅ Esquema de base de datos inicializado")
                return True
            else:
                print("❌ Error inicializando esquema")
                return False
        else:
            print("❌ Error de conexión a D1")
            return False

    except Exception as e:
        print(f"❌ Error probando D1: {e}")
        return False


def test_r2_connection():
    """Probar conexión con Cloudflare R2"""
    print("\n📁 Probando Cloudflare R2...")

    try:
        r2 = CloudflareR2Service()

        if not r2.enabled:
            print("❌ R2 no configurado - Verifica variables de entorno:")
            print(f"   CLOUDFLARE_R2_ACCESS_KEY: {'✅' if os.getenv('CLOUDFLARE_R2_ACCESS_KEY') else '❌'}")
            print(f"   CLOUDFLARE_R2_SECRET_KEY: {'✅' if os.getenv('CLOUDFLARE_R2_SECRET_KEY') else '❌'}")
            print(f"   CLOUDFLARE_R2_ENDPOINT: {'✅' if os.getenv('CLOUDFLARE_R2_ENDPOINT') else '❌'}")
            print(f"   CLOUDFLARE_R2_PUBLIC_URL: {'✅' if os.getenv('CLOUDFLARE_R2_PUBLIC_URL') else '❌'}")
            return False

        if r2.is_available():
            print("✅ R2 conectado exitosamente")
            stats = r2.get_bucket_stats()
            if stats.get("enabled"):
                print(f"✅ Bucket: {stats.get('bucket_name')}")
                print(f"📊 Archivos: {stats.get('total_files', 0)}")
                print(f"📏 Tamaño: {stats.get('total_size_mb', 0)} MB")
                print(f"🌐 URL pública: {stats.get('public_url')}")
                return True
            else:
                print(f"❌ Error obteniendo stats: {stats.get('error', 'Unknown')}")
                return False
        else:
            print("❌ Error de conexión a R2")
            return False

    except Exception as e:
        print(f"❌ Error probando R2: {e}")
        return False


def test_adapter():
    """Probar adaptador unificado"""
    print("\n🔄 Probando Adaptador Unificado...")

    try:
        adapter = CloudflareAdapter()

        # Obtener estado del sistema
        status = adapter.get_system_status()

        print(f"🗄️ Base de datos: {status['services']['database']}")
        print(f"📁 Almacenamiento: {status['services']['storage']}")
        print(f"🔄 Modo fallback: {'Sí' if status['fallback_mode'] else 'No'}")

        if not status['fallback_mode']:
            print("✅ Sistema completamente configurado para Cloudflare")
            return True
        else:
            print("⚠️ Sistema en modo fallback (SQLite + Local)")
            return False

    except Exception as e:
        print(f"❌ Error probando adaptador: {e}")
        return False


def main():
    """Función principal"""
    print("🧪 PROBANDO CONFIGURACIÓN CLOUDFLARE")
    print("=" * 60)

    # Verificar archivo .env
    if not os.path.exists('.env'):
        print("❌ Archivo .env no encontrado")
        print("📋 Crea un archivo .env con tus credenciales de Cloudflare")
        return False

    # Mostrar configuración actual
    print("📋 Configuración actual:")
    print(f"   USE_CLOUDFLARE_D1: {os.getenv('USE_CLOUDFLARE_D1', 'false')}")
    print(f"   USE_CLOUDFLARE_R2: {os.getenv('USE_CLOUDFLARE_R2', 'false')}")
    print("-" * 60)

    # Ejecutar pruebas
    results = []

    if os.getenv('USE_CLOUDFLARE_D1', 'false').lower() == 'true':
        results.append(test_d1_connection())
    else:
        print("⏭️ D1 deshabilitado en configuración")
        results.append(True)  # No es error si está deshabilitado

    if os.getenv('USE_CLOUDFLARE_R2', 'false').lower() == 'true':
        results.append(test_r2_connection())
    else:
        print("⏭️ R2 deshabilitado en configuración")
        results.append(True)  # No es error si está deshabilitado

    # Probar adaptador
    results.append(test_adapter())

    # Resultado final
    print("\n" + "=" * 60)
    if all(results):
        print("🎉 ¡TODAS LAS PRUEBAS EXITOSAS!")
        print("✅ Tu configuración de Cloudflare está lista")
        print("\n📋 Próximos pasos:")
        print("   1. Hacer commit de los cambios")
        print("   2. Deploy en Render con las variables de entorno")
        print("   3. Probar la API en producción")
        return True
    else:
        print("❌ ALGUNAS PRUEBAS FALLARON")
        print("🔧 Revisa las credenciales y configuración")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)