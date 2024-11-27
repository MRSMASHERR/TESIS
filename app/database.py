import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
import streamlit as st

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos AWS con valores explícitos (sin usar getenv)
DB_HOST = "greeniadb.c9o6eqmyqggg.us-east-1.rds.amazonaws.com"
DB_NAME = "reciclaje_db"  # Nombre fijo de la base de datos
DB_USER = "postgres"
DB_PASS = "America345"
DB_PORT = "5432"

def get_db_connection():
    try:
        # Imprimir información de depuración
        print(f"Intentando conectar a la base de datos: {DB_NAME}")
        
        # Configuración de conexión con SSL explícito
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,  # Usar el nombre correcto de la base de datos
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT,
            sslmode='prefer',     # Modo SSL explícito
            connect_timeout=10,    # Timeout de conexión
            cursor_factory=RealDictCursor
        )
        conn.set_session(autocommit=False)
        return conn
    except psycopg2.OperationalError as e:
        st.error(f"Error de conexión a la base de datos AWS: {e}")
        print(f"Error detallado: {str(e)}")  # Para depuración
        return None
    except Exception as e:
        st.error(f"Error inesperado: {e}")
        print(f"Error detallado: {str(e)}")  # Para depuración
        return None 