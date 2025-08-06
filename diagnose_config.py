"""
Script de diagnóstico para verificar la configuración de SQLiteCloud en producción
"""

import os
import sys
from pathlib import Path

# Agregar el directorio actual al path
sys.path.append(str(Path(__file__).parent))

def diagnose_config():
    """Diagnóstica la configuración de la aplicación"""
    
    print("🔍 KRONOS 2.0 - Diagnóstico de Configuración")
    print("=" * 60)
    
    # 1. Verificar variables de entorno
    print("\n📋 Variables de Entorno:")
    env_vars = [
        'KRONOS_ENV',
        'SQLITECLOUD_CONNECTION_STRING', 
        'LOCAL_DEVELOPMENT',
        'STREAMLIT_SHARING_MODE',
        'STREAMLIT_CLOUD',
        'DEPLOYMENT_ENV'
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            if 'CONNECTION_STRING' in var:
                # Enmascarar la cadena de conexión
                masked = value[:30] + "..." + value[-20:] if len(value) > 50 else value
                print(f"  ✅ {var}: {masked}")
            else:
                print(f"  ✅ {var}: {value}")
        else:
            print(f"  ❌ {var}: No definida")
    
    # 2. Verificar si estamos en Streamlit
    print("\n🌐 Entorno Streamlit:")
    try:
        import streamlit as st
        print("  ✅ Streamlit importado correctamente")
        
        # Verificar secrets en Streamlit
        try:
            if hasattr(st, 'secrets'):
                connection_string = st.secrets.get("SQLITECLOUD_CONNECTION_STRING")
                if connection_string:
                    masked = connection_string[:30] + "..." + connection_string[-20:]
                    print(f"  ✅ st.secrets.SQLITECLOUD_CONNECTION_STRING: {masked}")
                else:
                    print("  ❌ st.secrets.SQLITECLOUD_CONNECTION_STRING: No encontrada")
            else:
                print("  ⚠️  st.secrets no disponible (normal en desarrollo local)")
        except Exception as e:
            print(f"  ⚠️  Error leyendo secrets: {e}")
            
    except ImportError:
        print("  ❌ Streamlit no disponible")
    
    # 3. Verificar configuración de KRONOS
    print("\n⚙️  Configuración KRONOS:")
    try:
        from config import get_db_config, load_env_file
        
        # Cargar .env
        load_env_file()
        print("  ✅ Archivo .env cargado")
        
        # Obtener configuración
        config = get_db_config()
        print(f"  ✅ Entorno detectado: {config.get_environment()}")
        print(f"  ✅ Tipo de BD: {config.db_config.get('type', 'local')}")
        print(f"  ✅ Descripción: {config.db_config['description']}")
        
        # Verificar cadena de conexión
        if config.db_config['type'] == 'cloud':
            connection_string = config.db_config.get('connection_string')
            if connection_string and connection_string != 'None':
                masked = connection_string[:30] + "..." + connection_string[-20:]
                print(f"  ✅ Cadena de conexión: {masked}")
            else:
                print("  ❌ Cadena de conexión: No configurada")
        
    except Exception as e:
        print(f"  ❌ Error en configuración KRONOS: {e}")
    
    # 4. Probar conexión SQLiteCloud
    print("\n🔌 Prueba de Conexión:")
    try:
        # Importar sqlitecloud
        import sqlitecloud
        print("  ✅ Módulo sqlitecloud importado")
        
        # Obtener cadena de conexión
        connection_string = None
        
        # Primero intentar desde variables de entorno
        connection_string = os.getenv('SQLITECLOUD_CONNECTION_STRING')
        
        # Si no está, intentar desde Streamlit secrets
        if not connection_string:
            try:
                import streamlit as st
                connection_string = st.secrets.get("SQLITECLOUD_CONNECTION_STRING")
            except:
                pass
        
        if connection_string and connection_string != 'None':
            print("  ✅ Cadena de conexión obtenida")
            
            # Intentar conectar
            try:
                conn = sqlitecloud.connect(connection_string)
                print("  ✅ Conexión SQLiteCloud exitosa!")
                
                # Probar una consulta simple
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                print(f"  ✅ Tablas encontradas: {len(tables)}")
                
                conn.close()
                
            except Exception as e:
                print(f"  ❌ Error conectando: {e}")
        else:
            print("  ❌ No se pudo obtener la cadena de conexión")
            
    except ImportError:
        print("  ❌ Módulo sqlitecloud no disponible")
    except Exception as e:
        print(f"  ❌ Error en prueba de conexión: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Diagnóstico completado")

if __name__ == "__main__":
    diagnose_config()
