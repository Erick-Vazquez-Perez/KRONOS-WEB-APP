import streamlit as st
from database import init_database
from ui_components import (
    show_clients_gallery, 
    show_add_client, 
    show_manage_frequencies
)

# Configuración de la página
st.set_page_config(page_title="Agenda de Calendarios de Clientes", layout="wide")

def main():
    """Función principal de la aplicación"""
    st.title("Kronos Web App")
    
    # Inicializar base de datos
    init_database()
    
    # Inicializar estados de sesión
    initialize_session_state()
    
    # Sidebar para navegación
    st.sidebar.title("Menú Principal")
    page = st.sidebar.selectbox("Selecciona una opción", [
        "Clientes",
        "Agregar Cliente",
        "Administrar Frecuencias"
    ])
    
    # Navegación principal
    if page == "Clientes":
        show_clients_gallery()
    elif page == "Agregar Cliente":
        show_add_client()
    elif page == "Administrar Frecuencias":
        show_manage_frequencies()

def initialize_session_state():
    """Inicializa los estados de sesión necesarios"""
    if 'selected_client' not in st.session_state:
        st.session_state.selected_client = None
    if 'show_client_detail' not in st.session_state:
        st.session_state.show_client_detail = False
    if 'show_edit_modal' not in st.session_state:
        st.session_state.show_edit_modal = False

if __name__ == "__main__":
    main()