import streamlit as st
from database import get_db_connection
from views.reconocimiento import classify_waste, get_bottle_info, calcular_impacto_co2, mostrar_reconocimiento_residuos

def show_user_panel():
    # Establecer la navegación por defecto si no existe
    if 'navigation' not in st.session_state:
        st.session_state.navigation = "Inicio"

    # Crear tabs para las opciones de usuario
    tab1, tab2, tab3 = st.tabs([
        "🏠 Inicio",
        "📸 Reconocimiento",
        "👤 Mi Perfil"
    ])
    
    with tab1:
        show_user_home()
    with tab2:
        show_recognition()
    with tab3:
        show_user_profile()

def show_user_home():
    st.title("🏠 Inicio")
    st.write(f"👋 Bienvenido, {st.session_state.get('user_name', '')}")
    
    # Obtener estadísticas del usuario
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # Obtener totales
            cur.execute("""
                SELECT 
                    COALESCE(SUM(cantidad_plastico), 0) as total_botellas,
                    COALESCE(SUM(cantidad_co2_plastico), 0) as total_co2
                FROM reconocimiento 
                WHERE fk_usuario = %s
            """, (st.session_state.user_id,))
            
            stats = cur.fetchone()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("Total Reciclado")
                st.write(f"### {int(stats['total_botellas'])} botellas")
                
            with col2:
                st.write("Impacto CO2")
                st.write(f"### {stats['total_co2']:.2f} kg")
            
            # Mostrar actividades recientes
            cur.execute("""
                SELECT r.fecha_reconocimiento, p.nombre_plastico, r.cantidad_plastico, r.cantidad_co2_plastico
                FROM reconocimiento r
                JOIN plastico p ON r.fk_plastico = p.id_plastico
                WHERE r.fk_usuario = %s
                ORDER BY r.fecha_reconocimiento DESC
                LIMIT 5
            """, (st.session_state.user_id,))
            
            actividades = cur.fetchall()
            
            if actividades:
                for act in actividades:
                    st.info(f"""
                    📅 {act['fecha_reconocimiento'].strftime('%d/%m/%Y %H:%M')}
                    - Tipo: {act['nombre_plastico']}
                    - Cantidad: {act['cantidad_plastico']} botellas
                    - CO2 ahorrado: {act['cantidad_co2_plastico']:.2f} kg
                    """)
            else:
                st.info("No hay reconocimientos registrados aún")
            
        except Exception as e:
            st.error(f"Error al cargar estadísticas: {str(e)}")
        finally:
            conn.close()

def show_recognition():
    st.title("📸 Reconocimiento")
    try:
        # Pasamos solo el username sin verificación de empresa por ahora
        mostrar_reconocimiento_residuos(st.session_state.username)
    except Exception as e:
        st.error(f"Error en el reconocimiento: {str(e)}")
        st.info("Por favor, contacta al administrador del sistema")

def show_user_profile():
    st.title("👤 Mi Perfil")
    # Obtener datos del usuario
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # Obtener estadísticas generales
            cur.execute("""
                SELECT 
                    COUNT(*) as total_reconocimientos,
                    COALESCE(SUM(cantidad_plastico), 0) as total_botellas,
                    COALESCE(SUM(cantidad_co2_plastico), 0) as total_co2
                FROM reconocimiento 
                WHERE fk_usuario = %s
            """, (st.session_state.user_id,))
            
            stats = cur.fetchone()
            total_reconocimientos = stats['total_reconocimientos']
            total_botellas = stats['total_botellas']
            total_co2 = stats['total_co2']
            
            # Información Personal
            st.subheader("Información Personal")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Usuario:** {st.session_state.username}")
                st.write(f"**Correo:** {st.session_state.email}")
            
            with col2:
                nivel = "Principiante 🌱"
                if total_botellas >= 100:
                    nivel = "Experto 🌳"
                elif total_botellas >= 50:
                    nivel = "Intermedio 🌿"
                st.write(f"**Nivel:** {nivel}")
                st.write(f"**Total Reciclado:** {total_botellas} botellas")
            
            # Estadísticas
            st.subheader("📊 Mis Estadísticas")
            col3, col4 = st.columns(2)
            
            with col3:
                st.metric("Total Botellas", f"{total_botellas}")
            with col4:
                st.metric("Impacto CO2", f"{total_co2:.2f} kg")
            
            # Cambiar Contraseña
            st.subheader("🔐 Cambiar Contraseña")
            with st.form("cambiar_password"):
                current_password = st.text_input("Contraseña Actual", type="password")
                new_password = st.text_input("Nueva Contraseña", type="password")
                confirm_password = st.text_input("Confirmar Nueva Contraseña", type="password")
                
                if st.form_submit_button("Actualizar Contraseña"):
                    if not current_password or not new_password or not confirm_password:
                        st.error("Por favor complete todos los campos")
                    elif new_password != confirm_password:
                        st.error("Las contraseñas nuevas no coinciden")
                    elif len(new_password) < 8:
                        st.error("La nueva contraseña debe tener al menos 8 caracteres")
                    else:
                        # Verificar contraseña actual
                        cur.execute("""
                            SELECT contrasena_user 
                            FROM usuario 
                            WHERE id_usuario = %s
                        """, (st.session_state.user_id,))
                        
                        stored_password = cur.fetchone()['contrasena_user']
                        
                        if stored_password == current_password:  # Verificación simple
                            # Actualizar contraseña
                            cur.execute("""
                                UPDATE usuario 
                                SET contrasena_user = %s 
                                WHERE id_usuario = %s
                            """, (new_password, st.session_state.user_id))
                            
                            conn.commit()
                            st.success("¡Contraseña actualizada exitosamente!")
                        else:
                            st.error("La contraseña actual es incorrecta")
            
        except Exception as e:
            st.error(f"Error al cargar perfil: {str(e)}")
        finally:
            conn.close()

def guardar_reconocimiento(plastico_id, peso, cantidad, co2, usuario_id, admin_id):
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO reconocimiento (
                    fk_plastico,
                    peso_plastico,
                    cantidad_plastico,
                    cantidad_co2_plastico,
                    fecha_reconocimiento,
                    fk_usuario,
                    fk_administrador
                ) VALUES (
                    %s, %s, %s, %s, CURRENT_TIMESTAMP, %s, %s
                )
                RETURNING id_reconocimiento
            """, (
                plastico_id,
                peso,
                cantidad,
                co2,
                usuario_id,
                admin_id
            ))
            
            id_reconocimiento = cur.fetchone()['id_reconocimiento']
            conn.commit()
            return True, id_reconocimiento
            
        except Exception as e:
            conn.rollback()
            st.error(f"Error al guardar reconocimiento: {str(e)}")
            return False, None
        finally:
            conn.close()
    return False, None