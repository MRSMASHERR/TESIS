from app.database import get_db_connection


def test_db_connection():
    print("Iniciando prueba de conexión...")
    conn = get_db_connection()
    
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT version();")
            version = cur.fetchone()
            print("✅ Conexión exitosa!")
            print(f"Versión de PostgreSQL: {version['version']}")
            return True
        except Exception as e:
            print(f"❌ Error al ejecutar consulta: {e}")
            return False
        finally:
            conn.close()
    else:
        print("❌ No se pudo establecer la conexión")
        return False

if __name__ == "__main__":
    test_db_connection() 