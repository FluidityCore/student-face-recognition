#!/usr/bin/env python3
"""
Script para probar la API de reconocimiento facial en Railway
"""

import requests
import json
import sys
import os
from pathlib import Path


class APITester:
    """Clase para probar la API en Railway"""

    def __init__(self, api_url=None):
        # URL de tu API en Railway
        self.base_url = api_url or "https://student-face-recognition-production.up.railway.app"
        self.session = requests.Session()
        self.session.timeout = 30  # Timeout de 30 segundos

        # Verificar conexión inicial
        self.verify_connection()

    def verify_connection(self):
        """Verificar que la API esté accesible"""
        print(f"🔍 Verificando conexión a: {self.base_url}")

        try:
            response = self.session.get(f"{self.base_url}/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Conexión exitosa - Server: {data.get('server', 'unknown')}")
                print(f"📋 Version: {data.get('version', 'unknown')}")
            else:
                print(f"⚠️ API responde con status: {response.status_code}")
        except Exception as e:
            print(f"❌ Error de conexión: {e}")
            print(f"🔧 Verifica que tu dominio sea correcto: {self.base_url}")

    def test_health_check(self):
        """Probar health check"""
        print("🔄 Probando health check...")

        try:
            response = self.session.get(f"{self.base_url}/health")

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check OK - Status: {data.get('status')}")
                print(f"   🌍 Server: {data.get('server', 'unknown')}")
                print(f"   🗄️ Database: {data.get('database', {}).get('status', 'unknown')}")

                services = data.get('services', {})
                print(f"   🤖 Face Recognition: {'✅' if services.get('face_recognition') else '❌'}")
                print(f"   🖼️ Image Processor: {'✅' if services.get('image_processor') else '❌'}")
                print(f"   ☁️ Cloudflare R2: {'✅' if services.get('cloudflare_r2') else '❌'}")

                return True
            else:
                print(f"❌ Health check falló - Status: {response.status_code}")
                if response.text:
                    print(f"   Error: {response.text[:200]}")
                return False

        except Exception as e:
            print(f"❌ Error en health check: {e}")
            return False

    def test_root_endpoint(self):
        """Probar endpoint raíz"""
        print("🔄 Probando endpoint raíz...")

        try:
            response = self.session.get(f"{self.base_url}/")

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Endpoint raíz OK")
                print(f"   📝 Message: {data.get('message', 'N/A')}")
                print(f"   🌍 Environment: {data.get('environment', 'N/A')}")
                print(f"   💾 Storage: {data.get('storage', 'N/A')}")

                endpoints = data.get('endpoints', {})
                print(f"   📊 Endpoints disponibles: {len(endpoints)}")

                return True
            else:
                print(f"❌ Endpoint raíz falló - Status: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error en endpoint raíz: {e}")
            return False

    def test_railway_test_endpoint(self):
        """Probar endpoint específico de Railway"""
        print("🔄 Probando endpoint Railway test...")

        try:
            response = self.session.get(f"{self.base_url}/railway-test")

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Railway test OK")
                print(f"   🐍 Python: {data.get('python_version', 'N/A')[:20]}...")
                print(f"   🔗 Port: {data.get('env_port', 'N/A')}")

                if 'memory_percent' in data:
                    print(f"   🧠 Memory: {data.get('memory_percent', 0):.1f}%")
                if 'cpu_percent' in data:
                    print(f"   ⚡ CPU: {data.get('cpu_percent', 0):.1f}%")

                return True
            else:
                print(f"❌ Railway test falló - Status: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error en Railway test: {e}")
            return False

    def test_system_info(self):
        """Probar información del sistema"""
        print("🔄 Probando información del sistema...")

        try:
            response = self.session.get(f"{self.base_url}/info")

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Info del sistema OK")

                system = data.get('system', {})
                database = data.get('database', {})
                config = data.get('configuration', {})

                print(f"   📊 Estudiantes: {database.get('total_students', 0)}")
                print(f"   📈 Logs reconocimiento: {database.get('total_recognition_logs', 0)}")
                print(f"   🎯 Umbral: {system.get('recognition_threshold', 'N/A')}")
                print(f"   📁 Tamaño máx imagen: {system.get('max_image_size_mb', 'N/A')} MB")
                print(f"   🔧 Debug: {config.get('debug', False)}")
                print(f"   ☁️ Cloudflare R2: {config.get('use_cloudflare_r2', False)}")

                return True
            else:
                print(f"❌ Info del sistema falló - Status: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error en info del sistema: {e}")
            return False

    def test_students_endpoint(self):
        """Probar endpoint de estudiantes"""
        print("🔄 Probando endpoint de estudiantes...")

        try:
            response = self.session.get(f"{self.base_url}/api/students")

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Endpoint de estudiantes OK - Total: {len(data)}")

                if len(data) > 0:
                    # Mostrar info del primer estudiante
                    student = data[0]
                    print(f"   👤 Ejemplo: {student.get('nombres', 'N/A')} {student.get('apellidos', 'N/A')}")
                    print(f"   🆔 Código: {student.get('codigo', 'N/A')}")
                    print(f"   ⚠️ Requisitoriado: {student.get('requisitoriado', False)}")
                else:
                    print("   📝 No hay estudiantes registrados")

                return True
            else:
                print(f"❌ Endpoint de estudiantes falló - Status: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error en endpoint de estudiantes: {e}")
            return False

    def test_server_status(self):
        """Probar estado del servidor Railway"""
        print("🔄 Probando estado del servidor...")

        try:
            response = self.session.get(f"{self.base_url}/server-status")

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Server status OK")

                env = data.get('environment', {})
                features = data.get('features', {})
                system = data.get('system', {})

                print(f"   🌍 Server: {data.get('server', 'N/A')}")
                print(f"   🐍 Python: {data.get('python_version', 'N/A')}")
                print(f"   🔗 Port: {env.get('port', 'N/A')}")
                print(f"   🤖 Face Recognition: {'✅' if features.get('face_recognition') else '❌'}")
                print(f"   📊 psutil: {'✅' if features.get('psutil') else '❌'}")

                if system:
                    print(f"   🧠 Memory: {system.get('memory_percent', 0):.1f}%")
                    print(f"   ⚡ CPU: {system.get('cpu_percent', 0):.1f}%")

                return True
            else:
                print(f"❌ Server status falló - Status: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error en server status: {e}")
            return False

    def test_recognition_stats(self):
        """Probar estadísticas de reconocimiento"""
        print("🔄 Probando estadísticas de reconocimiento...")

        try:
            response = self.session.get(f"{self.base_url}/api/recognition/stats")

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Estadísticas OK")
                print(f"   📊 Total reconocimientos: {data.get('total_recognitions', 0)}")
                print(f"   ✅ Exitosos: {data.get('successful_recognitions', 0)}")
                print(f"   ❌ Fallidos: {data.get('failed_recognitions', 0)}")
                print(f"   📈 Tasa de éxito: {data.get('success_rate', 0):.1f}%")

                return True
            else:
                print(f"❌ Estadísticas fallaron - Status: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error en estadísticas: {e}")
            return False

    def test_docs_endpoint(self):
        """Probar que la documentación esté accesible"""
        print("🔄 Probando documentación API...")

        try:
            response = self.session.get(f"{self.base_url}/docs")

            if response.status_code == 200:
                print(f"✅ Documentación accesible")
                print(f"   📚 Swagger UI disponible en: {self.base_url}/docs")
                return True
            else:
                print(f"❌ Documentación no accesible - Status: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error accediendo a docs: {e}")
            return False

    def run_all_tests(self):
        """Ejecutar todas las pruebas"""
        print("🧪 Iniciando pruebas de la API en Railway")
        print("=" * 60)

        tests = [
            ("Health Check", self.test_health_check),
            ("Root Endpoint", self.test_root_endpoint),
            ("Railway Test", self.test_railway_test_endpoint),
            ("System Info", self.test_system_info),
            ("Students Endpoint", self.test_students_endpoint),
            ("Server Status", self.test_server_status),
            ("Recognition Stats", self.test_recognition_stats),
            ("API Documentation", self.test_docs_endpoint)
        ]

        passed = 0
        total = len(tests)

        for test_name, test_func in tests:
            print(f"\n🧪 {test_name}")
            print("-" * 40)

            if test_func():
                passed += 1

            print()

        print("=" * 60)
        print(f"📊 Resultados finales: {passed}/{total} pruebas exitosas")

        if passed == total:
            print("🎉 ¡Todas las pruebas pasaron! Tu API está funcionando perfectamente.")
            return True
        elif passed >= total * 0.8:  # 80% o más
            print("✅ La mayoría de pruebas pasaron. Tu API está funcionando bien.")
            return True
        else:
            print("❌ Varias pruebas fallaron. Revisa la configuración de tu API.")
            return False


def main():
    """Función principal"""
    print("🧪 API Tester - Reconocimiento Facial Railway Edition")
    print("=" * 60)

    # Obtener URL de argumentos de línea de comandos
    api_url = None
    if len(sys.argv) > 1:
        api_url = sys.argv[1]
        print(f"🌐 Usando URL proporcionada: {api_url}")
    else:
        print("💡 Uso: python test_api.py [URL_DE_TU_API]")
        print("💡 Ejemplo: python test_api.py https://tu-app.up.railway.app")
        print("💡 O edita el script para poner tu URL por defecto")

    # Crear tester y ejecutar pruebas
    tester = APITester(api_url)
    print(f"🎯 Testeando: {tester.base_url}")
    print("-" * 60)

    success = tester.run_all_tests()

    if success:
        print("\n🚀 ¡Tu API de Railway está lista para usar!")
        print(f"📱 Puedes usar el script de carga: python bulk_upload_railway.py")
        print(f"📚 Documentación: {tester.base_url}/docs")
        sys.exit(0)
    else:
        print(f"\n🔧 Revisa los errores y corrige la configuración")
        sys.exit(1)


if __name__ == "__main__":
    main()