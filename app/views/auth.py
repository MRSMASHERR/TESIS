import streamlit as st
from database import get_db_connection
import hashlib
import logging
from utils.email_sender import enviar_correo_bienvenida

logger = logging.getLogger(__name__)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def show_login():
    st.title("🔐 Iniciar Sesión")
    
    try:
        with st.form("login_form"):
            email = st.text_input("Correo electrónico")
            password = st.text_input("Contraseña", type="password")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                submit = st.form_submit_button("Iniciar Sesión")
            with col2:
                recovery = st.form_submit_button("¿Olvidaste tu contraseña?")
            
            if recovery:
                st.session_state.navigation = "Recuperar Contraseña"
                st.rerun()
            
            # Validación básica de entrada
            if submit:
                if not email or not password:
                    st.error("❌ Por favor complete todos los campos")
                    return
                
                # Validar formato de email
                if not '@' in email or not '.' in email:
                    st.error("❌ Formato de correo electrónico inválido")
                    return
                
                # Validar longitud de contraseña
                if len(password) < 8:
                    st.error("❌ La contraseña debe tener al menos 8 caracteres")
                    return
                
                hashed_password = hash_password(password)
                conn = get_db_connection()
                
                if conn:
                    try:
                        cur = conn.cursor()
                        
                        # Primero intentamos buscar en la tabla de administradores
                        cur.execute("""
                            SELECT 
                                id_administrador as id,
                                nombre_administrador as nombre,
                                correo_admin as email,
                                'Administrador' as tipo,
                                estado,
                                fk_rol
                            FROM administrador
                            WHERE correo_admin = %s 
                            AND contrasena_admin = %s
                        """, (email, hashed_password))
                        
                        user = cur.fetchone()
                        
                        # Si no es administrador, buscamos en la tabla de usuarios
                        if not user:
                            cur.execute("""
                                SELECT 
                                    id_usuario as id,
                                    nombre_usuario as nombre,
                                    correo_user as email,
                                    'Usuario' as tipo,
                                    estado,
                                    fk_rol
                                FROM usuario
                                WHERE correo_user = %s 
                                AND contrasena_user = %s
                            """, (email, hashed_password))
                            
                            user = cur.fetchone()
                        
                        if user:
                            if not user['estado']:
                                st.error("""
                                ❌ Usuario inactivo
                                
                                Por favor contacte a su administrador para activar su cuenta.
                                """)
                                return
                                
                            # Guardar datos en la sesión
                            st.session_state.logged_in = True
                            st.session_state.user_type = user['tipo']
                            st.session_state.user_id = user['id']
                            st.session_state.username = user['nombre']
                            st.session_state.email = user['email']
                            st.session_state.rol = user['fk_rol']
                            
                            # Mensaje de bienvenida personalizado
                            if user['tipo'] == 'Administrador':
                                st.success(f"✅ ¡Bienvenido/a, {user['nombre']}!")
                            else:
                                st.success(f"✅ ¡Bienvenido/a, {user['nombre']}!")
                            
                            st.rerun()
                        else:
                            st.error("""
                            ❌ Credenciales incorrectas
                            
                            Por favor verifique:
                            1. Su correo electrónico
                            2. Su contraseña
                            """)
                            
                    except Exception as e:
                        st.error(f"Error en el inicio de sesión: {str(e)}")
                    finally:
                        conn.close()
    
    except Exception as e:
        st.error(f"Error en el formulario de login: {str(e)}")
        logger.error(f"Error en login: {str(e)}")
    
    # Información adicional
    with st.expander("ℹ️ ¿Necesita ayuda?"):
        st.info("""
        👥 **Tipos de cuenta:**
        
        🏢 **Administrador**
        - Acceso con correo corporativo registrado
        - Gestión de usuarios y licencias
        
        👤 **Usuario**
        - Acceso con credenciales proporcionadas por su administrador
        - Funciones de reconocimiento y reciclaje
        
        ¿Olvidó su contraseña? Contacte a soporte o a su administrador.
        """)

def show_register():
    st.title("Registro de Administrador")
    
    with st.form("register_form"):
        # Datos personales
        nombre = st.text_input("Nombre completo")
        rut = st.text_input("RUT")
        email = st.text_input("Correo electrónico")
        password = st.text_input("Contraseña", type="password")
        confirm_password = st.text_input("Confirmar contraseña", type="password")
        
        # Datos de empresa
        nombre_empresa = st.text_input("Nombre de la empresa")
        numero_contacto = st.text_input("Número de contacto")
        direccion = st.text_input("Dirección")
        
        submitted = st.form_submit_button("Registrar")
        
        if submitted:
            if password != confirm_password:
                st.error("Las contraseñas no coinciden")
                return
                
            if not all([nombre, rut, email, password, nombre_empresa, numero_contacto, direccion]):
                st.error("Por favor complete todos los campos")
                return
                
            # Hash de la contraseña
            hashed_password = hash_password(password)
            
            # Conectar a la base de datos
            conn = get_db_connection()
            if conn:
                try:
                    cur = conn.cursor()
                    
                    # Primero insertar la empresa
                    cur.execute("""
                        INSERT INTO empresa (nombre_empresa)
                        VALUES (%s)
                        RETURNING id_empresa
                    """, (nombre_empresa,))
                    
                    id_empresa = cur.fetchone()['id_empresa']
                    
                    # Luego insertar el administrador
                    cur.execute("""
                        INSERT INTO administrador (
                            nombre_administrador, fk_empresa, numero_administrador,
                            direccion_administrador, correo_admin, rut_admin,
                            contrasena_admin, fk_rol
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, 1)
                    """, (nombre, id_empresa, numero_contacto, direccion, 
                          email, rut, hashed_password))
                    
                    conn.commit()
                    
                    # Enviar correo de bienvenida
                    if enviar_correo_bienvenida(email, nombre, password):
                        st.success("""
                        ✅ Registro exitoso! 
                        
                        Se ha enviado un correo con tus credenciales.
                        Por favor revisa tu bandeja de entrada y spam.
                        """)
                    else:
                        st.warning("""
                        ✅ Registro exitoso, pero hubo un problema al enviar el correo.
                        
                        Por favor guarda tus credenciales:
                        - Email: {}
                        - Contraseña: La que ingresaste en el registro
                        """.format(email))
                    
                    st.session_state.navigation = "Iniciar Sesión"
                    st.rerun()
                    
                except Exception as e:
                    conn.rollback()
                    st.error(f"Error en el registro: {e}")
                finally:
                    conn.close()