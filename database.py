import sqlite3
import pandas as pd
import json
import warnings
import threading
import time
import hashlib
from datetime import datetime, date
from config import get_database_path, get_db_config

# Suprimir warnings específicos de pandas sobre SQLAlchemy
warnings.filterwarnings('ignore', message='.*SQLAlchemy.*', category=UserWarning)
warnings.filterwarnings('ignore', message='.*pandas only supports SQLAlchemy.*', category=UserWarning)

# Sistema de cache mejorado con TTL y invalidación inteligente
class DatabaseCache:
    def __init__(self, default_ttl=60):
        self._cache = {}
        self._timestamps = {}
        self._lock = threading.RLock()
        self.default_ttl = default_ttl
        self.hit_count = 0
        self.miss_count = 0
    
    def _is_expired(self, key, custom_ttl=None):
        """Verifica si una entrada del cache ha expirado"""
        if key not in self._timestamps:
            return True
        ttl = custom_ttl or self.default_ttl
        age = time.time() - self._timestamps[key]
        # Debug: imprimir información de expiración
        # print(f"[CACHE DEBUG] Clave {key[:20]}... - Edad: {age:.1f}s, TTL: {ttl}s, Expirado: {age > ttl}")
        return age > ttl
    
    def get(self, key, custom_ttl=None):
        with self._lock:
            if key in self._cache and not self._is_expired(key, custom_ttl):
                self.hit_count += 1
                cached_value = self._cache[key]
                # Hacer copia segura dependiendo del tipo
                if isinstance(cached_value, pd.DataFrame):
                    return cached_value.copy()
                elif isinstance(cached_value, pd.Series):
                    return cached_value.copy()
                else:
                    return cached_value
            self.miss_count += 1
            return None
    
    def set(self, key, value, custom_ttl=None):
        with self._lock:
            # Hacer copia segura dependiendo del tipo antes de almacenar
            if isinstance(value, pd.DataFrame):
                self._cache[key] = value.copy()
            elif isinstance(value, pd.Series):
                self._cache[key] = value.copy()
            else:
                self._cache[key] = value
            self._timestamps[key] = time.time()
    
    def invalidate_pattern(self, pattern):
        with self._lock:
            keys_to_remove = [key for key in self._cache.keys() if pattern in key]
            for key in keys_to_remove:
                del self._cache[key]
                del self._timestamps[key]
    
    def clear_all(self):
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()
            self.hit_count = 0
            self.miss_count = 0
    
    def get_stats(self):
        total = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total * 100) if total > 0 else 0
        return {
            'hits': self.hit_count,
            'misses': self.miss_count,
            'hit_rate': hit_rate,
            'cached_items': len(self._cache)
        }

# Instancia global del cache
_db_cache = DatabaseCache(default_ttl=60)

# Connection pool simple
class ConnectionPool:
    def __init__(self, max_connections=5):
        self._connections = []
        self._max_connections = max_connections
        self._lock = threading.RLock()
    
    def get_connection(self):
        with self._lock:
            if self._connections:
                return self._connections.pop()
            return get_raw_db_connection()
    
    def return_connection(self, conn):
        with self._lock:
            if len(self._connections) < self._max_connections:
                self._connections.append(conn)
            else:
                try:
                    conn.close()
                except:
                    pass

_connection_pool = ConnectionPool()


class PooledConnectionProxy:
    """Proxy de conexión que retorna al pool en close().

    Esto permite reusar conexiones (especialmente en SQLiteCloud) sin cambiar el código
    existente que hace conn = get_db_connection(); ...; conn.close().
    """

    def __init__(self, conn):
        self._conn = conn
        self._returned = False

    def close(self):
        if self._conn is None or self._returned:
            return
        try:
            return_pooled_connection(self._conn)
        finally:
            self._returned = True
            self._conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False

    def cursor(self, *args, **kwargs):
        return self._conn.cursor(*args, **kwargs)

    def execute(self, *args, **kwargs):
        return self._conn.execute(*args, **kwargs)

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def __getattr__(self, name):
        return getattr(self._conn, name)

def clear_cache():
    """Limpia el cache de consultas"""
    _db_cache.clear_all()

def clear_cache_pattern(pattern):
    """Limpia entradas específicas del cache que contengan el patrón"""
    _db_cache.invalidate_pattern(pattern)

def get_cache_stats():
    """Obtiene estadísticas del cache para monitoreo"""
    return _db_cache.get_stats()

def debug_cache_keys():
    """Lista todas las claves del cache para debugging"""
    with _db_cache._lock:
        return list(_db_cache._cache.keys())

def reset_cache_stats():
    """Reinicia las estadísticas del cache"""
    with _db_cache._lock:
        _db_cache.hit_count = 0
        _db_cache.miss_count = 0

def get_raw_db_connection():
    """Obtiene una conexión *real* a la base de datos según el entorno."""
    config = get_db_config()
    return config.get_db_connection()


def get_db_connection():
    """Obtiene una conexión a la BD reutilizable.

    Importante: conn.close() NO cierra la conexión física; la retorna al pool.
    """
    return PooledConnectionProxy(get_pooled_connection())

def get_pooled_connection():
    """Obtiene una conexión del pool"""
    return _connection_pool.get_connection()

def return_pooled_connection(conn):
    """Retorna una conexión al pool"""
    _connection_pool.return_connection(conn)

def execute_query(query, params=None, use_pool=True):
    """Ejecuta una consulta de manera compatible con ambos tipos de BD con pooling opcional"""
    if use_pool:
        conn = get_pooled_connection()
    else:
        conn = get_db_connection()
    
    try:
        if params:
            result = conn.execute(query, params)
        else:
            result = conn.execute(query)
        
        # Para queries que devuelven datos
        if query.strip().upper().startswith('SELECT'):
            return result.fetchall()
        else:
            conn.commit()
            return result
    finally:
        if use_pool:
            return_pooled_connection(conn)
        else:
            conn.close()

def execute_batch_query(queries_with_params, use_transaction=True):
    """Ejecuta múltiples consultas en batch para mejor rendimiento"""
    conn = get_pooled_connection()
    cursor = conn.cursor()
    
    try:
        if use_transaction:
            cursor.execute("BEGIN TRANSACTION")
        
        results = []
        for query, params in queries_with_params:
            if params:
                result = cursor.execute(query, params)
            else:
                result = cursor.execute(query)
            
            if query.strip().upper().startswith('SELECT'):
                results.append(result.fetchall())
            else:
                results.append(result)
        
        if use_transaction:
            conn.commit()
        
        return results
        
    except Exception as e:
        if use_transaction:
            conn.rollback()
        raise e
    finally:
        return_pooled_connection(conn)

def create_database_indexes():
    """Crea índices para optimizar consultas frecuentes"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    indexes = [
        # Índices para catálogo de actividades
        "CREATE INDEX IF NOT EXISTS idx_activities_catalog_name ON activities_catalog(name)",

        # Índices para la tabla clients
        "CREATE INDEX IF NOT EXISTS idx_clients_name ON clients(name)",
        "CREATE INDEX IF NOT EXISTS idx_clients_codigo_ag ON clients(codigo_ag)",
        "CREATE INDEX IF NOT EXISTS idx_clients_codigo_we ON clients(codigo_we)",
        "CREATE INDEX IF NOT EXISTS idx_clients_tipo_region ON clients(tipo_cliente, region)",
        
        # Índices para la tabla client_activities
        "CREATE INDEX IF NOT EXISTS idx_client_activities_client_id ON client_activities(client_id)",
        "CREATE INDEX IF NOT EXISTS idx_client_activities_activity_name ON client_activities(activity_name)",
        "CREATE INDEX IF NOT EXISTS idx_client_activities_activity_id ON client_activities(activity_id)",
        "CREATE INDEX IF NOT EXISTS idx_client_activities_frequency_id ON client_activities(frequency_template_id)",
        "CREATE INDEX IF NOT EXISTS idx_client_activities_composite ON client_activities(client_id, activity_name)",
        
        # Índices para la tabla calculated_dates
        "CREATE INDEX IF NOT EXISTS idx_calculated_dates_client_id ON calculated_dates(client_id)",
        "CREATE INDEX IF NOT EXISTS idx_calculated_dates_activity ON calculated_dates(activity_name)",
        "CREATE INDEX IF NOT EXISTS idx_calculated_dates_activity_id ON calculated_dates(activity_id)",
        "CREATE INDEX IF NOT EXISTS idx_calculated_dates_date ON calculated_dates(date)",
        "CREATE INDEX IF NOT EXISTS idx_calculated_dates_composite ON calculated_dates(client_id, activity_name, date_position)",
        
        # Índices para la tabla frequency_templates
        "CREATE INDEX IF NOT EXISTS idx_frequency_templates_name ON frequency_templates(name)",
        "CREATE INDEX IF NOT EXISTS idx_frequency_templates_type ON frequency_templates(frequency_type)",
        "CREATE INDEX IF NOT EXISTS idx_frequency_templates_sap_code ON frequency_templates(calendario_sap_code)"
    ]
    
    try:
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        conn.commit()
        print("Índices de base de datos creados exitosamente")
        
    except Exception as e:
        print(f"Error creando índices: {e}")
        conn.rollback()
    finally:
        conn.close()

def execute_query_df(query, params=None, use_cache=False, cache_ttl=60):
    """Ejecuta una consulta y devuelve un DataFrame con cache optimizado"""
    
    # Generar clave de cache
    cache_key = None
    if use_cache:
        param_str = str(params) if params else "None"
        cache_key = hashlib.md5(f"{query}_{param_str}".encode()).hexdigest()
        
        # Verificar cache
        cached_result = _db_cache.get(cache_key, cache_ttl)
        if cached_result is not None:
            return cached_result
    
    # Suprimir warnings temporalmente para esta consulta específica
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        
        conn = get_pooled_connection()
        try:
            if params:
                df = pd.read_sql_query(query, conn, params=params)
            else:
                df = pd.read_sql_query(query, conn)
            
            # Guardar en cache si se solicitó
            if use_cache and cache_key:
                _db_cache.set(cache_key, df, cache_ttl)
            
            return df
        finally:
            return_pooled_connection(conn)

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
    try:
        db_path = get_database_path()
        config = get_db_config()
        
        print(f"[GREEN LOGISTICS] Inicializando base de datos: {db_path}")
        print(f"[GREEN LOGISTICS] Entorno: {config.get_environment()}")
        print(f"[GREEN LOGISTICS] Descripción: {config.db_config['description']}")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
    except Exception as e:
        print(f"[GREEN LOGISTICS] ERROR en inicialización de BD: {e}")
        import streamlit as st
        st.error(f"❌ Error de configuración de base de datos: {str(e)}")
        st.stop()
        return
    
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

    # Catálogo de actividades (normalización)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activities_catalog (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            is_active INTEGER DEFAULT 1
        )
    ''')

    # Actividades base con IDs fijos
    cursor.execute(
        "INSERT OR IGNORE INTO activities_catalog (id, name, is_active) VALUES (1, 'Fecha Envío OC', 1)"
    )
    cursor.execute(
        "INSERT OR IGNORE INTO activities_catalog (id, name, is_active) VALUES (2, 'Albaranado', 1)"
    )
    cursor.execute(
        "INSERT OR IGNORE INTO activities_catalog (id, name, is_active) VALUES (3, 'Fecha Entrega', 1)"
    )
    
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

    # Asegurar columna activity_id en client_activities (migración no destructiva)
    cursor.execute("PRAGMA table_info(client_activities)")
    ca_columns_info = cursor.fetchall()
    ca_column_names = [col[1] for col in ca_columns_info]
    if 'activity_id' not in ca_column_names:
        cursor.execute('ALTER TABLE client_activities ADD COLUMN activity_id INTEGER')
        print("Campo activity_id agregado a client_activities")
    
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
                activity_id INTEGER,
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

                        # Asegurar actividad en catálogo y obtener ID
                        cursor.execute("SELECT id FROM activities_catalog WHERE name = ?", (activity_name,))
                        activity_row = cursor.fetchone()
                        if activity_row:
                            activity_id = activity_row[0]
                        else:
                            cursor.execute("SELECT COALESCE(MAX(id), 3) + 1 FROM activities_catalog")
                            activity_id = cursor.fetchone()[0]
                            cursor.execute(
                                "INSERT OR IGNORE INTO activities_catalog (id, name, is_active) VALUES (?, ?, 1)",
                                (activity_id, activity_name)
                            )
                        
                        key = f"{client_id}_{activity_name}"
                        if key not in activity_counters:
                            activity_counters[key] = 1
                        else:
                            activity_counters[key] += 1
                        
                        if activity_counters[key] <= 4:
                            cursor.execute('''
                                INSERT INTO calculated_dates (client_id, activity_id, activity_name, date_position, date, is_custom)
                                VALUES (?, ?, ?, ?, ?, 0)
                            ''', (client_id, activity_id, activity_name, activity_counters[key], date))
                except Exception as e:
                    print(f"Error restaurando datos: {e}")
                    continue

    # Asegurar columna activity_id en calculated_dates (migración no destructiva)
    cursor.execute("PRAGMA table_info(calculated_dates)")
    cd_columns_info = cursor.fetchall()
    cd_column_names = [col[1] for col in cd_columns_info]
    if 'activity_id' not in cd_column_names:
        cursor.execute('ALTER TABLE calculated_dates ADD COLUMN activity_id INTEGER')
        print("Campo activity_id agregado a calculated_dates")

    # Backfill/migración: asegurar que todas las actividades existan en catálogo y poblar activity_id
    try:
        # 1) Actividades en client_activities
        cursor.execute("SELECT DISTINCT activity_name FROM client_activities WHERE activity_name IS NOT NULL")
        for (activity_name,) in cursor.fetchall():
            activity_name = str(activity_name).strip()
            if not activity_name:
                continue
            cursor.execute("SELECT id FROM activities_catalog WHERE name = ?", (activity_name,))
            row = cursor.fetchone()
            if row:
                activity_id = row[0]
            else:
                cursor.execute("SELECT COALESCE(MAX(id), 3) + 1 FROM activities_catalog")
                activity_id = cursor.fetchone()[0]
                cursor.execute(
                    "INSERT OR IGNORE INTO activities_catalog (id, name, is_active) VALUES (?, ?, 1)",
                    (activity_id, activity_name)
                )

            cursor.execute(
                "UPDATE client_activities SET activity_id = ? WHERE (activity_id IS NULL OR activity_id = 0) AND activity_name = ?",
                (activity_id, activity_name)
            )

        # 2) Actividades en calculated_dates
        cursor.execute("SELECT DISTINCT activity_name FROM calculated_dates WHERE activity_name IS NOT NULL")
        for (activity_name,) in cursor.fetchall():
            activity_name = str(activity_name).strip()
            if not activity_name:
                continue
            cursor.execute("SELECT id FROM activities_catalog WHERE name = ?", (activity_name,))
            row = cursor.fetchone()
            if row:
                activity_id = row[0]
            else:
                cursor.execute("SELECT COALESCE(MAX(id), 3) + 1 FROM activities_catalog")
                activity_id = cursor.fetchone()[0]
                cursor.execute(
                    "INSERT OR IGNORE INTO activities_catalog (id, name, is_active) VALUES (?, ?, 1)",
                    (activity_id, activity_name)
                )

            cursor.execute(
                "UPDATE calculated_dates SET activity_id = ? WHERE (activity_id IS NULL OR activity_id = 0) AND activity_name = ?",
                (activity_id, activity_name)
            )
    except Exception as e:
        print(f"Error migrando catálogo de actividades: {e}")
    
    conn.commit()
    
    # Crear índices para optimizar consultas
    create_database_indexes()
    
    # Actualizar códigos SAP de frecuencias existentes
    update_frequency_sap_codes()
    
    conn.close()

# === FUNCIONES DE CLIENTES OPTIMIZADAS ===

def get_clients(use_cache=True):
    """Obtiene todos los clientes con cache optimizado y filtro por país"""
    from auth_system import get_user_country_filter
    
    try:
        # Debug: Log de inicio
        print(f"[DEBUG] get_clients() iniciando, use_cache={use_cache}")
        
        # Obtener todos los clientes
        df = execute_query_df("SELECT * FROM clients ORDER BY name", use_cache=use_cache, cache_ttl=120)
        print(f"[DEBUG] execute_query_df retornó {len(df)} clientes")
        
        # Aplicar filtro de país si el usuario lo tiene
        country_filter = get_user_country_filter()
        print(f"[DEBUG] country_filter = {country_filter}")
        
        if country_filter:
            # Filtrar solo clientes del país específico
            original_count = len(df)
            df = df[df['pais'] == country_filter] if not df.empty and 'pais' in df.columns else df
            print(f"[DEBUG] Filtro aplicado: {original_count} -> {len(df)} clientes")
        
        print(f"[DEBUG] get_clients() retornando {len(df)} clientes")
        return df
    except Exception as e:
        print(f"[DEBUG] ERROR en get_clients(): {e}")
        print(f"[DEBUG] Tipo de error: {type(e).__name__}")
        return pd.DataFrame()

def get_clients_summary():
    """Obtiene un resumen de clientes (solo campos básicos) para listados rápidos con filtro por país"""
    from auth_system import get_user_country_filter
    
    try:
        query = "SELECT id, name, codigo_ag, codigo_we, tipo_cliente, region, pais FROM clients ORDER BY name"
        df = execute_query_df(query, use_cache=True, cache_ttl=300)
        
        # Aplicar filtro de país si el usuario lo tiene
        country_filter = get_user_country_filter()
        if country_filter:
            # Filtrar solo clientes del país específico
            df = df[df['pais'] == country_filter] if not df.empty and 'pais' in df.columns else df
        
        return df
    except Exception as e:
        print(f"Error obteniendo resumen de clientes: {e}")
        return pd.DataFrame()

def get_clients_batch(client_ids):
    """Obtiene múltiples clientes en una sola consulta con filtro por país"""
    from auth_system import get_user_country_filter
    
    if not client_ids:
        return pd.DataFrame()
    
    try:
        placeholders = ','.join(['?' for _ in client_ids])
        query = f"SELECT * FROM clients WHERE id IN ({placeholders}) ORDER BY name"
        df = execute_query_df(query, params=client_ids, use_cache=True, cache_ttl=60)
        
        # Aplicar filtro de país si el usuario lo tiene
        country_filter = get_user_country_filter()
        if country_filter:
            # Filtrar solo clientes del país específico
            df = df[df['pais'] == country_filter] if not df.empty and 'pais' in df.columns else df
        
        return df
    except Exception as e:
        print(f"Error obteniendo clientes batch: {e}")
        return pd.DataFrame()

def get_client_by_id(client_id, use_cache=True):
    """Obtiene un cliente por su ID - Versión optimizada con cache y filtro por país"""
    from auth_system import get_user_country_filter
    
    if use_cache:
        # Intentar obtener del cache primero
        cache_key = f"client_{client_id}"
        cached_client = _db_cache.get(cache_key, 60)
        if cached_client is not None:
            # Verificar filtro de país si existe
            country_filter = get_user_country_filter()
            if country_filter:
                if cached_client.get('pais') != country_filter:
                    return None  # Cliente no accesible para este usuario
            return cached_client
    
    conn = get_pooled_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
        client_data = cursor.fetchone()
        
        if client_data:
            column_names = [description[0] for description in cursor.description]
            client_dict = dict(zip(column_names, client_data))
            client_series = pd.Series(client_dict)
            
            # Verificar filtro de país
            country_filter = get_user_country_filter()
            if country_filter:
                if client_dict.get('pais') != country_filter:
                    return None  # Cliente no accesible para este usuario
            
            # Guardar en cache
            if use_cache:
                cache_key = f"client_{client_id}"
                _db_cache.set(cache_key, client_series, 60)
            
            print(f"Cliente encontrado: {client_dict}")
            return client_series
        else:
            print(f"No se encontró cliente con ID {client_id}")
            return None
            
    except Exception as e:
        print(f"Error obteniendo cliente {client_id}: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return None
    finally:
        return_pooled_connection(conn)

def add_client(name, codigo_ag, codigo_we, csr, vendedor, calendario_sap, tipo_cliente='Otro', region='Otro', pais='Colombia'):
    """Agrega un nuevo cliente con invalidación de cache"""
    conn = get_pooled_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO clients (name, codigo_ag, codigo_we, csr, vendedor, calendario_sap, tipo_cliente, region, pais)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, codigo_ag, codigo_we, csr, vendedor, calendario_sap, tipo_cliente, region, pais))
        client_id = cursor.lastrowid
        
        conn.commit()
        print(f"Cliente {client_id} creado exitosamente")
        
        # Invalidar cache relacionado con clientes
        _db_cache.invalidate_pattern("clients")
        
        return client_id
        
    except Exception as e:
        print(f"Error creando cliente: {e}")
        conn.rollback()
        return None
    finally:
        return_pooled_connection(conn)

def update_client(client_id, name, codigo_ag, codigo_we, csr, vendedor, calendario_sap, tipo_cliente='Otro', region='Otro', pais='Colombia'):
    """Actualiza la información de un cliente con invalidación de cache"""
    conn = get_pooled_connection()
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
        print(f"  País: '{pais}'")
        
        # Realizar la actualización
        cursor.execute('''
            UPDATE clients 
            SET name = ?, codigo_ag = ?, codigo_we = ?, csr = ?, vendedor = ?, calendario_sap = ?, tipo_cliente = ?, region = ?, pais = ?
            WHERE id = ?
        ''', (name, codigo_ag, codigo_we, csr, vendedor, calendario_sap, tipo_cliente, region, pais, client_id))
        
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
        
        print(f"Cliente ID {client_id} actualizado exitosamente. Filas afectadas: {cursor.rowcount}")
        
        # Invalidar cache relacionado con este cliente específico
        _db_cache.invalidate_pattern("clients")
        _db_cache.invalidate_pattern(f"client_{client_id}")
        
        return True
        
    except Exception as e:
        print(f"Error actualizando cliente ID {client_id}: {e}")
        import traceback
        print(f"Traceback completo: {traceback.format_exc()}")
        conn.rollback()
        return False
    finally:
        return_pooled_connection(conn)

def delete_client(client_id):
    """Elimina un cliente y todos sus datos relacionados con invalidación de cache"""
    conn = get_pooled_connection()
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
        
        # Usar transacción para mantener consistencia
        cursor.execute("BEGIN TRANSACTION")
        
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
        print(f"Cliente '{client_name}' (ID {client_id}) eliminado exitosamente")
        print(f"  Total eliminado: 1 cliente, {deleted_activities} actividades, {deleted_dates} fechas")
        
        # Invalidar todo el cache relacionado con clientes y este cliente específico
        _db_cache.invalidate_pattern("clients")
        _db_cache.invalidate_pattern(f"client_{client_id}")
        _db_cache.invalidate_pattern(f"activities_{client_id}")
        _db_cache.invalidate_pattern(f"dates_{client_id}")
        
        return True
        
    except Exception as e:
        print(f"Error eliminando cliente ID {client_id}: {e}")
        import traceback
        print(f"Traceback completo: {traceback.format_exc()}")
        conn.rollback()
        return False
    finally:
        return_pooled_connection(conn)

# === FUNCIONES DE FRECUENCIAS OPTIMIZADAS ===

def get_frequency_templates(use_cache=True):
    """Obtiene todas las plantillas de frecuencias con cache"""
    try:
        return execute_query_df("SELECT * FROM frequency_templates ORDER BY name", use_cache=use_cache, cache_ttl=300)
    except Exception as e:
        print(f"Error obteniendo frecuencias: {e}")
        return pd.DataFrame()

def get_frequency_template_by_id(template_id, use_cache=True):
    """Obtiene una plantilla de frecuencia específica"""
    if use_cache:
        cache_key = f"frequency_{template_id}"
        cached_freq = _db_cache.get(cache_key, 300)
        if cached_freq is not None:
            return cached_freq
    
    try:
        query = "SELECT * FROM frequency_templates WHERE id = ?"
        df = execute_query_df(query, params=(template_id,))
        
        if not df.empty and use_cache:
            cache_key = f"frequency_{template_id}"
            _db_cache.set(cache_key, df.iloc[0], 300)
            
        return df.iloc[0] if not df.empty else None
    except Exception as e:
        print(f"Error obteniendo frecuencia {template_id}: {e}")
        return None

def add_frequency_template(name, frequency_type, frequency_config, description, manual_sap_code=None):
    """Agrega una nueva plantilla de frecuencia con invalidación de cache"""
    conn = get_pooled_connection()
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
        
        # Invalidar cache de frecuencias
        _db_cache.invalidate_pattern("frequency")
        
        return True
    except Exception as e:
        print(f"Error agregando frecuencia: {e}")
        conn.rollback()
        return False
    finally:
        return_pooled_connection(conn)

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

# === FUNCIONES DE ACTIVIDADES OPTIMIZADAS ===

def get_client_activities(client_id, use_cache=True):
    """Obtiene las actividades de un cliente en orden específico con cache"""
    if use_cache:
        cache_key = f"activities_{client_id}"
        cached_activities = _db_cache.get(cache_key, 120)
        if cached_activities is not None:
            return cached_activities
    
    try:
        query = '''
            SELECT
                ca.id,
                ca.client_id,
                ca.activity_id,
                COALESCE(ac.name, ca.activity_name) as activity_name,
                ca.frequency_template_id,
                ft.name as frequency_name,
                ft.frequency_type,
                ft.frequency_config,
                ft.calendario_sap_code
            FROM client_activities ca
            JOIN frequency_templates ft ON ca.frequency_template_id = ft.id
            LEFT JOIN activities_catalog ac ON ac.id = ca.activity_id
            WHERE ca.client_id = ?
            ORDER BY
                CASE COALESCE(ca.activity_id, 999999)
                    WHEN 1 THEN 1
                    WHEN 2 THEN 2
                    WHEN 3 THEN 3
                    ELSE 4
                END,
                COALESCE(ac.name, ca.activity_name)
        '''
        df = execute_query_df(query, params=(client_id,))
        
        if use_cache:
            cache_key = f"activities_{client_id}"
            _db_cache.set(cache_key, df, 120)
        
        return df
    except Exception as e:
        print(f"Error obteniendo actividades del cliente {client_id}: {e}")
        return pd.DataFrame()

def get_multiple_client_activities(client_ids):
    """Obtiene actividades de múltiples clientes en una sola consulta"""
    if not client_ids:
        return pd.DataFrame()
    
    try:
        placeholders = ','.join(['?' for _ in client_ids])
        query = f'''
            SELECT
                ca.id,
                ca.client_id,
                ca.activity_id,
                COALESCE(ac.name, ca.activity_name) as activity_name,
                ca.frequency_template_id,
                ft.name as frequency_name,
                ft.frequency_type,
                ft.frequency_config,
                ft.calendario_sap_code
            FROM client_activities ca
            JOIN frequency_templates ft ON ca.frequency_template_id = ft.id
            LEFT JOIN activities_catalog ac ON ac.id = ca.activity_id
            WHERE ca.client_id IN ({placeholders})
            ORDER BY ca.client_id,
                CASE COALESCE(ca.activity_id, 999999)
                    WHEN 1 THEN 1
                    WHEN 2 THEN 2
                    WHEN 3 THEN 3
                    ELSE 4
                END,
                COALESCE(ac.name, ca.activity_name)
        '''
        return execute_query_df(query, params=client_ids, use_cache=True, cache_ttl=120)
    except Exception as e:
        print(f"Error obteniendo actividades batch: {e}")
        return pd.DataFrame()

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
        ("Fecha Envío OC", 1, 1),   # (nombre, activity_id, frequency_template_id)
        ("Albaranado", 2, 2),       # (nombre, activity_id, frequency_template_id)
        ("Fecha Entrega", 3, 3)     # (nombre, activity_id, frequency_template_id)
    ]
    
    try:
        for activity_name, activity_id, freq_id in default_activities:
            cursor.execute('''
                SELECT COUNT(*) FROM client_activities 
                WHERE client_id = ? AND activity_name = ?
            ''', (client_id, activity_name))
            
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                    INSERT INTO client_activities (client_id, activity_id, activity_name, frequency_template_id)
                    VALUES (?, ?, ?, ?)
                ''', (client_id, activity_id, activity_name, freq_id))
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
    """Actualiza la frecuencia de una actividad específica con invalidación de cache"""
    conn = get_pooled_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id FROM activities_catalog WHERE name = ?", (activity_name,))
        row = cursor.fetchone()
        activity_id = row[0] if row else None

        if activity_id is None:
            cursor.execute("SELECT COALESCE(MAX(id), 3) + 1 FROM activities_catalog")
            activity_id = cursor.fetchone()[0]
            cursor.execute(
                "INSERT OR IGNORE INTO activities_catalog (id, name, is_active) VALUES (?, ?, 1)",
                (activity_id, activity_name)
            )

        cursor.execute('''
            UPDATE client_activities 
            SET frequency_template_id = ?, activity_id = ?
            WHERE client_id = ? AND (activity_id = ? OR activity_name = ?)
        ''', (frequency_template_id, activity_id, client_id, activity_id, activity_name))
        
        conn.commit()
        print(f"Frecuencia actualizada para {activity_name}")
        
        # Si es la actividad Albaranado, actualizar automáticamente el calendario SAP del cliente
        auto_update_client_calendario_sap(client_id, activity_name, frequency_template_id)
        
        # Invalidar cache relacionado
        _db_cache.invalidate_pattern(f"activities_{client_id}")
        
        return True
    except Exception as e:
        print(f"Error actualizando frecuencia: {e}")
        conn.rollback()
        return False
    finally:
        return_pooled_connection(conn)

def add_client_activity(client_id, activity_name, frequency_template_id):
    """Agrega una nueva actividad a un cliente con invalidación de cache"""
    conn = get_pooled_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id FROM activities_catalog WHERE name = ?", (activity_name,))
        row = cursor.fetchone()
        activity_id = row[0] if row else None

        if activity_id is None:
            cursor.execute("SELECT COALESCE(MAX(id), 3) + 1 FROM activities_catalog")
            activity_id = cursor.fetchone()[0]
            cursor.execute(
                "INSERT OR IGNORE INTO activities_catalog (id, name, is_active) VALUES (?, ?, 1)",
                (activity_id, activity_name)
            )

        cursor.execute('''
            INSERT INTO client_activities (client_id, activity_id, activity_name, frequency_template_id)
            VALUES (?, ?, ?, ?)
        ''', (client_id, activity_id, activity_name, frequency_template_id))
        
        conn.commit()
        print(f"Actividad {activity_name} agregada al cliente {client_id}")
        
        # Si es la actividad Albaranado, actualizar automáticamente el calendario SAP del cliente
        auto_update_client_calendario_sap(client_id, activity_name, frequency_template_id)
        
        # Invalidar cache relacionado
        _db_cache.invalidate_pattern(f"activities_{client_id}")
        
        return True
    except Exception as e:
        print(f"Error agregando actividad: {e}")
        conn.rollback()
        return False
    finally:
        return_pooled_connection(conn)

def delete_client_activity(client_id, activity_name):
    """Elimina una actividad de un cliente con invalidación de cache"""
    conn = get_pooled_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id FROM activities_catalog WHERE name = ?", (activity_name,))
        row = cursor.fetchone()
        activity_id = row[0] if row else None

        # Usar transacción para mantener consistencia
        cursor.execute("BEGIN TRANSACTION")
        
        # Eliminar actividad
        cursor.execute('''
            DELETE FROM client_activities 
            WHERE client_id = ? AND (activity_id = ? OR activity_name = ?)
        ''', (client_id, activity_id, activity_name))
        
        # Eliminar fechas asociadas
        cursor.execute('''
            DELETE FROM calculated_dates 
            WHERE client_id = ? AND (activity_id = ? OR activity_name = ?)
        ''', (client_id, activity_id, activity_name))
        
        conn.commit()
        print(f"Actividad {activity_name} eliminada del cliente {client_id}")
        
        # Invalidar cache relacionado
        _db_cache.invalidate_pattern(f"activities_{client_id}")
        _db_cache.invalidate_pattern(f"dates_{client_id}")
        
        return True
    except Exception as e:
        print(f"Error eliminando actividad: {e}")
        conn.rollback()
        return False
    finally:
        return_pooled_connection(conn)

# === FUNCIONES DE FECHAS OPTIMIZADAS ===

def get_calculated_dates(client_id, use_cache=True):
    """Obtiene las fechas calculadas para un cliente en orden específico con cache"""
    # Convertir numpy.int64 a int de Python para evitar problemas de serialización
    client_id = int(client_id)
    
    if use_cache:
        cache_key = f"dates_{client_id}"
        cached_dates = _db_cache.get(cache_key, 60)
        if cached_dates is not None:
            return cached_dates
    
    conn = get_pooled_connection()
    try:
        dates = pd.read_sql_query('''
            SELECT
                cd.id,
                cd.client_id,
                cd.activity_id,
                COALESCE(ac.name, cd.activity_name) as activity_name,
                cd.date_position,
                cd.date,
                cd.is_custom
            FROM calculated_dates cd
            LEFT JOIN activities_catalog ac ON ac.id = cd.activity_id
            WHERE cd.client_id = ?
            ORDER BY
                CASE COALESCE(cd.activity_id, 999999)
                    WHEN 1 THEN 1
                    WHEN 2 THEN 2
                    WHEN 3 THEN 3
                    ELSE 4
                END,
                cd.date_position
        ''', conn, params=(client_id,))
        
        if use_cache:
            cache_key = f"dates_{client_id}"
            _db_cache.set(cache_key, dates, 60)
            
    except Exception as e:
        print(f"Error en get_calculated_dates: {e}")
        init_database()
        conn_retry = get_pooled_connection()
        try:
            dates = pd.read_sql_query('''
                SELECT
                    cd.id,
                    cd.client_id,
                    cd.activity_id,
                    COALESCE(ac.name, cd.activity_name) as activity_name,
                    cd.date_position,
                    cd.date,
                    cd.is_custom
                FROM calculated_dates cd
                LEFT JOIN activities_catalog ac ON ac.id = cd.activity_id
                WHERE cd.client_id = ?
                ORDER BY
                    CASE COALESCE(cd.activity_id, 999999)
                        WHEN 1 THEN 1
                        WHEN 2 THEN 2
                        WHEN 3 THEN 3
                        ELSE 4
                    END,
                    cd.date_position
            ''', conn_retry, params=(client_id,))
        except:
            dates = pd.DataFrame()
        finally:
            return_pooled_connection(conn_retry)
    finally:
        return_pooled_connection(conn)
    
    return dates

def get_multiple_calculated_dates(client_ids):
    """Obtiene fechas calculadas de múltiples clientes en una sola consulta"""
    if not client_ids:
        return pd.DataFrame()
    
    try:
        placeholders = ','.join(['?' for _ in client_ids])
        query = f'''
            SELECT
                cd.id,
                cd.client_id,
                cd.activity_id,
                COALESCE(ac.name, cd.activity_name) as activity_name,
                cd.date_position,
                cd.date,
                cd.is_custom
            FROM calculated_dates cd
            LEFT JOIN activities_catalog ac ON ac.id = cd.activity_id
            WHERE cd.client_id IN ({placeholders})
            ORDER BY cd.client_id,
                CASE COALESCE(cd.activity_id, 999999)
                    WHEN 1 THEN 1
                    WHEN 2 THEN 2
                    WHEN 3 THEN 3
                    ELSE 4
                END,
                cd.date_position
        '''
        return execute_query_df(query, params=client_ids, use_cache=True, cache_ttl=60)
    except Exception as e:
        print(f"Error obteniendo fechas batch: {e}")
        return pd.DataFrame()

def save_calculated_dates(client_id, activity_name, dates_list):
    """Guarda hasta 4 fechas para una actividad específica en posiciones secuenciales con invalidación de cache"""
    if not dates_list:
        print(f"No hay fechas para guardar para actividad {activity_name}")
        return
        
    conn = get_pooled_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id FROM activities_catalog WHERE name = ?", (activity_name,))
        row = cursor.fetchone()
        activity_id = row[0] if row else None

        if activity_id is None:
            cursor.execute("SELECT COALESCE(MAX(id), 3) + 1 FROM activities_catalog")
            activity_id = cursor.fetchone()[0]
            cursor.execute(
                "INSERT OR IGNORE INTO activities_catalog (id, name, is_active) VALUES (?, ?, 1)",
                (activity_id, activity_name)
            )

        # Usar transacción para operaciones atómicas
        cursor.execute("BEGIN TRANSACTION")
        
        # Eliminar fechas existentes para esta actividad
        cursor.execute('''
            DELETE FROM calculated_dates 
            WHERE client_id = ? AND (activity_id = ? OR activity_name = ?)
        ''', (client_id, activity_id, activity_name))
        
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
                    INSERT INTO calculated_dates (client_id, activity_id, activity_name, date_position, date)
                    VALUES (?, ?, ?, ?, ?)
                ''', (client_id, activity_id, activity_name, position, date_str))
        
        conn.commit()
        print(f"Guardadas {min(len(dates_list), 4)} fechas para {activity_name} en posiciones secuenciales")
        
        # Invalidar cache de fechas para este cliente
        _db_cache.invalidate_pattern(f"dates_{client_id}")
        
    except Exception as e:
        print(f"Error guardando fechas para {activity_name}: {e}")
        conn.rollback()
    finally:
        return_pooled_connection(conn)

def update_calculated_date(client_id, activity_name, date_position, new_date):
    """Actualiza una fecha específica con invalidación de cache"""
    conn = get_pooled_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id FROM activities_catalog WHERE name = ?", (activity_name,))
        row = cursor.fetchone()
        activity_id = row[0] if row else None

        cursor.execute('''
            UPDATE calculated_dates 
            SET date = ?, is_custom = 1
            WHERE client_id = ? AND date_position = ? AND (activity_id = ? OR activity_name = ?)
        ''', (new_date, client_id, date_position, activity_id, activity_name))
        conn.commit()
        
        # Invalidar cache de fechas para este cliente
        _db_cache.invalidate_pattern(f"dates_{client_id}")
        
    except Exception as e:
        print(f"Error actualizando fecha: {e}")
        conn.rollback()
    finally:
        return_pooled_connection(conn)

# === FUNCIONES DE COPIA DE FECHAS ===

def get_clients_with_matching_frequencies(source_client_id, use_cache=True):
    """Obtiene clientes que tienen las mismas frecuencias de actividades que el cliente de origen con cache"""
    if use_cache:
        cache_key = f"matching_frequencies_{source_client_id}"
        cached_result = _db_cache.get(cache_key, 180)
        if cached_result is not None:
            return cached_result
    
    conn = get_pooled_connection()
    try:
        query = '''
        SELECT DISTINCT c.id, c.name, c.codigo_ag, c.codigo_we, c.csr, c.vendedor
        FROM clients c
        WHERE c.id != ? 
        AND NOT EXISTS (
            -- Verificar que no haya actividades en origen que no estén en destino con la misma frecuencia
            SELECT 1 FROM client_activities ca_source
            WHERE ca_source.client_id = ?
            AND NOT EXISTS (
                SELECT 1 FROM client_activities ca_dest
                WHERE ca_dest.client_id = c.id
                AND ca_dest.activity_name = ca_source.activity_name
                AND ca_dest.frequency_template_id = ca_source.frequency_template_id
            )
        )
        AND NOT EXISTS (
            -- Verificar que no haya actividades en destino que no estén en origen con la misma frecuencia
            SELECT 1 FROM client_activities ca_dest
            WHERE ca_dest.client_id = c.id
            AND NOT EXISTS (
                SELECT 1 FROM client_activities ca_source
                WHERE ca_source.client_id = ?
                AND ca_source.activity_name = ca_dest.activity_name
                AND ca_source.frequency_template_id = ca_dest.frequency_template_id
            )
        )
        ORDER BY c.name
        '''
        df = pd.read_sql_query(query, conn, params=(source_client_id, source_client_id, source_client_id))
        
        if use_cache:
            cache_key = f"matching_frequencies_{source_client_id}"
            _db_cache.set(cache_key, df, 180)
        
        return df
    except Exception as e:
        print(f"Error obteniendo clientes compatibles: {e}")
        return pd.DataFrame()
    finally:
        return_pooled_connection(conn)

def copy_dates_to_clients(source_client_id, target_client_ids):
    """Copia las fechas del cliente origen a los clientes destino de manera optimizada con invalidación de cache"""
    if not target_client_ids:
        return True, "No hay clientes seleccionados"
    
    conn = get_pooled_connection()
    cursor = conn.cursor()
    
    try:
        # Usar transacción para operaciones atómicas
        cursor.execute("BEGIN TRANSACTION")
        
        # Obtener todas las fechas del cliente origen
        cursor.execute('''
            SELECT activity_id, activity_name, date_position, date, is_custom
            FROM calculated_dates 
            WHERE client_id = ?
            ORDER BY activity_name, date_position
        ''', (source_client_id,))
        
        source_dates = cursor.fetchall()
        
        if not source_dates:
            conn.rollback()
            return False, "El cliente origen no tiene fechas para copiar"
        
        # Preparar datos para inserción batch
        insert_data = []
        for target_client_id in target_client_ids:
            for activity_id, activity_name, date_position, date_value, is_custom in source_dates:
                insert_data.append((target_client_id, activity_id, activity_name, date_position, date_value, is_custom))
        
        # Eliminar fechas existentes de los clientes destino en una sola operación
        placeholders = ','.join(['?' for _ in target_client_ids])
        cursor.execute(f'''
            DELETE FROM calculated_dates 
            WHERE client_id IN ({placeholders})
        ''', target_client_ids)
        
        # Insertar nuevas fechas en batch
        cursor.executemany('''
            INSERT INTO calculated_dates (client_id, activity_id, activity_name, date_position, date, is_custom)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', insert_data)
        
        conn.commit()
        
        copied_count = len(source_dates)
        target_count = len(target_client_ids)
        
        # Invalidar cache de fechas para todos los clientes afectados
        for client_id in target_client_ids:
            _db_cache.invalidate_pattern(f"dates_{client_id}")
        
        return True, f"Se copiaron {copied_count} fechas a {target_count} cliente(s) exitosamente"
        
    except Exception as e:
        print(f"Error copiando fechas: {e}")
        conn.rollback()
        return False, f"Error al copiar fechas: {str(e)}"
    finally:
        return_pooled_connection(conn)

def get_client_activity_summary(client_id, use_cache=True):
    """Obtiene un resumen de las actividades y frecuencias de un cliente con cache"""
    if use_cache:
        cache_key = f"activity_summary_{client_id}"
        cached_summary = _db_cache.get(cache_key, 180)
        if cached_summary is not None:
            return cached_summary
    
    conn = get_pooled_connection()
    try:
        query = '''
        SELECT ca.activity_name, ft.name as frequency_name
        FROM client_activities ca
        JOIN frequency_templates ft ON ca.frequency_template_id = ft.id
        WHERE ca.client_id = ?
        ORDER BY 
            CASE ca.activity_name
                WHEN 'Fecha Envío OC' THEN 1
                WHEN 'Albaranado' THEN 2
                WHEN 'Fecha Entrega' THEN 3
                ELSE 4
            END
        '''
        df = pd.read_sql_query(query, conn, params=(client_id,))
        
        if use_cache:
            cache_key = f"activity_summary_{client_id}"
            _db_cache.set(cache_key, df, 180)
        
        return df
    except Exception as e:
        print(f"Error obteniendo resumen de actividades: {e}")
        return pd.DataFrame()
    finally:
        return_pooled_connection(conn)

# === FUNCIONES DE ANÁLISIS Y MONITOREO ===

def get_database_statistics():
    """Obtiene estadísticas de la base de datos para monitoreo"""
    conn = get_pooled_connection()
    cursor = conn.cursor()
    
    try:
        stats = {}
        
        # Contar registros por tabla
        tables = ['clients', 'frequency_templates', 'client_activities', 'calculated_dates']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[f"{table}_count"] = cursor.fetchone()[0]
        
        # Estadísticas del cache
        cache_stats = _db_cache.get_stats()
        stats.update(cache_stats)
        
        return stats
        
    except Exception as e:
        print(f"Error obteniendo estadísticas: {e}")
        return {}
    finally:
        return_pooled_connection(conn)

def test_cache_functionality():
    """Función para probar que el cache funciona correctamente"""
    print("=== PRUEBA DE CACHE ===")
    
    # Resetear estadísticas
    reset_cache_stats()
    
    # Hacer consulta inicial (debería ser MISS)
    print("1. Primera consulta (esperamos MISS):")
    clients1 = get_clients(use_cache=True)
    stats1 = get_cache_stats()
    print(f"   Estadísticas: {stats1}")
    
    # Hacer segunda consulta (debería ser HIT)
    print("2. Segunda consulta (esperamos HIT):")
    clients2 = get_clients(use_cache=True)
    stats2 = get_cache_stats()
    print(f"   Estadísticas: {stats2}")
    
    # Probar cache específico de cliente
    if not clients1.empty:
        client_id = clients1.iloc[0]['id']
        print(f"3. Consulta cliente ID {client_id} (esperamos MISS):")
        client1 = get_client_by_id(client_id, use_cache=True)
        stats3 = get_cache_stats()
        print(f"   Estadísticas: {stats3}")
        
        print(f"4. Segunda consulta cliente ID {client_id} (esperamos HIT):")
        client2 = get_client_by_id(client_id, use_cache=True)
        stats4 = get_cache_stats()
        print(f"   Estadísticas: {stats4}")
    
    # Mostrar claves del cache
    cache_keys = debug_cache_keys()
    print(f"5. Claves en cache: {cache_keys}")
    
    return get_cache_stats()

def optimize_database():
    """Ejecuta comandos de optimización de la base de datos"""
    conn = get_pooled_connection()
    cursor = conn.cursor()
    
    try:
        # Analizar tablas para actualizar estadísticas del optimizador
        cursor.execute("ANALYZE")
        
        # Vacuum para limpiar espacio no utilizado
        cursor.execute("VACUUM")
        
        print("Optimización de base de datos completada")
        return True
        
    except Exception as e:
        print(f"Error en optimización de BD: {e}")
        return False
    finally:
        return_pooled_connection(conn)

def save_calculated_dates_by_year(client_id, activity_name, dates_list, year):
    """Guarda fechas para una actividad específica de un año específico, preservando otros años"""
    if not dates_list:
        print(f"No hay fechas para guardar para actividad {activity_name} del año {year}")
        return
        
    # Convertir client_id para evitar problemas de serialización
    client_id = int(client_id)
    
    conn = get_pooled_connection()
    cursor = conn.cursor()
    
    try:
        # Usar transacción para operaciones atómicas
        cursor.execute("BEGIN TRANSACTION")
        
        # Eliminar solo fechas del año específico para esta actividad
        cursor.execute('''
            DELETE FROM calculated_dates 
            WHERE client_id = ? AND activity_name = ? 
            AND date LIKE ?
        ''', (client_id, activity_name, f"{year}-%"))
        
        # Obtener la máxima posición existente para esta actividad
        cursor.execute('''
            SELECT COALESCE(MAX(date_position), 0) 
            FROM calculated_dates 
            WHERE client_id = ? AND activity_name = ?
        ''', (client_id, activity_name))
        
        max_position = cursor.fetchone()[0]
        
        # Insertar nuevas fechas con posiciones que no conflicten
        for i, date_item in enumerate(dates_list):
            if date_item:
                position = max_position + i + 1  # Continuar desde la máxima posición existente
                
                # Manejo más robusto de diferentes tipos de fecha
                if hasattr(date_item, 'strftime'):
                    date_str = date_item.strftime('%Y-%m-%d')
                else:
                    date_str = str(date_item)
                
                # Verificar que la fecha sea del año correcto
                if date_str.startswith(f"{year}-"):
                    cursor.execute('''
                        INSERT INTO calculated_dates (client_id, activity_name, date_position, date)
                        VALUES (?, ?, ?, ?)
                    ''', (client_id, activity_name, position, date_str))
        
        conn.commit()
        # Contar fechas válidas guardadas de manera más simple
        dates_saved_count = len([d for d in dates_list if d])
        print(f"Guardadas {dates_saved_count} fechas para {activity_name} del año {year}")
        
        # Invalidar cache relacionado
        _db_cache.invalidate_pattern(f"dates_{client_id}")
        
    except Exception as e:
        conn.rollback()
        print(f"Error guardando fechas calculadas por año: {e}")
        raise e
    finally:
        return_pooled_connection(conn)
