import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos
DB_CONFIG = {
    "HOST": os.getenv("DB_HOST", "greeniadb.c9o6eqmyqggg.us-east-1.rds.amazonaws.com"),
    "NAME": os.getenv("DB_NAME", "reciclaje_db"),
    "USER": os.getenv("DB_USER", "postgres"),
    "PASS": os.getenv("DB_PASS", "America345"),
    "PORT": os.getenv("DB_PORT", "5432")
}

# Configuración del correo electrónico
EMAIL_CONFIG = {
    "EMAIL_ADDRESS": "greenia.sistema@gmail.com",
    "EMAIL_PASSWORD": "cuzh zerw eekr hcpp",
    "SMTP_SERVER": "smtp.gmail.com",
    "SMTP_PORT": 587
}

# Configuración de Roboflow
ROBOFLOW_CONFIG = {
    "API_KEY": os.getenv("ROBOFLOW_API_KEY", "heEHust0x8LCWpzRlGaA"),
    "MODEL": "plastic-recyclable-detection/1",
    "SIZE": 416,
    "CONFIDENCE_THRESHOLD": 0.40,
    "OVERLAP_THRESHOLD": 30
}

# Configuración de la aplicación
APP_CONFIG = {
    "TITLE": "GreenIA",
    "ICON": "🌱",
    "LAYOUT": "wide",
    "SESSION_EXPIRY": 3600,  # 1 hora en segundos
    "MAX_UPLOAD_SIZE": 10 * 1024 * 1024  # 10MB en bytes
}

# Configuración de seguridad
SECURITY_CONFIG = {
    "PASSWORD_MIN_LENGTH": 8,
    "MAX_LOGIN_ATTEMPTS": 3,
    "TOKEN_EXPIRY": 24  # horas para tokens de recuperación
}

# Configuración de logging
LOGGING_CONFIG = {
    "LEVEL": "INFO",
    "FORMAT": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "FILE": "app.log"
} 