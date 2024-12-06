import streamlit as st
from database import get_db_connection
import pandas as pd
from views.auth import hash_password
import plotly.express as px
import re
from utils.email_sender import enviar_correo_bienvenida

# Definir el mapeo de tipos de plástico
PLASTIC_TYPE_NAMES = {
    '1': 'PET (Tereftalato de polietileno)',
    '2': 'HDPE (Polietileno de alta densidad)',
    '3': 'PVC (Policloruro de vinilo)',
    '4': 'LDPE (Polietileno de baja densidad)',
    '5': 'PP (Polipropileno)',
    '6': 'PS (Poliestireno)',
    '7': 'OTHER (Otros plásticos)',
    '11': 'PP (Polipropileno)',
    '14': 'PET (Tereftalato de polietileno)'
}

# Agregar las funciones de validación al inicio del archivo
def validar_numero_telefono(telefono: str) -> bool:
    """
    Valida que el número de teléfono solo contenga números
    y tenga el formato correcto (+56 9 XXXX XXXX)
    """
    telefono_limpio = telefono.replace(" ", "").replace("+", "")
    return (
        telefono_limpio.isdigit() and
        len(telefono_limpio) >= 9 and
        len(telefono_limpio) <= 11
    )

def validar_rut(rut: str) -> bool:
    """
    Valida el formato del RUT chileno
    """
    try:
        rut_limpio = rut.replace(".", "").replace("-", "").upper()
        if len(rut_limpio) < 8 or len(rut_limpio) > 9:
            return False
        cuerpo = rut_limpio[:-1]
        dv = rut_limpio[-1]
        return cuerpo.isdigit() and (dv.isdigit() or dv == 'K')
    except Exception:
        return False

def show_admin_panel():
    # Establecer la navegación por defecto si no existe
    if 'navigation' not in st.session_state:
        st.session_state.navigation = "Lista de Usuarios"

    # Crear tabs para las opciones de administrador
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Lista de Usuarios",
        "➕ Crear Usuario",
        "🔄 Actualizar Usuario",
        "📊 Reportes"
    ])
    
    with tab1:
        mostrar_lista_usuarios()
    with tab2:
        crear_usuario()
    with tab3:
        actualizar_usuario()
    with tab4:
        mostrar_reportes()

def show_admin_profile():
    st.title("👤 Mi Perfil de Administrador")
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # Obtener datos actuales del administrador
            cur.execute("""
                SELECT 
                    a.*,
                    e.nombre_empresa
                FROM administrador a
                JOIN empresa e ON a.fk_empresa = e.id_empresa
                WHERE a.id_administrador = %s
            """, (st.session_state.user_id,))
            
            admin_data = cur.fetchone()
            
            if admin_data:
                # Información Personal
                st.subheader("Información Personal")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Nombre:** {admin_data['nombre_administrador']}")
                    st.write(f"**RUT:** {admin_data['rut_admin']}")
                    st.write(f"**Email:** {admin_data['correo_admin']}")
                
                with col2:
                    st.write(f"**Empresa:** {admin_data['nombre_empresa']}")
                    st.write(f"**Teléfono:** {admin_data['numero_administrador']}")
                    st.write(f"**Dirección:** {admin_data['direccion_administrador']}")
                
                # Licencias
                st.subheader("📊 Información de Licencias")
                st.info(f"Licencias disponibles: {admin_data['numero_licencia']}")
                
                # Cambio de Contraseña
                st.subheader("🔐 Cambiar Contraseña")
                with st.form("cambiar_password"):
                    current_password = st.text_input("Contraseña actual", type="password")
                    new_password = st.text_input("Nueva contraseña", type="password")
                    confirm_password = st.text_input("Confirmar nueva contraseña", type="password")
                    
                    if st.form_submit_button("Actualizar Contraseña"):
                        if new_password != confirm_password:
                            st.error("Las contraseñas nuevas no coinciden")
                        else:
                            # Verificar contraseña actual
                            cur.execute("""
                                SELECT id_administrador 
                                FROM administrador 
                                WHERE id_administrador = %s 
                                AND contrasena_admin = %s
                            """, (
                                st.session_state.user_id,
                                hash_password(current_password)
                            ))
                            
                            if cur.fetchone():
                                # Actualizar contraseña
                                cur.execute("""
                                    UPDATE administrador 
                                    SET contrasena_admin = %s 
                                    WHERE id_administrador = %s
                                """, (
                                    hash_password(new_password),
                                    st.session_state.user_id
                                ))
                                conn.commit()
                                st.success("✅ Contraseña actualizada exitosamente")
                            else:
                                st.error("❌ Contraseña actual incorrecta")
                
                # Actualizar Información
                st.subheader("📝 Actualizar Información")
                with st.form("actualizar_info"):
                    col3, col4 = st.columns(2)
                    
                    with col3:
                        nuevo_telefono = st.text_input(
                            "Teléfono",
                            value=admin_data['numero_administrador']
                        )
                        nuevo_email = st.text_input(
                            "Email",
                            value=admin_data['correo_admin']
                        )
                    
                    with col4:
                        nueva_direccion = st.text_input(
                            "Dirección",
                            value=admin_data['direccion_administrador']
                        )
                    
                    if st.form_submit_button("Actualizar Información"):
                        try:
                            cur.execute("""
                                UPDATE administrador 
                                SET 
                                    numero_administrador = %s,
                                    correo_admin = %s,
                                    direccion_administrador = %s
                                WHERE id_administrador = %s
                            """, (
                                nuevo_telefono,
                                nuevo_email,
                                nueva_direccion,
                                st.session_state.user_id
                            ))
                            conn.commit()
                            st.success("✅ Información actualizada exitosamente")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al actualizar información: {str(e)}")
                
        except Exception as e:
            st.error(f"Error al cargar perfil: {str(e)}")
        finally:
            conn.close()

def mostrar_lista_usuarios():
    st.subheader("Lista de Usuarios")
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    id_usuario,
                    nombre_usuario,
                    rut_usuario,
                    correo_user,
                    estado
                FROM usuario 
                WHERE fk_administrador = %s
                ORDER BY nombre_usuario
            """, (st.session_state.user_id,))
            
            usuarios = cur.fetchall()
            
            if usuarios:
                # Crear DataFrame con todos los usuarios
                df = pd.DataFrame(
                    [[u['nombre_usuario'], 
                      u['rut_usuario'], 
                      u['correo_user'],
                      '🟢 Activo' if u['estado'] else '🔴 Inactivo'] 
                     for u in usuarios],
                    columns=['Nombre', 'RUT', 'Correo', 'Estado']
                )
                
                st.dataframe(
                    df,
                    hide_index=True,
                    use_container_width=True
                )
                
                # Contar solo usuarios activos para las licencias
                usuarios_activos = sum(1 for u in usuarios if u['estado'])
                
                st.markdown("---")
                st.markdown("### 🎫 Licencias")
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"Licencias utilizadas: {usuarios_activos}/10")
                with col2:
                    licencias_disponibles = 10 - usuarios_activos
                    st.success(f"Licencias disponibles: {licencias_disponibles}")
            else:
                st.info("No hay usuarios registrados")
                st.success("Tienes 10 licencias disponibles")
                
        except Exception as e:
            st.error(f"Error al cargar usuarios: {str(e)}")
        finally:
            conn.close()

def crear_usuario():
    st.subheader("Crear Nuevo Usuario")
    
    # Verificar licencias disponibles
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            # Contar solo usuarios activos
            cur.execute("""
                SELECT COUNT(*) as total_activos
                FROM usuario 
                WHERE fk_administrador = %s AND estado = true
            """, (st.session_state.user_id,))
            
            result = cur.fetchone()
            usuarios_activos = result['total_activos']
            
            if usuarios_activos >= 10:
                st.warning("⚠️ Has alcanzado el límite de licencias activas (10). Desactiva algunos usuarios para crear nuevos.")
                return
            
            # Mostrar formulario de creación
            with st.form("crear_usuario"):
                col1, col2 = st.columns(2)
                
                with col1:
                    nuevo_nombre = st.text_input(
                        "Nombre completo",
                        help="Ingrese nombre y apellido del usuario"
                    )
                    nuevo_email = st.text_input(
                        "Correo electrónico",
                        help="ejemplo@dominio.com"
                    )
                
                with col2:
                    nuevo_telefono = st.text_input(
                        "Teléfono",
                        help="Formato: +56 9 XXXX XXXX (solo números)"
                    )
                    nuevo_rut = st.text_input(
                        "RUT",
                        help="Formato: XX.XXX.XXX-Y (Y puede ser número o K)"
                    )
                    nueva_password = st.text_input(
                        "Contraseña", 
                        type="password",
                        help="Mínimo 8 caracteres, debe incluir números y letras"
                    )
                
                if st.form_submit_button("Crear Usuario"):
                    # Validaciones
                    errores = []
                    
                    # Validar nombre
                    if not nuevo_nombre or len(nuevo_nombre.strip()) < 3:
                        errores.append("❌ El nombre debe tener al menos 3 caracteres")
                    elif not all(c.isalpha() or c.isspace() for c in nuevo_nombre):
                        errores.append("❌ El nombre solo debe contener letras y espacios")
                    
                    # Validar email
                    if not nuevo_email or '@' not in nuevo_email or '.' not in nuevo_email:
                        errores.append("❌ El correo electrónico no es válido")
                    else:
                        # Verificar si el email ya existe
                        cur.execute("""
                            SELECT COUNT(*) as count 
                            FROM usuario 
                            WHERE correo_user = %s
                        """, (nuevo_email,))
                        if cur.fetchone()['count'] > 0:
                            errores.append("❌ Este correo electrónico ya está registrado")
                    
                    # Validar teléfono
                    if not validar_numero_telefono(nuevo_telefono):
                        errores.append("❌ Formato de teléfono inválido. Use solo números y el formato +56 9 XXXX XXXX")
                    
                    # Validar RUT
                    if not validar_rut(nuevo_rut):
                        errores.append("❌ Formato de RUT inválido. Use el formato XX.XXX.XXX-Y (Y puede ser número o K)")
                    
                    # Validar contraseña
                    if len(nueva_password) < 8:
                        errores.append("❌ La contraseña debe tener al menos 8 caracteres")
                    elif not any(c.isdigit() for c in nueva_password):
                        errores.append("❌ La contraseña debe incluir al menos un número")
                    elif not any(c.isalpha() for c in nueva_password):
                        errores.append("❌ La contraseña debe incluir al menos una letra")
                    
                    # Mostrar errores si existen
                    if errores:
                        for error in errores:
                            st.error(error)
                        return
                    
                    # Si no hay errores, proceder con la creación
                    try:
                        cur.execute("""
                            INSERT INTO usuario (
                                nombre_usuario,
                                rut_usuario,
                                correo_user,
                                contrasena_user,
                                estado,
                                fk_administrador
                            ) VALUES (%s, %s, %s, %s, true, %s)
                        """, (
                            nuevo_nombre.strip(),
                            nuevo_rut,
                            nuevo_email.lower(),
                            hash_password(nueva_password),
                            st.session_state.user_id
                        ))
                        
                        conn.commit()
                        
                        # Enviar correo de bienvenida
                        if enviar_correo_bienvenida(nuevo_email, nuevo_nombre, nueva_password):
                            st.success("""
                            ✅ Usuario creado exitosamente
                            
                            Se ha enviado un correo con las credenciales al usuario.
                            """)
                        else:
                            st.warning("""
                            ✅ Usuario creado exitosamente
                            ❗ No se pudo enviar el correo de bienvenida
                            """)
                        
                        st.rerun()
                        
                    except Exception as e:
                        conn.rollback()
                        st.error(f"Error al crear usuario: {str(e)}")
                        
        except Exception as e:
            st.error(f"Error al verificar licencias: {str(e)}")
        finally:
            conn.close()

def actualizar_usuario():
    st.subheader("Actualizar Usuario")
    usuarios = obtener_usuarios()
    
    if usuarios:
        usuario_seleccionado = st.selectbox(
            "Seleccionar usuario",
            options=[f"{u['nombre_usuario']} ({u['correo_user']})" for u in usuarios],
            format_func=lambda x: x.split(" (")[0]
        )
        
        if usuario_seleccionado:
            usuario = next(u for u in usuarios if f"{u['nombre_usuario']} ({u['correo_user']})" == usuario_seleccionado)
            mostrar_formulario_actualizacion(usuario)
    else:
        st.info("No hay usuarios para actualizar")

# Funciones auxiliares
def toggle_user_status(user_id, new_status):
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                UPDATE usuario 
                SET estado = %s 
                WHERE id_usuario = %s
            """, (new_status, user_id))
            conn.commit()
            return True
        except Exception as e:
            st.error(f"Error al actualizar estado: {e}")
            return False
        finally:
            conn.close()

def crear_nuevo_usuario(nombre, email, rut, password):
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO usuario (
                    nombre_usuario, correo_user, rut_usuario,
                    contrasena_user, fk_administrador, fk_rol, estado
                ) VALUES (%s, %s, %s, %s, %s, 2, true)
            """, (nombre, email, rut, hash_password(password), st.session_state.user_id))
            conn.commit()
            return True
        except Exception as e:
            st.error(f"Error al crear usuario: {e}")
            return False
        finally:
            conn.close()

def obtener_usuarios():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT * FROM usuario 
                WHERE fk_administrador = %s
                ORDER BY nombre_usuario
            """, (st.session_state.user_id,))
            return cur.fetchall()
        finally:
            conn.close()
    return []

def mostrar_formulario_actualizacion(usuario):
    with st.form("actualizar_usuario"):
        col1, col2 = st.columns(2)
        with col1:
            nuevo_nombre = st.text_input("Nombre", value=usuario['nombre_usuario'])
            nuevo_email = st.text_input("Email", value=usuario['correo_user'])
        with col2:
            nuevo_rut = st.text_input("RUT", value=usuario['rut_usuario'])
            nueva_password = st.text_input("Nueva contraseña (opcional)", type="password")
        
        nuevo_estado = st.checkbox("Usuario activo", value=usuario['estado'])
        
        if st.form_submit_button("Actualizar"):
            actualizar_datos_usuario(
                usuario['id_usuario'],
                nuevo_nombre,
                nuevo_email,
                nuevo_rut,
                nueva_password,
                nuevo_estado
            )

def actualizar_datos_usuario(id_usuario, nombre, email, rut, password, estado):
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # Construir la consulta SQL dinámicamente
            update_fields = []
            update_values = []
            
            # Agregar campos que siempre se actualizan
            update_fields.extend([
                "nombre_usuario = %s",
                "correo_user = %s",
                "rut_usuario = %s",
                "estado = %s"
            ])
            update_values.extend([nombre, email, rut, estado])
            
            # Agregar contraseña solo si se proporcionó una nueva
            if password:
                update_fields.append("contrasena_user = %s")
                update_values.append(hash_password(password))
            
            # Agregar el ID del usuario al final de los valores
            update_values.append(id_usuario)
            
            # Construir y ejecutar la consulta
            query = f"""
                UPDATE usuario 
                SET {", ".join(update_fields)}
                WHERE id_usuario = %s
            """
            
            cur.execute(query, update_values)
            conn.commit()
            st.success("✅ Usuario actualizado exitosamente")
            st.rerun()
            
        except Exception as e:
            st.error(f"Error al actualizar usuario: {str(e)}")
            conn.rollback()
        finally:
            conn.close()

def mostrar_reportes():
    st.subheader("📊 Reportes y Estadísticas")
    
    # Selector de tipo de reporte
    tipo_reporte = st.selectbox(
        "Seleccione el tipo de reporte",
        ["Actividad de Usuarios", "Impacto Ambiental", "Resumen General"]
    )
    
    # Filtros de fecha
    col1, col2 = st.columns(2)
    with col1:
        fecha_inicio = st.date_input("Fecha inicial")
    with col2:
        fecha_fin = st.date_input("Fecha final")
    
    if tipo_reporte == "Actividad de Usuarios":
        mostrar_reporte_actividad(fecha_inicio, fecha_fin)
    elif tipo_reporte == "Impacto Ambiental":
        mostrar_reporte_impacto(fecha_inicio, fecha_fin)
    else:
        mostrar_reporte_general(fecha_inicio, fecha_fin)

def mostrar_reporte_actividad(fecha_inicio, fecha_fin):
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    u.nombre_usuario,
                    COUNT(r.id_reconocimiento) as total_reconocimientos,
                    SUM(r.cantidad_plastico) as total_plastico,
                    SUM(r.cantidad_co2_plastico) as impacto_total
                FROM usuario u
                LEFT JOIN reconocimiento r ON u.id_usuario = r.fk_usuario
                WHERE r.fecha_reconocimiento BETWEEN %s AND %s
                AND u.fk_administrador = %s
                GROUP BY u.nombre_usuario
                ORDER BY total_plastico DESC
            """, (fecha_inicio, fecha_fin, st.session_state.user_id))
            
            resultados = cur.fetchall()
            
            if resultados:
                df = pd.DataFrame(resultados)
                
                # Métricas generales
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Usuarios Activos", len(resultados))
                with col2:
                    total_plastico = sum(r['total_plastico'] for r in resultados)
                    st.metric("Total Plástico Reciclado", f"{total_plastico:.2f} kg")
                with col3:
                    total_impacto = sum(r['impacto_total'] for r in resultados)
                    st.metric("Impacto CO2 Total", f"{total_impacto:.2f} kg")
                
                # Gráfico de actividad
                st.bar_chart(
                    data=df.set_index('nombre_usuario')['total_plastico'],
                    use_container_width=True
                )
                
                # Tabla detallada
                st.dataframe(
                    df,
                    hide_index=True,
                    use_container_width=True
                )
                
                # Opción de descarga
                csv = df.to_csv(index=False)
                st.download_button(
                    "📥 Descargar Reporte",
                    csv,
                    "reporte_actividad.csv",
                    "text/csv"
                )
            else:
                st.info("No hay datos para el período seleccionado")
                
        except Exception as e:
            st.error(f"Error al generar reporte: {str(e)}")
        finally:
            conn.close()

def mostrar_reporte_impacto(fecha_inicio, fecha_fin):
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    r.fk_plastico,
                    COUNT(*) as total_reconocimientos,
                    SUM(r.cantidad_plastico) as total_plastico,
                    SUM(r.cantidad_co2_plastico) as impacto_total
                FROM reconocimiento r
                JOIN usuario u ON r.fk_usuario = u.id_usuario
                WHERE r.fecha_reconocimiento BETWEEN %s AND %s
                AND u.fk_administrador = %s
                GROUP BY r.fk_plastico
            """, (fecha_inicio, fecha_fin, st.session_state.user_id))
            
            resultados = cur.fetchall()
            
            if resultados:
                # Crear DataFrame
                df = pd.DataFrame(resultados)
                
                # Convertir los IDs a nombres descriptivos
                df['tipo_plastico'] = df['fk_plastico'].astype(str).map(lambda x: PLASTIC_TYPE_NAMES.get(x, f'Tipo {x} (Desconocido)'))
                
                # Métricas generales
                col1, col2 = st.columns(2)
                with col1:
                    total_plastico = sum(r['total_plastico'] for r in resultados)
                    st.metric("Total Plástico Reciclado", f"{total_plastico:.2f} kg")
                with col2:
                    total_impacto = sum(r['impacto_total'] for r in resultados)
                    st.metric("Impacto CO2 Total", f"{total_impacto:.2f} kg")
                
                # Gráfico de distribución
                fig = px.pie(
                    df,
                    values='total_plastico',
                    names='tipo_plastico',
                    title='Distribución por Tipo de Plástico'
                )

                # Personalizar el diseño
                fig.update_traces(
                    textposition='inside',
                    textinfo='percent+label',
                    hovertemplate="<b>%{label}</b><br>" +
                                 "Cantidad: %{value:.2f} kg<br>" +
                                 "Porcentaje: %{percent}<br>"
                )

                st.plotly_chart(fig, use_container_width=True)
                
                # Tabla detallada
                st.dataframe(
                    df,
                    hide_index=True,
                    use_container_width=True
                )
                
                # Opción de descarga
                csv = df.to_csv(index=False)
                st.download_button(
                    "📥 Descargar Reporte",
                    csv,
                    "reporte_impacto.csv",
                    "text/csv"
                )
            else:
                st.info("No hay datos para el período seleccionado")
                
        except Exception as e:
            st.error(f"Error al generar reporte: {str(e)}")
        finally:
            conn.close()

def mostrar_reporte_general(fecha_inicio, fecha_fin):
    st.header("📊 Resumen General")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Estadísticas Generales")
        conn = get_db_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("""
                    SELECT 
                        COUNT(DISTINCT u.id_usuario) as total_usuarios,
                        COUNT(DISTINCT r.id_reconocimiento) as total_reconocimientos,
                        COALESCE(SUM(r.peso_plastico), 0) as total_plastico,
                        COALESCE(SUM(r.cantidad_co2_plastico), 0) as impacto_total
                    FROM usuario u
                    LEFT JOIN reconocimiento r ON u.id_usuario = r.fk_usuario
                    WHERE u.fk_administrador = %s
                    AND (r.fecha_reconocimiento BETWEEN %s AND %s 
                         OR r.fecha_reconocimiento IS NULL)
                """, (st.session_state.user_id, fecha_inicio, fecha_fin))
                
                stats = cur.fetchone()
                if stats:
                    st.metric("Total Usuarios", stats['total_usuarios'])
                    st.metric("Total Reconocimientos", stats['total_reconocimientos'])
                    st.metric("Total Plástico Reciclado", f"{stats['total_plastico']:.2f} kg")
                    st.metric("Impacto CO2 Total", f"{stats['impacto_total']:.2f} kg")
            except Exception as e:
                st.error(f"Error al obtener estadísticas: {str(e)}")
            finally:
                conn.close()
    
    with col2:
        st.subheader("🎯 Metas y Objetivos")
        # Meta mensual de reciclaje
        st.markdown("### Meta Mensual de Reciclaje")
        st.metric(
            "1000 botellas",
            "70% completado",
            delta="70%",
            delta_color="normal"
        )
        
        # Meta de reducción CO2
        st.markdown("### Meta de Reducción CO2")
        st.metric(
            "500 kg",
            "85% completado",
            delta="85%",
            delta_color="normal"
        )
    
    # Sección de Tendencias
    st.subheader("📊 Tendencias")
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    DATE_TRUNC('day', r.fecha_reconocimiento) as fecha,
                    SUM(r.peso_plastico) as total_plastico,
                    SUM(r.cantidad_co2_plastico) as impacto_total
                FROM reconocimiento r
                JOIN usuario u ON r.fk_usuario = u.id_usuario
                WHERE u.fk_administrador = %s
                AND r.fecha_reconocimiento BETWEEN %s AND %s
                GROUP BY DATE_TRUNC('day', r.fecha_reconocimiento)
                ORDER BY fecha
            """, (st.session_state.user_id, fecha_inicio, fecha_fin))
            
            resultados = cur.fetchall()
            
            if resultados:
                df = pd.DataFrame(resultados)
                fig = px.line(
                    df,
                    x='fecha',
                    y=['total_plastico', 'impacto_total'],
                    title='Tendencia de Reciclaje e Impacto',
                    labels={
                        'total_plastico': 'Plástico Reciclado (kg)',
                        'impacto_total': 'Impacto CO2 (kg)',
                        'fecha': 'Fecha'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay datos suficientes para mostrar tendencias")
                
        except Exception as e:
            st.error(f"Error al generar tendencias: {str(e)}")
        finally:
            conn.close()

def show_admin_dashboard():
    st.title("📊 Panel de Control")
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # Obtener estadísticas generales de usuarios asignados
            cur.execute("""
                WITH stats AS (
                    SELECT 
                        COUNT(DISTINCT u.id_usuario) as total_usuarios,
                        COUNT(DISTINCT r.id_reconocimiento) as total_reconocimientos,
                        COALESCE(SUM(r.cantidad_plastico), 0) as total_plastico,
                        COALESCE(SUM(r.cantidad_co2_plastico), 0) as total_co2
                    FROM usuario u
                    LEFT JOIN reconocimiento r ON u.id_usuario = r.fk_usuario
                    WHERE u.fk_administrador = %s
                )
                SELECT 
                    total_usuarios,
                    total_reconocimientos,
                    total_plastico,
                    total_co2,
                    CASE 
                        WHEN total_plastico >= 1000 THEN total_plastico * 100.0 / 1000
                        ELSE 0 
                    END as meta_reciclaje,
                    CASE 
                        WHEN total_co2 >= 500 THEN total_co2 * 100.0 / 500
                        ELSE 0 
                    END as meta_co2
                FROM stats
            """, (st.session_state.user_id,))
            
            stats = cur.fetchone()
            
            # Mostrar Estadísticas Generales
            st.subheader("📈 Estadísticas Generales")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Usuarios", f"{stats['total_usuarios']}")
            with col2:
                st.metric("Total Reconocimientos", f"{stats['total_reconocimientos']}")
            with col3:
                st.metric("Total Plástico Reciclado", f"{stats['total_plastico']:.2f} kg")
            with col4:
                st.metric("Impacto CO2 Total", f"{stats['total_co2']:.2f} kg")
            
            # Mostrar Metas y Objetivos
            st.subheader("🎯 Metas y Objetivos")
            col5, col6 = st.columns(2)
            
            with col5:
                st.write("### Meta Mensual de Reciclaje")
                st.write("1000 botellas")
                progress = min(stats['meta_reciclaje'], 100)
                st.progress(progress/100)
                st.write(f"{progress:.0f}% completado")
            
            with col6:
                st.write("### Meta de Reducción CO2")
                st.write("500 kg")
                progress_co2 = min(stats['meta_co2'], 100)
                st.progress(progress_co2/100)
                st.write(f"{progress_co2:.0f}% completado")
            
            # Mostrar Tendencias
            st.subheader("📊 Tendencias")
            
            # Obtener datos de tendencias por mes
            cur.execute("""
                SELECT 
                    DATE_TRUNC('month', r.fecha_reconocimiento) as mes,
                    COUNT(DISTINCT u.id_usuario) as usuarios_activos,
                    SUM(r.cantidad_plastico) as plastico_reciclado,
                    SUM(r.cantidad_co2_plastico) as co2_reducido
                FROM usuario u
                LEFT JOIN reconocimiento r ON u.id_usuario = r.fk_usuario
                WHERE u.fk_administrador = %s
                GROUP BY mes
                ORDER BY mes DESC
                LIMIT 6
            """, (st.session_state.user_id,))
            
            tendencias = cur.fetchall()
            
            if tendencias:
                # Aquí puedes agregar gráficos con los datos de tendencias
                st.write("Últimos 6 meses de actividad:")
                for t in tendencias:
                    st.info(f"""
                    📅 {t['mes'].strftime('%B %Y')}
                    - Usuarios Activos: {t['usuarios_activos']}
                    - Plástico Reciclado: {t['plastico_reciclado']:.2f} kg
                    - CO2 Reducido: {t['co2_reducido']:.2f} kg
                    """)
            else:
                st.info("No hay datos suficientes para mostrar tendencias")
            
        except Exception as e:
            st.error(f"Error al cargar estadísticas: {str(e)}")
        finally:
            conn.close()