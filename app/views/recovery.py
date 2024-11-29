import streamlit as st
from database import get_db_connection
from views.auth import hash_password
import uuid
from datetime import datetime, timedelta
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from config import EMAIL_CONFIG

logger = logging.getLogger(__name__)

def show_reset_password_form(token):
    """Muestra el formulario para restablecer la contraseña"""
    st.title("🔑 Restablecer Contraseña")
    
    with st.form("reset_password_form"):
        password = st.text_input("Nueva Contraseña", type="password")
        confirm_password = st.text_input("Confirmar Contraseña", type="password")
        submit = st.form_submit_button("Cambiar Contraseña")
        
        if submit:
            if not password or not confirm_password:
                st.error("❌ Por favor completa todos los campos")
                return
            
            if password != confirm_password:
                st.error("❌ Las contraseñas no coinciden")
                return
            
            if len(password) < 8:
                st.error("❌ La contraseña debe tener al menos 8 caracteres")
                return
            
            if procesar_cambio_password(token, password):
                st.success("✅ Contraseña actualizada correctamente")
            else:
                st.error("❌ Error al actualizar la contraseña")

def show_recovery_page():
    st.title("🔑 Recuperación de Contraseña")
    
    # Verificar si hay un token de recuperación
    if 'reset_token' in st.query_params:
        show_reset_password_form(st.query_params['reset_token'])
    else:
        with st.form("recovery_form"):
            email = st.text_input("Ingresa tu correo electrónico")
            submit = st.form_submit_button("Recuperar Contraseña")
            
            if submit:
                if not email:
                    st.error("❌ Por favor ingresa tu correo electrónico")
                    return
                
                if not '@' in email or not '.' in email:
                    st.error("❌ Formato de correo electrónico inválido")
                    return
                
                if procesar_recuperacion(email):
                    st.success("""
                    ✅ Se ha enviado un correo con las instrucciones para recuperar tu contraseña
                    
                    Por favor, revisa tu bandeja de entrada y spam.
                    """)
                else:
                    st.error("""
                    ❌ No se encontró una cuenta con ese correo electrónico
                    
                    Por favor verifica:
                    1. Que el correo sea correcto
                    2. Que la cuenta esté registrada
                    """)

def enviar_correo_reset(email, nombre, token):
    """Envía correo de recuperación de contraseña"""
    try:
        # URL de recuperación (ajusta según tu dominio)
        reset_url = f"https://greenia.streamlit.app/?reset_token={token}"
        
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG["EMAIL_ADDRESS"]
        msg['To'] = email
        msg['Subject'] = "Recuperación de Contraseña - GreenIA"

        body = f"""
        Hola {nombre},

        Has solicitado recuperar tu contraseña.
        Para establecer una nueva contraseña, haz clic en el siguiente enlace:

        {reset_url}

        Este enlace expirará en 24 horas.

        Si no solicitaste este cambio, por favor ignora este correo.

        Saludos,
        Equipo GreenIA
        """

        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(EMAIL_CONFIG["SMTP_SERVER"], EMAIL_CONFIG["SMTP_PORT"])
        server.starttls()
        server.login(EMAIL_CONFIG["EMAIL_ADDRESS"], EMAIL_CONFIG["EMAIL_PASSWORD"])
        text = msg.as_string()
        server.sendmail(EMAIL_CONFIG["EMAIL_ADDRESS"], email, text)
        server.quit()
        return True

    except Exception as e:
        logger.error(f"Error al enviar correo: {str(e)}")
        return False

def procesar_recuperacion(email):
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # Buscar usuario
            cur.execute("""
                SELECT id_usuario, nombre_usuario, correo_user
                FROM usuario 
                WHERE correo_user = %s
            """, (email,))
            
            usuario = cur.fetchone()
            
            if usuario:
                # Generar token único
                token = str(uuid.uuid4())
                expiracion = datetime.now() + timedelta(hours=24)
                
                # Guardar token en la base de datos
                cur.execute("""
                    INSERT INTO reset_tokens (token, email, expiracion)
                    VALUES (%s, %s, %s)
                """, (token, email, expiracion))
                
                conn.commit()
                
                # Enviar correo con el enlace
                if enviar_correo_reset(
                    email=usuario['correo_user'],
                    nombre=usuario['nombre_usuario'],
                    token=token
                ):
                    return True
                else:
                    logger.error(f"Error al enviar correo a {email}")
                    return False
            
            return False
            
        except Exception as e:
            logger.error(f"Error en recuperación: {str(e)}")
            conn.rollback()
            return False
        finally:
            conn.close() 

def procesar_cambio_password(token, nueva_password):
    """Procesa el cambio de contraseña con el token de recuperación"""
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # Verificar que el token sea válido y no haya expirado
            cur.execute("""
                SELECT email 
                FROM reset_tokens 
                WHERE token = %s 
                AND expiracion > NOW() 
                AND usado = FALSE
            """, (token,))
            
            result = cur.fetchone()
            
            if not result:
                logger.error("Token inválido o expirado")
                return False
                
            email = result['email']
            
            # Actualizar la contraseña del usuario
            cur.execute("""
                UPDATE usuario 
                SET password_user = %s 
                WHERE correo_user = %s
            """, (hash_password(nueva_password), email))
            
            # Marcar el token como usado
            cur.execute("""
                UPDATE reset_tokens 
                SET usado = TRUE 
                WHERE token = %s
            """, (token,))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error al cambiar contraseña: {str(e)}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    return False 