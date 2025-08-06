"""
Script de prueba específico para el login
"""

import streamlit as st
from auth_system import auth_system, require_auth

st.set_page_config(
    page_title="Test Login KRONOS",
    page_icon="🔐",
    layout="centered"
)

def main():
    """Función principal para probar solo el login"""
    
    # Verificar si está autenticado
    if not auth_system.is_authenticated():
        # Mostrar solo el formulario de login
        auth_system.show_login_form()
    else:
        # Si está autenticado, mostrar mensaje de éxito
        st.success("¡Login exitoso!")
        st.write(f"Bienvenido, {auth_system.get_current_user()['name']}")
        
        if st.button("Cerrar Sesión"):
            auth_system.logout()
            st.rerun()

if __name__ == "__main__":
    main()
