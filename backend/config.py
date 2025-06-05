# config.py
# Configuración de BD (usando tu configuración existente)
DB_CONFIG = {
    'host': 'localhost',
    'port': 3307,
    'user': 'root',
    'password': 'root',
    'database': 'idrecognition'
}

# Configuración de imagen (igual que tu script)
IMG_SIZE = (100, 100)

# Umbral de similitud para reconocimiento
SIMILARITY_THRESHOLD = 0.7