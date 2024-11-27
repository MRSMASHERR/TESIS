import streamlit as st

def init_page():
    """Inicializa la configuración base de la página"""
    st.markdown("""
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    """, unsafe_allow_html=True)
    
    # Cargar CSS base
    with open('app/static/styles/base.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def show_header():
    """Muestra el header común para todas las páginas"""
    st.markdown("""
        <nav class="navbar navbar-expand-lg navbar-dark">
            <div class="container-fluid">
                <a class="navbar-brand" href="#">
                    <i class="fas fa-leaf"></i> GreenIA
                </a>
            </div>
        </nav>
    """, unsafe_allow_html=True)

def show_footer():
    """Muestra el footer común para todas las páginas"""
    st.markdown("""
        <footer class="footer mt-auto py-3 bg-light">
            <div class="container text-center">
                <span class="text-muted">© 2024 GreenIA - Todos los derechos reservados</span>
            </div>
        </footer>
    """, unsafe_allow_html=True)

def show_page_container(title, content_function):
    """Estructura base para todas las páginas"""
    init_page()
    show_header()
    
    st.markdown(f"""
        <div class="main-container">
            <div class="container">
                <h1 class="mb-4">{title}</h1>
                <div class="fade-in">
    """, unsafe_allow_html=True)
    
    content_function()
    
    st.markdown("""
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    show_footer() 