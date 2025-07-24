import sqlite3
import pandas as pd
import json
from datetime import datetime, date
from config import get_database_path, get_db_config

def get_db_connection():
    """Obtiene una conexión a la base de datos según el entorno"""
    db_path = get_database_path()
    return sqlite3.connect(db_path)

def get_sap_calendar_mapping():
    """Retorna el mapeo de frecuencias a códigos de calendario SAP"""
    return {
        "2do Lunes del mes": "16",
        "1er y 3er Lunes del mes": "M7", 
        "1er Viernes del mes": "17",
        "1er y 3er Jueves del mes": "18",
        "3er Lunes del mes": "19",
        "2do Martes del mes": "20",
        "2do y 4to Miércoles del mes": "ME",
        "1er y 3er Miércoles del mes": "MD",
        "3er Martes del mes": "21",
        "2do y 4to Jueves del mes": "22",
        "1er Miércoles del mes": "23",
        "2do y 4to Lunes del mes": "24",
        "Martes de cada semana": "M9",
        "3er Miércoles del mes": "25",
        "3er Jueves del mes": "26",
        "4to Jueves del mes": "27",
        "2do Miércoles del mes": "28",
        "1er Martes del mes": "29",
        "Lunes de cada semana": "M8",
        "2do Viernes del mes": "30",
        "1er y 3er Martes del mes": "MB",
        "4to Viernes del mes": "31",
        "1er 2do y 3er Lunes del mes": "32",
        "3er Viernes del mes": "33",
        "1er y 2do Lunes del mes": "34",
        "Miércoles de cada semana": "M3",
        "Jueves de cada semana": "M4",
        "1er Lunes del mes": "35"
    }

def update_frequency_sap_codes():
    """Actualiza los códigos SAP de las frecuencias existentes basándose en el mapeo"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    mapping = get_sap_calendar_mapping()
    
    try:
        for frequency_name, sap_code in mapping.items():
            cursor.execute('''
                UPDATE frequency_templates 
                SET calendario_sap_code = ?
                WHERE name = ?
            ''', (sap_code, frequency_name))
        
        conn.commit()
        print("Códigos SAP actualizados para las frecuencias existentes")
        
    except Exception as e:
        print(f"Error actualizando códigos SAP: {e}")
        conn.rollback()
    finally:
        conn.close()

def auto_update_client_calendario_sap(client_id, activity_name, frequency_template_id):
    """Actualiza automáticamente el calendario SAP del cliente cuando se asigna la actividad Albaranado"""
    if activity_name != "Albaranado":
        return
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Obtener el código SAP de la frecuencia seleccionada
        cursor.execute('''
            SELECT calendario_sap_code FROM frequency_templates 
            WHERE id = ?
        ''', (frequency_template_id,))
        
        result = cursor.fetchone()
        if result:
            sap_code = result[0] or "0"
            
            # Actualizar el campo calendario_sap del cliente
            cursor.execute('''
                UPDATE clients 
                SET calendario_sap = ?
                WHERE id = ?
            ''', (sap_code, client_id))
            
            conn.commit()
            print(f"Calendario SAP del cliente {client_id} actualizado automáticamente a: {sap_code}")
            
    except Exception as e:
        print(f"Error actualizando calendario SAP automáticamente: {e}")
        conn.rollback()
    finally:
        conn.close()

def init_database():
    """Inicializa la base de datos y crea las tablas necesarias"""
    db_path = get_database_path()
    config = get_db_config()
    
    print(f"[KRONOS] Inicializando base de datos: {db_path}")
    print(f"[KRONOS] Entorno: {config.get_environment()}")
    print(f"[KRONOS] Descripción: {config.db_config['description']}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tabla de clientes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            codigo_ag TEXT,
            codigo_we TEXT,
            csr TEXT,
            vendedor TEXT,
            calendario_sap TEXT,
            tipo_cliente TEXT DEFAULT 'Otro',
            region TEXT DEFAULT 'Otro',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Verificar si los campos tipo_cliente y region existen, si no, agregarlos
    cursor.execute("PRAGMA table_info(clients)")
    columns_info = cursor.fetchall()
    column_names = [col[1] for col in columns_info]
    
    if 'tipo_cliente' not in column_names:
        cursor.execute('ALTER TABLE clients ADD COLUMN tipo_cliente TEXT DEFAULT "Otro"')
        print("Campo tipo_cliente agregado a clients")
        
    if 'region' not in column_names:
        cursor.execute('ALTER TABLE clients ADD COLUMN region TEXT DEFAULT "Otro"')
        print("Campo region agregado a clients")
    
    # Tabla de frecuencias disponibles
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS frequency_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            frequency_type TEXT NOT NULL,
            frequency_config TEXT,
            description TEXT,
            calendario_sap_code TEXT DEFAULT '0'
        )
    ''')
    
    # Verificar si el campo calendario_sap_code existe, si no, agregarlo
    cursor.execute("PRAGMA table_info(frequency_templates)")
    columns_info = cursor.fetchall()
    column_names = [col[1] for col in columns_info]
    
    if 'calendario_sap_code' not in column_names:
        cursor.execute('ALTER TABLE frequency_templates ADD COLUMN calendario_sap_code TEXT DEFAULT "0"')
        print("Campo calendario_sap_code agregado a frequency_templates")
    
    # Tabla de actividades por cliente
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS client_activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            activity_name TEXT NOT NULL,
            frequency_template_id INTEGER,
            FOREIGN KEY (client_id) REFERENCES clients (id),
            FOREIGN KEY (frequency_template_id) REFERENCES frequency_templates (id)
        )
    ''')
    
    # Verificar si la tabla calculated_dates existe y su estructura
    cursor.execute("PRAGMA table_info(calculated_dates)")
    columns_info = cursor.fetchall()
    column_names = [col[1] for col in columns_info]
    
    # Si la tabla no existe o no tiene la estructura correcta, recrearla
    if not columns_info or 'date_position' not in column_names:
        # Hacer backup de datos existentes si los hay
        backup_data = []
        try:
            cursor.execute("SELECT * FROM calculated_dates")
            backup_data = cursor.fetchall()
            cursor.execute("DROP TABLE IF EXISTS calculated_dates")
        except:
            pass
        
        # Crear tabla con nueva estructura
        cursor.execute('''
            CREATE TABLE calculated_dates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER,
                activity_name TEXT NOT NULL,
                date_position INTEGER NOT NULL DEFAULT 1,
                date DATE NOT NULL,
                is_custom BOOLEAN DEFAULT 0,
                FOREIGN KEY (client_id) REFERENCES clients (id),
                UNIQUE(client_id, activity_name, date_position)
            )
        ''')
        
        # Restaurar datos si los había (asignando posiciones)
        if backup_data:
            activity_counters = {}
            for row in backup_data:
                try:
                    if len(row) >= 4:
                        client_id = row[1]
                        activity_name = row[2]
                        date = row[3]
                        
                        key = f"{client_id}_{activity_name}"
                        if key not in activity_counters:
                            activity_counters[key] = 1
                        else:
                            activity_counters[key] += 1
                        
                        if activity_counters[key] <= 4:
                            cursor.execute('''
                                INSERT INTO calculated_dates (client_id, activity_name, date_position, date, is_custom)
                                VALUES (?, ?, ?, ?, 0)
                            ''', (client_id, activity_name, activity_counters[key], date))
                except Exception as e:
                    print(f"Error restaurando datos: {e}")
                    continue
    
    conn.commit()
    
    # Actualizar códigos SAP de frecuencias existentes
    update_frequency_sap_codes()
    
    conn.close()

# === FUNCIONES DE CLIENTES ===

def get_clients():
    """Obtiene todos los clientes"""
    conn = get_db_connection()
    try:
        clients = pd.read_sql_query("SELECT * FROM clients", conn)
    except Exception as e:
        print(f"Error obteniendo clientes: {e}")
        clients = pd.DataFrame()
    conn.close()
    return clients

def get_client_by_id(client_id):
    """Obtiene un cliente por su ID - Versión mejorada"""
    conn = get_db_connection()
    try:
        # Usar fetchone directamente en lugar de pandas para mayor control
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
        client_data = cursor.fetchone()
        
        if client_data:
            # Obtener los nombres de las columnas
            column_names = [description[0] for description in cursor.description]
            # Crear un diccionario con los datos
            client_dict = dict(zip(column_names, client_data))
            print(f"Cliente encontrado: {client_dict}")
            return pd.Series(client_dict)
        else:
            print(f"No se encontró cliente con ID {client_id}")
            return None
            
    except Exception as e:
        print(f"Error obteniendo cliente {client_id}: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return None
    finally:
        conn.close()

def add_client(name, codigo_ag, codigo_we, csr, vendedor, calendario_sap, tipo_cliente='Otro', region='Otro'):
    """Agrega un nuevo cliente"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO clients (name, codigo_ag, codigo_we, csr, vendedor, calendario_sap, tipo_cliente, region)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, codigo_ag, codigo_we, csr, vendedor, calendario_sap, tipo_cliente, region))
        client_id = cursor.lastrowid
        
        conn.commit()
        print(f"Cliente {client_id} creado exitosamente")
        return client_id
        
    except Exception as e:
        print(f"Error creando cliente: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def update_client(client_id, name, codigo_ag, codigo_we, csr, vendedor, calendario_sap, tipo_cliente='Otro', region='Otro'):
    """Actualiza la información de un cliente"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Debug: verificar que el cliente existe antes de actualizar
        cursor.execute("SELECT id, name FROM clients WHERE id = ?", (client_id,))
        existing_client = cursor.fetchone()
        
        if not existing_client:
            print(f"Error: Cliente con ID {client_id} no encontrado")
            return False
        
        print(f"Cliente encontrado: ID {existing_client[0]}, Nombre: {existing_client[1]}")
        print(f"Actualizando con nuevos datos:")
        print(f"  Nombre: '{name}'")
        print(f"  Código AG: '{codigo_ag}'")
        print(f"  Código WE: '{codigo_we}'")
        print(f"  CSR: '{csr}'")
        print(f"  Vendedor: '{vendedor}'")
        print(f"  Calendario SAP: '{calendario_sap}'")
        print(f"  Tipo Cliente: '{tipo_cliente}'")
        print(f"  Región: '{region}'")
        
        # Realizar la actualización
        cursor.execute('''
            UPDATE clients 
            SET name = ?, codigo_ag = ?, codigo_we = ?, csr = ?, vendedor = ?, calendario_sap = ?, tipo_cliente = ?, region = ?
            WHERE id = ?
        ''', (name, codigo_ag, codigo_we, csr, vendedor, calendario_sap, tipo_cliente, region, client_id))
        
        # Verificar que se actualizó al menos una fila
        if cursor.rowcount == 0:
            print(f"Advertencia: No se actualizó ninguna fila para cliente ID {client_id}")
            conn.rollback()
            return False
        
        conn.commit()
        
        # Verificar la actualización
        cursor.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
        updated_client = cursor.fetchone()
        print(f"Cliente actualizado exitosamente:")
        print(f"  Datos finales: {updated_client}")
        
        print(f"✅ Cliente ID {client_id} actualizado exitosamente. Filas afectadas: {cursor.rowcount}")
        return True
        
    except Exception as e:
        print(f"❌ Error actualizando cliente ID {client_id}: {e}")
        import traceback
        print(f"Traceback completo: {traceback.format_exc()}")
        conn.rollback()
        return False
    finally:
        conn.close()

def delete_client(client_id):
    """Elimina un cliente y todos sus datos relacionados"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Verificar que el cliente existe
        cursor.execute("SELECT id, name FROM clients WHERE id = ?", (client_id,))
        existing_client = cursor.fetchone()
        
        if not existing_client:
            print(f"Error: Cliente con ID {client_id} no encontrado")
            return False
        
        client_name = existing_client[1]
        print(f"Eliminando cliente: ID {client_id}, Nombre: {client_name}")
        
        # Eliminar en orden para mantener integridad referencial
        # 1. Eliminar fechas calculadas
        cursor.execute("DELETE FROM calculated_dates WHERE client_id = ?", (client_id,))
        deleted_dates = cursor.rowcount
        print(f"  Fechas calculadas eliminadas: {deleted_dates}")
        
        # 2. Eliminar actividades del cliente
        cursor.execute("DELETE FROM client_activities WHERE client_id = ?", (client_id,))
        deleted_activities = cursor.rowcount
        print(f"  Actividades eliminadas: {deleted_activities}")
        
        # 3. Eliminar el cliente
        cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))
        deleted_client = cursor.rowcount
        
        if deleted_client == 0:
            print(f"Error: No se pudo eliminar el cliente ID {client_id}")
            conn.rollback()
            return False
        
        conn.commit()
        print(f"✅ Cliente '{client_name}' (ID {client_id}) eliminado exitosamente")
        print(f"  Total eliminado: 1 cliente, {deleted_activities} actividades, {deleted_dates} fechas")
        return True
        
    except Exception as e:
        print(f"❌ Error eliminando cliente ID {client_id}: {e}")
        import traceback
        print(f"Traceback completo: {traceback.format_exc()}")
        conn.rollback()
        return False
    finally:
        conn.close()

# === FUNCIONES DE FRECUENCIAS ===

def get_frequency_templates():
    """Obtiene todas las plantillas de frecuencias"""
    conn = get_db_connection()
    try:
        templates = pd.read_sql_query("SELECT * FROM frequency_templates", conn)
    except Exception as e:
        print(f"Error obteniendo frecuencias: {e}")
        templates = pd.DataFrame()
    conn.close()
    return templates

def add_frequency_template(name, frequency_type, frequency_config, description, manual_sap_code=None):
    """Agrega una nueva plantilla de frecuencia"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Usar código SAP manual si se proporciona, sino obtener automáticamente basado en el nombre
    if manual_sap_code is not None:
        calendario_sap_code = manual_sap_code.strip() if manual_sap_code.strip() else "0"
    else:
        mapping = get_sap_calendar_mapping()
        calendario_sap_code = mapping.get(name, "0")
    
    try:
        cursor.execute('''
            INSERT INTO frequency_templates (name, frequency_type, frequency_config, description, calendario_sap_code)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, frequency_type, frequency_config, description, calendario_sap_code))
        conn.commit()
        print(f"Frecuencia '{name}' creada con código SAP: {calendario_sap_code}")
        return True
    except Exception as e:
        print(f"Error agregando frecuencia: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def update_frequency_template(template_id, name, frequency_type, frequency_config, description, manual_sap_code=None):
    """Actualiza una plantilla de frecuencia existente"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Usar código SAP manual si se proporciona, sino obtener automáticamente basado en el nombre
    if manual_sap_code is not None:
        calendario_sap_code = manual_sap_code.strip() if manual_sap_code.strip() else "0"
    else:
        mapping = get_sap_calendar_mapping()
        calendario_sap_code = mapping.get(name, "0")
    
    try:
        cursor.execute('''
            UPDATE frequency_templates 
            SET name = ?, frequency_type = ?, frequency_config = ?, description = ?, calendario_sap_code = ?
            WHERE id = ?
        ''', (name, frequency_type, frequency_config, description, calendario_sap_code, template_id))
        
        conn.commit()
        print(f"Frecuencia '{name}' actualizada exitosamente con código SAP: {calendario_sap_code}")
        return True
    except Exception as e:
        print(f"Error actualizando frecuencia: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def delete_frequency_template(template_id):
    """Elimina una plantilla de frecuencia"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Verificar si la frecuencia está siendo usada por algún cliente
        cursor.execute('''
            SELECT COUNT(*) FROM client_activities 
            WHERE frequency_template_id = ?
        ''', (template_id,))
        
        usage_count = cursor.fetchone()[0]
        
        if usage_count > 0:
            print(f"No se puede eliminar: la frecuencia está siendo usada por {usage_count} actividades")
            return False, f"Esta frecuencia está siendo usada por {usage_count} actividad(es). No se puede eliminar."
        
        cursor.execute('DELETE FROM frequency_templates WHERE id = ?', (template_id,))
        
        conn.commit()
        print(f"Frecuencia eliminada exitosamente")
        return True, "Frecuencia eliminada exitosamente"
        
    except Exception as e:
        print(f"Error eliminando frecuencia: {e}")
        conn.rollback()
        return False, f"Error al eliminar frecuencia: {e}"
    finally:
        conn.close()

def get_frequency_usage_count(template_id):
    """Obtiene el número de actividades que usan una frecuencia específica"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT COUNT(*) FROM client_activities 
            WHERE frequency_template_id = ?
        ''', (template_id,))
        
        count = cursor.fetchone()[0]
        return count
    except Exception as e:
        print(f"Error obteniendo uso de frecuencia: {e}")
        return 0
    finally:
        conn.close()

# === FUNCIONES DE ACTIVIDADES ===

def get_client_activities(client_id):
    """Obtiene las actividades de un cliente en orden específico"""
    conn = get_db_connection()
    try:
        activities = pd.read_sql_query('''
            SELECT ca.*, ft.name as frequency_name, ft.frequency_type, ft.frequency_config, ft.calendario_sap_code
            FROM client_activities ca
            JOIN frequency_templates ft ON ca.frequency_template_id = ft.id
            WHERE ca.client_id = ?
            ORDER BY 
                CASE ca.activity_name
                    WHEN 'Fecha envío OC' THEN 1
                    WHEN 'Albaranado' THEN 2
                    WHEN 'Fecha Entrega' THEN 3
                    ELSE 4
                END
        ''', conn, params=(client_id,))
    except Exception as e:
        print(f"Error obteniendo actividades del cliente {client_id}: {e}")
        activities = pd.DataFrame()
    conn.close()
    return activities

def create_default_activities(client_id):
    """Crea las actividades predeterminadas para un cliente"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar que existan las frecuencias predeterminadas
    cursor.execute("SELECT COUNT(*) FROM frequency_templates")
    if cursor.fetchone()[0] == 0:
        conn.close()
        return
    
    # Actividades predeterminadas en el orden requerido
    default_activities = [
        ("Fecha envío OC", 1),   # Primera actividad
        ("Albaranado", 2),       # Segunda actividad
        ("Fecha Entrega", 3)     # Tercera actividad
    ]
    
    try:
        for activity_name, freq_id in default_activities:
            cursor.execute('''
                SELECT COUNT(*) FROM client_activities 
                WHERE client_id = ? AND activity_name = ?
            ''', (client_id, activity_name))
            
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                    INSERT INTO client_activities (client_id, activity_name, frequency_template_id)
                    VALUES (?, ?, ?)
                ''', (client_id, activity_name, freq_id))
                print(f"Creada actividad: {activity_name} para cliente {client_id}")
                
                # Si es la actividad Albaranado, actualizar automáticamente el calendario SAP del cliente
                if activity_name == "Albaranado":
                    auto_update_client_calendario_sap(client_id, activity_name, freq_id)
        
        conn.commit()
    except Exception as e:
        print(f"Error creando actividades predeterminadas: {e}")
    finally:
        conn.close()

def update_client_activity_frequency(client_id, activity_name, frequency_template_id):
    """Actualiza la frecuencia de una actividad específica"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE client_activities 
            SET frequency_template_id = ?
            WHERE client_id = ? AND activity_name = ?
        ''', (frequency_template_id, client_id, activity_name))
        
        conn.commit()
        print(f"Frecuencia actualizada para {activity_name}")
        
        # Si es la actividad Albaranado, actualizar automáticamente el calendario SAP del cliente
        auto_update_client_calendario_sap(client_id, activity_name, frequency_template_id)
        
        return True
    except Exception as e:
        print(f"Error actualizando frecuencia: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def add_client_activity(client_id, activity_name, frequency_template_id):
    """Agrega una nueva actividad a un cliente"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO client_activities (client_id, activity_name, frequency_template_id)
            VALUES (?, ?, ?)
        ''', (client_id, activity_name, frequency_template_id))
        
        conn.commit()
        print(f"Actividad {activity_name} agregada al cliente {client_id}")
        
        # Si es la actividad Albaranado, actualizar automáticamente el calendario SAP del cliente
        auto_update_client_calendario_sap(client_id, activity_name, frequency_template_id)
        
        return True
    except Exception as e:
        print(f"Error agregando actividad: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def delete_client_activity(client_id, activity_name):
    """Elimina una actividad de un cliente"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Eliminar actividad
        cursor.execute('''
            DELETE FROM client_activities 
            WHERE client_id = ? AND activity_name = ?
        ''', (client_id, activity_name))
        
        # Eliminar fechas asociadas
        cursor.execute('''
            DELETE FROM calculated_dates 
            WHERE client_id = ? AND activity_name = ?
        ''', (client_id, activity_name))
        
        conn.commit()
        print(f"Actividad {activity_name} eliminada del cliente {client_id}")
        return True
    except Exception as e:
        print(f"Error eliminando actividad: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# === FUNCIONES DE FECHAS ===

def get_calculated_dates(client_id):
    """Obtiene las fechas calculadas para un cliente en orden específico"""
    conn = get_db_connection()
    try:
        dates = pd.read_sql_query('''
            SELECT * FROM calculated_dates 
            WHERE client_id = ? 
            ORDER BY 
                CASE activity_name
                    WHEN 'Fecha envío OC' THEN 1
                    WHEN 'Albaranado' THEN 2
                    WHEN 'Fecha Entrega' THEN 3
                    ELSE 4
                END, 
                date_position
        ''', conn, params=(client_id,))
    except Exception as e:
        conn.close()
        print(f"Error en get_calculated_dates: {e}")
        init_database()
        conn = get_db_connection()
        try:
            dates = pd.read_sql_query('''
                SELECT * FROM calculated_dates 
                WHERE client_id = ? 
                ORDER BY 
                    CASE activity_name
                        WHEN 'Fecha envío OC' THEN 1
                        WHEN 'Albaranado' THEN 2
                        WHEN 'Fecha Entrega' THEN 3
                        ELSE 4
                    END, 
                    date_position
            ''', conn, params=(client_id,))
        except:
            dates = pd.DataFrame()
    
    conn.close()
    return dates

def save_calculated_dates(client_id, activity_name, dates_list):
    """Guarda hasta 4 fechas para una actividad específica en posiciones secuenciales"""
    if not dates_list:
        print(f"No hay fechas para guardar para actividad {activity_name}")
        return
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Eliminar fechas existentes para esta actividad
        cursor.execute('''
            DELETE FROM calculated_dates 
            WHERE client_id = ? AND activity_name = ?
        ''', (client_id, activity_name))
        
        # Insertar nuevas fechas en posiciones secuenciales (1, 2, 3, 4)
        for position, date in enumerate(dates_list[:4], 1):
            if date:
                # Manejo más robusto de diferentes tipos de fecha
                if isinstance(date, (datetime, date)):
                    date_str = date.strftime('%Y-%m-%d')
                elif hasattr(date, 'strftime'):
                    date_str = date.strftime('%Y-%m-%d')
                else:
                    date_str = str(date)
                
                cursor.execute('''
                    INSERT INTO calculated_dates (client_id, activity_name, date_position, date)
                    VALUES (?, ?, ?, ?)
                ''', (client_id, activity_name, position, date_str))
        
        conn.commit()
        print(f"Guardadas {min(len(dates_list), 4)} fechas para {activity_name} en posiciones secuenciales")
        
    except Exception as e:
        print(f"Error guardando fechas para {activity_name}: {e}")
        conn.rollback()
    finally:
        conn.close()

def update_calculated_date(client_id, activity_name, date_position, new_date):
    """Actualiza una fecha específica"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE calculated_dates 
        SET date = ?, is_custom = 1
        WHERE client_id = ? AND activity_name = ? AND date_position = ?
    ''', (new_date, client_id, activity_name, date_position))
    conn.commit()
    conn.close()