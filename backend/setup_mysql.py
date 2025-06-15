#!/usr/bin/env python3
"""
Script para configurar MySQL para el proyecto de reconocimiento facial
Ejecutar antes de usar la API en modo local
"""

import os
import sys
import pymysql
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


def get_mysql_config():
    """Obtener configuración MySQL desde variables de entorno"""
    return {
        'host': os.getenv("MYSQL_HOST", "localhost"),
        'port': int(os.getenv("MYSQL_PORT", "3307")),
        'user': os.getenv("MYSQL_USER", "root"),
        'password': os.getenv("MYSQL_PASSWORD", "root"),
        'database': os.getenv("MYSQL_DATABASE", "face_recognition_db"),
        'charset': 'utf8mb4'
    }


def test_mysql_connection():
    """Probar conexión con MySQL servidor"""
    config = get_mysql_config()

    print("🔍 Probando conexión con MySQL servidor...")
    print(f"   Host: {config['host']}")
    print(f"   Puerto: {config['port']}")
    print(f"   Usuario: {config['user']}")

    try:
        # Conectar sin especificar base de datos
        connection = pymysql.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            charset=config['charset']
        )

        print("✅ Conexión con MySQL servidor exitosa")
        connection.close()
        return True

    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        print("\n🔧 Verifica que:")
        print("   1. MySQL esté ejecutándose")
        print("   2. Las credenciales sean correctas")
        print("   3. El puerto 3307 esté abierto")
        return False


def create_database():
    """Crear base de datos si no existe"""
    config = get_mysql_config()

    print(f"\n🗄️ Creando base de datos '{config['database']}'...")

    try:
        # Conectar sin especificar base de datos
        connection = pymysql.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            charset=config['charset']
        )

        with connection.cursor() as cursor:
            # Crear base de datos si no existe
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{config['database']}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"✅ Base de datos '{config['database']}' creada/verificada")

            # Verificar que se creó
            cursor.execute("SHOW DATABASES")
            databases = [row[0] for row in cursor.fetchall()]

            if config['database'] in databases:
                print(f"✅ Base de datos '{config['database']}' confirmada")
            else:
                print(f"❌ Error: Base de datos '{config['database']}' no encontrada")
                return False

        connection.close()
        return True

    except Exception as e:
        print(f"❌ Error creando base de datos: {e}")
        return False


def test_database_connection():
    """Probar conexión con la base de datos específica"""
    config = get_mysql_config()

    print(f"\n🔗 Probando conexión con base de datos '{config['database']}'...")

    try:
        connection = pymysql.connect(**config)

        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()

            if result and result[0] == 1:
                print("✅ Conexión con base de datos exitosa")
                connection.close()
                return True
            else:
                print("❌ Error en query de prueba")
                return False

    except Exception as e:
        print(f"❌ Error de conexión con base de datos: {e}")
        return False


def create_tables():
    """Crear tablas necesarias usando MySQLService"""
    print("\n📋 Creando tablas de la aplicación...")

    try:
        # Importar y usar MySQLService
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from app.services.mysql_service import MySQLService

        mysql_service = MySQLService()

        if mysql_service.enabled:
            print("✅ Tablas creadas por MySQLService")
            return True
        else:
            print("❌ MySQLService no pudo inicializarse")
            return False

    except Exception as e:
        print(f"❌ Error creando tablas: {e}")
        return False


def show_connection_info():
    """Mostrar información de conexión para la aplicación"""
    config = get_mysql_config()

    print("\n" + "=" * 60)
    print("🎉 CONFIGURACIÓN MYSQL COMPLETADA")
    print("=" * 60)
    print(f"🗄️ Base de datos: {config['database']}")
    print(f"🔗 Host: {config['host']}:{config['port']}")
    print(f"👤 Usuario: {config['user']}")
    print(f"🔧 Charset: {config['charset']}")

    print("\n📝 Variables de entorno necesarias:")
    print(f"   MYSQL_HOST={config['host']}")
    print(f"   MYSQL_PORT={config['port']}")
    print(f"   MYSQL_USER={config['user']}")
    print(f"   MYSQL_PASSWORD={config['password']}")
    print(f"   MYSQL_DATABASE={config['database']}")

    print("\n🚀 Para usar en modo desarrollo:")
    print("   USE_CLOUDFLARE_D1=false")
    print("   USE_CLOUDFLARE_R2=false")

    print("\n▶️ Ejecutar aplicación:")
    print("   python -m app.main")
    print("   o")
    print("   uvicorn app.main:app --reload")


def main():
    """Función principal del setup"""
    print("🛠️ SETUP MYSQL PARA RECONOCIMIENTO FACIAL")
    print("=" * 50)

    # Paso 1: Probar conexión con servidor
    if not test_mysql_connection():
        print("\n❌ Setup fallido: No se puede conectar a MySQL")
        sys.exit(1)

    # Paso 2: Crear base de datos
    if not create_database():
        print("\n❌ Setup fallido: No se pudo crear la base de datos")
        sys.exit(1)

    # Paso 3: Probar conexión con base de datos
    if not test_database_connection():
        print("\n❌ Setup fallido: No se puede conectar a la base de datos")
        sys.exit(1)

    # Paso 4: Crear tablas
    if not create_tables():
        print("\n❌ Setup fallido: No se pudieron crear las tablas")
        sys.exit(1)

    # Paso 5: Mostrar información final
    show_connection_info()


if __name__ == "__main__":
    main()