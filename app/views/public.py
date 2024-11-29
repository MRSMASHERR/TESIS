import os
import streamlit as st
from views.auth import hash_password
from database import get_db_connection
import hashlib
import re


def show_home():
    st.title("Bienvenido a GreenIA")
    st.subheader("Sistema de Gestión de Residuos Reciclables")
    
    st.write("Únete a nuestra comunidad y contribuye al medio ambiente.")
    
    # Sección principal con dos columnas
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
    
    # Sección Sobre Nosotros
    st.markdown("---")
    st.markdown("### 💚 Sobre Nosotros")
    st.markdown("""
    GreenIA es una innovadora plataforma que combina tecnología de inteligencia artificial 
    con la gestión de residuos reciclables. Nuestra misión es facilitar y promover el 
    reciclaje responsable en empresas y organizaciones.
    
    #### 🎯 Nuestra Misión
    Transformar la gestión de residuos mediante tecnología inteligente, contribuyendo 
    a un futuro más sostenible.
    
    #### 🌍 Nuestro Impacto
    - Reducción de la huella de carbono
    - Optimización del proceso de reciclaje
    - Educación ambiental
    - Contribución a los ODS
    """)
    
    # Sección Por Qué Elegirnos
    st.markdown("---")
    st.markdown("### ✨ ¿Por Qué Elegirnos?")
    
    col3, col4, col5 = st.columns(3)
    
    with col3:
        st.markdown("""
        #### 🤖 Tecnología IA
        Reconocimiento automático de residuos mediante inteligencia artificial
        """)
    
    with col4:
        st.markdown("""
        #### 📊 Análisis Detallado
        Reportes y estadísticas en tiempo real de tu impacto ambiental
        """)
    
    with col5:
        st.markdown("""
        #### 🔒 Seguridad
        Datos protegidos y gestión segura de usuarios
        """)
    
    # Sección de Contacto
    st.markdown("---")
    st.markdown("### 📞 Contacto")
    st.markdown("""
    ¿Tienes dudas? Contáctanos:
    
    📧 Email: greenia.sistema@gmail.com
    📱 Teléfono: +56 9 77714168
    🏢 Dirección: Av. Principal 123, Santiago, Chile
    
    ⏰ Horario de atención:
    Lunes a Viernes: 9:00 - 18:00
    """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray; font-size: 14px;'>
        © 2024 GreenIA - Todos los derechos reservados<br>
        Síguenos en nuestras redes sociales
    </div>
    """, unsafe_allow_html=True)

def show_register():
    st.title("🏢 Comprar Licencia Anual")
    
    # Panel informativo actualizado
    with st.expander("ℹ️ Información de la Licencia", expanded=True):
        st.write("""
        ### 💎 Licencia Anual de Administrador
        Valor: $6.069.775 CLP / año
        
        #### 📦 Beneficios Incluidos:
        - 10 licencias de usuario para tu equipo
        - Acceso al sistema de reconocimiento de residuos
        - Dashboard personalizado para tu empresa
        - Reportes detallados de reciclaje
        - Soporte técnico prioritario
        
        #### 💡 ¿Cómo funciona?
        1. Completa el registro de tu empresa
        2. Realiza el pago de la licencia anual
        3. Recibe tus credenciales por correo
        4. Crea cuentas para tu equipo
        5. Comienza a gestionar el reciclaje
        
        #### 🔒 Seguridad y Garantía
        - Datos protegidos y encriptados
        - Panel de administración exclusivo
        - Gestión de usuarios controlada
        - Facturación automática anual
        - Soporte técnico garantizado
        """)
    
    # Agregar JavaScript para validación de entrada
    st.markdown("""
        <script>
            function soloNumeros(evt) {
                var charCode = (evt.which) ? evt.which : evt.keyCode;
                if (charCode > 31 && (charCode < 48 || charCode > 57)) {
                    evt.preventDefault();
                    return false;
                }
                return true;
            }
        </script>
    """, unsafe_allow_html=True)
    
    # Formulario de registro
    with st.form("registro_admin", clear_on_submit=False):
        st.subheader("📋 Datos de Facturación")
        
        col1, col2 = st.columns(2)
        
        with col1:
            nombre = st.text_input(
                "Nombre del Representante Legal",
                help="Ingrese nombre completo",
                key="nombre_legal"
            )
            
            rut = st.text_input(
                "RUT Empresa",
                help="Formato: XX.XXX.XXX-Y (con puntos y guión)",
                key="rut_empresa",
                on_change=None,
                max_chars=12  # Limitar longitud máxima
            )
            
            # Limpiar RUT de caracteres no permitidos
            if rut:
                rut = ''.join(c for c in rut if c.isdigit() or c in '.-K')
            
            email = st.text_input(
                "Email",
                help="ejemplo@dominio.com",
                key="email_empresa"
            )
            
        with col2:
            empresa = st.text_input(
                "Nombre de la Empresa",
                help="Nombre legal de la empresa",
                key="nombre_empresa"
            )
            
            telefono = st.text_input(
                "Teléfono",
                help="Formato: +56 9 XXXX XXXX (solo números)",
                key="telefono_empresa",
                max_chars=12  # Limitar longitud máxima
            )
            
            # Limpiar teléfono de caracteres no permitidos
            if telefono:
                telefono = ''.join(c for c in telefono if c.isdigit() or c == '+')
            
            direccion = st.text_input(
                "Dirección",
                help="Dirección completa de la empresa",
                key="direccion_empresa"
            )
        
        col3, col4 = st.columns(2)
        with col3:
            password = st.text_input(
                "Contraseña", 
                type="password",
                help="Mínimo 8 caracteres",
                key="password_empresa"
            )
        
        with col4:
            confirm_password = st.text_input(
                "Confirmar Contraseña", 
                type="password",
                help="Debe coincidir con la contraseña",
                key="confirm_password_empresa"
            )
        
        # Cambiar el texto del botón
        submitted = st.form_submit_button("Comprar Licencia")
        
        if submitted:
            errores = []
            
            # Validar todos los campos requeridos
            if not nombre or not empresa or not rut or not email or not telefono or not direccion:
                errores.append("❌ Todos los campos son obligatorios")
            
            # Validar RUT
            if not validar_rut(rut):
                errores.append("❌ El formato del RUT no es válido")
            
            # Validar email
            if not validar_email(email):
                errores.append("❌ El formato del email no es válido")
            
            # Validar teléfono
            if not validar_telefono(telefono):
                errores.append("❌ El formato del teléfono no es válido")
            
            # Validar contraseña
            if len(password) < 8:
                errores.append("❌ La contraseña debe tener al menos 8 caracteres")
            
            if password != confirm_password:
                errores.append("❌ Las contraseñas no coinciden")

            # Mostrar errores si existen
            if errores:
                for error in errores:
                    st.error(error)
                return

            try:
                # Obtener conexión a la base de datos
                conn = get_db_connection()
                if not conn:
                    st.error("❌ Error de conexión con la base de datos")
                    return
                
                # Crear cursor
                cur = conn.cursor()
                
                # Verificar si el email ya existe
                cur.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
                if cur.fetchone():
                    st.error("❌ Este email ya está registrado")
                    return
                
                # Insertar nuevo usuario
                cur.execute("""
                    INSERT INTO usuarios (nombre, empresa, rut, email, telefono, direccion, password, rol)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'admin')
                    RETURNING id
                """, (nombre, empresa, rut, email, telefono, direccion, hash_password(password)))
                
                # Confirmar la transacción
                conn.commit()
                
                # Solo si llegamos aquí, mostrar el mensaje de éxito
                st.success("✅ ¡Compra Exitosa!")
                
                st.image("https://www.paypalobjects.com/webstatic/mktg/logo/pp_cc_mark_111x69.jpg", 
                        width=200,
                        caption="Pago procesado con PayPal")
                
                st.info("""
                🎉 ¡Felicitaciones! Tu licencia ha sido activada.
                
                📧 Se ha enviado un correo con tus credenciales.
                ⚡ Ya puedes iniciar sesión en el sistema.
                
                Siguiente paso: Haz clic en "Iniciar Sesión" en el menú lateral.
                """)
                
            except Exception as e:
                st.error(f"❌ Error en el proceso de registro: {str(e)}")
                if 'conn' in locals():
                    conn.rollback()
            finally:
                if 'cur' in locals():
                    cur.close()
                if 'conn' in locals():
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

def validar_telefono(telefono: str) -> bool:
    """Valida que el teléfono contenga solo números y opcionalmente '+'"""
    telefono_limpio = telefono.replace('+', '')
    return (
        telefono_limpio.isdigit() and
        len(telefono_limpio) >= 9 and
        len(telefono_limpio) <= 11
    )

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

def validar_numero_telefono(telefono: str) -> bool:
    """
    Valida que el número de teléfono solo contenga números
    y tenga el formato correcto (+56 9 XXXX XXXX)
    """
    # Eliminar espacios y el '+'
    telefono_limpio = telefono.replace(" ", "").replace("+", "")
    return (
        telefono_limpio.isdigit() and  # Solo números
        len(telefono_limpio) >= 9 and  # Al menos 9 dígitos
        len(telefono_limpio) <= 11     # Máximo 11 dígitos
    )

def validar_rut(rut: str) -> bool:
    """Valida el formato del RUT y que contenga solo números (y K al final)"""
    try:
        rut_limpio = rut.replace(".", "").replace("-", "").upper()
        if not rut_limpio[:-1].isdigit():
            return False
        if not (rut_limpio[-1].isdigit() or rut_limpio[-1] == 'K'):
            return False
        return True
    except:
        return False

