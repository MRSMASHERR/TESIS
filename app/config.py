import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Entorno de ejecución
ENV = os.getenv('ENV', 'production')
IS_PRODUCTION = ENV == 'production'

# Configuración de la aplicación
APP_CONFIG = {
    'TITLE': 'GreenIA',
    'ICON': '🌱',
    'VERSION': '1.0.0',
    'BASE_URL': os.getenv('BASE_URL', 'https://greenia.streamlit.app'),
    'API_URL': os.getenv('API_URL', 'https://greenia.streamlit.app/api')
}

# Configuración de seguridad
SECURITY_CONFIG = {
    'JWT_SECRET': os.getenv('JWT_SECRET'),
    'JWT_ALGORITHM': 'HS256',
    'ACCESS_TOKEN_EXPIRE_MINUTES': 1440,  # 24 horas
    'MAX_LOGIN_ATTEMPTS': 3,
    'BLOCK_DURATION': 60,  # minutos
    'PASSWORD_MIN_LENGTH': 8,
    'REQUIRE_SPECIAL_CHAR': True,
    'ALLOWED_ORIGINS': os.getenv('ALLOWED_ORIGINS', 'https://greenia.streamlit.app').split(',')
}

# Configuración de Rate Limiting
RATE_LIMIT = {
    'WINDOW_SIZE': int(os.getenv('RATE_LIMIT_WINDOW', 60)),  # segundos
    'MAX_REQUESTS': int(os.getenv('MAX_REQUESTS', 100)),     # por ventana
    'BURST_LIMIT': int(os.getenv('BURST_LIMIT', 20))        # por segundo
}

# Configuración de Base de Datos
DB_CONFIG = {
    "HOST": os.getenv("DB_HOST", "greeniadb.c9o6eqmyqggg.us-east-1.rds.amazonaws.com"),
    "NAME": os.getenv("DB_NAME", "reciclaje_db"),
    "USER": os.getenv("DB_USER", "postgres"),
    "PASS": os.getenv("DB_PASSWORD", "America345"),
    "PORT": os.getenv("DB_PORT", "5432")
}

# Actualizar BASE_URL para producción
BASE_URL = "https://greeia.streamlit.app"

# Actualizar configuración de Roboflow
ROBOFLOW_CONFIG = {
    "API_KEY": os.getenv("ROBOFLOW_API_KEY", "heEHust0x8LCWpzRlGaA"),
    "MODEL": "plastic-recyclable-detection/2",
    "SIZE": 416,
    "CONFIDENCE_THRESHOLD": 0.40,
    "OVERLAP_THRESHOLD": 30
}

# Configuración del correo electrónico
EMAIL_CONFIG = {
    "EMAIL_ADDRESS": "greenia.sistema@gmail.com",
    "EMAIL_PASSWORD": "cuzh zerw eekr hcpp",
    "SMTP_SERVER": "smtp.gmail.com",
    "SMTP_PORT": 587
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