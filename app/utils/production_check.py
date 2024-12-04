import os
import sys
from typing import List, Dict
import logging
from app.config import (
    APP_CONFIG, 
    SECURITY_CONFIG, 
    DB_CONFIG, 
    IS_PRODUCTION
)

logger = logging.getLogger(__name__)

def check_production_config() -> tuple[bool, List[str]]:
    """Verifica la configuración de producción"""
    errors = []
    
    # Verificar variables críticas
    required_vars = {
        'JWT_SECRET': SECURITY_CONFIG.get('JWT_SECRET', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ'),
        'DB_HOST': DB_CONFIG.get('host', 'greeniadb.c9o6eqmyqggg.us-east-1.rds.amazonaws.com'),
        'DB_PASSWORD': DB_CONFIG.get('password', 'America345'),
        'ROBOFLOW_API_KEY': os.getenv('ROBOFLOW_API_KEY', 'heEHust0x8LCWpzRlGaA'),
        'STREAMLIT_SERVER_HEADLESS': os.getenv('STREAMLIT_SERVER_HEADLESS', 'true')
    }
    
    for var, value in required_vars.items():
        if not value or value == 'default':
            errors.append(f"Variable crítica no configurada: {var}")
    
    # Verificar configuración de seguridad
    if IS_PRODUCTION:
        if 'localhost' in SECURITY_CONFIG['ALLOWED_ORIGINS']:
            errors.append("ALLOWED_ORIGINS contiene localhost en producción")
        
        if DB_CONFIG['sslmode'] != 'require':
            errors.append("SSL no está habilitado para la base de datos")
        
        if len(SECURITY_CONFIG['JWT_SECRET']) < 32:
            errors.append("JWT_SECRET es demasiado corto para producción")
    
    # Verificar URLs
    if not APP_CONFIG['BASE_URL'].startswith('https'):
        errors.append("BASE_URL debe usar HTTPS en producción")
    
    # Verificar configuración de Streamlit
    if IS_PRODUCTION:
        if not os.getenv('STREAMLIT_SERVER_HEADLESS') == 'true':
            errors.append("STREAMLIT_SERVER_HEADLESS debe ser 'true' en producción")
    
    return len(errors) == 0, errors

def setup_production():
    """Configura el entorno de producción"""
    is_valid, errors = check_production_config()
    
    if not is_valid:
        for error in errors:
            logger.error(f"Error de configuración: {error}")
        if IS_PRODUCTION:
            logger.critical("Errores críticos en configuración de producción")
            sys.exit(1)
    
    # Configurar seguridad adicional
    if IS_PRODUCTION:
        os.environ['PYTHONHASHSEED'] = '0'
        os.environ['PYTHONWARNINGS'] = 'ignore'
        
        # Deshabilitar debugging
        os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
        os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
    
    logger.info(f"Ambiente configurado para: {'producción' if IS_PRODUCTION else 'desarrollo'}")

if __name__ == "__main__":
    setup_production() 