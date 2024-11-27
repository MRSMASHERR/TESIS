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

def main():
    # Inicializar estado de sesión si no existe
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    # Verificar si hay un token de recuperación en la URL
    if 'reset_token' in st.query_params and not st.session_state.get('logged_in', False):
        show_recovery_page()
        return
    
    # Contenido principal
    if not st.session_state.get('logged_in', False):
        with st.sidebar:
            st.title("🌱 GreenIA")
            choice = st.radio(
                "Navegación",
                ["Inicio", "Registro Empresa", "Iniciar Sesión", "Recuperar Contraseña"],
                key="nav_public"
            )
        
        if choice == "Inicio":
            show_home()
        elif choice == "Registro Empresa":
            show_register()
        elif choice == "Iniciar Sesión":
            show_login()
        elif choice == "Recuperar Contraseña":
            show_recovery_page()
    else:
        # Sidebar para usuarios logueados
        with st.sidebar:
            st.title("🌱 GreenIA")
            
            # Opciones según el tipo de usuario
            if st.session_state.get('user_type') == "Administrador":
                choice = st.radio(
                    "Navegación",
                    ["Panel de Gestión", "Mi Perfil"],
                    key="nav_admin"
                )
            else:
                # Usuario normal
                st.radio(
                    "Navegación",
                    ["Inicio", "Reconocimiento", "Mi Perfil"],
                    key="nav_user",
                    on_change=lambda: setattr(st.session_state, 'navigation', st.session_state.nav_user)
                )
            
            # Botón de cerrar sesión
            if st.button("Cerrar Sesión"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        
        # Mostrar contenido en el área principal
        if st.session_state.get('user_type') == "Administrador":
            if choice == "Panel de Gestión":
                show_admin_panel()
            elif choice == "Mi Perfil":
                show_admin_profile()
        else:
            # Contenido del usuario normal
            show_user_panel()

if __name__ == "__main__":
    main() 