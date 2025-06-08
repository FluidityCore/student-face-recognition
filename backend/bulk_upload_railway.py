#!/usr/bin/env python3
"""
Script para cargar estudiantes en lote a Railway API
Formato: APELLIDO1_APELLIDO2_NOMBRE1_NOMBRE2_CODIGO_usuario.jpg
"""

import requests
import os
import re
import time
from pathlib import Path


class BulkUploader:
    def __init__(self, api_url="https://student-face-recognition-production.up.railway.app"):
        self.api_url = api_url
        self.session = requests.Session()
        self.session.timeout = 120  # Timeout de 2 minutos

        # Headers para Railway
        self.session.headers.update({
            'User-Agent': 'UPAO-Bulk-Uploader/1.0',
            'Accept': 'application/json'
        })

        # Verificar conexión a la API
        self.verify_api_connection()

    def verify_api_connection(self):
        """Verificar que la API esté disponible"""
        print(f"🔍 Verificando conexión a Railway API...")
        print(f"🌐 URL: {self.api_url}")

        # Probar endpoints básicos
        endpoints_to_try = ["/health", "/"]

        for endpoint in endpoints_to_try:
            try:
                response = self.session.get(f"{self.api_url}{endpoint}", timeout=30)

                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"✅ API conectada exitosamente!")

                        if endpoint == "/health":
                            services = data.get('services', {})
                            print(f"🤖 Face Recognition: {'✅' if services.get('face_recognition') else '❌'}")
                            print(f"☁️ Cloudflare R2: {'✅' if services.get('cloudflare_r2') else '❌'}")

                        return True

                    except ValueError:
                        # Si no es JSON pero status 200, está bien
                        print(f"✅ API conectada")
                        return True

                elif response.status_code in [502, 503, 504]:
                    continue
                else:
                    continue

            except requests.exceptions.Timeout:
                continue
            except requests.exceptions.RequestException:
                continue

        # Si ningún endpoint funcionó
        print("❌ No se pudo conectar a la API")
        print("🔧 Verifica que:")
        print("   1. Tu API esté desplegada y activa en Railway")
        print("   2. El dominio sea correcto")
        print(f"   3. Puedas acceder a: {self.api_url}")

        continuar = input("\n¿Intentar de todas formas? (s/N): ").strip().lower()
        if continuar not in ['s', 'si', 'sí', 'y', 'yes']:
            print("❌ Cancelando operación")
            exit(1)

    def parse_filename(self, filename):
        """
        Extraer información del estudiante desde el nombre del archivo
        Formato: APELLIDO1_APELLIDO2_NOMBRE1_NOMBRE2_CODIGO_usuario.jpg
        """
        try:
            # Remover extensión
            name_without_ext = Path(filename).stem

            # Dividir por guiones bajos
            parts = name_without_ext.split('_')

            if len(parts) < 6:
                print(f"⚠️ Formato incorrecto en {filename}")
                print(f"   Formato esperado: APELLIDO1_APELLIDO2_NOMBRE1_NOMBRE2_CODIGO_usuario.jpg")
                return None

            # Identificar código (parte que es solo números)
            codigo_index = None
            for i, part in enumerate(parts):
                if re.match(r'^\d+$', part) and len(part) >= 6:  # Al menos 6 dígitos
                    codigo_index = i
                    break

            if codigo_index is None:
                print(f"⚠️ No se encontró código válido en {filename}")
                return None

            if codigo_index < 2:
                print(f"⚠️ No hay suficientes partes antes del código en {filename}")
                return None

            # Extraer componentes
            nombres_parts = parts[codigo_index - 2:codigo_index]  # 2 partes antes del código
            apellidos_parts = parts[:codigo_index - 2] if codigo_index > 2 else []
            codigo = parts[codigo_index]
            usuario_parts = parts[codigo_index + 1:] if codigo_index + 1 < len(parts) else []

            # Construir nombres
            if not nombres_parts:
                print(f"⚠️ No se encontraron nombres en {filename}")
                return None

            nombres = ' '.join(nombres_parts).title()
            apellidos = ' '.join(apellidos_parts).title() if apellidos_parts else "Sin Apellido"
            usuario = '_'.join(usuario_parts) if usuario_parts else f"user_{codigo}"
            correo = f"{usuario}@upao.edu.pe"

            return {
                'nombres': nombres,
                'apellidos': apellidos,
                'codigo': codigo,
                'correo': correo,
                'usuario': usuario
            }

        except Exception as e:
            print(f"❌ Error al parsear {filename}: {e}")
            return None

    def add_student_auto(self, image_path, requisitoriado=False):
        """Agregar estudiante extrayendo info del nombre del archivo"""
        try:
            # Parsear información del archivo
            student_info = self.parse_filename(image_path.name)

            if not student_info:
                return False

            print(f"📝 {student_info['nombres']} {student_info['apellidos']} ({student_info['codigo']})")

            # Validar tamaño de imagen
            file_size = image_path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)

            if file_size_mb > 10:  # Límite de 10MB
                print(f"❌ Imagen demasiado grande: {file_size_mb:.1f}MB (máximo 10MB)")
                return False

            # Preparar datos para la API
            data = {
                'nombre': student_info['nombres'],
                'apellidos': student_info['apellidos'],
                'codigo': student_info['codigo'],
                'correo': student_info['correo'],
                'requisitoriado': str(requisitoriado).lower()
            }

            # Enviar a la API Railway
            print(f"📤 Procesando...")

            start_time = time.time()

            with open(image_path, 'rb') as f:
                # Determinar el tipo MIME correcto
                mime_type = 'image/jpeg'
                if image_path.suffix.lower() in ['.png']:
                    mime_type = 'image/png'
                elif image_path.suffix.lower() in ['.bmp']:
                    mime_type = 'image/bmp'

                files = {'image': (image_path.name, f, mime_type)}

                response = self.session.post(
                    f"{self.api_url}/api/students/",
                    data=data,
                    files=files,
                    timeout=120
                )

            process_time = time.time() - start_time

            if response.status_code == 200:
                result = response.json()
                student_id = result.get('id', 'unknown')
                print(f"✅ Agregado exitosamente! ID: {student_id} ({process_time:.1f}s)")
                return True
            else:
                print(f"❌ Error: {response.status_code}")
                try:
                    error_detail = response.json()
                    detail = error_detail.get('detail', 'Error desconocido')

                    if 'already exists' in detail.lower():
                        print(f"   ℹ️ El estudiante ya existe")
                    elif 'face' in detail.lower():
                        print(f"   🤖 Problema con reconocimiento facial")
                    else:
                        print(f"   📄 {detail}")

                except ValueError:
                    print(f"   📄 {response.text[:100]}")

                return False

        except requests.exceptions.Timeout:
            print(f"⏱️ Timeout - Reconocimiento facial tomando demasiado tiempo")
            return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión: {e}")
            return False
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            return False

    def process_folder_interactive(self, folder_path):
        """Procesar carpeta con modo interactivo"""
        folder = Path(folder_path)

        if not folder.exists():
            print(f"❌ La carpeta {folder} no existe")
            return

        # Buscar archivos de imagen
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
        image_files = [f for f in folder.iterdir()
                       if f.is_file() and f.suffix.lower() in image_extensions]

        if not image_files:
            print(f"❌ No se encontraron imágenes en {folder}")
            return

        print(f"📁 Carpeta: {folder}")
        print(f"🖼️ Imágenes encontradas: {len(image_files)}")
        print("=" * 70)

        success_count = 0
        failed_count = 0

        for i, image_file in enumerate(image_files, 1):
            print(f"\n[{i}/{len(image_files)}] {image_file.name}")
            print("-" * 50)

            # Mostrar información que se extraería
            student_info = self.parse_filename(image_file.name)

            if not student_info:
                failed_count += 1
                continue

            # Mostrar preview
            print(f"👤 {student_info['nombres']} {student_info['apellidos']}")
            print(f"🆔 {student_info['codigo']}")
            print(f"📧 {student_info['correo']}")

            # Preguntar por requisitoriado
            while True:
                requisitoriado_input = input("⚠️ ¿Es requisitoriado? (s/N): ").strip().lower()
                if requisitoriado_input in ['', 'n', 'no']:
                    requisitoriado = False
                    break
                elif requisitoriado_input in ['s', 'si', 'sí', 'y', 'yes']:
                    requisitoriado = True
                    break
                else:
                    print("❓ Por favor responde 's' para sí o 'n' para no")

            # Confirmar antes de agregar
            confirmar = input("✅ ¿Agregar este estudiante? (S/n): ").strip().lower()
            if confirmar in ['', 's', 'si', 'sí', 'y', 'yes']:
                if self.add_student_auto(image_file, requisitoriado):
                    success_count += 1
                else:
                    failed_count += 1
            else:
                print("⏭️ Saltando...")
                failed_count += 1

        print("\n" + "=" * 70)
        print(f"📊 Resumen:")
        print(f"✅ Agregados: {success_count}")
        print(f"❌ Fallos/Saltados: {failed_count}")
        print(f"📈 Tasa de éxito: {(success_count / len(image_files) * 100):.1f}%")

    def process_folder_batch(self, folder_path, default_requisitoriado=False):
        """Procesar carpeta en lote sin interacción"""
        folder = Path(folder_path)

        if not folder.exists():
            print(f"❌ La carpeta {folder} no existe")
            return

        # Buscar archivos de imagen
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
        image_files = [f for f in folder.iterdir()
                       if f.is_file() and f.suffix.lower() in image_extensions]

        if not image_files:
            print(f"❌ No se encontraron imágenes en {folder}")
            return

        print(f"📁 Procesando {len(image_files)} imágenes en modo lote...")
        print(f"⚠️ Requisitoriado por defecto: {default_requisitoriado}")
        print(f"⏱️ Tiempo estimado: {len(image_files) * 1.5:.0f} minutos")
        print("=" * 70)

        success_count = 0
        failed_count = 0
        start_time = time.time()

        for i, image_file in enumerate(image_files, 1):
            elapsed = time.time() - start_time
            avg_time = elapsed / i if i > 0 else 0
            remaining = (len(image_files) - i) * avg_time

            print(f"\n[{i}/{len(image_files)}] {image_file.name}")
            print(f"⏱️ Transcurrido: {elapsed / 60:.1f}min | Restante: ~{remaining / 60:.1f}min")

            if self.add_student_auto(image_file, default_requisitoriado):
                success_count += 1
            else:
                failed_count += 1

        total_time = time.time() - start_time
        print("\n" + "=" * 70)
        print(f"🎉 Proceso completado!")
        print(f"✅ Agregados: {success_count}")
        print(f"❌ Fallos: {failed_count}")
        print(f"⏱️ Tiempo total: {total_time / 60:.1f} minutos")
        print(f"📈 Tasa de éxito: {(success_count / len(image_files) * 100):.1f}%")

    def test_single_upload(self, image_path):
        """Probar con una sola imagen"""
        print(f"🧪 Prueba con imagen individual...")

        if not Path(image_path).exists():
            print(f"❌ Archivo no encontrado: {image_path}")
            return False

        return self.add_student_auto(Path(image_path), False)


def main():
    """Función principal"""
    print("🎓 Cargador de Estudiantes UPAO - Railway Edition")
    print("☁️ Conectando a API en producción...")
    print("=" * 70)

    uploader = BulkUploader()

    # Configuración - Cambiar esta ruta según tu sistema
    carpeta_imagenes = r"C:\Proyectos\student-face-recognition\backend\estudiantes_fotos"

    print(f"\n📁 Carpeta: {carpeta_imagenes}")
    print(f"📝 Formato: APELLIDO1_APELLIDO2_NOMBRE1_NOMBRE2_CODIGO_usuario.jpg")
    print(f"📏 Tamaño máximo: 10MB por imagen")

    print("\n🔧 Modos disponibles:")
    print("1. Interactivo - Pregunta por cada estudiante")
    print("2. Lote - Todos con el mismo estado")
    print("3. Prueba - Solo una imagen")

    while True:
        modo = input("\n¿Qué modo prefieres? (1/2/3): ").strip()

        if modo == "1":
            print("\n🔄 Modo interactivo...")
            confirmar = input("¿Continuar? (S/n): ").strip().lower()
            if confirmar in ['', 's', 'si', 'sí', 'y', 'yes']:
                uploader.process_folder_interactive(carpeta_imagenes)
            break

        elif modo == "2":
            while True:
                req_default = input("¿Todos son requisitoriados por defecto? (s/N): ").strip().lower()
                if req_default in ['', 'n', 'no']:
                    requisitoriado_defecto = False
                    break
                elif req_default in ['s', 'si', 'sí', 'y', 'yes']:
                    requisitoriado_defecto = True
                    break

            print(f"\n🔄 Modo lote (requisitoriado: {requisitoriado_defecto})...")
            confirmar = input("¿Continuar? (S/n): ").strip().lower()
            if confirmar in ['', 's', 'si', 'sí', 'y', 'yes']:
                uploader.process_folder_batch(carpeta_imagenes, requisitoriado_defecto)
            break

        elif modo == "3":
            imagen_prueba = input("Nombre del archivo de prueba: ").strip()
            full_path = f"{carpeta_imagenes}/{imagen_prueba}"
            success = uploader.test_single_upload(full_path)
            if success:
                print("\n✅ Prueba exitosa!")
            else:
                print("\n❌ Prueba falló")
            break

        else:
            print("❓ Por favor selecciona 1, 2 o 3")


if __name__ == "__main__":
    main()