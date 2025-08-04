"""
Módulo para gestión de días festivos y anomalías de calendario
"""
from datetime import datetime, date, timedelta
import calendar
import pandas as pd
from database import get_db_connection

# Configuración de días festivos por año
HOLIDAYS = {
    2024: [
        ("2024-01-01", "Año Nuevo"),
        ("2024-03-29", "Viernes Santo"),
        ("2024-05-01", "Día del Trabajo"),
        ("2024-09-16", "Independencia"),
        ("2024-11-20", "Revolución Mexicana"),
        ("2024-12-25", "Navidad"),
    ],
    2025: [
        ("2025-01-01", "Año Nuevo"),
        ("2025-02-03", "Día de la Constitución"),
        ("2025-03-17", "Natalicio de Benito Juárez"),
        ("2025-04-18", "Viernes Santo"),
        ("2025-05-01", "Día del Trabajo"),
        ("2025-09-15", "Grito de Independencia"),
        ("2025-09-16", "Independencia"),
        ("2025-11-17", "Revolución Mexicana"),
        ("2025-12-25", "Navidad"),
    ]
}

def get_holidays_for_month(year, month):
    """Obtiene los días festivos para un mes específico"""
    if year not in HOLIDAYS:
        return []
    
    month_holidays = []
    for holiday_date, description in HOLIDAYS[year]:
        holiday_datetime = datetime.strptime(holiday_date, '%Y-%m-%d').date()
        if holiday_datetime.year == year and holiday_datetime.month == month:
            month_holidays.append((holiday_datetime, description))
    
    return month_holidays

def get_incomplete_weeks_info(year, month):
    """
    Analiza las semanas incompletas del mes y qué días de la semana se ven afectados.
    Se considera que un día puede verse afectado si aparece en una semana incompleta,
    ya que esto puede reducir las oportunidades de cumplir con frecuencias semanales.
    Solo considera días hábiles (lunes a viernes).
    """
    # Primer y último día del mes
    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    
    # Obtener día de la semana del primer día (0=Lunes, 6=Domingo)
    first_weekday = first_day.weekday()
    last_weekday = last_day.weekday()
    
    # Días de la semana en español (solo días hábiles)
    weekdays = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
    
    incomplete_weeks_info = {
        'first_week_missing': [],
        'last_week_missing': [],
        'first_week_present': [],
        'last_week_present': [],
        'affected_weekdays': []
    }
    
    # Primera semana incompleta
    if first_weekday > 0:  # Si no empieza en lunes
        # Días hábiles que faltan en la primera semana
        for i in range(min(first_weekday, 5)):  # Solo hasta viernes (índice 4)
            incomplete_weeks_info['first_week_missing'].append(weekdays[i])
        
        # Días hábiles que SÍ están presentes en la primera semana
        for i in range(first_weekday, min(7, 5)):  # Solo días hábiles
            if i < 5:  # Solo hasta viernes
                incomplete_weeks_info['first_week_present'].append(weekdays[i])
    
    # Última semana incompleta
    if last_weekday < 6:  # Si no termina en domingo
        # Días hábiles que SÍ están presentes en la última semana
        for i in range(0, min(last_weekday + 1, 5)):  # Solo hasta viernes
            incomplete_weeks_info['last_week_present'].append(weekdays[i])
        
        # Días hábiles que faltan en la última semana
        for i in range(min(last_weekday + 1, 5), 5):  # Solo días hábiles faltantes
            incomplete_weeks_info['last_week_missing'].append(weekdays[i])
    
    # Los días afectados son aquellos que aparecen en semanas incompletas
    # porque pueden tener menos oportunidades de cumplir frecuencias
    affected_days = set()
    
    # Si hay primera semana incompleta, los días hábiles presentes pueden verse afectados
    if incomplete_weeks_info['first_week_present']:
        affected_days.update(incomplete_weeks_info['first_week_present'])
    
    # Si hay última semana incompleta, los días hábiles presentes pueden verse afectados  
    if incomplete_weeks_info['last_week_present']:
        affected_days.update(incomplete_weeks_info['last_week_present'])
    
    incomplete_weeks_info['affected_weekdays'] = list(affected_days)
    
    return incomplete_weeks_info

def get_weekday_from_frequency_name(frequency_name):
    """
    Extrae el día de la semana de un nombre de frecuencia.
    Solo retorna días hábiles (lunes a viernes).
    """
    frequency_lower = frequency_name.lower()
    
    if 'lunes' in frequency_lower:
        return 'Lunes'
    elif 'martes' in frequency_lower:
        return 'Martes'
    elif 'miércoles' in frequency_lower or 'miercoles' in frequency_lower:
        return 'Miércoles'
    elif 'jueves' in frequency_lower:
        return 'Jueves'
    elif 'viernes' in frequency_lower:
        return 'Viernes'
    # No incluimos sábado ni domingo ya que solo trabajamos días hábiles
    
    return None

def get_comprehensive_anomalies(year=None, month=None):
    """
    Obtiene anomalías completas incluyendo:
    1. Fechas de albaranado posteriores a entrega
    2. Clientes afectados por semanas incompletas
    3. Clientes con fechas de albaranado en días festivos
    """
    if year is None:
        year = datetime.now().year
    if month is None:
        month = datetime.now().month
    
    conn = get_db_connection()
    
    # 1. Anomalías tradicionales (albaranado > entrega)
    delivery_anomalies = get_delivery_anomalies_detailed(conn, year, month)
    
    # 2. Anomalías por semanas incompletas
    incomplete_week_anomalies = get_incomplete_week_anomalies(conn, year, month)
    
    # 3. Anomalías por días festivos
    holiday_anomalies = get_holiday_anomalies(conn, year, month)
    
    conn.close()
    
    return {
        'delivery_anomalies': delivery_anomalies,
        'incomplete_week_anomalies': incomplete_week_anomalies,
        'holiday_anomalies': holiday_anomalies,
        'total_affected_clients': len(set(
            list(incomplete_week_anomalies.get('client_id', [])) +
            list(holiday_anomalies.get('client_id', []))
        ))
    }

def get_delivery_anomalies():
    """Función de compatibilidad con el código existente"""
    current_date = datetime.now()
    anomalies = get_comprehensive_anomalies(current_date.year, current_date.month)
    return anomalies['delivery_anomalies']

def get_delivery_anomalies_detailed(conn, year, month):
    """Obtiene anomalías de entrega detalladas para un mes específico"""
    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    
    query = """
    SELECT 
        c.id as client_id,
        c.name, 
        c.codigo_ag, 
        c.codigo_we, 
        c.csr, 
        c.vendedor,
        c.tipo_cliente,
        c.region,
        alb.date as fecha_albaranado,
        ent.date as fecha_entrega,
        alb.date_position as pos_albaranado,
        ent.date_position as pos_entrega
    FROM clients c
    JOIN calculated_dates alb ON c.id = alb.client_id AND alb.activity_name = 'Albaranado'
    JOIN calculated_dates ent ON c.id = ent.client_id AND ent.activity_name = 'Fecha Entrega' 
                                AND alb.date_position = ent.date_position
    WHERE date(alb.date) > date(ent.date)
    AND (
        (date(alb.date) >= ? AND date(alb.date) <= ?) OR
        (date(ent.date) >= ? AND date(ent.date) <= ?)
    )
    ORDER BY c.name, alb.date_position
    """
    
    df = pd.read_sql_query(query, conn, params=(
        first_day.strftime('%Y-%m-%d'), last_day.strftime('%Y-%m-%d'),
        first_day.strftime('%Y-%m-%d'), last_day.strftime('%Y-%m-%d')
    ))
    
    return df

def get_incomplete_week_anomalies(conn, year, month):
    """
    Obtiene clientes con albaranado que se verán afectados por semanas incompletas
    """
    incomplete_weeks = get_incomplete_weeks_info(year, month)
    affected_weekdays = incomplete_weeks['affected_weekdays']
    
    if not affected_weekdays:
        return pd.DataFrame()
    
    # Obtener clientes con actividad Albaranado y sus frecuencias
    query = """
    SELECT DISTINCT
        c.id as client_id,
        c.name,
        c.codigo_ag,
        c.codigo_we,
        c.csr,
        c.vendedor,
        c.tipo_cliente,
        c.region,
        ft.name as frequency_name,
        cd.date as fecha_albaranado,
        cd.date_position
    FROM clients c
    JOIN client_activities ca ON c.id = ca.client_id AND ca.activity_name = 'Albaranado'
    JOIN frequency_templates ft ON ca.frequency_template_id = ft.id
    JOIN calculated_dates cd ON c.id = cd.client_id AND cd.activity_name = 'Albaranado'
    WHERE date(cd.date) >= ? AND date(cd.date) <= ?
    ORDER BY c.name, cd.date_position
    """
    
    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    
    df = pd.read_sql_query(query, conn, params=(
        first_day.strftime('%Y-%m-%d'), 
        last_day.strftime('%Y-%m-%d')
    ))
    
    # Filtrar solo los clientes cuya frecuencia coincida con días afectados
    if not df.empty:
        df['weekday_from_frequency'] = df['frequency_name'].apply(get_weekday_from_frequency_name)
        df = df[df['weekday_from_frequency'].isin(affected_weekdays)]
        df['reason'] = df['weekday_from_frequency'].apply(
            lambda x: f"Semana incompleta afecta {x}"
        )
    
    return df

def get_holiday_anomalies(conn, year, month):
    """
    Obtiene clientes con fechas de albaranado que caen en días festivos
    """
    holidays = get_holidays_for_month(year, month)
    
    if not holidays:
        return pd.DataFrame()
    
    # Crear lista de fechas festivas
    holiday_dates = [holiday[0].strftime('%Y-%m-%d') for holiday in holidays]
    holiday_descriptions = {holiday[0].strftime('%Y-%m-%d'): holiday[1] for holiday in holidays}
    
    # Placeholders para la query
    placeholders = ','.join(['?' for _ in holiday_dates])
    
    query = f"""
    SELECT DISTINCT
        c.id as client_id,
        c.name,
        c.codigo_ag,
        c.codigo_we,
        c.csr,
        c.vendedor,
        c.tipo_cliente,
        c.region,
        cd.date as fecha_albaranado,
        cd.date_position
    FROM clients c
    JOIN calculated_dates cd ON c.id = cd.client_id AND cd.activity_name = 'Albaranado'
    WHERE date(cd.date) IN ({placeholders})
    ORDER BY c.name, cd.date_position
    """
    
    df = pd.read_sql_query(query, conn, params=holiday_dates)
    
    # Agregar descripción del festivo
    if not df.empty:
        df['holiday_description'] = df['fecha_albaranado'].apply(
            lambda x: holiday_descriptions.get(x, 'Día festivo')
        )
        df['reason'] = df['holiday_description'].apply(
            lambda x: f"Cae en festivo: {x}"
        )
    
    return df
