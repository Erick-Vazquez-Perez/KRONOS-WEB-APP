import streamlit as st
import base64
from database import init_database
from config import get_db_config, is_read_only_mode
from ui_components import (
    show_clients_gallery, 
    show_add_client, 
    show_manage_frequencies
)
from werfen_styles import get_custom_css, get_werfen_header, get_werfen_footer

# Configuración de la página
st.set_page_config(
    page_title="Kronos - Werfen",
    page_icon="favicon.ico",
    layout="wide",
    initial_sidebar_state="expanded"
)

def get_logo_base64():
    """Convierte el logo a base64 para evitar el botón de fullscreen"""
    try:
        with open("logo.png", "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        return ""

def main():
    """Función principal de la aplicación"""
    
    # Aplicar estilos CSS personalizados
    st.markdown(get_custom_css(), unsafe_allow_html=True)
    
    # Mostrar header personalizado de Werfen
    st.markdown(get_werfen_header(), unsafe_allow_html=True)
    
    # Obtener configuración de entorno
    config = get_db_config()
    
    # Mostrar información del entorno en desarrollo
    if config.is_development():
        st.info("**Entorno de Desarrollo** - Todas las funciones habilitadas")
    config.show_environment_info()
    
    # Inicializar base de datos
    init_database()
    
    # Inicializar estados de sesión
    initialize_session_state()
    
    # Sidebar para navegación
    # Mostrar logo de Werfen en la sidebar usando HTML para evitar el botón fullscreen
    st.sidebar.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <img src="data:image/png;base64,{}" width="200" style="max-width: 100%;">
    </div>
    """.format(get_logo_base64()), unsafe_allow_html=True)
    st.sidebar.markdown("---")  # Línea separadora
    
    # Inicializar el estado de la página si no existe
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Clientes"
    
    # Función auxiliar para crear botones con indicador de estado activo
    def nav_button(label, key, disabled=False):
        is_active = st.session_state.current_page == label
        
        # Crear contenedor con clase CSS condicional para botón activo
        if is_active:
            st.sidebar.markdown('<div class="nav-active">', unsafe_allow_html=True)
        
        button_clicked = st.sidebar.button(
            label,
            key=key,
            disabled=disabled,
            use_container_width=True
        )
        
        if is_active:
            st.sidebar.markdown('</div>', unsafe_allow_html=True)
        
        return button_clicked
    
    # Botón Clientes
    if nav_button("Clientes", "nav_clients"):
        st.session_state.current_page = "Clientes"
        st.rerun()
    
    # Botones adicionales solo en modo desarrollo
    if not is_read_only_mode():
        # Botón Agregar Cliente
        if nav_button("Agregar Cliente", "nav_add_client"):
            st.session_state.current_page = "Agregar Cliente"
            st.rerun()
        
        # Botón Administrar Frecuencias
        if nav_button("Administrar Frecuencias", "nav_frequencies"):
            st.session_state.current_page = "Administrar Frecuencias"
            st.rerun()
    
    st.sidebar.markdown("---")  # Línea separadora
    
    # Nuevos botones para funciones futuras
    st.sidebar.markdown("### Próximamente")
    
    # Botón Dashboard
    if nav_button("Dashboard", "nav_dashboard", disabled=True):
        st.sidebar.info("Dashboard estará disponible próximamente con métricas y gráficos interactivos.")
    
    # Botón Chat IA  
    if nav_button("Chat con IA", "nav_chat", disabled=True):
        st.sidebar.info("Chat con IA estará disponible próximamente para ayudarte con consultas inteligentes.")
    
    # Usar el estado para determinar qué página mostrar
    page = st.session_state.current_page
    
    # Navegación principal
    if page == "Clientes":
        show_clients_gallery()
    elif page == "Agregar Cliente" and not is_read_only_mode():
        show_add_client()
    elif page == "Administrar Frecuencias" and not is_read_only_mode():
        show_manage_frequencies()
    elif is_read_only_mode() and page in ["Agregar Cliente", "Administrar Frecuencias"]:
        st.error("Esta función no está disponible en modo producción")

def initialize_session_state():
    """Inicializa los estados de sesión necesarios"""
    if 'selected_client' not in st.session_state:
        st.session_state.selected_client = None
    if 'show_client_detail' not in st.session_state:
        st.session_state.show_client_detail = False
    if 'show_edit_modal' not in st.session_state:
        st.session_state.show_edit_modal = False
    
    # Inicializar estados de filtros (se eliminan cuando se hace "limpiar")
    # No inicializar con valores por defecto para permitir que los widgets se inicialicen naturalmente

if __name__ == "__main__":
    main()
    # Mostrar footer
    st.markdown(get_werfen_footer(), unsafe_allow_html=True)