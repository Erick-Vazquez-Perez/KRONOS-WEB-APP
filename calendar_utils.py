import pandas as pd
from datetime import datetime
from database import get_calculated_dates
from date_calculator import recalculate_client_dates

def create_client_calendar_table(client_id, show_full_year=True):
    """Crea la tabla de calendario para un cliente - puede mostrar año completo o solo algunas fechas"""
    dates_df = get_calculated_dates(client_id)
    
    if dates_df.empty:
        recalculate_client_dates(client_id)
        dates_df = get_calculated_dates(client_id)
    
    if dates_df.empty:
        return pd.DataFrame()
    
    if 'activity_name' not in dates_df.columns:
        return pd.DataFrame()
    
    activities = dates_df['activity_name'].unique()
    
    if len(activities) == 0:
        return pd.DataFrame()
    
    if show_full_year:
        return create_full_year_calendar_table(dates_df, activities)
    else:
        return create_compact_calendar_table(dates_df, activities)

def create_full_year_calendar_table(dates_df, activities):
    """Crea una tabla de calendario completa organizada por meses"""
    # Mapeo de meses en español
    month_names_spanish = {
        1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr', 5: 'May', 6: 'Jun',
        7: 'Jul', 8: 'Ago', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'
    }
    
    # Agrupar fechas por actividad y mes
    table_data = []
    
    # Obtener todos los meses con fechas
    dates_df['month'] = pd.to_datetime(dates_df['date']).dt.to_period('M')
    months = sorted(dates_df['month'].unique())
    
    for activity in activities:
        activity_dates = dates_df[dates_df['activity_name'] == activity].sort_values('date')
        
        row = {"Actividad": activity}
        
        # Crear columnas para cada mes
        for month in months:
            month_str = str(month)  # Ej: "2025-01"
            month_name = month_names_spanish[month.month]  # Usar nombres en español
            
            # Obtener fechas de esta actividad en este mes
            month_dates = activity_dates[activity_dates['month'] == month]
            
            if not month_dates.empty:
                # Formatear fechas del mes
                formatted_dates = []
                for _, date_row in month_dates.iterrows():
                    try:
                        date_obj = datetime.strptime(date_row['date'], '%Y-%m-%d')
                        formatted_dates.append(date_obj.strftime('%d'))
                    except:
                        continue
                
                # Unir fechas con comas si hay múltiples en el mes
                row[month_name] = ", ".join(formatted_dates) if formatted_dates else ""
            else:
                row[month_name] = ""
        
        table_data.append(row)
    
    df = pd.DataFrame(table_data)
    
    # Reordenar columnas: Actividad + meses en orden
    month_columns = [month_names_spanish[month.month] for month in months]
    column_order = ["Actividad"] + month_columns
    df = df.reindex(columns=column_order, fill_value="")
    
    return df

def create_compact_calendar_table(dates_df, activities):
    """Crea una tabla compacta con las primeras fechas de cada actividad"""
    table_data = []
    
    for activity in activities:
        activity_dates = dates_df[dates_df['activity_name'] == activity].sort_values('date_position')
        
        row = {"Actividad": activity}
        
        # Mostrar hasta 12 fechas (una por mes aproximadamente)
        for i in range(1, 13):
            matching_row = activity_dates[activity_dates['date_position'] == i]
            
            if not matching_row.empty:
                try:
                    date_str = matching_row.iloc[0]['date']
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    formatted_date = date_obj.strftime('%d-%b')
                    row[f"Fecha {i}"] = formatted_date
                except:
                    row[f"Fecha {i}"] = ""
            else:
                row[f"Fecha {i}"] = ""
        
        table_data.append(row)
    
    df = pd.DataFrame(table_data)
    
    # Reordenar columnas
    date_columns = [f"Fecha {i}" for i in range(1, 13)]
    column_order = ["Actividad"] + date_columns
    df = df.reindex(columns=column_order, fill_value="")
    
    return df

def create_monthly_calendar_view(client_id, selected_month=None):
    """Crea una vista de calendario específica para un mes"""
    dates_df = get_calculated_dates(client_id)
    
    if dates_df.empty:
        return pd.DataFrame()
    
    if selected_month is None:
        selected_month = datetime.now().strftime('%Y-%m')
    
    # Filtrar fechas del mes seleccionado
    dates_df['date_obj'] = pd.to_datetime(dates_df['date'])
    dates_df['month_key'] = dates_df['date_obj'].dt.strftime('%Y-%m')
    month_dates = dates_df[dates_df['month_key'] == selected_month]
    
    if month_dates.empty:
        return pd.DataFrame({"Mensaje": ["No hay fechas programadas para este mes"]})
    
    # Crear tabla por actividad
    activities = month_dates['activity_name'].unique()
    table_data = []
    
    for activity in activities:
        activity_dates = month_dates[month_dates['activity_name'] == activity].sort_values('date')
        
        dates_list = []
        for _, date_row in activity_dates.iterrows():
            try:
                date_obj = datetime.strptime(date_row['date'], '%Y-%m-%d')
                dates_list.append(date_obj.strftime('%d-%b'))
            except:
                continue
        
        row = {
            "Actividad": activity,
            "Fechas del Mes": ", ".join(dates_list) if dates_list else "Sin fechas"
        }
        table_data.append(row)
    
    return pd.DataFrame(table_data)

def get_client_year_summary(client_id):
    """Obtiene un resumen del año para un cliente"""
    dates_df = get_calculated_dates(client_id)
    
    if dates_df.empty:
        return {
            "total_fechas": 0,
            "actividades": 0,
            "meses_con_actividad": 0,
            "proxima_fecha": None
        }
    
    # Calcular estadísticas
    total_fechas = len(dates_df)
    actividades = len(dates_df['activity_name'].unique())
    
    # Contar meses con actividad
    dates_df['month'] = pd.to_datetime(dates_df['date']).dt.to_period('M')
    meses_con_actividad = len(dates_df['month'].unique())
    
    # Encontrar próxima fecha
    today = datetime.now().date()
    future_dates = dates_df[pd.to_datetime(dates_df['date']).dt.date >= today]
    
    proxima_fecha = None
    if not future_dates.empty:
        next_date = future_dates.sort_values('date').iloc[0]
        proxima_fecha = {
            "fecha": next_date['date'],
            "actividad": next_date['activity_name']
        }
    
    return {
        "total_fechas": total_fechas,
        "actividades": actividades,
        "meses_con_actividad": meses_con_actividad,
        "proxima_fecha": proxima_fecha
    }

def format_frequency_description(frequency_type, frequency_config):
    """Formatea la descripción de una frecuencia para mostrar de manera legible"""
    try:
        import json
        config = json.loads(frequency_config)
        
        if frequency_type == "nth_weekday":
            weekday_names = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
            weekday = weekday_names[config.get('weekday', 0)]
            weeks = config.get('weeks', [])
            weeks_text = ", ".join([f"{w}°" for w in weeks])
            return f"{weeks_text} {weekday} del mes"
        
        elif frequency_type == "specific_days":
            days = config.get('days', [])
            days_text = ", ".join([str(d) for d in days])
            return f"Días {days_text} del mes"
        
        return "Configuración personalizada"
    
    except Exception as e:
        print(f"Error formateando descripción de frecuencia: {e}")
        return "Configuración inválida"

def get_available_months(client_id):
    """Obtiene la lista de meses que tienen fechas programadas para un cliente"""
    dates_df = get_calculated_dates(client_id)
    
    if dates_df.empty:
        return []
    
    try:
        dates_df['date_obj'] = pd.to_datetime(dates_df['date'])
        dates_df['month_key'] = dates_df['date_obj'].dt.strftime('%Y-%m')
        dates_df['month_name'] = dates_df['date_obj'].dt.strftime('%B %Y')
        
        months = dates_df[['month_key', 'month_name']].drop_duplicates().sort_values('month_key')
        return months.to_dict('records')
    except:
        return []

def get_available_years(client_id):
    """Obtiene la lista de años que tienen fechas programadas para un cliente"""
    dates_df = get_calculated_dates(client_id)
    
    if dates_df.empty:
        return []
    
    try:
        dates_df['date_obj'] = pd.to_datetime(dates_df['date'])
        years = sorted(dates_df['date_obj'].dt.year.unique())
        return years
    except:
        return []

def create_client_calendar_table_by_year(client_id, year):
    """Crea la tabla de calendario para un cliente filtrada por año específico"""
    dates_df = get_calculated_dates(client_id)
    
    if dates_df.empty:
        recalculate_client_dates(client_id)
        dates_df = get_calculated_dates(client_id)
    
    if dates_df.empty:
        return pd.DataFrame()
    
    # Filtrar por año
    try:
        dates_df['date_obj'] = pd.to_datetime(dates_df['date'])
        dates_df = dates_df[dates_df['date_obj'].dt.year == year]
        
        if dates_df.empty:
            return pd.DataFrame()
            
        if 'activity_name' not in dates_df.columns:
            return pd.DataFrame()
        
        activities = dates_df['activity_name'].unique()
        
        if len(activities) == 0:
            return pd.DataFrame()
        
        return create_full_year_calendar_table(dates_df, activities)
        
    except Exception as e:
        print(f"Error filtrando calendario por año {year}: {e}")
        return pd.DataFrame()

def get_client_year_summary_by_year(client_id, year):
    """Obtiene un resumen del año específico para un cliente"""
    dates_df = get_calculated_dates(client_id)
    
    if dates_df.empty:
        return {
            "total_fechas": 0,
            "actividades": 0,
            "meses_con_actividad": 0,
            "proxima_fecha": None
        }
    
    # Filtrar por año
    try:
        dates_df['date_obj'] = pd.to_datetime(dates_df['date'])
        dates_df = dates_df[dates_df['date_obj'].dt.year == year]
        
        if dates_df.empty:
            return {
                "total_fechas": 0,
                "actividades": 0,
                "meses_con_actividad": 0,
                "proxima_fecha": None
            }
        
        # Calcular estadísticas
        total_fechas = len(dates_df)
        actividades = len(dates_df['activity_name'].unique())
        
        # Contar meses con actividad
        dates_df['month'] = dates_df['date_obj'].dt.to_period('M')
        meses_con_actividad = len(dates_df['month'].unique())
        
        # Encontrar próxima fecha del año especificado
        today = datetime.now().date()
        future_dates = dates_df[dates_df['date_obj'].dt.date >= today]
        
        proxima_fecha = None
        if not future_dates.empty:
            next_date = future_dates.sort_values('date').iloc[0]
            proxima_fecha = {
                "fecha": next_date['date'],
                "actividad": next_date['activity_name']
            }
        
        return {
            "total_fechas": total_fechas,
            "actividades": actividades,
            "meses_con_actividad": meses_con_actividad,
            "proxima_fecha": proxima_fecha
        }
        
    except Exception as e:
        print(f"Error obteniendo resumen del año {year}: {e}")
        return {
            "total_fechas": 0,
            "actividades": 0,
            "meses_con_actividad": 0,
            "proxima_fecha": None
        }