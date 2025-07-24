import streamlit as st
import base64
from database import init_database
from config import get_db_config, is_read_only_mode
from ui_components import (
    show_clients_gallery, 
    show_add_client, 
    show_manage_frequencies
)
from dashboard_components import show_dashboard
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
    
    # Navegación usando selectbox (más simple y estable)
    if is_read_only_mode():
        # Solo mostrar Dashboard y Clientes en producción
        page_options = ["Dashboard", "Clientes"]
        help_text = "Modo producción - Solo dashboard y vista de clientes disponible"
    else:
        # Mostrar todas las opciones en desarrollo
        page_options = ["Dashboard", "Clientes", "Agregar Cliente", "Administrar Frecuencias"]
        help_text = "Selecciona la página que deseas ver"
    
    # Selectbox para navegación
    page = st.sidebar.selectbox(
        "Navegación:",
        page_options,
        index=0,
        help=help_text,
        key="page_selector"
    )
    
    st.sidebar.markdown("---")  # Línea separadora
    
    # Información sobre funciones futuras
    st.sidebar.markdown("### Próximamente")
    st.sidebar.info("Chat con IA integrada")
    st.sidebar.info("Exportación avanzada")
    
    # Navegación principal
    if page == "Dashboard":
        show_dashboard()
    elif page == "Clientes":
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