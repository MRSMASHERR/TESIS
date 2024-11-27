import streamlit as st
from database import get_db_connection
from views.auth import hash_password
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string
import logging
import uuid
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

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

def show_reset_password_form(token):
    st.title("🔐 Establecer Nueva Contraseña")
    
    if verificar_token(token):
        with st.form("reset_password_form"):
            nueva_password = st.text_input("Nueva contraseña", type="password")
            confirmar_password = st.text_input("Confirmar contraseña", type="password")
            submit = st.form_submit_button("Cambiar Contraseña")
            
            if submit:
                if not nueva_password or not confirmar_password:
                    st.error("❌ Por favor completa todos los campos")
                    return
                    
                if nueva_password != confirmar_password:
                    st.error("❌ Las contraseñas no coinciden")
                    return
                    
                if len(nueva_password) < 8:
                    st.error("❌ La contraseña debe tener al menos 8 caracteres")
                    return
                    
                if actualizar_password(token, nueva_password):
                    st.success("""
                    ✅ Contraseña actualizada exitosamente
                    
                    Ya puedes iniciar sesión con tu nueva contraseña.
                    """)
                    st.session_state.show_login = True
                else:
                    st.error("❌ Error al actualizar la contraseña")
        
        # Botón fuera del formulario
        if st.session_state.get('show_login', False):
            if st.button("Ir al Login"):
                st.query_params.clear()
                st.session_state.page = "login"
                st.rerun()
    else:
        st.error("""
        ❌ El enlace de recuperación no es válido o ha expirado
        
        Por favor solicita un nuevo enlace de recuperación.
        """)
        if st.button("Solicitar nuevo enlace"):
            st.query_params.clear()
            st.rerun()

def procesar_recuperacion(email):
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # Primero buscar en administradores
            cur.execute("""
                SELECT 
                    id_administrador as id,
                    nombre_administrador as nombre,
                    correo_admin as email,
                    'administrador' as tipo
                FROM administrador 
                WHERE correo_admin = %s
            """, (email,))
            
            usuario = cur.fetchone()
            
            # Si no es administrador, buscar en usuarios
            if not usuario:
                cur.execute("""
                    SELECT 
                        id_usuario as id,
                        nombre_usuario as nombre,
                        correo_user as email,
                        'usuario' as tipo
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
                    INSERT INTO reset_tokens (token, email, tipo_usuario, expiracion)
                    VALUES (%s, %s, %s, %s)
                """, (token, email, usuario['tipo'], expiracion))
                
                conn.commit()
                
                # Enviar correo con el enlace
                if enviar_correo_reset(
                    email=usuario['email'],
                    nombre=usuario['nombre'],
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

def verificar_token(token):
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT * FROM reset_tokens
                WHERE token = %s AND usado = false AND expiracion > NOW()
            """, (token,))
            
            return cur.fetchone() is not None
        except Exception as e:
            logger.error(f"Error verificando token: {str(e)}")
            return False
        finally:
            conn.close()
    return False

def actualizar_password(token, nueva_password):
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # Obtener información del token
            cur.execute("""
                SELECT email, tipo_usuario
                FROM reset_tokens
                WHERE token = %s AND usado = false AND expiracion > NOW()
            """, (token,))
            
            token_info = cur.fetchone()
            if not token_info:
                return False
            
            # Hash de la nueva contraseña
            password_hash = hash_password(nueva_password)
            
            # Actualizar contraseña según el tipo de usuario
            if token_info['tipo_usuario'] == 'administrador':
                cur.execute("""
                    UPDATE administrador 
                    SET contrasena_admin = %s 
                    WHERE correo_admin = %s
                """, (password_hash, token_info['email']))
            else:
                cur.execute("""
                    UPDATE usuario 
                    SET contrasena_user = %s 
                    WHERE correo_user = %s
                """, (password_hash, token_info['email']))
            
            # Marcar token como usado
            cur.execute("""
                UPDATE reset_tokens
                SET usado = true
                WHERE token = %s
            """, (token,))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error actualizando password: {str(e)}")
            conn.rollback()
            return False
        finally:
            conn.close()
    return False

def enviar_correo_reset(email, nombre, token):
    try:
        # Configuración del servidor de correo
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = "greenia.sistema@gmail.com"
        sender_password = "cuzh zerw eekr hcpp"
        
        # Crear mensaje
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = email
        msg['Subject'] = "Recuperación de Contraseña - Sistema de Reciclaje"
        
        # URL de recuperación (ajusta según tu dominio)
        reset_url = f"http://localhost:8501/?reset_token={token}"
        
        # Cuerpo del mensaje
        body = f"""
        Hola {nombre},

        Has solicitado recuperar tu contraseña.
        Para establecer una nueva contraseña, haz clic en el siguiente enlace:

        {reset_url}

        Este enlace expirará en 24 horas.

        Si no solicitaste este cambio, por favor ignora este correo.

        Saludos,
        Sistema de Reciclaje
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Conectar y enviar
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        return True
        
    except Exception as e:
        logger.error(f"Error enviando correo: {str(e)}")
        return False 