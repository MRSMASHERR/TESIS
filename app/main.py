import streamlit as st
from views.public import show_home, show_register
from views.auth import show_login
from views.admin import show_admin_panel, show_admin_profile
from views.user import show_user_panel
from views.recovery import show_recovery_page

# Configuración de la página
st.set_page_config(
    page_title="GreenIA",
    page_icon="🌱",
    layout="wide"
)

def create_navbar():
    col_title, col_logout = st.columns([10, 2])
    
    with col_title:
        st.write("### GreenIA")
    
    with col_logout:
        if st.button("Cerrar Sesión", use_container_width=True, type="secondary"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Crear tabs según el tipo de usuario
    if st.session_state.get('user_type') == "Administrador":
        tab1, tab2 = st.tabs([
            "Panel de Gestión",
            "Mi Perfil"
        ])
        
        with tab1:
            show_admin_panel()  # Esto ya contiene sus propias tabs
            
        with tab2:
            show_admin_profile()  # Solo muestra el perfil cuando se selecciona esta tab
            
    else:
        show_user_panel()  # Esto ya contiene sus propias tabs
    
    st.divider()

def main():
    # Inicializar estado de sesión si no existe
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    # Verificar modo prueba
    if st.query_params.get("test_mode") == "true":
        st.warning("🔧 Modo de prueba activado")
        st.session_state.test_mode = True
    
    # Verificar token de recuperación
    if 'reset_token' in st.query_params and not st.session_state.get('logged_in', False):
        show_recovery_page()
        return
    
    # Contenido principal
    if not st.session_state.get('logged_in', False):
        # Usuario no logueado
        tab1, tab2, tab3, tab4 = st.tabs(["Inicio", "Registro Empresa", "Iniciar Sesión", "Recuperar Contraseña"])
        
        with tab1:
            show_home()
        with tab2:
            show_register()
        with tab3:
            show_login()
        with tab4:
            show_recovery_page()
    else:
        # Usuario logueado - mostrar navbar y contenido
        create_navbar()
        
        # Mostrar información de pruebas
        if st.session_state.get('test_mode'):
            with st.expander("🔍 Información de Pruebas"):
                st.json({
                    "session_id": st.session_state.get('_session_id'),
                    "user_type": st.session_state.get('user_type'),
                    "navigation": st.session_state.get('navigation')
                })

if __name__ == "__main__":
    main() 