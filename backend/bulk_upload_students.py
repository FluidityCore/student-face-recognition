#!/usr/bin/env python3
"""
Script para cargar estudiantes en lote desde nombres de archivo estructurados
Formato: APELLIDO1_APELLIDO2_NOMBRE1_NOMBRE2_CODIGO_usuario.jpg
"""

import requests
import os
import re
from pathlib import Path


class SmartBulkUploader:
    def __init__(self, api_url="https://tu-app.onrender.com"):
        self.api_url = api_url
        self.session = requests.Session()

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
                raise ValueError(f"Formato incorrecto. Se esperan al menos 6 partes, se encontraron {len(parts)}")

            # Identificar código (parte que es solo números)
            codigo_index = None
            for i, part in enumerate(parts):
                if re.match(r'^\d+$', part):  # Solo números
                    codigo_index = i
                    break

            if codigo_index is None:
                raise ValueError("No se encontró código numérico en el nombre del archivo")

            # Extraer componentes
            apellidos_parts = parts[:codigo_index - 2]  # Todo antes de los nombres
            nombres_parts = parts[codigo_index - 2:codigo_index]  # 2 partes antes del código
            codigo = parts[codigo_index]
            usuario_parts = parts[codigo_index + 1:]  # Todo después del código

            # Construir nombres
            apellidos = ' '.join(apellidos_parts).title()
            nombres = ' '.join(nombres_parts).title()
            usuario = '_'.join(usuario_parts)
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

            print(f"📝 Información extraída:")
            print(f"   Nombres: {student_info['nombres']}")
            print(f"   Apellidos: {student_info['apellidos']}")
            print(f"   Código: {student_info['codigo']}")
            print(f"   Correo: {student_info['correo']}")
            print(f"   Requisitoriado: {requisitoriado}")

            # Preparar datos para la API
            data = {
                'nombre': student_info['nombres'],
                'apellidos': student_info['apellidos'],
                'codigo': student_info['codigo'],
                'correo': student_info['correo'],
                'requisitoriado': requisitoriado
            }

            # Enviar a la API
            with open(image_path, 'rb') as f:
                files = {'image': (image_path.name, f, 'image/jpeg')}

                response = self.session.post(
                    f"{self.api_url}/api/students/",
                    data=data,
                    files=files
                )

            if response.status_code == 200:
                result = response.json()
                print(f"✅ {student_info['nombres']} {student_info['apellidos']} agregado (ID: {result['id']})")
                return True
            else:
                print(f"❌ Error de API: {response.status_code}")
                if response.text:
                    print(f"   Detalle: {response.text[:200]}")
                return False

        except Exception as e:
            print(f"❌ Error al procesar {image_path.name}: {e}")
            return False

    def process_folder_interactive(self, folder_path):
        """Procesar carpeta con modo interactivo para requisitoriados"""
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
        print("=" * 60)

        success_count = 0

        for i, image_file in enumerate(image_files, 1):
            print(f"\n[{i}/{len(image_files)}] Procesando: {image_file.name}")
            print("-" * 40)

            # Mostrar información que se extraería
            student_info = self.parse_filename(image_file.name)

            if not student_info:
                print("⚠️ No se pudo extraer información. Saltando...")
                continue

            # Mostrar preview de la información
            print(f"📝 Se agregará como:")
            print(f"   👤 {student_info['nombres']} {student_info['apellidos']}")
            print(f"   🆔 {student_info['codigo']}")
            print(f"   📧 {student_info['correo']}")

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
                print("⏭️ Saltando estudiante...")

        print("\n" + "=" * 60)
        print(f"📊 Resumen:")
        print(f"✅ Estudiantes agregados: {success_count}")
        print(f"📁 Total procesados: {len(image_files)}")
        print(f"⏭️ Saltados: {len(image_files) - success_count}")

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

        print(f"📁 Procesando {len(image_files)} imágenes en modo lote...")
        print(f"⚠️ Requisitoriado por defecto: {default_requisitoriado}")
        print("=" * 60)

        success_count = 0

        for i, image_file in enumerate(image_files, 1):
            print(f"[{i}/{len(image_files)}] {image_file.name}")

            if self.add_student_auto(image_file, default_requisitoriado):
                success_count += 1
            print()

        print("=" * 60)
        print(f"✅ Completado: {success_count}/{len(image_files)} estudiantes agregados")


def main():
    """Función principal"""
    print("🎓 Cargador Inteligente de Estudiantes UPAO")
    print("=" * 50)

    uploader = SmartBulkUploader()

    # Configuración
    carpeta_imagenes = "estudiantes_fotos"  # Cambiar si es necesario

    print(f"📁 Carpeta de imágenes: {carpeta_imagenes}")
    print("\n🔧 Modos disponibles:")
    print("1. Interactivo - Pregunta por cada estudiante si es requisitoriado")
    print("2. Lote - Todos con el mismo estado de requisitoriado")

    while True:
        modo = input("\n¿Qué modo prefieres? (1/2): ").strip()

        if modo == "1":
            print("\n🔄 Iniciando modo interactivo...")
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
                else:
                    print("❓ Por favor responde 's' para sí o 'n' para no")

            print(f"\n🔄 Iniciando modo lote (requisitoriado: {requisitoriado_defecto})...")
            uploader.process_folder_batch(carpeta_imagenes, requisitoriado_defecto)
            break
        else:
            print("❓ Por favor selecciona 1 o 2")


if __name__ == "__main__":
    main()