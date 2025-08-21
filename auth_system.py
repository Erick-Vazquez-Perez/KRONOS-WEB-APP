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
    GLCO_USER = "glcouser"

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
                },
                "country_filter": None  # Sin filtro, ve todos los países
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
                },
                "country_filter": None  # Sin filtro, ve todos los países
            },
            "glcouser": {
                "password_hash": self._hash_password("GLCOUser2024!"),
                "role": UserRole.GLCO_USER,
                "name": "GLCO User",
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
                },
                "country_filter": "Colombia"  # Solo ve clientes de Colombia
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
            st.session_state.user_country_filter = user.get("country_filter")
            st.session_state.login_time = datetime.now()
            st.session_state.session_id = f"{username}_{datetime.now().timestamp()}"
            return True
        return False
    
    def logout(self):
        """Cierra la sesión"""
        for key in ['authenticated', 'username', 'user_role', 'user_name', 'user_permissions', 'user_country_filter', 'login_time', 'session_id']:
            if key in st.session_state:
                del st.session_state[key]
    
    def is_authenticated(self) -> bool:
        """Verifica si el usuario está autenticado y la sesión es válida"""
        if not st.session_state.get('authenticated', False):
            return False
        
        # Verificar que la sesión no sea muy antigua (opcional: 8 horas)
        login_time = st.session_state.get('login_time')
        if login_time and (datetime.now() - login_time).total_seconds() > 28800:  # 8 horas
            self.logout()
            return False
        
        return True
    
    def get_current_user(self) -> dict:
        """Obtiene información del usuario actual"""
        if not self.is_authenticated():
            return None
        
        return {
            'username': st.session_state.get('username'),
            'role': st.session_state.get('user_role'),
            'name': st.session_state.get('user_name'),
            'permissions': st.session_state.get('user_permissions', {}),
            'country_filter': st.session_state.get('user_country_filter'),
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
    
    def get_country_filter(self) -> str:
        """Obtiene el filtro de país del usuario actual"""
        if not self.is_authenticated():
            return None
        return st.session_state.get('user_country_filter')
    
    def has_country_filter(self) -> bool:
        """Verifica si el usuario tiene un filtro de país activo"""
        country_filter = self.get_country_filter()
        return country_filter is not None and country_filter != ""
    
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
        import base64
        
        # Función para obtener el logo en base64
        def get_logo_base64():
            try:
                with open("logo.png", "rb") as img_file:
                    return base64.b64encode(img_file.read()).decode()
            except FileNotFoundError:
                return ""
        
        logo_base64 = get_logo_base64()
        
        # CSS para login compacto
        st.markdown("""
        <style>
        .main .block-container {
            padding: 1rem !important;
            max-width: 100% !important;
        }
        
        header[data-testid="stHeader"] {
            display: none !important;
        }
        
        footer {
            display: none !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Crear un diseño centrado usando columnas
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            # Logo
            if logo_base64:
                st.markdown(f"""
                <div style="text-align: center; margin-bottom: 1rem;">
                    <img src="data:image/png;base64,{logo_base64}" width="150" style="max-width: 100%;">
                </div>
                """, unsafe_allow_html=True)
            
            # Título
            st.markdown("""
            <h1 style="text-align: center; color: #2c3e50; font-size: 1.5rem; font-weight: 600; margin: 0.5rem 0;">
                KRONOS 2.0
            </h1>
            <p style="text-align: center; color: #6c757d; font-size: 0.9rem; margin-bottom: 1.5rem;">
                Gestión de Calendarios
            </p>
            """, unsafe_allow_html=True)
            
            # Contenedor con borde para el formulario
            st.markdown("""
            <div style="
                background: #f8f9fa; 
                border: 2px solid #e9ecef; 
                border-radius: 10px; 
                padding: 1.5rem; 
                margin: 1rem 0;
            ">
            """, unsafe_allow_html=True)
            
            # Formulario
            with st.form("login_form", clear_on_submit=False):
                username = st.text_input("", placeholder="Usuario", label_visibility="collapsed", key="username_input")
                password = st.text_input("", type="password", placeholder="Contraseña", label_visibility="collapsed", key="password_input")
                submitted = st.form_submit_button("Acceder", type="primary", use_container_width=True)
                
                if submitted:
                    if username and password:
                        if self.login(username, password):
                            st.success("¡Acceso concedido!")
                            st.rerun()
                        else:
                            st.error("Usuario o contraseña incorrectos")
                    else:
                        st.warning("Complete todos los campos")
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Información de credenciales
            st.markdown("""
            <div style="
                background: #f8f9fa; 
                border-radius: 8px; 
                padding: 1rem; 
                margin-top: 1rem; 
                border-left: 3px solid #007bff;
            ">
                <h5 style="font-size: 0.85rem; color: #495057; margin-bottom: 0.5rem;">Acceso de Prueba</h5>
                <div style="font-size: 0.75rem; font-family: monospace; background: white; padding: 0.3rem 0.5rem; margin: 0.2rem 0; border-radius: 4px; color: #495057;">
                    kronosuser / KronosUser2024!
                </div>
                <div style="font-size: 0.75rem; font-family: monospace; background: white; padding: 0.3rem 0.5rem; margin: 0.2rem 0; border-radius: 4px; color: #495057;">
                    kronosadmin / KronosAdmin2024!
                </div>
                <div style="font-size: 0.75rem; font-family: monospace; background: white; padding: 0.3rem 0.5rem; margin: 0.2rem 0; border-radius: 4px; color: #495057;">
                    glcouser / GLCOUser2024!
                </div>
                <div style="font-size: 0.7rem; color: #6c757d; margin-top: 0.5rem;">
                    GLCOUser: Solo visualización de clientes de Colombia
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    def show_user_info(self, at_bottom=False):
        """Muestra información del usuario en la sidebar"""
        if self.is_authenticated():
            user = self.get_current_user()
            
            # Si se especifica at_bottom, no mostrar aquí
            if at_bottom:
                return
            
            with st.sidebar:
                st.markdown("---")
                st.markdown("### Usuario Activo")
                
                # Información del usuario sin emojis
                role_name = "Administrador" if self.is_admin() else "Usuario"
                
                user_info = f"""
                **{user['name']}**  
                Usuario: `{user['username']}`  
                Rol: {role_name}  
                Sesión: {user['login_time'].strftime('%H:%M')}
                """
                
                # Agregar información del filtro de país si existe
                if user.get('country_filter'):
                    user_info += f"\nPaís: {user['country_filter']}"
                
                st.markdown(user_info)
                
                # Indicador de permisos sin emojis
                if self.is_read_only():
                    st.warning("Modo Solo Lectura")
                else:
                    st.success("Permisos de Edición")
                
                # Botón de logout sin emoji
                if st.button("Cerrar Sesión", use_container_width=True):
                    self.logout()
                    st.rerun()
                
                st.markdown("---")
    
    def show_user_info_bottom(self):
        """Muestra información del usuario al final de la sidebar"""
        if self.is_authenticated():
            user = self.get_current_user()
            
            with st.sidebar:
                st.markdown("---")
                st.markdown("**Usuario Activo**")
                
                role_name = "Admin" if self.is_admin() else "Usuario"
                status = "Solo lectura" if self.is_read_only() else "Edición"
                
                user_info = f"""
                <div style="font-size: 0.8em; color: #666;">
                <strong>{user['name']}</strong><br>
                <code>{user['username']}</code> • {role_name}<br>
                {status} • {user['login_time'].strftime('%H:%M')}
                """
                
                # Agregar información del filtro de país si existe
                if user.get('country_filter'):
                    user_info += f"<br>País: {user['country_filter']}"
                
                user_info += "</div>"
                
                st.markdown(user_info, unsafe_allow_html=True)
                
                if st.button("Cerrar Sesión", use_container_width=True, key="logout_bottom"):
                    self.logout()
                    st.rerun()

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

def get_user_country_filter():
    """Función helper para obtener el filtro de país del usuario actual"""
    if not auth_system.is_authenticated():
        return None
    return auth_system.get_country_filter()

def has_country_filter():
    """Función helper para verificar si el usuario tiene filtro de país"""
    return auth_system.has_country_filter()
