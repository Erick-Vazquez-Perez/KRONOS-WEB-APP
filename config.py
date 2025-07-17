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
        
        # 1. Verificar variable de entorno específica (mayor prioridad)
        if os.getenv('KRONOS_ENV'):
            env = os.getenv('KRONOS_ENV').lower()
            if env in ['development', 'production', 'testing']:
                return env
        
        # 2. DETECCIÓN ROBUSTA DE PRODUCCIÓN (nuevas variables)
        production_indicators = [
            'STREAMLIT_SHARING_MODE',  # Streamlit Cloud
            'STREAMLIT_CLOUD',         # Streamlit Cloud nueva versión
            'STREAMLIT_SERVER_PORT',   # Streamlit en servidor
            'DYNO',                    # Heroku
            'RENDER',                  # Render
            'VERCEL',                  # Vercel
            'RAILWAY_ENVIRONMENT',     # Railway
            'NETLIFY',                 # Netlify
            'CF_PAGES',                # Cloudflare Pages
            'GITHUB_ACTIONS',          # GitHub Actions
            'CI',                      # Continuous Integration
            'DEPLOYMENT_ENV'           # Variable genérica de despliegue
        ]
        
        for indicator in production_indicators:
            if os.getenv(indicator):
                print(f"[KRONOS] Producción detectada por: {indicator}={os.getenv(indicator)}")
                return 'production'
        
        # 3. Verificar hostname de servidor (nuevo)
        try:
            import socket
            hostname = socket.gethostname().lower()
            
            # Hostnames típicos de servidores en la nube
            cloud_patterns = [
                'streamlit', 'heroku', 'render', 'vercel', 'railway',
                'netlify', 'aws', 'gcp', 'azure', 'digitalocean',
                'server', 'prod', 'production'
            ]
            
            for pattern in cloud_patterns:
                if pattern in hostname:
                    print(f"[KRONOS] Producción detectada por hostname: {hostname}")
                    return 'production'
        except:
            pass
        
        # 4. Verificar si existe un archivo .env o estamos en desarrollo local
        current_dir = Path(__file__).parent
        if (current_dir / '.env').exists():
            # Si existe .env, leer la configuración
            try:
                with open(current_dir / '.env', 'r') as f:
                    content = f.read()
                    if 'KRONOS_ENV=development' in content:
                        return 'development'
                    elif 'KRONOS_ENV=production' in content:
                        # Solo usar si estamos realmente en local
                        if self._is_local_environment():
                            return 'production'
                        else:
                            print("[KRONOS] Ignorando .env en servidor, usando detección automática")
                            return 'production'
            except:
                pass
        
        # 5. Verificar si estamos ejecutando desde localhost
        if self._is_local_environment():
            return 'development'
        
        # 6. Por defecto en servidores, usar producción
        print("[KRONOS] Entorno no detectado claramente, asumiendo producción en servidor")
        return 'production'
    
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
            
            return any(local_indicators)
        except:
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
        return self.db_config['database_name']
    
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
        
        # CONDICIÓN ESTRICTA: Solo mostrar en desarrollo Y entorno local
        if self.is_development() and self._is_local_environment():
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
        
        # En producción o servidor, no mostrar nada (silencioso)
        elif not self._is_local_environment():
            # Opcional: Log interno para debugging del servidor (no visible al usuario)
            pass

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
