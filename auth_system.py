"""
Sistema de autenticación y autorización para KRONOS 2.0
"""

import streamlit as st
import hashlib
import hmac
from datetime import datetime, timedelta
from enum import Enum

class UserRole(Enum):
    ADMIN = "kronosadmin"
    USER = "kronosuser"

class AuthSystem:
    """Sistema de autenticación y autorización"""
    
    def __init__(self):
        # Usuarios predefinidos (en producción podrían venir de BD)
        self.users = {
            "kronosadmin": {
                "password_hash": self._hash_password("KronosAdmin2024!"),
                "role": UserRole.ADMIN,
                "name": "KronosAdministrator",
                "permissions": {
                    "read": True,
                    "write": True,
                    "delete": True,
                    "admin": True,
                    "modify_clients": True,
                    "modify_activities": True,
                    "modify_frequencies": True,
                    "export_data": True,
                    "view_debug": True
                }
            },
            "kronosuser": {
                "password_hash": self._hash_password("KronosUser2024!"),
                "role": UserRole.USER,
                "name": "KronosUser",
                "permissions": {
                    "read": True,
                    "write": False,
                    "delete": False,
                    "admin": False,
                    "modify_clients": False,
                    "modify_activities": False,
                    "modify_frequencies": False,
                    "export_data": True,
                    "view_debug": False
                }
            }
        }
    
    def _hash_password(self, password: str) -> str:
        """Hashea una contraseña usando SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def authenticate(self, username: str, password: str) -> bool:
        """Autentica un usuario"""
        if username not in self.users:
            return False
        
        user = self.users[username]
        password_hash = self._hash_password(password)
        
        return hmac.compare_digest(user["password_hash"], password_hash)
    
    def login(self, username: str, password: str) -> bool:
        """Realiza el login y almacena la sesión"""
        if self.authenticate(username, password):
            user = self.users[username]
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.user_role = user["role"]
            st.session_state.user_name = user["name"]
            st.session_state.user_permissions = user["permissions"]
            st.session_state.login_time = datetime.now()
            return True
        return False
    
    def logout(self):
        """Cierra la sesión"""
        for key in ['authenticated', 'username', 'user_role', 'user_name', 'user_permissions', 'login_time']:
            if key in st.session_state:
                del st.session_state[key]
    
    def is_authenticated(self) -> bool:
        """Verifica si el usuario está autenticado"""
        return st.session_state.get('authenticated', False)
    
    def get_current_user(self) -> dict:
        """Obtiene información del usuario actual"""
        if not self.is_authenticated():
            return None
        
        return {
            'username': st.session_state.get('username'),
            'role': st.session_state.get('user_role'),
            'name': st.session_state.get('user_name'),
            'permissions': st.session_state.get('user_permissions', {}),
            'login_time': st.session_state.get('login_time')
        }
    
    def has_permission(self, permission: str) -> bool:
        """Verifica si el usuario actual tiene un permiso específico"""
        if not self.is_authenticated():
            return False
        
        permissions = st.session_state.get('user_permissions', {})
        return permissions.get(permission, False)
    
    def is_admin(self) -> bool:
        """Verifica si el usuario actual es administrador"""
        return self.has_permission('admin')
    
    def is_read_only(self) -> bool:
        """Verifica si el usuario está en modo solo lectura"""
        return not self.has_permission('write')
    
    def require_permission(self, permission: str, error_message: str = None):
        """Decorator/función para requerir un permiso específico"""
        if not self.has_permission(permission):
            if error_message:
                st.error(error_message)
            else:
                st.error(f"❌ No tienes permisos para realizar esta acción. Se requiere: {permission}")
            st.stop()
    
    def show_login_form(self):
        """Muestra el formulario de login"""
        st.markdown("""
        <div style="display: flex; justify-content: center; align-items: center; height: 60vh;">
            <div style="background: white; padding: 2rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); max-width: 400px; width: 100%;">
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("### 🔐 Acceso KRONOS 2.0")
            st.markdown("---")
            
            with st.form("login_form"):
                username = st.text_input("Usuario", placeholder="Ingresa tu usuario")
                password = st.text_input("Contraseña", type="password", placeholder="Ingresa tu contraseña")
                
                submitted = st.form_submit_button("🚀 Iniciar Sesión", use_container_width=True)
                
                if submitted:
                    if username and password:
                        if self.login(username, password):
                            st.success("✅ ¡Acceso concedido!")
                            st.rerun()
                        else:
                            st.error("❌ Usuario o contraseña incorrectos")
                    else:
                        st.warning("⚠️ Por favor, completa todos los campos")
            
            st.markdown("---")
            st.markdown("""
            <div style="text-align: center; color: #666; font-size: 0.8em;">
                <p><strong>Usuarios de prueba:</strong></p>
                <p>📋 <code>kronosuser</code> / <code>KronosUser2024!</code> (Solo lectura)</p>
                <p>⚙️ <code>kronosadmin</code> / <code>KronosAdmin2024!</code> (Administrador)</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div></div>", unsafe_allow_html=True)
    
    def show_user_info(self):
        """Muestra información del usuario en la sidebar"""
        if self.is_authenticated():
            user = self.get_current_user()
            
            with st.sidebar:
                st.markdown("---")
                st.markdown("### 👤 Usuario Activo")
                
                # Información del usuario
                role_emoji = "⚙️" if self.is_admin() else "📋"
                role_name = "Administrador" if self.is_admin() else "Usuario"
                
                st.markdown(f"""
                **{role_emoji} {user['name']}**  
                📧 `{user['username']}`  
                🔑 {role_name}  
                ⏰ {user['login_time'].strftime('%H:%M')}
                """)
                
                # Indicador de permisos
                if self.is_read_only():
                    st.warning("🔒 Modo Solo Lectura")
                else:
                    st.success("✏️ Permisos de Edición")
                
                # Botón de logout
                if st.button("🚪 Cerrar Sesión", use_container_width=True):
                    self.logout()
                    st.rerun()
                
                st.markdown("---")

# Instancia global del sistema de autenticación
auth_system = AuthSystem()

def require_auth():
    """Decorator para requerir autenticación"""
    if not auth_system.is_authenticated():
        auth_system.show_login_form()
        st.stop()

def require_permission(permission: str, error_message: str = None):
    """Función helper para requerir permisos"""
    auth_system.require_permission(permission, error_message)

def is_read_only_mode():
    """Función helper para verificar modo solo lectura"""
    if not auth_system.is_authenticated():
        return True
    return auth_system.is_read_only()

def get_current_user():
    """Función helper para obtener usuario actual"""
    return auth_system.get_current_user()
