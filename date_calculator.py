import json
import calendar
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from database import get_client_activities, save_calculated_dates, create_default_activities

def get_nth_weekday_of_month(year, month, weekday, n):
    """Obtiene el n-ésimo día de la semana de un mes"""
    first_day = datetime(year, month, 1)
    first_weekday = first_day.weekday()
    
    days_ahead = weekday - first_weekday
    if days_ahead < 0:
        days_ahead += 7
    
    first_occurrence = first_day + timedelta(days=days_ahead)
    nth_occurrence = first_occurrence + timedelta(weeks=n-1)
    
    if nth_occurrence.month != month:
        return None
    
    return nth_occurrence.date()

def calculate_dates_for_frequency(frequency_type, frequency_config, start_date=None, full_year=True):
    """Calcula las fechas basadas en la frecuencia especificada para todo el año"""
    dates = []
    
    # Si no se especifica fecha de inicio, usar enero del año actual
    if start_date is None:
        current_year = datetime.now().year
        start_date = datetime(current_year, 1, 1).date()
    else:
        current_year = start_date.year
    
    print(f"Calculando fechas para todo el año {current_year}: tipo={frequency_type}, config={frequency_config}")
    
    # Calcular para todos los meses del año (enero a diciembre)
    for month in range(1, 13):  # Meses 1-12
        try:
            if frequency_type == "nth_weekday":
                config = json.loads(frequency_config)
                weekday = config["weekday"]  # 0=lunes, 1=martes, etc.
                weeks = config["weeks"]
                
                print(f"Calculando nth_weekday para {current_year}-{month:02d}: weekday={weekday}, weeks={weeks}")
                
                for week in weeks:
                    date = get_nth_weekday_of_month(current_year, month, weekday, week)
                    if date:
                        dates.append(date)
                        print(f"Fecha agregada: {date}")
            
            elif frequency_type == "specific_days":
                config = json.loads(frequency_config)
                days = config["days"]
                
                print(f"Calculando specific_days para {current_year}-{month:02d}: days={days}")
                
                for day in days:
                    try:
                        date = datetime(current_year, month, day).date()
                        dates.append(date)
                        print(f"Fecha agregada: {date}")
                    except ValueError:
                        # Si el día no existe en este mes, tomar el último día del mes
                        if day > 28:
                            last_day = calendar.monthrange(current_year, month)[1]
                            date = datetime(current_year, month, last_day).date()
                            dates.append(date)
                            print(f"Fecha ajustada agregada: {date}")
            
        except Exception as e:
            print(f"Error procesando mes {current_year}-{month:02d}: {e}")
            continue
    
    sorted_dates = sorted(dates)
    print(f"Total de fechas calculadas para el año {current_year}: {len(sorted_dates)}")
    print(f"Primeras 5 fechas: {sorted_dates[:5] if sorted_dates else 'Ninguna'}")
    print(f"Últimas 5 fechas: {sorted_dates[-5:] if len(sorted_dates) >= 5 else sorted_dates}")
    
    return sorted_dates

def recalculate_client_dates(client_id):
    """Recalcula todas las fechas para un cliente para todo el año"""
    activities = get_client_activities(client_id)
    
    if activities.empty:
        # Si no hay actividades, crear las predeterminadas
        create_default_activities(client_id)
        activities = get_client_activities(client_id)
    
    if activities.empty:
        print(f"No se pudieron crear actividades para cliente {client_id}")
        return
    
    # Calcular fechas para todo el año actual
    current_year = datetime.now().year
    start_date = datetime(current_year, 1, 1).date()
    
    print(f"Recalculando fechas para cliente {client_id} - Año completo {current_year}")
    
    for _, activity in activities.iterrows():
        try:
            # Calcular todas las fechas del año
            all_dates = calculate_dates_for_frequency(
                activity['frequency_type'], 
                activity['frequency_config'], 
                start_date,
                full_year=True
            )
            
            if all_dates:
                # Guardar todas las fechas del año
                save_calculated_dates_full_year(client_id, activity['activity_name'], all_dates)
                print(f"Guardadas {len(all_dates)} fechas para {activity['activity_name']} (año completo)")
            else:
                print(f"No se generaron fechas para {activity['activity_name']}")
                
        except Exception as e:
            print(f"Error calculando fechas para {activity['activity_name']}: {e}")

def save_calculated_dates_full_year(client_id, activity_name, dates_list):
    """Guarda todas las fechas del año para una actividad específica"""
    if not dates_list:
        print(f"No hay fechas para guardar para actividad {activity_name}")
        return
    
    from database import save_calculated_dates
    
    # Organizar fechas por meses para mejor visualización
    dates_by_month = {}
    
    for date in dates_list:
        month_key = date.strftime('%Y-%m')
        if month_key not in dates_by_month:
            dates_by_month[month_key] = []
        dates_by_month[month_key].append(date)
    
    # Guardar fechas usando posiciones secuenciales dentro de cada grupo
    all_positions = []
    position = 1
    
    for month_key in sorted(dates_by_month.keys()):
        month_dates = sorted(dates_by_month[month_key])
        for date in month_dates:
            all_positions.append((position, date))
            position += 1
    
    # Guardar usando el método existente pero con todas las fechas
    dates_to_save = [item[1] for item in all_positions]
    
    # Guardar en lotes para no sobrecargar la base de datos
    batch_size = 50  # Máximo 50 fechas por vez
    for i in range(0, len(dates_to_save), batch_size):
        batch = dates_to_save[i:i + batch_size]
        save_calculated_dates_batch(client_id, activity_name, batch, i + 1)
    
    print(f"Guardadas {len(dates_to_save)} fechas para {activity_name} (año completo) en {len(dates_by_month)} meses")

def save_calculated_dates_batch(client_id, activity_name, dates_batch, start_position):
    """Guarda un lote de fechas con posiciones específicas"""
    import sqlite3
    from datetime import datetime
    
    if not dates_batch:
        return
        
    conn = sqlite3.connect('client_calendar.db')
    cursor = conn.cursor()
    
    try:
        # Si es el primer lote, limpiar fechas existentes
        if start_position == 1:
            cursor.execute('''
                DELETE FROM calculated_dates 
                WHERE client_id = ? AND activity_name = ?
            ''', (client_id, activity_name))
        
        # Insertar fechas del lote
        for i, date in enumerate(dates_batch):
            position = start_position + i
            date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)
            
            cursor.execute('''
                INSERT INTO calculated_dates (client_id, activity_name, date_position, date)
                VALUES (?, ?, ?, ?)
            ''', (client_id, activity_name, position, date_str))
        
        conn.commit()
        print(f"Lote guardado: posiciones {start_position} a {start_position + len(dates_batch) - 1}")
        
    except Exception as e:
        print(f"Error guardando lote de fechas: {e}")
        conn.rollback()
    finally:
        conn.close()