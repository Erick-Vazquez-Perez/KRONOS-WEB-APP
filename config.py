import os
import streamlit as st
from pathlib import Path

# Cargar variables de entorno desde .env si existe
def load_env_file():
    """Carga variables de entorno desde archivo .env"""
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
        except Exception as e:
            print(f"[KRONOS] Advertencia: Error cargando .env: {e}")

# Cargar .env al importar el módulo
load_env_file()

class DatabaseConfig:
    """Configuración de bases de datos para diferentes entornos"""
    
    def __init__(self):
        self.environment = self._detect_environment()
        self.db_config = self._get_db_config()
    
    def _detect_environment(self):
        """Detecta automáticamente el entorno actual"""
        
        # 0. DETECCIÓN PRIORITARIA DE STREAMLIT CLOUD (antes que todo)
        try:
            import streamlit as st
            # Detectar si estamos en Streamlit Cloud por la URL o contexto
            if hasattr(st, '_get_script_run_ctx'):
                ctx = st._get_script_run_ctx()
                if ctx and hasattr(ctx, 'session_info'):
                    # Si estamos en un contexto de Streamlit con sesión, probablemente es Cloud
                    print("[KRONOS] Streamlit Cloud detectado por contexto de sesión")
                    return 'production'
        except:
            pass
        
        # 1. DETECCIÓN AGRESIVA DE PRODUCCIÓN (variables de entorno)
        production_indicators = [
            'STREAMLIT_SHARING_MODE',    # Streamlit Cloud legacy
            'STREAMLIT_CLOUD',           # Streamlit Cloud nueva versión
            'STREAMLIT_SERVER_PORT',     # Streamlit en servidor
            'STREAMLIT_BROWSER_GATHER_USAGE_STATS',  # Streamlit Cloud específico
            'DYNO',                      # Heroku
            'RENDER',                    # Render
            'VERCEL',                    # Vercel
            'RAILWAY_ENVIRONMENT',       # Railway
            'NETLIFY',                   # Netlify
            'CF_PAGES',                  # Cloudflare Pages
            'GITHUB_ACTIONS',            # GitHub Actions
            'CI',                        # Continuous Integration
            'DEPLOYMENT_ENV',            # Variable genérica de despliegue
            'NODE_ENV'                   # Node environment
        ]
        
        for indicator in production_indicators:
            value = os.getenv(indicator)
            if value:
                print(f"[KRONOS] Producción detectada por: {indicator}={value}")
                return 'production'
        
        # 2. Verificar variable de entorno específica (solo si no hay indicadores de producción)
        if os.getenv('KRONOS_ENV'):
            env = os.getenv('KRONOS_ENV').lower()
            if env in ['development', 'production', 'testing']:
                # Si KRONOS_ENV dice development y estamos en localhost, respetarlo
                if env == 'development' and self._is_localhost():
                    print("[KRONOS] KRONOS_ENV=development respetado en localhost")
                    return env
                # Si KRONOS_ENV dice development pero estamos en servidor remoto, forzar producción
                elif env == 'development' and not self._is_localhost():
                    print("[KRONOS] KRONOS_ENV=development ignorado en servidor remoto, forzando producción")
                    return 'production'
                return env
        
        # 3. Verificar hostname de servidor (reforzado)
        try:
            import socket
            hostname = socket.gethostname().lower()
            
            # Hostnames típicos de servidores en la nube
            cloud_patterns = [
                'streamlit', 'heroku', 'render', 'vercel', 'railway',
                'netlify', 'aws', 'gcp', 'azure', 'digitalocean',
                'server', 'prod', 'production', 'cloud'
            ]
            
            for pattern in cloud_patterns:
                if pattern in hostname:
                    print(f"[KRONOS] Producción detectada por hostname: {hostname}")
                    return 'production'
        except:
            pass
        
        # 4. DETECCIÓN POR URL O DOMINIO (nuevo método)
        try:
            # Si estamos ejecutando en un servidor web (no localhost)
            import socket
            ip = socket.gethostbyname(socket.gethostname())
            if not ip.startswith('127.') and not ip.startswith('192.168.') and not ip.startswith('10.'):
                print(f"[KRONOS] Producción detectada por IP no local: {ip}")
                return 'production'
        except:
            pass
        
        # 5. Si no estamos en entorno local, SIEMPRE es producción (excepto si es localhost)
        if not self._is_local_environment() and not self._is_localhost():
            print("[KRONOS] No es entorno local ni localhost, forzando producción")
            return 'production'
        
        # 6. Verificar si existe un archivo .env (solo como última opción)
        current_dir = Path(__file__).parent
        if (current_dir / '.env').exists():
            try:
                with open(current_dir / '.env', 'r') as f:
                    content = f.read()
                    if 'KRONOS_ENV=development' in content and self._is_local_environment():
                        return 'development'
            except:
                pass
        
        # 7. FALLBACK FINAL: Si llegamos aquí y no es local, ES PRODUCCIÓN
        print("[KRONOS] Fallback: Asumiendo producción por exclusión")
        return 'production'
    
    def _is_localhost(self):
        """Detecta si estamos ejecutando específicamente en localhost"""
        try:
            import socket
            
            # Verificar si estamos ejecutando en localhost/127.0.0.1
            try:
                # Intentar conectar a localhost para verificar que estamos ejecutando localmente
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('127.0.0.1', 8501))  # Puerto típico de Streamlit
                sock.close()
                if result == 0:
                    print("[KRONOS] Localhost detectado - Streamlit ejecutándose en 127.0.0.1:8501")
                    return True
            except:
                pass
            
            # Verificar hostname localhost
            hostname = socket.gethostname().lower()
            if 'localhost' in hostname or hostname == 'localhost':
                print(f"[KRONOS] Localhost detectado por hostname: {hostname}")
                return True
            
            # Verificar IP local
            try:
                ip = socket.gethostbyname(hostname)
                if ip.startswith('127.'):
                    print(f"[KRONOS] Localhost detectado por IP: {ip}")
                    return True
            except:
                pass
            
            return False
            
        except Exception as e:
            print(f"[KRONOS] Error detectando localhost: {e}")
            return False
    
    def _is_local_environment(self):
        """Detecta si estamos ejecutando en un entorno local"""
        try:
            import socket
            hostname = socket.gethostname().lower()
            
            # Indicadores de entorno local
            local_indicators = [
                'localhost' in hostname,
                hostname.startswith('desktop-'),
                hostname.startswith('laptop-'),
                hostname.startswith('pc-'),
                'local' in hostname,
                '127.0.0.1' in hostname
            ]
            
            # Verificar si estamos en localhost/127.0.0.1
            try:
                ip = socket.gethostbyname(hostname)
                if ip.startswith('127.') or ip.startswith('192.168.') or ip.startswith('10.'):
                    local_indicators.append(True)
            except:
                pass
            
            # Verificar rutas que indican entorno no local
            current_path = str(Path(__file__).parent).lower()
            non_local_paths = [
                'onedrive',  # Tu caso específico
                'sharepoint',
                'dropbox',
                'googledrive',
                '/tmp/',
                '/var/',
                'c:\\windows\\temp'
            ]
            
            for path in non_local_paths:
                if path in current_path:
                    print(f"[KRONOS] Entorno no local detectado por ruta: {current_path}")
                    return False
            
            is_local = any(local_indicators)
            print(f"[KRONOS] Detección local: {is_local} (hostname: {hostname})")
            return is_local
            
        except Exception as e:
            print(f"[KRONOS] Error detectando entorno local: {e}")
            return False
    
    def _get_db_config(self):
        """Obtiene la configuración de base de datos según el entorno"""
        
        configs = {
            'development': {
                'database_name': 'client_calendar_dev.db',
                'description': 'Base de datos de desarrollo',
                'backup_enabled': True,
                'debug_mode': True
            },
            'production': {
                'database_name': 'client_calendar.db',
                'description': 'Base de datos de producción',
                'backup_enabled': True,
                'debug_mode': False
            },
            'testing': {
                'database_name': 'client_calendar_test.db',
                'description': 'Base de datos de pruebas',
                'backup_enabled': False,
                'debug_mode': True
            }
        }
        
        return configs.get(self.environment, configs['development'])
    
    def get_database_path(self):
        """Retorna la ruta completa de la base de datos"""
        db_name = self.db_config['database_name']
        
        # En producción (Streamlit Cloud), usar ruta absoluta basada en el directorio del proyecto
        if self.is_production():
            # Obtener el directorio donde está este archivo config.py
            project_dir = Path(__file__).parent.absolute()
            db_path = project_dir / db_name
            print(f"[KRONOS] Ruta de BD en producción: {db_path}")
            return str(db_path)
        else:
            # En desarrollo, usar ruta relativa como antes
            print(f"[KRONOS] Ruta de BD en desarrollo: {db_name}")
            return db_name
    
    def get_db_connection(self):
        """Obtiene una conexión a la base de datos según el entorno"""
        import sqlite3
        db_path = self.get_database_path()
        return sqlite3.connect(db_path)
    
    def get_environment(self):
        """Retorna el entorno actual"""
        return self.environment
    
    def is_development(self):
        """Verifica si estamos en desarrollo"""
        return self.environment == 'development'
    
    def is_production(self):
        """Verifica si estamos en producción"""
        return self.environment == 'production'
    
    def get_config_info(self):
        """Retorna información de configuración para debugging"""
        return {
            'environment': self.environment,
            'database': self.db_config['database_name'],
            'description': self.db_config['description'],
            'debug_mode': self.db_config['debug_mode'],
            'backup_enabled': self.db_config['backup_enabled']
        }
    
    def show_environment_info(self):
        """Muestra información del entorno en Streamlit (SOLO en desarrollo local)"""
        
        # VERIFICACIÓN TRIPLE: 
        # 1. Debe ser development
        # 2. Debe ser entorno local  
        # 3. NO debe estar en Streamlit Cloud
        
        # Verificación específica de Streamlit Cloud
        try:
            import streamlit as st
            # Si podemos acceder al contexto de Streamlit, probablemente estamos en Cloud
            if hasattr(st, '_get_script_run_ctx'):
                ctx = st._get_script_run_ctx()
                if ctx:
                    print("[KRONOS] Contexto Streamlit detectado - Panel bloqueado")
                    return  # SALIR INMEDIATAMENTE - NO MOSTRAR PANEL
        except:
            pass
        
        # Verificación por variables de entorno de Streamlit Cloud
        streamlit_cloud_vars = [
            'STREAMLIT_SHARING_MODE',
            'STREAMLIT_CLOUD', 
            'STREAMLIT_SERVER_PORT',
            'STREAMLIT_BROWSER_GATHER_USAGE_STATS'
        ]
        
        for var in streamlit_cloud_vars:
            if os.getenv(var):
                print(f"[KRONOS] Variable Streamlit Cloud detectada: {var} - Panel bloqueado")
                return  # SALIR INMEDIATAMENTE
        
        # CONDICIÓN ESTRICTA: Solo mostrar en desarrollo Y (entorno local O localhost)
        if self.is_development() and (self._is_local_environment() or self._is_localhost()):
            print("[KRONOS] Mostrando panel de desarrollo (entorno local o localhost confirmado)")
            info = self.get_config_info()
            
            with st.expander("🔧 Información del Entorno (Solo Desarrollo Local)", expanded=False):
                st.json(info)
                
                # Mostrar variables de entorno relevantes
                env_vars = {}
                relevant_vars = [
                    'KRONOS_ENV', 'STREAMLIT_SHARING_MODE', 'STREAMLIT_CLOUD',
                    'DYNO', 'RENDER', 'VERCEL', 'RAILWAY_ENVIRONMENT'
                ]
                
                for var in relevant_vars:
                    value = os.getenv(var)
                    if value:
                        env_vars[var] = value
                
                if env_vars:
                    st.write("**Variables de entorno detectadas:**")
                    st.json(env_vars)
                
                # Botones para cambiar entorno (solo en desarrollo local)
                st.warning("⚠️ Estos botones solo funcionan en desarrollo local")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("🔧 Usar DEV", help="Cambiar a base de datos de desarrollo"):
                        os.environ['KRONOS_ENV'] = 'development'
                        st.rerun()
                
                with col2:
                    if st.button("🚀 Usar PRD", help="Cambiar a base de datos de producción"):
                        os.environ['KRONOS_ENV'] = 'production'
                        st.rerun()
                
                with col3:
                    if st.button("🧪 Usar TEST", help="Cambiar a base de datos de pruebas"):
                        os.environ['KRONOS_ENV'] = 'testing'
                        st.rerun()
        else:
            # Log para debugging (no visible al usuario)
            print(f"[KRONOS] Panel bloqueado - Development: {self.is_development()}, Local: {self._is_local_environment()}, Localhost: {self._is_localhost()}")

# Instancia global de configuración
db_config = DatabaseConfig()

def get_db_config():
    """Función helper para obtener la configuración de BD"""
    return db_config

def get_database_path():
    """Función helper para obtener la ruta de la BD"""
    return db_config.get_database_path()

def is_development():
    """Función helper para verificar si estamos en desarrollo"""
    return db_config.is_development()

def is_production():
    """Función helper para verificar si estamos en producción"""
    return db_config.is_production()
