import streamlit as st
import base64
from database import init_database
from config import get_db_config
from auth_system import auth_system, require_auth, is_read_only_mode, get_current_user
from ui_components import (
    show_clients_gallery, 
    show_add_client, 
    show_manage_frequencies
)
from dashboard_components import show_dashboard, show_performance_dashboard, show_system_health
from werfen_styles import get_custom_css, get_werfen_header, get_werfen_footer

# Configuración de la página
st.set_page_config(
    page_title="Green Logistics - Werfen",
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


def inject_scroll_reset_on_tabs():
    """Inyecta JS para volver al inicio al cambiar de pestaña (st.tabs)."""
    st.markdown(
        """
        <script>
        const bindScrollReset = () => {
            document.querySelectorAll('[role="tab"]').forEach(tab => {
                if (!tab.dataset.scrollBound) {
                    tab.addEventListener('click', () => {
                        window.scrollTo({ top: 0, behavior: 'smooth' });
                    });
                    tab.dataset.scrollBound = 'true';
                }
            });
        };

        const observer = new MutationObserver(() => bindScrollReset());
        bindScrollReset();
        observer.observe(document.body, { childList: true, subtree: true });
        </script>
        """,
        unsafe_allow_html=True,
    )

def main():
    """Función principal de la aplicación"""
    
    # Aplicar estilos CSS personalizados
    st.markdown(get_custom_css(), unsafe_allow_html=True)
    inject_scroll_reset_on_tabs()
    
    # SISTEMA DE AUTENTICACIÓN - Requerir login
    require_auth()
    
    # NO mostrar información del usuario aquí - se mostrará al final
    
    # Obtener configuración de entorno y usuario actual
    config = get_db_config()
    current_user = get_current_user()
    
    # Inicializar base de datos (solo una vez por sesión para evitar lentitud en cada rerun)
    if not st.session_state.get("_db_initialized", False):
        init_database()
        st.session_state["_db_initialized"] = True
    
    # Inicializar estados de sesión
    initialize_session_state()
    
    # Sidebar para navegación
    # Mostrar logo de Werfen en la sidebar usando HTML para evitar el botón fullscreen
    st.sidebar.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <img src="data:image/png;base64,{}" width="200" style="max-width: 100%;">
        <h3 style="color: #06038D; font-size: 1.2rem; font-weight: 600; margin-top: 10px; margin-bottom: 0;">Green Logistics</h3>
    </div>
    """.format(get_logo_base64()), unsafe_allow_html=True)
    st.sidebar.markdown("---")  # Línea separadora
    
    # Navegación usando selectbox - Basado en permisos del usuario
    if is_read_only_mode():
        # Usuario de solo lectura - Solo Dashboard, Clientes y Generar Calendarios
        page_options = ["Dashboard", "Clientes"]
        help_text = f"Usuario {current_user['username']} - Solo lectura"
    else:
        # Usuario administrador - Todas las opciones
        page_options = [
            "Dashboard",
            "Clientes",
            "Agregar Cliente",
            "Administrar Frecuencias",
            "Generar Cartas",
            "Generar Calendarios Anuales"
        ]
        help_text = f"Usuario {current_user['username']} - Permisos completos"

        # Solo administradores del sistema pueden gestionar usuarios
        if auth_system.is_admin():
            page_options.append("Usuarios")
    
    # Selectbox para navegación
    page = st.sidebar.selectbox(
        "Navegación:",
        page_options,
        index=0,
        help=help_text,
        key="page_selector"
    )

    # Si la página cambia, cerrar diálogos de usuario abiertos para evitar que aparezcan al navegar
    prev_page = st.session_state.get("_current_page")
    if prev_page is None or page != prev_page:
        st.session_state["_current_page"] = page
        st.session_state["show_user_dialog"] = False
        st.session_state["show_change_pwd_form"] = False
    
    
    # Mostrar estado del sistema
    show_system_health()
    
    # Mostrar información del usuario al final de la sidebar
    auth_system.show_user_info_bottom()
    
    # Navegación principal
    if page == "Dashboard":
        show_dashboard()
    elif page == "Clientes":
        show_clients_gallery()
    elif page == "Agregar Cliente" and not is_read_only_mode():
        show_add_client()
    elif page == "Administrar Frecuencias" and not is_read_only_mode():
        show_manage_frequencies()
    elif page == "Generar Cartas":
        # Import dinámico para evitar problemas de dependencias
        try:
            from ui_calendar_generator import show_calendar_generator
            show_calendar_generator()
        except ImportError as e:
            st.error(f"Error cargando módulo de generación de calendarios: {e}")
            st.info("Asegúrate de que las dependencias python-docx y openpyxl estén instaladas.")
    elif page == "Generar Calendarios Anuales":
        # Import dinámico para el nuevo generador de fechas múltiples
        try:
            from multi_year_generator import show_multi_year_generator
            show_multi_year_generator()
        except ImportError as e:
            st.error(f"Error cargando módulo de generación de fechas múltiples: {e}")
            st.info("Verifica que todos los módulos estén disponibles.")
    elif page == "Usuarios" and auth_system.is_admin():
        auth_system.render_user_admin_panel()

    # Diálogo de perfil/contraseña (se muestra cuando el usuario lo solicita desde la sidebar)
    auth_system.render_user_dialog()

def initialize_session_state():
    """Inicializa los estados de sesión necesarios"""
    if 'selected_client' not in st.session_state:
        st.session_state.selected_client = None
    if 'show_client_detail' not in st.session_state:
        st.session_state.show_client_detail = False
    if 'show_edit_modal' not in st.session_state:
        st.session_state.show_edit_modal = False
    if 'show_user_dialog' not in st.session_state:
        st.session_state.show_user_dialog = False
    if 'show_change_pwd_form' not in st.session_state:
        st.session_state.show_change_pwd_form = False
    
    # Inicializar estados de filtros (se eliminan cuando se hace "limpiar")
    # No inicializar con valores por defecto para permitir que los widgets se inicialicen naturalmente

if __name__ == "__main__":
    main()
    # Mostrar footer
    st.markdown(get_werfen_footer(), unsafe_allow_html=True)