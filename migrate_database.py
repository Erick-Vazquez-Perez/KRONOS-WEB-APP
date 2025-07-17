"""
Script de migración de datos entre bases de datos de Kronos
Permite copiar datos de PRD a DEV o viceversa
"""

import sqlite3
import os
from datetime import datetime
import shutil

def backup_database(source_db, backup_path=None):
    """Crear backup de una base de datos"""
    if backup_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{source_db}.backup_{timestamp}"
    
    try:
        shutil.copy2(source_db, backup_path)
        print(f"✅ Backup creado: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ Error creando backup: {e}")
        return None

def get_tables_and_data(db_path):
    """Obtener todas las tablas y sus datos de una base de datos"""
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada: {db_path}")
        return None
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Obtener lista de tablas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    # Obtener esquema y datos de cada tabla
    db_data = {}
    
    for table in tables:
        # Obtener esquema
        cursor.execute(f"SELECT sql FROM sqlite_master WHERE name='{table}'")
        schema = cursor.fetchone()[0]
        
        # Obtener datos
        cursor.execute(f"SELECT * FROM {table}")
        data = cursor.fetchall()
        
        # Obtener nombres de columnas
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in cursor.fetchall()]
        
        db_data[table] = {
            'schema': schema,
            'columns': columns,
            'data': data
        }
        
        print(f"📋 Tabla '{table}': {len(data)} registros")
    
    conn.close()
    return db_data

def copy_data_to_database(target_db, source_data, mode='replace'):
    """Copiar datos a una base de datos destino"""
    
    # Crear backup del destino si existe
    if os.path.exists(target_db):
        backup_path = backup_database(target_db)
        if not backup_path:
            print("❌ No se pudo crear backup del destino. Cancelando operación.")
            return False
    
    conn = sqlite3.connect(target_db)
    cursor = conn.cursor()
    
    try:
        for table_name, table_data in source_data.items():
            print(f"📦 Procesando tabla: {table_name}")
            
            # Modificar el esquema para usar IF NOT EXISTS
            schema_sql = table_data['schema']
            if 'CREATE TABLE' in schema_sql and 'IF NOT EXISTS' not in schema_sql:
                schema_sql = schema_sql.replace('CREATE TABLE', 'CREATE TABLE IF NOT EXISTS')
            
            # Crear tabla si no existe (con IF NOT EXISTS añadido)
            try:
                cursor.execute(schema_sql)
                print(f"✅ Tabla {table_name} preparada")
            except sqlite3.Error as e:
                print(f"⚠️ Advertencia creando tabla {table_name}: {e}")
                # Continuar - la tabla probablemente ya existe
            
            if mode == 'replace':
                # Limpiar tabla existente
                cursor.execute(f"DELETE FROM {table_name}")
                print(f"🗑️ Datos existentes eliminados de {table_name}")
            
            # Insertar datos
            if table_data['data']:
                placeholders = ','.join(['?' for _ in table_data['columns']])
                insert_sql = f"INSERT OR REPLACE INTO {table_name} VALUES ({placeholders})"
                
                try:
                    cursor.executemany(insert_sql, table_data['data'])
                    print(f"✅ {len(table_data['data'])} registros insertados en {table_name}")
                except sqlite3.Error as e:
                    print(f"❌ Error insertando en {table_name}: {e}")
                    # Continuar con la siguiente tabla
            
        conn.commit()
        print("✅ Migración completada exitosamente")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error durante la migración: {e}")
        return False
    
    finally:
        conn.close()

def migrate_prd_to_dev():
    """Migrar datos de producción a desarrollo"""
    print("🔄 Iniciando migración PRD → DEV")
    print("=" * 50)
    
    prd_db = "client_calendar.db"
    dev_db = "client_calendar_dev.db"
    
    # Verificar que existe PRD
    if not os.path.exists(prd_db):
        print(f"❌ Base de datos de producción no encontrada: {prd_db}")
        return False
    
    # Obtener datos de PRD
    print("📖 Leyendo datos de producción...")
    prd_data = get_tables_and_data(prd_db)
    
    if not prd_data:
        print("❌ No se pudieron leer los datos de producción")
        return False
    
    # Copiar a DEV
    print(f"\n📝 Copiando datos a desarrollo ({dev_db})...")
    success = copy_data_to_database(dev_db, prd_data, mode='replace')
    
    if success:
        print(f"\n✅ Migración PRD → DEV completada")
        print(f"🔧 Ahora puedes trabajar en desarrollo sin afectar producción")
        
        # Mostrar estadísticas finales
        print("\n📊 Estadísticas de la migración:")
        for table_name, table_data in prd_data.items():
            print(f"   • {table_name}: {len(table_data['data'])} registros")
    
    return success

def migrate_dev_to_prd():
    """Migrar datos de desarrollo a producción (¡CUIDADO!)"""
    print("⚠️  MIGRACIÓN DEV → PRD")
    print("=" * 50)
    print("🚨 ADVERTENCIA: Esta operación sobrescribirá la base de datos de PRODUCCIÓN")
    print("🚨 Asegúrate de que realmente quieres hacer esto")
    
    confirmation = input("\n¿Estás seguro? Escribe 'SI ESTOY SEGURO' para continuar: ")
    
    if confirmation != "SI ESTOY SEGURO":
        print("❌ Operación cancelada por seguridad")
        return False
    
    dev_db = "client_calendar_dev.db"
    prd_db = "client_calendar.db"
    
    # Verificar que existe DEV
    if not os.path.exists(dev_db):
        print(f"❌ Base de datos de desarrollo no encontrada: {dev_db}")
        return False
    
    # Crear backup adicional de PRD
    if os.path.exists(prd_db):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{prd_db}.BACKUP_BEFORE_DEV_MIGRATION_{timestamp}"
        backup_database(prd_db, backup_path)
        print(f"🛡️ Backup de seguridad creado: {backup_path}")
    
    # Obtener datos de DEV
    print("📖 Leyendo datos de desarrollo...")
    dev_data = get_tables_and_data(dev_db)
    
    if not dev_data:
        print("❌ No se pudieron leer los datos de desarrollo")
        return False
    
    # Copiar a PRD
    print(f"\n📝 Copiando datos a producción ({prd_db})...")
    success = copy_data_to_database(prd_db, dev_data, mode='replace')
    
    if success:
        print(f"\n✅ Migración DEV → PRD completada")
        print(f"🚀 Los datos de desarrollo están ahora en producción")
    
    return success

def show_database_info():
    """Mostrar información de ambas bases de datos"""
    print("📊 INFORMACIÓN DE BASES DE DATOS")
    print("=" * 50)
    
    databases = [
        ("Producción", "client_calendar.db"),
        ("Desarrollo", "client_calendar_dev.db"),
        ("Pruebas", "client_calendar_test.db")
    ]
    
    for env_name, db_path in databases:
        print(f"\n🗃️ {env_name} ({db_path}):")
        
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Obtener tablas
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                print(f"   ✅ Existe - {len(tables)} tablas")
                
                # Contar registros en tablas principales
                important_tables = ['clients', 'client_activities', 'calculated_dates', 'frequency_templates']
                
                for table in important_tables:
                    if table in tables:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        print(f"      • {table}: {count} registros")
                
                # Mostrar última modificación
                stat = os.stat(db_path)
                mod_time = datetime.fromtimestamp(stat.st_mtime)
                print(f"      • Última modificación: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                conn.close()
                
            except Exception as e:
                print(f"   ❌ Error leyendo BD: {e}")
        else:
            print(f"   ❌ No existe")

def main():
    """Función principal del script de migración"""
    print("🔄 SCRIPT DE MIGRACIÓN DE DATOS - KRONOS")
    print("=" * 60)
    
    while True:
        print("\n📋 Opciones disponibles:")
        print("1. 📊 Mostrar información de bases de datos")
        print("2. 🔄 Migrar PRD → DEV (seguro)")
        print("3. ⚠️  Migrar DEV → PRD (¡cuidado!)")
        print("4. 🛡️ Crear backup manual")
        print("5. ❌ Salir")
        
        choice = input("\n🎯 Selecciona una opción (1-5): ").strip()
        
        if choice == "1":
            show_database_info()
        
        elif choice == "2":
            migrate_prd_to_dev()
        
        elif choice == "3":
            migrate_dev_to_prd()
        
        elif choice == "4":
            db_path = input("📁 Ruta de la base de datos a respaldar: ").strip()
            if os.path.exists(db_path):
                backup_database(db_path)
            else:
                print(f"❌ Archivo no encontrado: {db_path}")
        
        elif choice == "5":
            print("👋 ¡Hasta luego!")
            break
        
        else:
            print("❌ Opción no válida")
        
        input("\n⏸️  Presiona Enter para continuar...")

if __name__ == "__main__":
    main()
