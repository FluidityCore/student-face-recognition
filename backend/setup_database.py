#!/usr/bin/env python3
"""
Script para configurar la base de datos inicial
"""

import sys
import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

# Cargar variables de entorno
load_dotenv()


def create_database():
    """Crear la base de datos si no existe"""

    # Configuración de conexión
    config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '3307')),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', 'root')
    }

    db_name = os.getenv('DB_NAME', 'student_recognition')

    try:
        print("🔄 Conectando a MySQL...")

        # Conectar sin especificar base de datos
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()

        # Verificar si la base de datos existe
        cursor.execute(f"SHOW DATABASES LIKE '{db_name}'")
        result = cursor.fetchone()

        if result:
            print(f"✅ La base de datos '{db_name}' ya existe")
        else:
            # Crear base de datos
            cursor.execute(f"CREATE DATABASE {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"✅ Base de datos '{db_name}' creada exitosamente")

        cursor.close()
        connection.close()

        return True

    except Error as e:
        print(f"❌ Error de MySQL: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False


def setup_tables():
    """Configurar tablas usando SQLAlchemy"""
    try:
        print("🔄 Configurando tablas...")

        # Importar después de asegurar que la BD existe
        from app.models.database import create_tables, test_database_connection

        # Probar conexión
        if not test_database_connection():
            print("❌ No se pudo conectar a la base de datos")
            return False

        # Crear tablas
        create_tables()
        print("✅ Tablas configuradas exitosamente")

        return True

    except Exception as e:
        print(f"❌ Error al configurar tablas: {e}")
        return False


def verify_setup():
    """Verificar que todo esté configurado correctamente"""
    try:
        print("🔄 Verificando configuración...")

        from app.models.database import get_database_stats, SessionLocal
        from app.services.database_service import ConfigService

        # Verificar estadísticas
        stats = get_database_stats()
        if stats is not None:
            print(f"📊 Estudiantes en BD: {stats['total_students']}")
            print(f"📊 Reconocimientos registrados: {stats['total_recognitions']}")

        # Verificar configuración
        db = SessionLocal()
        config_service = ConfigService()

        threshold = config_service.get_recognition_threshold(db)
        print(f"⚙️ Umbral de reconocimiento: {threshold}")

        db.close()

        print("✅ Verificación completada")
        return True

    except Exception as e:
        print(f"❌ Error en verificación: {e}")
        return False


def main():
    """Función principal"""
    print("🏗️ Configurador de Base de Datos - Reconocimiento Facial")
    print("=" * 60)

    # Mostrar configuración
    print("📋 Configuración:")
    print(f"   Host: {os.getenv('DB_HOST', 'localhost')}")
    print(f"   Puerto: {os.getenv('DB_PORT', '3307')}")
    print(f"   Usuario: {os.getenv('DB_USER', 'root')}")
    print(f"   Base de datos: {os.getenv('DB_NAME', 'student_recognition')}")
    print("-" * 60)

    # Paso 1: Crear base de datos
    if not create_database():
        print("❌ No se pudo crear la base de datos")
        sys.exit(1)

    # Paso 2: Configurar tablas
    if not setup_tables():
        print("❌ No se pudieron configurar las tablas")
        sys.exit(1)

    # Paso 3: Verificar configuración
    if not verify_setup():
        print("❌ La verificación falló")
        sys.exit(1)

    print("\n🎉 ¡Configuración completada exitosamente!")
    print("\n📋 Próximos pasos:")
    print("   1. Ejecutar: python run_server.py")
    print("   2. Abrir: http://localhost:8000/docs")
    print("   3. Probar endpoints de la API")


if __name__ == "__main__":
    main()