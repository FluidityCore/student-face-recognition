import mysql.connector
import json
from config import DATABASE_CONFIG
from models.student import Student
from typing import List


def get_database_connection():
    try:
        connection = mysql.connector.connect(**DATABASE_CONFIG)
        return connection
    except mysql.connector.Error as err:
        print(f"Error al conectar a la base de datos: {err}")
        return None


def get_all_students() -> List[Student]:
    connection = get_database_connection()
    if not connection:
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
                       SELECT id, nombre, apellidos, correo, requisitoriado, kp
                       FROM estudiantes
                       WHERE kp IS NOT NULL
                       """)

        results = cursor.fetchall()
        students = []

        for row in results:
            # Convertir JSON string a lista
            kp_data = json.loads(row['kp']) if row['kp'] else []

            student = Student(
                id=row['id'],
                nombre=row['nombre'],
                apellidos=row['apellidos'],
                correo=row['correo'],
                requisitoriado=bool(row['requisitoriado']),
                kp=kp_data
            )
            students.append(student)

        cursor.close()
        connection.close()
        return students

    except Exception as e:
        print(f"Error al obtener estudiantes: {e}")
        return []


def get_student_by_id(student_id: int) -> Student:
    connection = get_database_connection()
    if not connection:
        return None

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
                       SELECT id, nombre, apellidos, correo, requisitoriado, kp
                       FROM estudiantes
                       WHERE id = %s
                         AND kp IS NOT NULL
                       """, (student_id,))

        row = cursor.fetchone()
        if row:
            kp_data = json.loads(row['kp']) if row['kp'] else []
            student = Student(
                id=row['id'],
                nombre=row['nombre'],
                apellidos=row['apellidos'],
                correo=row['correo'],
                requisitoriado=bool(row['requisitoriado']),
                kp=kp_data
            )
            cursor.close()
            connection.close()
            return student

        cursor.close()
        connection.close()
        return None

    except Exception as e:
        print(f"Error al obtener estudiante: {e}")
        return None