#!/usr/bin/env python3
"""
Script de prueba para verificar la conexión con SQLiteCloud
"""

import os
import sys
from pathlib import Path

# Agregar el directorio actual al path para importar config
sys.path.append(str(Path(__file__).parent))

from config import get_db_config, load_env_file

def test_connection():
    """Prueba la conexión a la base de datos"""
    
    print("🔧 KRONOS 2.0 - Test de Conexión SQLiteCloud")
    print("=" * 50)
    
    # Cargar variables de entorno
    load_env_file()
    
    # Obtener configuración
    config = get_db_config()
    
    print(f"Entorno detectado: {config.get_environment()}")
    print(f"Tipo de BD: {config.db_config.get('type', 'local')}")
    print(f"Descripción: {config.db_config['description']}")
    
    # Verificar variable de entorno
    connection_string = os.getenv('SQLITECLOUD_CONNECTION_STRING')
    if connection_string:
        print(f"✅ Variable SQLITECLOUD_CONNECTION_STRING encontrada")
        # Mostrar solo una parte por seguridad
        masked = connection_string[:30] + "..." + connection_string[-20:]
        print(f"   Conexión: {masked}")
    else:
        print("❌ Variable SQLITECLOUD_CONNECTION_STRING NO encontrada")
        return False
    
    print("\n🔌 Probando conexión...")
    
    try:
        # Intentar conectar
        conn = config.get_db_connection()
        print("✅ Conexión establecida exitosamente!")
        
        # Probar una consulta simple
        print("\n🔍 Probando consulta...")
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"✅ Consulta exitosa! Tablas encontradas: {len(tables)}")
        for table in tables:
            print(f"   - {table[0]}")
        
        # Cerrar conexión
        conn.close()
        print("\n🎉 ¡Prueba de conexión completada exitosamente!")
        return True
        
    except Exception as e:
        print(f"❌ Error en la conexión: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
