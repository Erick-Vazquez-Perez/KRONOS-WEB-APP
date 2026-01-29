"""
Sistema de autenticación y autorización para Green Logistics
"""

import os
import streamlit as st
import bcrypt
import pandas as pd
from datetime import datetime
from enum import Enum
from typing import Optional

from database import (
    init_database,
    get_user_by_username,
    create_user,
    update_user,
    set_user_password,
    list_users,
    ensure_admin_user,
    record_login_failure,
    record_login_success,
    record_login_event,
    get_login_counts_by_day,
)

class UserRole(Enum):
    ADMIN = "gladmin"
    MX_USER = "glmxuser"
    CO_USER = "glcouser"
    CS_USER = "glcsuser"


SESSION_TTL_SECONDS = 8 * 60 * 60
MAX_FAILED_ATTEMPTS = 10
LOCKOUT_MINUTES = 10
BCRYPT_ROUNDS = 12
DEFAULT_ADMIN_USERNAME = UserRole.ADMIN.value


def _default_permissions_for_role(role: UserRole) -> dict:
    """Permisos sugeridos por rol."""
    if role == UserRole.ADMIN:
        return {
            "read": True,
            "write": True,
            "delete": True,
            "admin": True,
            "modify_clients": True,
            "modify_activities": True,
            "modify_frequencies": True,
            "export_data": True,
            "view_debug": True,
        }
    # Usuarios de negocio (lectura + export)
    return {
        "read": True,
        "write": False,
        "delete": False,
        "admin": False,
        "modify_clients": False,
        "modify_activities": False,
        "modify_frequencies": False,
        "export_data": True,
        "view_debug": False,
    }

class AuthSystem:
    """Sistema de autenticación respaldado en BD con hashing fuerte y control de permisos."""

    def __init__(self):
        self.pepper = self._load_secret("AUTH_PEPPER", env_fallback="AUTH_PEPPER", required=True)
        self.admin_bootstrap_password = self._load_secret(
            "ADMIN_BOOTSTRAP_PASSWORD", env_fallback="GLADMIN_BOOTSTRAP_PASSWORD", required=False
        )
        self._db_ready = False
        self._bootstrap_done = False

    # --- Utilidades internas ---

    def _load_secret(self, key: str, env_fallback: Optional[str] = None, required: bool = False) -> Optional[str]:
        """Obtiene valores de secrets o variables de entorno, con validación opcional."""
        value = None
        try:
            value = st.secrets.get(key)
        except Exception:
            value = None

        if not value and env_fallback:
            value = os.getenv(env_fallback)

        if required and not value:
            st.error(f"Falta configurar el secreto seguro {key} para autenticación.")
        return value

    def _ensure_db_ready(self):
        """Inicializa BD si no está lista (idempotente)."""
        if self._db_ready:
            return
        init_database()
        self._db_ready = True

    def _bootstrap_admin_user(self):
        """Crea/actualiza el usuario administrador base usando secrets."""
        if self._bootstrap_done:
            return

        self._ensure_db_ready()

        if not self.pepper:
            return  # Ya se mostró error en _load_secret

        if not self.admin_bootstrap_password:
            st.warning(
                "Configura ADMIN_BOOTSTRAP_PASSWORD en secrets para asegurar el usuario gladmin."
            )
            self._bootstrap_done = True
            return

        try:
            admin_hash = self._hash_password(self.admin_bootstrap_password)
            ensure_admin_user(
                username=DEFAULT_ADMIN_USERNAME,
                password_hash=admin_hash,
                name="Green Logistics Administrator",
                role=UserRole.ADMIN.value,
                permissions=_default_permissions_for_role(UserRole.ADMIN),
                country_filter=None,
            )
        except Exception as e:
            st.error(f"No se pudo asegurar el usuario administrador: {e}")
        finally:
            self._bootstrap_done = True

    def _hash_password(self, password: str) -> str:
        if not password:
            raise ValueError("La contraseña es obligatoria")
        if not self.pepper:
            raise ValueError("No hay pepper configurado para hashing")
        salted = (password + self.pepper).encode("utf-8")
        return bcrypt.hashpw(salted, bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode("utf-8")

    def _verify_password(self, password: str, stored_hash: str) -> bool:
        try:
            salted = (password + (self.pepper or "")).encode("utf-8")
            return bcrypt.checkpw(salted, stored_hash.encode("utf-8"))
        except Exception:
            return False

    def _parse_ts(self, value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except Exception:
            return None

    def _normalize_permissions(self, role: UserRole, permissions: Optional[dict]) -> dict:
        base = _default_permissions_for_role(role)
        if permissions:
            try:
                base.update({k: bool(v) for k, v in permissions.items()})
            except Exception:
                pass
        if role == UserRole.ADMIN:
            base.update({"admin": True, "write": True, "delete": True})
        return base

    # --- Autenticación ---

    def authenticate(self, username: str, password: str):
        """Autentica un usuario contra la BD. Retorna (bool, mensaje|user dict)."""
        self._ensure_db_ready()
        self._bootstrap_admin_user()

        user = get_user_by_username(username, include_inactive=True)
        if not user:
            return False, "Usuario o contraseña incorrectos"

        if not user.get("is_active", False):
            return False, "Cuenta desactivada. Contacta a un administrador."

        locked_until = self._parse_ts(user.get("locked_until"))
        now = datetime.utcnow()
        if locked_until and locked_until > now:
            minutes_left = max(1, int((locked_until - now).total_seconds() // 60))
            return False, f"Cuenta bloqueada por intentos fallidos. Intente en {minutes_left} min."

        if not self._verify_password(password, user.get("password_hash", "")):
            record_login_failure(username, MAX_FAILED_ATTEMPTS, LOCKOUT_MINUTES)
            refreshed = get_user_by_username(username, include_inactive=True)
            locked_after = self._parse_ts(refreshed.get("locked_until") if refreshed else None)
            if locked_after and locked_after > now:
                return False, "Cuenta bloqueada temporalmente por múltiples intentos fallidos."
            return False, "Usuario o contraseña incorrectos"

        record_login_success(username)
        record_login_event(username)
        return True, user

    def login(self, username: str, password: str) -> bool:
        """Realiza login, guarda sesión y rehace permisos."""
        ok, result = self.authenticate(username, password)
        if not ok:
            st.error(result)
            return False

        user = result
        try:
            role_enum = UserRole(user.get("role", UserRole.CS_USER.value))
        except Exception:
            role_enum = UserRole.CS_USER

        perms = self._normalize_permissions(role_enum, user.get("permissions"))

        # Forzar filtro por país según rol operativo
        country_filter = user.get("country_filter")
        if role_enum == UserRole.MX_USER:
            country_filter = "México"
        elif role_enum == UserRole.CO_USER:
            country_filter = "Colombia"

        st.session_state.authenticated = True
        st.session_state.username = user.get("username")
        st.session_state.user_role = role_enum
        st.session_state.user_name = user.get("name")
        st.session_state.user_permissions = perms
        st.session_state.user_country_filter = country_filter
        st.session_state.login_time = datetime.now()
        st.session_state.session_id = f"{username}_{datetime.now().timestamp()}"
        st.session_state._last_auth_check = datetime.utcnow().isoformat()
        return True

    def logout(self):
        """Cierra la sesión y limpia estado sensible."""
        for key in [
            'authenticated', 'username', 'user_role', 'user_name', 'user_permissions',
            'user_country_filter', 'login_time', 'session_id', '_last_auth_check'
        ]:
            if key in st.session_state:
                del st.session_state[key]

    def is_authenticated(self) -> bool:
        """Verifica autenticación y que la cuenta siga activa."""
        if not st.session_state.get('authenticated', False):
            return False

        login_time = st.session_state.get('login_time')
        if login_time and (datetime.now() - login_time).total_seconds() > SESSION_TTL_SECONDS:
            self.logout()
            return False

        # Revalidar cada 5 minutos que el usuario siga activo y con permisos vigentes
        last_check = self._parse_ts(st.session_state.get('_last_auth_check'))
        if not last_check or (datetime.utcnow() - last_check).total_seconds() > 300:
            user = get_user_by_username(st.session_state.get('username'), include_inactive=True)
            if not user or not user.get('is_active', False):
                self.logout()
                return False
            try:
                role_enum = UserRole(user.get('role', UserRole.CS_USER.value))
            except Exception:
                role_enum = UserRole.CS_USER
            st.session_state.user_permissions = self._normalize_permissions(role_enum, user.get('permissions'))
            st.session_state.user_role = role_enum
            country_filter = user.get('country_filter')
            if role_enum == UserRole.MX_USER:
                country_filter = "México"
            elif role_enum == UserRole.CO_USER:
                country_filter = "Colombia"
            st.session_state.user_country_filter = country_filter
            st.session_state._last_auth_check = datetime.utcnow().isoformat()

        return True

    # --- Helpers de usuario/permisos ---

    def get_current_user(self) -> Optional[dict]:
        """Obtiene información del usuario actual."""
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
        if not self.is_authenticated():
            return False
        permissions = st.session_state.get('user_permissions', {})
        return permissions.get(permission, False)

    def is_admin(self) -> bool:
        return self.has_permission('admin')

    def is_read_only(self) -> bool:
        return not self.has_permission('write')

    def get_country_filter(self) -> Optional[str]:
        if not self.is_authenticated():
            return None
        return st.session_state.get('user_country_filter')

    def has_country_filter(self) -> bool:
        country_filter = self.get_country_filter()
        return country_filter is not None and country_filter != ""

    def require_permission(self, permission: str, error_message: str = None):
        if not self.has_permission(permission):
            st.error(error_message or f"❌ No tienes permisos para realizar esta acción. Se requiere: {permission}")
            st.stop()

    # --- Administración de usuarios (UI) ---

    def create_user_account(self, username: str, password: str, name: str, role: UserRole,
                             permissions: Optional[dict], country_filter: Optional[str]):
        self._ensure_db_ready()
        perms = self._normalize_permissions(role, permissions)
        password_hash = self._hash_password(password)
        return create_user(
            username=username,
            password_hash=password_hash,
            role=role.value,
            name=name,
            permissions=perms,
            country_filter=country_filter,
            created_by=st.session_state.get('username'),
            is_active=True,
        )

    def update_user_account(self, username: str, name: Optional[str], role: UserRole,
                             permissions: Optional[dict], country_filter: Optional[str],
                             is_active: bool, new_password: Optional[str]):
        self._ensure_db_ready()
        perms = self._normalize_permissions(role, permissions)
        updated = update_user(
            username=username,
            name=name,
            role=role.value,
            permissions=perms,
            country_filter=country_filter,
            is_active=is_active,
            updated_by=st.session_state.get('username'),
        )
        if new_password:
            password_hash = self._hash_password(new_password)
            set_user_password(
                username=username,
                password_hash=password_hash,
                updated_by=st.session_state.get('username'),
            )
        return updated

    def show_login_form(self):
        """Muestra el formulario de login con estilos corporativos."""
        import base64

        self._ensure_db_ready()
        self._bootstrap_admin_user()

        if not self.pepper:
            st.error("Falta configurar AUTH_PEPPER en secrets para habilitar el login.")
            st.stop()

        def get_logo_base64():
            try:
                with open("logo.png", "rb") as img_file:
                    return base64.b64encode(img_file.read()).decode()
            except FileNotFoundError:
                return ""

        logo_base64 = get_logo_base64()

        st.markdown(
            """
            <style>
            header[data-testid="stHeader"],
            footer { display: none !important; }
            .main .block-container { padding-top: 2.25rem !important; padding-bottom: 2.25rem !important; max-width: 1100px !important; }
            @keyframes gl-fade-in { 0% { opacity: 0; transform: translateY(14px); filter: blur(2px);} 100% { opacity: 1; transform: translateY(0); filter: blur(0);} }
            @media (prefers-reduced-motion: reduce) { div[data-testid="stForm"], div[data-testid="stForm"] * { animation: none !important; transition: none !important; } }
            div[data-testid="stAppViewContainer"] {
                background:
                    radial-gradient(1200px 700px at 15% 15%, rgba(255,255,255,0.18), rgba(255,255,255,0) 60%),
                    radial-gradient(1200px 700px at 85% 25%, rgba(6,3,141,0.18), rgba(6,3,141,0) 55%),
                    linear-gradient(135deg, var(--werfen-blue) 0%, var(--werfen-blue-light) 45%, var(--werfen-orange) 115%) !important;
            }
            div[data-testid="stForm"] {
                background: var(--werfen-gray) !important;
                border: 1px solid var(--werfen-gray-dark) !important;
                border-radius: 18px !important;
                padding: 1.25rem 1.25rem 1rem 1.25rem !important;
                box-shadow: 0 14px 30px rgba(0, 0, 0, 0.14) !important;
                position: relative;
                overflow: hidden;
                animation: gl-fade-in 520ms cubic-bezier(0.22, 1, 0.36, 1) both;
            }
            div[data-testid="stForm"] .stTextInput > div > div > input {
                border-radius: 12px !important;
                border: 2px solid rgba(6, 3, 141, 0.16) !important;
                padding: 0.7rem 0.9rem !important;
                font-size: 14px !important;
                background: rgba(255, 255, 255, 0.95) !important;
            }
            div[data-testid="stForm"] .stTextInput > div > div > input:focus {
                border-color: var(--werfen-blue) !important;
                box-shadow: 0 0 0 3px rgba(6, 3, 141, 0.12) !important;
            }
            div[data-testid="stForm"] .stButton > button[kind="primary"],
            div[data-testid="stForm"] .stButton > button[data-testid="baseButton-primary"] {
                background: linear-gradient(90deg, var(--werfen-blue) 0%, var(--werfen-blue-light) 55%, var(--werfen-orange) 135%) !important;
                border-color: transparent !important;
                color: white !important;
                border-radius: 12px !important;
                min-height: 46px !important;
                box-shadow: 0 10px 20px rgba(6, 3, 141, 0.18) !important;
            }
            div[data-testid="stForm"] .stButton > button[kind="primary"]:hover,
            div[data-testid="stForm"] .stButton > button[data-testid="baseButton-primary"]:hover {
                filter: brightness(1.02);
                transform: translateY(-1px);
                box-shadow: 0 14px 26px rgba(6, 3, 141, 0.22) !important;
            }
            .gl-login-title { text-align: center; margin: 0.25rem 0 0.15rem 0; font-weight: 800; letter-spacing: 0.2px; color: var(--werfen-blue); font-size: 1.55rem; animation: gl-fade-in 640ms cubic-bezier(0.22, 1, 0.36, 1) both; animation-delay: 120ms; }
            .gl-login-subtitle { text-align: center; margin: 0 0 1.1rem 0; color: rgba(0, 0, 0, 0.62); font-size: 0.95rem; animation: gl-fade-in 640ms cubic-bezier(0.22, 1, 0.36, 1) both; animation-delay: 170ms; }
            .gl-login-logo { display: block; margin: 0.9rem auto 0.4rem auto; width: 50%; height: auto; animation: gl-fade-in 720ms cubic-bezier(0.22, 1, 0.36, 1) both; animation-delay: 60ms; }
            div[data-testid="stForm"] label, div[data-testid="stForm"] .stTextInput, div[data-testid="stForm"] .stButton { animation: gl-fade-in 560ms cubic-bezier(0.22, 1, 0.36, 1) both; }
            </style>
            """,
            unsafe_allow_html=True,
        )

        col1, col2, col3 = st.columns([1.2, 1, 1.2])

        with col2:
            with st.form("login_form", clear_on_submit=False):
                if logo_base64:
                    st.markdown(
                        f'<img class="gl-login-logo" src="data:image/png;base64,{logo_base64}" alt="Werfen" />',
                        unsafe_allow_html=True,
                    )

                st.markdown('<h1 class="gl-login-title">Green Logistics</h1>', unsafe_allow_html=True)
                st.markdown('<p class="gl-login-subtitle">Sistema de calendarización</p>', unsafe_allow_html=True)

                username = st.text_input(
                    "Usuario",
                    placeholder="Ingresa tu usuario",
                    label_visibility="visible",
                    key="username_input",
                )
                password = st.text_input(
                    "Contraseña",
                    type="password",
                    placeholder="Ingresa tu contraseña",
                    label_visibility="visible",
                    key="password_input",
                )

                submitted = st.form_submit_button("Acceder", type="primary", use_container_width=True)

                if submitted:
                    if username and password:
                        if self.login(username.strip(), password):
                            st.success("¡Acceso concedido!")
                            st.rerun()
                        else:
                            st.error("Usuario o contraseña incorrectos")
                    else:
                        st.warning("Complete todos los campos")

    def show_user_info(self, at_bottom=False):
        """Muestra información del usuario en la sidebar."""
        if not self.is_authenticated():
            return

        user = self.get_current_user()
        if at_bottom:
            return

        with st.sidebar:
            st.markdown("---")
            st.markdown("### Usuario Activo")

            role_name = "Administrador" if self.is_admin() else "Usuario"
            login_time = user['login_time']
            session_str = login_time.strftime('%H:%M') if hasattr(login_time, 'strftime') else ""
            user_info = f"""
            **{user['name']}**  
            Usuario: `{user['username']}`  
            Rol: {role_name}  
            Sesión: {session_str}
            """

            if user.get('country_filter'):
                user_info += f"\nPaís: {user['country_filter']}"

            st.markdown(user_info)

            if st.button("Ver usuario", use_container_width=True):
                st.session_state["show_user_dialog"] = True

    def show_user_info_bottom(self):
        """Muestra información del usuario al final de la sidebar."""
        if not self.is_authenticated():
            return

        user = self.get_current_user()
        with st.sidebar:
            st.markdown("---")
            st.markdown("**Usuario Activo**")

            role_name = "Admin" if self.is_admin() else "Usuario"
            status = "Solo lectura" if self.is_read_only() else "Edición"
            login_time = user['login_time']
            session_str = login_time.strftime('%H:%M') if hasattr(login_time, 'strftime') else ""

            user_info = f"""
            <div style="font-size: 0.8em; color: #666;">
            <strong>{user['name']}</strong><br>
            <code>{user['username']}</code> - {role_name}<br>
            {status} - {session_str}
            """

            if user.get('country_filter'):
                user_info += f"<br>País: {user['country_filter']}"

            user_info += "</div>"

            st.markdown(user_info, unsafe_allow_html=True)

            if st.button("Ver usuario", use_container_width=True, key="show_user_dialog_bottom"):
                st.session_state["show_user_dialog"] = True

    def render_user_dialog(self):
        """Muestra un diálogo con los datos del usuario y acciones."""
        if not st.session_state.get("show_user_dialog"):
            return

        user = self.get_current_user()
        if not user:
            st.session_state["show_user_dialog"] = False
            return

        db_user = get_user_by_username(user['username'], include_inactive=True)
        if not db_user:
            st.session_state["show_user_dialog"] = False
            st.error("No se encontró el usuario en la base de datos.")
            return

        def initials(full_name: str) -> str:
            parts = [p for p in (full_name or "").split() if p]
            if not parts:
                return "US"
            return (parts[0][0] + (parts[1][0] if len(parts) > 1 else "")).upper()

        def _dialog_body():
            col_avatar, col_info = st.columns([1, 3])
            with col_avatar:
                st.markdown(
                    f"""
                    <div style="width:72px;height:72px;border-radius:50%;background:linear-gradient(135deg,#06038D,#FF7F32);display:flex;align-items:center;justify-content:center;color:white;font-weight:700;font-size:22px;">
                    {initials(user.get('name',''))}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col_info:
                st.markdown(f"**{user.get('name','')}**")
                st.markdown(f"Usuario: `{user.get('username','')}`")
                st.markdown(f"Rol: {user.get('role').value if user.get('role') else 'N/D'}")
                if user.get('country_filter'):
                    st.markdown(f"Filtro país: {user['country_filter']}")
                perms = user.get('permissions') or {}
                perm_desc = []
                if perms.get('admin'): perm_desc.append('Admin')
                if perms.get('write'): perm_desc.append('Edición')
                if perms.get('read'): perm_desc.append('Lectura')
                st.markdown(f"Permisos: {', '.join(perm_desc) if perm_desc else 'N/D'}")

            st.markdown("---")

            if "show_change_pwd_form" not in st.session_state:
                st.session_state["show_change_pwd_form"] = False

            if not st.session_state["show_change_pwd_form"]:
                col_a, col_b = st.columns([1, 1])
                with col_a:
                    if st.button("Cambiar contraseña", type="primary", use_container_width=True):
                        st.session_state["show_change_pwd_form"] = True
                        st.rerun()
                with col_b:
                    if st.button("Cerrar sesión", use_container_width=True):
                        self.logout()
                        st.session_state["show_user_dialog"] = False
                        st.session_state["show_change_pwd_form"] = False
                        st.rerun()
                return

            with st.form("change_password_form"):
                st.text_input("Usuario", value=user['username'], disabled=True)
                current_pwd = st.text_input("Contraseña actual", type="password")
                new_pwd = st.text_input("Nueva contraseña", type="password")
                confirm_pwd = st.text_input("Confirmar nueva contraseña", type="password")

                col_a, col_b = st.columns([1, 1])
                with col_a:
                    submit_change = st.form_submit_button("Guardar", type="primary")
                with col_b:
                    cancel_change = st.form_submit_button("Cancelar")

            if cancel_change:
                st.session_state["show_change_pwd_form"] = False
                st.rerun()

            if submit_change:
                if not (current_pwd and new_pwd and confirm_pwd):
                    st.error("Completa todos los campos.")
                    return
                if len(new_pwd) < 8:
                    st.error("La nueva contraseña debe tener al menos 8 caracteres.")
                    return
                if new_pwd != confirm_pwd:
                    st.error("La confirmación no coincide.")
                    return
                if not self._verify_password(current_pwd, db_user.get("password_hash", "")):
                    st.error("La contraseña actual no es correcta.")
                    return
                if self._verify_password(new_pwd, db_user.get("password_hash", "")):
                    st.error("La nueva contraseña no puede ser igual a la actual.")
                    return

                try:
                    new_hash = self._hash_password(new_pwd)
                    ok = set_user_password(
                        username=user['username'],
                        password_hash=new_hash,
                        updated_by=user['username'],
                    )
                    if ok:
                        st.success("Contraseña actualizada correctamente. Se cerrará la sesión para que ingreses con la nueva contraseña.")
                        self.logout()
                        st.session_state["show_change_pwd_form"] = False
                        st.session_state["show_user_dialog"] = False
                        st.rerun()
                    else:
                        st.error("No se pudo actualizar la contraseña.")
                except Exception as e:
                    st.error(f"Error al actualizar la contraseña: {e}")

        if hasattr(st, "dialog"):
            try:
                st.dialog("Usuario")(_dialog_body)()
            except Exception:
                st.warning("No se pudo abrir el diálogo; se mostrará en línea.")
                _dialog_body()
        else:
            st.warning("El diálogo modal no está disponible en esta versión de Streamlit. Se mostrará en línea.")
            _dialog_body()

    def render_user_admin_panel(self):
        """UI para que gladmin gestione usuarios."""
        self.require_permission('admin')
        self._ensure_db_ready()

        st.markdown("### Administración de usuarios")

        users_df = list_users(include_inactive=True)
        st.dataframe(users_df, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("#### Uso de la app (logins)")

        month_options = [
            ("Enero", 1), ("Febrero", 2), ("Marzo", 3), ("Abril", 4), ("Mayo", 5), ("Junio", 6),
            ("Julio", 7), ("Agosto", 8), ("Septiembre", 9), ("Octubre", 10), ("Noviembre", 11), ("Diciembre", 12)
        ]
        current_month = datetime.now().month
        default_idx = next((i for i, (_, m) in enumerate(month_options) if m == current_month), 0)
        selected_month_tuple = st.selectbox(
            "Mes",
            options=month_options,
            index=default_idx,
            format_func=lambda opt: opt[0],
            key="login_usage_month"
        )
        selected_month_name, selected_month_num = selected_month_tuple
        current_year = datetime.now().year

        login_df = get_login_counts_by_day(current_year, selected_month_num)
        if login_df.empty:
            st.info(f"Sin logins registrados en {selected_month_name} {current_year}.")
        else:
            login_df['day'] = login_df['day'].astype(int)
            pivot_df = login_df.pivot(index='day', columns='username', values='login_count').fillna(0).sort_index()
            st.line_chart(pivot_df, use_container_width=True)
            st.caption("Cantidad de logins por día (línea por usuario)")

        st.markdown("---")
        st.markdown("#### Alta de usuario")

        with st.form("create_user_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_username = st.text_input("Usuario", placeholder="ej. gluser01", key="create_new_username")
                new_name = st.text_input("Nombre completo", key="create_new_name")
                new_role = st.selectbox("Rol", options=list(UserRole), format_func=lambda r: r.value, key="create_new_role")
                new_country = st.text_input("Filtro de país (opcional)", key="create_new_country")
            with col2:
                perms_template = _default_permissions_for_role(new_role)
                perms = {
                    "read": st.checkbox("Lectura", value=perms_template.get("read", True), key="create_perm_read"),
                    "write": st.checkbox("Escritura", value=perms_template.get("write", False), key="create_perm_write"),
                    "delete": st.checkbox("Eliminar", value=perms_template.get("delete", False), key="create_perm_delete"),
                    "admin": st.checkbox("Administrador", value=perms_template.get("admin", False), key="create_perm_admin"),
                    "modify_clients": st.checkbox("Modificar clientes", value=perms_template.get("modify_clients", False), key="create_perm_modify_clients"),
                    "modify_activities": st.checkbox("Modificar actividades", value=perms_template.get("modify_activities", False), key="create_perm_modify_activities"),
                    "modify_frequencies": st.checkbox("Modificar frecuencias", value=perms_template.get("modify_frequencies", False), key="create_perm_modify_frequencies"),
                    "export_data": st.checkbox("Exportar datos", value=perms_template.get("export_data", True), key="create_perm_export_data"),
                    "view_debug": st.checkbox("Ver debug", value=perms_template.get("view_debug", False), key="create_perm_view_debug"),
                }
                new_password = st.text_input("Contraseña temporal", type="password", key="create_new_password")

            create_submitted = st.form_submit_button("Crear usuario", type="primary")
            if create_submitted:
                if not (new_username and new_password and new_name):
                    st.error("Usuario, nombre y contraseña son obligatorios")
                elif get_user_by_username(new_username, include_inactive=True):
                    st.error("El usuario ya existe")
                else:
                    ok = self.create_user_account(
                        username=new_username.strip(),
                        password=new_password,
                        name=new_name.strip(),
                        role=new_role,
                        permissions=perms,
                        country_filter=new_country.strip() or None,
                    )
                    if ok:
                        st.success("Usuario creado")
                        for k in [
                            "create_new_username","create_new_name","create_new_role","create_new_country","create_new_password",
                            "create_perm_read","create_perm_write","create_perm_delete","create_perm_admin",
                            "create_perm_modify_clients","create_perm_modify_activities","create_perm_modify_frequencies",
                            "create_perm_export_data","create_perm_view_debug",
                        ]:
                            if k in st.session_state:
                                st.session_state.pop(k)
                        st.rerun()
                    else:
                        st.error("No se pudo crear el usuario")

        st.markdown("---")
        st.markdown("#### Editar usuario")

        existing_users = users_df['username'].tolist() if not users_df.empty else []
        if not existing_users:
            st.info("No hay usuarios cargados todavía")
            return

        selected_username = st.selectbox("Selecciona un usuario", options=existing_users)
        selected_user = get_user_by_username(selected_username, include_inactive=True) if selected_username else None

        if not selected_user:
            st.warning("Usuario no encontrado")
            return

        with st.form("edit_user_form"):
            col1, col2 = st.columns(2)
            with col1:
                edit_name = st.text_input("Nombre", value=selected_user.get('name', ''), key="edit_name")
                try:
                    edit_role = st.selectbox(
                        "Rol",
                        options=list(UserRole),
                        index=list(UserRole).index(UserRole(selected_user.get('role', UserRole.CS_USER.value))),
                    )
                except Exception:
                    edit_role = st.selectbox("Rol", options=list(UserRole), index=0)
                edit_country = st.text_input("Filtro de país", value=selected_user.get('country_filter') or "", key="edit_country")
                edit_active = st.checkbox("Activo", value=bool(selected_user.get('is_active', True)), key="edit_active")
            with col2:
                current_perms = selected_user.get('permissions') or _default_permissions_for_role(edit_role)
                edit_perms = {
                    "read": st.checkbox("Lectura", value=current_perms.get("read", True), key="edit_read"),
                    "write": st.checkbox("Escritura", value=current_perms.get("write", False), key="edit_write"),
                    "delete": st.checkbox("Eliminar", value=current_perms.get("delete", False), key="edit_delete"),
                    "admin": st.checkbox("Administrador", value=current_perms.get("admin", False), key="edit_admin"),
                    "modify_clients": st.checkbox("Modificar clientes", value=current_perms.get("modify_clients", False), key="edit_modify_clients"),
                    "modify_activities": st.checkbox("Modificar actividades", value=current_perms.get("modify_activities", False), key="edit_modify_activities"),
                    "modify_frequencies": st.checkbox("Modificar frecuencias", value=current_perms.get("modify_frequencies", False), key="edit_modify_frequencies"),
                    "export_data": st.checkbox("Exportar datos", value=current_perms.get("export_data", True), key="edit_export_data"),
                    "view_debug": st.checkbox("Ver debug", value=current_perms.get("view_debug", False), key="edit_view_debug"),
                }
                new_password = st.text_input("Restablecer contraseña (opcional)", type="password", key="edit_password")

            edit_submitted = st.form_submit_button("Guardar cambios", type="primary")
            if edit_submitted:
                ok = self.update_user_account(
                    username=selected_username,
                    name=edit_name.strip(),
                    role=edit_role,
                    permissions=edit_perms,
                    country_filter=edit_country.strip() or None,
                    is_active=edit_active,
                    new_password=new_password if new_password else None,
                )
                if ok:
                    st.success("Usuario actualizado")
                    st.rerun()
                else:
                    st.error("No se pudo actualizar el usuario")

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
