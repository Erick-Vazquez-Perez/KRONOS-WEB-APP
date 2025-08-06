"""
Script de demostración del sistema de autenticación KRONOS 2.0
"""

import streamlit as st
from auth_system import auth_system, require_auth, get_current_user

def demo_permissions():
    """Demostración de los permisos del usuario"""
    
    # Requiere estar autenticado
    require_auth()
    
    st.title("🔐 Demo Sistema de Autenticación KRONOS")
    
    # Mostrar información del usuario
    user = get_current_user()
    
    st.header("👤 Información del Usuario")
    st.json(user)
    
    st.header("🔑 Permisos del Usuario")
    
    permissions = [
        'read', 'write', 'delete', 'admin', 
        'modify_clients', 'modify_activities', 
        'modify_frequencies', 'export_data', 'view_debug'
    ]
    
    for permission in permissions:
        has_perm = auth_system.has_permission(permission)
        emoji = "✅" if has_perm else "❌"
        st.write(f"{emoji} **{permission}**: {has_perm}")
    
    st.header("🧪 Pruebas de Funcionalidad")
    
    # Test 1: Verificar modo solo lectura
    if auth_system.is_read_only():
        st.warning("🔒 **Modo Solo Lectura** - Las funciones de edición están deshabilitadas")
    else:
        st.success("✏️ **Modo Edición** - Tienes permisos para modificar datos")
    
    # Test 2: Botones según permisos
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if auth_system.has_permission('modify_clients'):
            if st.button("➕ Agregar Cliente", type="primary"):
                st.success("¡Acción permitida! (Simulación)")
        else:
            st.button("➕ Agregar Cliente", disabled=True, help="Sin permisos")
    
    with col2:
        if auth_system.has_permission('modify_frequencies'):
            if st.button("⚙️ Gestionar Frecuencias", type="primary"):
                st.success("¡Acción permitida! (Simulación)")
        else:
            st.button("⚙️ Gestionar Frecuencias", disabled=True, help="Sin permisos")
    
    with col3:
        if auth_system.has_permission('admin'):
            if st.button("🛠️ Funciones Admin", type="primary"):
                st.success("¡Acción permitida! (Simulación)")
        else:
            st.button("🛠️ Funciones Admin", disabled=True, help="Sin permisos")
    
    # Test 3: Información del entorno
    if auth_system.has_permission('view_debug'):
        with st.expander("🔧 Información de Debug"):
            import os
            st.write("**Variables de entorno relevantes:**")
            debug_vars = ['KRONOS_ENV', 'LOCAL_DEVELOPMENT', 'SQLITECLOUD_CONNECTION_STRING']
            for var in debug_vars:
                value = os.getenv(var, 'No definida')
                if 'CONNECTION_STRING' in var and value != 'No definida':
                    # Enmascarar la cadena de conexión
                    value = value[:30] + "..." + value[-20:] if len(value) > 50 else value
                st.code(f"{var}: {value}")

if __name__ == "__main__":
    st.set_page_config(
        page_title="Demo Auth KRONOS",
        page_icon="🔐",
        layout="wide"
    )
    
    demo_permissions()
