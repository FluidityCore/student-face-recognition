#!/usr/bin/env python3
"""
Script para probar la API de reconocimiento facial
"""

import requests
import json
import sys
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


class APITester:
    """Clase para probar la API"""

    def __init__(self):
        self.base_url = f"http://{os.getenv('API_HOST', 'localhost')}:{os.getenv('API_PORT', '8000')}"
        self.session = requests.Session()

    def test_health_check(self):
        """Probar health check"""
        print("🔄 Probando health check...")

        try:
            response = self.session.get(f"{self.base_url}/health")

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check OK - Status: {data.get('status')}")
                return True
            else:
                print(f"❌ Health check falló - Status: {response.status_code}")
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
                print(f"✅ Endpoint raíz OK - Message: {data.get('message')}")
                return True
            else:
                print(f"❌ Endpoint raíz falló - Status: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error en endpoint raíz: {e}")
            return False

    def test_system_info(self):
        """Probar información del sistema"""
        print("🔄 Probando información del sistema...")

        try:
            response = self.session.get(f"{self.base_url}/info")

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Info del sistema OK")
                print(f"   📊 Estudiantes: {data.get('database', {}).get('total_students', 0)}")
                print(f"   🎯 Umbral: {data.get('system', {}).get('recognition_threshold', 'N/A')}")
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
                return True
            else:
                print(f"❌ Endpoint de estudiantes falló - Status: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error en endpoint de estudiantes: {e}")
            return False

    def test_face_detection(self, image_path=None):
        """Probar detección facial"""
        print("🔄 Probando detección facial...")

        if not image_path or not os.path.exists(image_path):
            print("ℹ️ No se proporcionó imagen para prueba de detección")
            return True

        try:
            with open(image_path, 'rb') as f:
                files = {'image': ('test.jpg', f, 'image/jpeg')}
                response = self.session.post(
                    f"{self.base_url}/api/test-face-detection",
                    files=files
                )

            if response.status_code == 200:
                data = response.json()
                detected = data.get('face_detected', False)
                print(f"✅ Detección facial OK - Rostro detectado: {detected}")
                return True
            else:
                print(f"❌ Detección facial falló - Status: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error en detección facial: {e}")
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
                print(f"   📈 Tasa de éxito: {data.get('success_rate', 0)}%")
                return True
            else:
                print(f"❌ Estadísticas fallaron - Status: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error en estadísticas: {e}")
            return False

    def run_all_tests(self, image_path=None):
        """Ejecutar todas las pruebas"""
        print("🧪 Iniciando pruebas de la API")
        print("=" * 50)

        tests = [
            self.test_health_check,
            self.test_root_endpoint,
            self.test_system_info,
            self.test_students_endpoint,
            lambda: self.test_face_detection(image_path),
            self.test_recognition_stats
        ]

        passed = 0
        total = len(tests)

        for test in tests:
            if test():
                passed += 1
            print("-" * 30)

        print(f"\n📊 Resultados: {passed}/{total} pruebas exitosas")

        if passed == total:
            print("🎉 ¡Todas las pruebas pasaron!")
            return True
        else:
            print("❌ Algunas pruebas fallaron")
            return False


def main():
    """Función principal"""
    print("🧪 Tester de API - Reconocimiento Facial")
    print("=" * 50)

    # Verificar si hay imagen de prueba
    test_image = None
    if len(sys.argv) > 1:
        test_image = sys.argv[1]
        if os.path.exists(test_image):
            print(f"📷 Usando imagen de prueba: {test_image}")
        else:
            print(f"⚠️ Imagen no encontrada: {test_image}")
            test_image = None

    # Crear tester y ejecutar pruebas
    tester = APITester()

    print(f"🌐 URL base: {tester.base_url}")
    print("-" * 50)

    success = tester.run_all_tests(test_image)

    if success:
        print("\n✅ API funcionando correctamente")
        sys.exit(0)
    else:
        print("\n❌ Hay problemas con la API")
        sys.exit(1)


if __name__ == "__main__":
    main()