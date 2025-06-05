# app/database/connection.py
import mysql.connector
from mysql.connector import Error as MySQLError
import logging
from config import DB_CONFIG

logger = logging.getLogger(__name__)

def get_db_connection():
    """Crear conexión a MySQL"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except MySQLError as e:
        logger.error(f"Error conectando a MySQL: {e}")
        return None
