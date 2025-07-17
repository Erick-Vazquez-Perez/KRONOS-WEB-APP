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
        
        # 1. Verificar variable de entorno específica
        if os.getenv('KRONOS_ENV'):
            return os.getenv('KRONOS_ENV').lower()
        
        # 2. Verificar si estamos en Streamlit Cloud (producción)
        if os.getenv('STREAMLIT_SHARING_MODE') or os.getenv('STREAMLIT_CLOUD'):
            return 'production'
        
        # 3. Verificar otros indicadores de producción
        production_indicators = [
            'DYNO',  # Heroku
            'RENDER',  # Render
            'VERCEL',  # Vercel
            'RAILWAY_ENVIRONMENT',  # Railway
        ]
        
        for indicator in production_indicators:
            if os.getenv(indicator):
                return 'production'
        
        # 4. Verificar si existe un archivo .env o estamos en desarrollo local
        current_dir = Path(__file__).parent
        if (current_dir / '.env').exists() or (current_dir / 'requirements-dev.txt').exists():
            return 'development'
        
        # 5. Verificar si estamos ejecutando desde localhost
        try:
            import socket
            hostname = socket.gethostname()
            if 'localhost' in hostname.lower() or hostname.startswith('DESKTOP-') or hostname.startswith('LAPTOP-'):
                return 'development'
        except:
            pass
        
        # 6. Por defecto, usar development en local
        return 'development'
    
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
        """Muestra información del entorno en Streamlit (solo en desarrollo)"""
        if self.is_development():
            info = self.get_config_info()
            
            with st.expander("🔧 Información del Entorno (Solo Desarrollo)", expanded=False):
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
                
                # Botón para cambiar entorno manualmente (solo en desarrollo)
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
