#!/usr/bin/env python3
"""
Script para descargar y configurar los modelos dlib necesarios
para el sistema de reconocimiento facial académico
"""

import os
import sys
import urllib.request
import bz2
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DlibModelSetup:
    """Configurador de modelos dlib para el proyecto académico"""

    def __init__(self):
        self.models_dir = Path(__file__).parent / "dlib_models"
        self.models_dir.mkdir(exist_ok=True)

        self.models = {
            "shape_predictor_68_face_landmarks.dat": {
                "url": "http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2",
                "description": "Predictor de 68 landmarks faciales",
                "size_mb": "95 MB comprimido, ~200 MB descomprimido"
            },
            "dlib_face_recognition_resnet_model_v1.dat": {
                "url": "http://dlib.net/files/dlib_face_recognition_resnet_model_v1.dat.bz2",
                "description": "Modelo ResNet para embeddings 128D",
                "size_mb": "22 MB comprimido, ~45 MB descomprimido"
            }
        }

    def check_existing_models(self):
        """Verificar qué modelos ya están descargados"""
        logger.info("🔍 Verificando modelos existentes...")

        existing_models = []
        missing_models = []

        for model_name in self.models.keys():
            model_path = self.models_dir / model_name
            if model_path.exists():
                size_mb = model_path.stat().st_size / (1024 * 1024)
                logger.info(f"   ✅ {model_name} - {size_mb:.1f} MB")
                existing_models.append(model_name)
            else:
                logger.info(f"   ❌ {model_name} - No encontrado")
                missing_models.append(model_name)

        return existing_models, missing_models

    def download_model(self, model_name: str) -> bool:
        """Descargar un modelo específico"""
        model_info = self.models[model_name]
        model_path = self.models_dir / model_name
        compressed_path = model_path.with_suffix(model_path.suffix + '.bz2')

        try:
            logger.info(f"📥 Descargando {model_name}...")
            logger.info(f"   📝 {model_info['description']}")
            logger.info(f"   📊 Tamaño: {model_info['size_mb']}")
            logger.info(f"   🔗 URL: {model_info['url']}")

            # Descargar archivo comprimido
            urllib.request.urlretrieve(model_info['url'], compressed_path)
            logger.info(f"   ✅ Descarga completada")

            # Descomprimir
            logger.info(f"   📦 Descomprimiendo...")
            with bz2.BZ2File(compressed_path, 'rb') as source:
                with open(model_path, 'wb') as target:
                    target.write(source.read())

            # Limpiar archivo comprimido
            compressed_path.unlink()

            # Verificar tamaño final
            size_mb = model_path.stat().st_size / (1024 * 1024)
            logger.info(f"   ✅ {model_name} listo - {size_mb:.1f} MB")

            return True

        except Exception as e:
            logger.error(f"   ❌ Error descargando {model_name}: {e}")

            # Limpiar archivos parciales
            for path in [model_path, compressed_path]:
                if path.exists():
                    path.unlink()

            return False

    def download_all_models(self):
        """Descargar todos los modelos necesarios"""
        existing_models, missing_models = self.check_existing_models()

        if not missing_models:
            logger.info("🎉 Todos los modelos ya están disponibles")
            return True

        logger.info(f"📥 Descargando {len(missing_models)} modelo(s) faltante(s)...")

        success_count = 0
        total_count = len(missing_models)

        for model_name in missing_models:
            if self.download_model(model_name):
                success_count += 1
            else:
                logger.error(f"❌ Falló la descarga de {model_name}")

        if success_count == total_count:
            logger.info("🎉 Todos los modelos descargados exitosamente")
            return True
        else:
            logger.error(f"❌ Solo {success_count}/{total_count} modelos descargados")
            return False

    def verify_models(self):
        """Verificar que los modelos funcionan correctamente"""
        logger.info("🧪 Verificando funcionamiento de modelos...")

        try:
            import dlib

            # Verificar detector de rostros
            logger.info("   🔍 Probando detector de rostros HOG...")
            face_detector = dlib.get_frontal_face_detector()
            logger.info("   ✅ Detector HOG inicializado")

            # Verificar predictor de landmarks
            landmarks_path = self.models_dir / "shape_predictor_68_face_landmarks.dat"
            if landmarks_path.exists():
                logger.info("   📍 Probando predictor de landmarks...")
                shape_predictor = dlib.shape_predictor(str(landmarks_path))
                logger.info("   ✅ Predictor de landmarks inicializado")
            else:
                logger.error("   ❌ Archivo de landmarks no encontrado")
                return False

            # Verificar encoder facial
            encoder_path = self.models_dir / "dlib_face_recognition_resnet_model_v1.dat"
            if encoder_path.exists():
                logger.info("   🧠 Probando encoder ResNet...")
                face_encoder = dlib.face_recognition_model_v1(str(encoder_path))
                logger.info("   ✅ Encoder ResNet inicializado")
            else:
                logger.error("   ❌ Archivo de encoder no encontrado")
                return False

            logger.info("🎉 Todos los modelos verificados exitosamente")
            return True

        except ImportError:
            logger.error("❌ dlib no está instalado. Ejecuta: pip install dlib")
            return False
        except Exception as e:
            logger.error(f"❌ Error verificando modelos: {e}")
            return False

    def get_models_info(self):
        """Obtener información detallada de los modelos"""
        logger.info("📋 Información de modelos dlib:")
        logger.info("=" * 60)

        total_size = 0

        for model_name, model_info in self.models.items():
            model_path = self.models_dir / model_name
            status = "✅ Descargado" if model_path.exists() else "❌ Faltante"

            if model_path.exists():
                size_mb = model_path.stat().st_size / (1024 * 1024)
                total_size += size_mb
                size_str = f"{size_mb:.1f} MB"
            else:
                size_str = model_info['size_mb']

            logger.info(f"📄 {model_name}")
            logger.info(f"   Estado: {status}")
            logger.info(f"   Descripción: {model_info['description']}")
            logger.info(f"   Tamaño: {size_str}")
            logger.info(f"   Ubicación: {model_path}")
            logger.info("")

        logger.info(f"📊 Tamaño total descargado: {total_size:.1f} MB")
        logger.info("=" * 60)

    def create_symlinks(self):
        """Crear enlaces simbólicos en ubicaciones comunes"""
        common_locations = [
            Path(__file__).parent / "app" / "models",
            Path(__file__).parent / "models",
            Path.home() / ".dlib" / "models"
        ]

        logger.info("🔗 Creando enlaces simbólicos...")

        for location in common_locations:
            try:
                location.mkdir(parents=True, exist_ok=True)

                for model_name in self.models.keys():
                    source = self.models_dir / model_name
                    target = location / model_name

                    if source.exists() and not target.exists():
                        try:
                            # Intentar enlace simbólico
                            target.symlink_to(source.resolve())
                            logger.info(f"   ✅ {target}")
                        except OSError:
                            # Si falla, copiar archivo
                            import shutil
                            shutil.copy2(source, target)
                            logger.info(f"   📋 {target} (copia)")

            except Exception as e:
                logger.warning(f"   ⚠️ No se pudo crear enlace en {location}: {e}")


def main():
    """Función principal del setup"""
    logger.info("🤖 SETUP DE MODELOS DLIB PARA RECONOCIMIENTO FACIAL ACADÉMICO")
    logger.info("=" * 70)

    # Verificar que dlib esté instalado
    try:
        import dlib

        # Intentar obtener versión (no todas las versiones tienen DLIB_VERSION)
        try:
            version = dlib.DLIB_VERSION
        except AttributeError:
            # Fallback: usar __version__ o detectar automáticamente
            try:
                version = dlib.__version__
            except AttributeError:
                version = "19.22+ (Versión personalizada detectada)"

        logger.info(f"✅ dlib {version} instalado")

        # Log adicional para tu versión específica
        if "19.22.99" in str(version) or "win_amd64" in dlib.__file__:
            logger.info("🔧 Versión local personalizada detectada (compatible)")

    except ImportError:
        logger.error("❌ dlib no está instalado")
        logger.error("💡 Para desarrollo local: pip install dlib-19.22.99-cp39-cp39-win_amd64.whl")
        logger.error("💡 Para Railway/Linux: pip install dlib")
        logger.error("💡 En sistemas Ubuntu/Debian: sudo apt-get install libopenblas-dev liblapack-dev")
        sys.exit(1)

    # Inicializar configurador
    setup = DlibModelSetup()

    # Mostrar información actual
    setup.get_models_info()

    # Descargar modelos faltantes
    logger.info("🚀 Iniciando descarga de modelos...")
    if not setup.download_all_models():
        logger.error("❌ Error en la descarga de modelos")
        sys.exit(1)

    # Verificar que funcionan
    if not setup.verify_models():
        logger.error("❌ Error en la verificación de modelos")
        sys.exit(1)

    # Crear enlaces simbólicos
    setup.create_symlinks()

    # Información final
    logger.info("\n🎉 SETUP COMPLETADO EXITOSAMENTE")
    logger.info("=" * 50)
    logger.info("📁 Modelos instalados en: " + str(setup.models_dir))
    logger.info("🚀 Tu sistema está listo para reconocimiento facial académico")
    logger.info("\n📝 JUSTIFICACIÓN ACADÉMICA:")
    logger.info("✅ Modelos dlib explicados paso a paso")
    logger.info("✅ Proceso de extracción documentado")
    logger.info("✅ Sistema de aprendizaje adaptativo")
    logger.info("✅ Comparación multi-métrica")
    logger.info("✅ NO usa face_recognition como caja negra")

    logger.info("\n▶️  Próximos pasos:")
    logger.info("1. Ejecutar la aplicación: python -m app.main")
    logger.info("2. Probar reconocimiento: POST /api/recognize")
    logger.info("3. Ver documentación: http://localhost:8000/docs")


if __name__ == "__main__":
    main()