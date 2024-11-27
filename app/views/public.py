import streamlit as st
from views.auth import hash_password
from database import get_db_connection
import hashlib
import re


def show_home():
    st.title("🌱 Bienvenido a GreenIA")
    st.subheader("Sistema de Gestión de Residuos Reciclables")
    
    st.write("Únete a nuestra comunidad y contribuye al medio ambiente.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🏢 Para Empresas")
        st.markdown("""
        👉 Regístrate como administrador y obtén:
        - 10 licencias de usuario
        - Panel de gestión
        - Reportes y estadísticas
        """)
        
    with col2:
        st.markdown("### 👥 Para Usuarios")
        st.markdown("""
        👉 Contacta a tu administrador para:
        - Obtener tus credenciales
        - Acceder al sistema
        - Comenzar a reciclar
        """)

def show_register():
    st.title("🏢 Registro de Empresa")
    
    # Panel informativo
    with st.expander("ℹ️ Información del Registro", expanded=True):
        st.write("""
        ### Beneficios del Registro
        - Acceso al sistema de reconocimiento de residuos
        - Dashboard personalizado
        - Reportes detallados
        - Soporte técnico
        """)
    
    # Formulario de registro
    with st.form("registro_admin", clear_on_submit=False):
        st.subheader("📋 Datos de la Empresa")
        
        col1, col2 = st.columns(2)
        
        with col1:
            nombre = st.text_input(
                "Nombre del Representante Legal",
                help="Ingrese nombre completo"
            )
            
            rut = st.text_input(
                "RUT Empresa",
                help="Formato: XX.XXX.XXX-Y (con puntos y guión)"
            )
            
            email = st.text_input(
                "Email",
                help="ejemplo@dominio.com"
            )
            
        with col2:
            empresa = st.text_input(
                "Nombre de la Empresa",
                help="Nombre legal de la empresa"
            )
            
            telefono = st.text_input(
                "Teléfono",
                help="Formato: +56 9 XXXX XXXX"
            )
            
            direccion = st.text_input(
                "Dirección",
                help="Dirección completa de la empresa"
            )
        
        col3, col4 = st.columns(2)
        with col3:
            password = st.text_input(
                "Contraseña", 
                type="password",
                help="Mínimo 8 caracteres"
            )
        
        with col4:
            confirm_password = st.text_input(
                "Confirmar Contraseña", 
                type="password",
                help="Debe coincidir con la contraseña"
            )
        
        if st.form_submit_button("Registrar Empresa"):
            # Validar datos
            errores = validar_datos_registro({
                'nombre': nombre,
                'rut': rut,
                'email': email,
                'empresa': empresa,
                'telefono': telefono,
                'direccion': direccion,
                'password': password
            })
            
            if password != confirm_password:
                errores.append("Las contraseñas no coinciden")
                
            if len(password) < 8:
                errores.append("La contraseña debe tener al menos 8 caracteres")
            
            # Mostrar errores si existen
            if errores:
                for error in errores:
                    st.error(error)
                return
            
            # Si no hay errores, proceder con el registro
            conn = get_db_connection()
            if conn:
                try:
                    cur = conn.cursor()
                    
                    # Verificar duplicados
                    cur.execute("SELECT id_empresa FROM empresa WHERE rut_admin = %s", (rut,))
                    if cur.fetchone():
                        st.error("El RUT de empresa ya está registrado")
                        return
                    
                    cur.execute("SELECT id_administrador FROM administrador WHERE correo_admin = %s", (email,))
                    if cur.fetchone():
                        st.error("El email ya está registrado")
                        return
                    
                    # Insertar empresa
                    cur.execute("""
                        INSERT INTO empresa (
                            nombre_empresa,
                            direccion_empresa
                        ) VALUES (%s, %s)
                        RETURNING id_empresa
                    """, (empresa, direccion))
                    
                    resultado = cur.fetchone()
                    id_empresa = resultado['id_empresa']
                    
                    # Insertar administrador
                    cur.execute("""
                        INSERT INTO administrador (
                            nombre_administrador,
                            rut_admin,
                            correo_admin,
                            contrasena_admin,
                            numero_administrador,
                            direccion_administrador,
                            numero_licencia,
                            fk_empresa,
                            estado
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        nombre,
                        rut,
                        email,
                        hash_password(password),
                        telefono,
                        direccion,
                        10,  # número de licencia por defecto
                        id_empresa,
                        True  # estado activo por defecto
                    ))
                    
                    conn.commit()
                    st.success("✅ ¡Registro completado exitosamente!")
                    st.info("Por favor, inicia sesión con tu email y contraseña")
                    
                except Exception as e:
                    conn.rollback()
                    st.error(f"Error en el registro: {str(e)}")
                    print(f"Error detallado: {str(e)}")
                finally:
                    conn.close()

def validar_rut_empresa(rut):
    try:
        # Verificar que el RUT no esté vacío
        if not rut:
            return False
            
        # Eliminar puntos y guión del RUT
        rut_limpio = rut.replace(".", "").replace("-", "")
        
        # Verificar que comience con 7, 8 o 9
        if not rut_limpio[0] in ['7', '8', '9']:
            return False
        
        # Verificar formato básico
        if not re.match(r'^\d{7,8}[0-9K]$', rut_limpio):
            return False
        
        # Separar número y dígito verificador
        numero = rut_limpio[:-1]
        dv = rut_limpio[-1].upper()
        
        # Calcular dígito verificador
        suma = 0
        multiplicador = 2
        
        for d in reversed(numero):
            suma += int(d) * multiplicador
            multiplicador = multiplicador + 1 if multiplicador < 7 else 2
        
        dv_esperado = '0' if 11 - (suma % 11) == 11 else 'K' if 11 - (suma % 11) == 10 else str(11 - (suma % 11))
        
        return dv == dv_esperado
        
    except Exception as e:
        print(f"Error en validación de RUT: {str(e)}")
        return False

def validar_email(email):
    # Patrón básico de email
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(patron, email) is not None

def validar_telefono(telefono):
    # Formato: +56 9 XXXX XXXX
    telefono = telefono.replace(" ", "").replace("+", "")
    return telefono.isdigit() and len(telefono) >= 9

def validar_datos_registro(datos):
    errores = []
    
    if not validar_rut_empresa(datos['rut']):
        errores.append("El RUT de empresa no es válido")
    
    if not validar_email(datos['email']):
        errores.append("El formato del email no es válido")
    
    if not validar_telefono(datos['telefono']):
        errores.append("El formato del teléfono no es válido")
    
    if not datos['nombre'] or len(datos['nombre']) < 3:
        errores.append("El nombre es demasiado corto")
    
    if not datos['empresa'] or len(datos['empresa']) < 3:
        errores.append("El nombre de la empresa es demasiado corto")
    
    if not datos['direccion'] or len(datos['direccion']) < 5:
        errores.append("La dirección es demasiado corta")
        
    return errores

