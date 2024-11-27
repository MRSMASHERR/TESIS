import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import EMAIL_CONFIG
import logging

logger = logging.getLogger(__name__)

def enviar_correo_bienvenida(destinatario, nombre, password):
    """Envía correo de bienvenida con credenciales"""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG["EMAIL_ADDRESS"]
        msg['To'] = destinatario
        msg['Subject'] = "Bienvenido a GreenIA - Tus credenciales de acceso"

        body = f"""
        Hola {nombre},

        Bienvenido a GreenIA. Tus credenciales de acceso son:

        Email: {destinatario}
        Contraseña: {password}

        Por favor, cambia tu contraseña después del primer inicio de sesión.

        Saludos,
        Equipo GreenIA
        """

        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(EMAIL_CONFIG["SMTP_SERVER"], EMAIL_CONFIG["SMTP_PORT"])
        server.starttls()
        server.login(EMAIL_CONFIG["EMAIL_ADDRESS"], EMAIL_CONFIG["EMAIL_PASSWORD"])
        text = msg.as_string()
        server.sendmail(EMAIL_CONFIG["EMAIL_ADDRESS"], destinatario, text)
        server.quit()
        return True

    except Exception as e:
        logger.error(f"Error al enviar correo: {str(e)}")
        return False 