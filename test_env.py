#!/usr/bin/env python3
"""
Script para verificar la detección de entorno de KRONOS 2.0
"""

import sys
import os
from pathlib import Path

# Agregar el directorio actual al path para importar config
sys.path.append(str(Path(__file__).parent))

from config import get_db_config, is_read_only_mode, is_production

def test_environment_detection():
    """Prueba la detección de entorno"""
    print("=" * 60)
    print("KRONOS 2.0 - Test de Detección de Entorno")
    print("=" * 60)
    
    # Obtener configuración
    config = get_db_config()
    
    print(f"🔍 Entorno detectado: {config.environment}")
    print(f"📁 Base de datos: {config.db_config['database_name']}")
    print(f"📝 Descripción: {config.db_config['description']}")
    print(f"🔧 Modo debug: {config.db_config['debug_mode']}")
    print(f"🔐 Modo solo lectura: {is_read_only_mode()}")
    print(f"🏭 Es producción: {is_production()}")
    
    print("\n" + "=" * 60)
    print("Variables de entorno relevantes:")
    print("=" * 60)
    
    env_vars = [
        'KRONOS_ENV',
        'LOCAL_DEVELOPMENT',
        'STREAMLIT_SHARING_MODE',
        'STREAMLIT_CLOUD',
        'STREAMLIT_SERVER_PORT',
        'CI',
        'DEPLOYMENT_ENV'
    ]
    
    for var in env_vars:
        value = os.getenv(var, 'No definida')
        print(f"{var}: {value}")
    
    print("\n" + "=" * 60)
    print("Información del sistema:")
    print("=" * 60)
    
    import socket
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        print(f"Hostname: {hostname}")
        print(f"IP: {ip}")
    except Exception as e:
        print(f"Error obteniendo info de red: {e}")
    
    print(f"Ruta actual: {Path(__file__).parent}")
    print(f"Python: {sys.version}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_environment_detection()
