"""
Módulo para generar fechas de múltiples años para clientes
Permite generar calendarios para diferentes años y mostrar preview antes de confirmar
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
import json

try:
    from database import (
        get_clients, get_client_by_id, get_client_activities, 
        save_calculated_dates, get_calculated_dates
    )
    from date_calculator import calculate_dates_for_frequency
    from calendar_utils import create_client_calendar_table, get_client_year_summary
    from client_constants import get_tipos_cliente, get_regiones, get_paises
    from auth_system import require_permission, is_read_only_mode, get_user_country_filter, has_country_filter
    from werfen_styles import get_metric_card_html, get_button_html
except ImportError as e:
    st.error(f"Error importando módulos requeridos: {e}")
    st.stop()

def show_multi_year_generator():
    """Muestra la interfaz principal del generador de fechas múltiples"""
    
    # Verificar permisos - Solo administradores pueden generar fechas
    require_permission('modify_clients', 
                      "No tienes permisos para generar fechas. Se requiere rol de administrador.")
    
    st.header("Generador de Fechas para Múltiples Años")
    st.write("Genera calendarios para diferentes años y clientes con preview antes de confirmar")
    
    # Inicializar estados de sesión
    initialize_generator_session_state()
    
    # Contenedor principal con tabs
    tab1, tab2, tab3 = st.tabs(["Configurar Generación", "Preview de Fechas", "Historial de Generaciones"])
    
    with tab1:
        show_generation_config_tab()
    
    with tab2:
        show_preview_tab()
    
    with tab3:
        show_history_tab()

def initialize_generator_session_state():
    """Inicializa los estados de sesión necesarios para el generador"""
    if 'generator_config' not in st.session_state:
        st.session_state.generator_config = {
            'target_years': [],
            'selection_type': 'specific',
            'selected_clients': [],
            'selected_type': None,
            'selected_region': None,
            'selected_country': None,
            'preview_data': None,
            'generation_complete': False
        }
    
    if 'generator_preview_ready' not in st.session_state:
        st.session_state.generator_preview_ready = False
    
    if 'generator_history' not in st.session_state:
        st.session_state.generator_history = []

def show_generation_config_tab():
    """Muestra la pestaña de configuración de la generación"""
    st.subheader("Configuración de Generación")
    
    # Sección 1: Selección de años
    st.markdown("### 1. Seleccionar Años")
    show_year_selector()
    
    st.divider()
    
    # Sección 2: Selección de clientes
    st.markdown("### 2. Seleccionar Clientes")
    show_client_selector()
    
    st.divider()
    
    # Sección 3: Resumen y generación de preview
    st.markdown("### 3. Generar Preview")
    show_generation_summary()

def show_year_selector():
    """Muestra el selector de años para generar fechas"""
    current_year = datetime.now().year
    
    # Rango de años disponibles (5 años hacia atrás y 10 hacia adelante)
    year_options = list(range(current_year - 5, current_year + 11))
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_years = st.multiselect(
            "Selecciona los años para generar calendarios:",
            options=year_options,
            default=[current_year + 1] if current_year + 1 in year_options else [current_year],
            help="Puedes seleccionar múltiples años. Se generarán calendarios completos para cada año."
        )

    
    # Actualizar estado
    st.session_state.generator_config['target_years'] = selected_years
    
    if selected_years:
        st.success(f"Años seleccionados: {', '.join(map(str, sorted(selected_years)))}")
    else:
        st.warning("Selecciona al menos un año para continuar")

def show_client_selector():
    """Muestra las opciones para seleccionar clientes"""
    
    # Tipo de selección
    selection_type = st.radio(
        "Tipo de selección:",
        options=['specific', 'type', 'region', 'country'],
        format_func=lambda x: {
            'specific': 'Clientes específicos',
            'type': 'Por tipo de cliente',
            'region': 'Por región',
            'country': 'Por país'
        }[x],
        horizontal=True,
        key="selection_type_radio"
    )
    
    st.session_state.generator_config['selection_type'] = selection_type
    
    # Obtener clientes disponibles
    try:
        clients_df = get_clients(use_cache=True)
        st.write(f"Debug: Se obtuvieron {len(clients_df)} clientes de la base de datos")  # Habilitado temporalmente para debug
        
        if clients_df.empty:
            st.error("No hay clientes disponibles en la base de datos")
            
            with st.expander("Información de troubleshooting"):
                st.info("Posibles causas y soluciones:")
                st.write("- **Verificar base de datos**: Asegúrate de que la aplicación esté conectada a la base de datos correcta")
                st.write("- **Verificar datos**: Confirma que existan clientes en el sistema")
                st.write("- **Verificar permisos**: El usuario debe tener permisos para ver clientes")
                st.write("- **Reiniciar aplicación**: A veces ayuda recargar la página")
                
                # Intentar mostrar información adicional de la base de datos
                try:
                    from database import get_pooled_connection, return_pooled_connection
                    conn = get_pooled_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM clients")
                    count = cursor.fetchone()[0]
                    st.write(f"Total registros en tabla clients: {count}")
                    
                    if count > 0:
                        st.warning("Existen clientes en la base de datos, pero la función get_clients() no los está retornando. Esto podría ser un problema de permisos o filtros.")
                    else:
                        st.warning("No hay registros en la tabla clients. Necesitas agregar clientes primero.")
                    
                    return_pooled_connection(conn)
                except Exception as db_e:
                    st.write(f"Error verificando base de datos: {db_e}")
            
            return
        
        # Aplicar filtro de país del usuario si existe
        if has_country_filter():
            user_country = get_user_country_filter()
            original_count = len(clients_df)
            clients_df = clients_df[clients_df['pais'] == user_country]
            # st.write(f"Debug: Filtro de país aplicado. Clientes antes: {original_count}, después: {len(clients_df)}")
            
            if clients_df.empty:
                st.warning(f"No hay clientes disponibles para el país: {user_country}")
                return
        
    except Exception as e:
        st.error(f"Error obteniendo clientes: {e}")
        st.write("Detalles del error para debug:")
        st.code(str(e))
        st.write("Tipo de error:", type(e).__name__)
        
        # Intentar una consulta directa como fallback
        try:
            st.write("Intentando consulta directa...")
            from database import get_pooled_connection, return_pooled_connection
            conn = get_pooled_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM clients")
            count = cursor.fetchone()[0]
            st.write(f"Consulta directa exitosa: {count} clientes en la base de datos")
            return_pooled_connection(conn)
        except Exception as direct_e:
            st.write(f"Error en consulta directa: {direct_e}")
        
        return
    
    # Mostrar selector según el tipo elegido
    if selection_type == 'specific':
        show_specific_clients_selector(clients_df)
    elif selection_type == 'type':
        show_type_selector(clients_df)
    elif selection_type == 'region':
        show_region_selector(clients_df)
    elif selection_type == 'country':
        show_country_selector(clients_df)

def show_specific_clients_selector(clients_df):
    """Selector para clientes específicos"""
    
    # Filtro de búsqueda
    search_term = st.text_input(
        "Buscar clientes:",
        placeholder="Escribe el nombre o código del cliente...",
        key="client_search"
    )
    
    # Filtrar clientes si hay término de búsqueda
    if search_term:
        mask = (
            clients_df['name'].str.contains(search_term, case=False, na=False) |
            clients_df['codigo_ag'].str.contains(search_term, case=False, na=False) |
            clients_df['codigo_we'].str.contains(search_term, case=False, na=False)
        )
        filtered_clients = clients_df[mask]
    else:
        filtered_clients = clients_df
    
    # Aplicar filtro de país si el usuario tiene restricción
    if has_country_filter():
        user_country = get_user_country_filter()
        filtered_clients = filtered_clients[filtered_clients['pais'] == user_country]
    
    if filtered_clients.empty:
        st.warning("No se encontraron clientes con el criterio de búsqueda")
        return
    
    # Selector múltiple de clientes
    client_options = []
    client_mapping = {}
    
    for _, client in filtered_clients.iterrows():
        display_name = f"{client['name']} ({client['codigo_ag']}) - {client['pais']}"
        client_options.append(display_name)
        client_mapping[display_name] = client['id']
    
    selected_client_names = st.multiselect(
        f"Seleccionar clientes ({len(client_options)} disponibles):",
        options=client_options,
        help="Puedes seleccionar múltiples clientes"
    )
    
    # Actualizar estado
    selected_client_ids = [client_mapping[name] for name in selected_client_names]
    st.session_state.generator_config['selected_clients'] = selected_client_ids
    
    # Mostrar resumen
    if selected_client_ids:
        st.success(f"Clientes seleccionados: {len(selected_client_ids)}")
        
        # Mostrar lista de clientes seleccionados
        with st.expander("Ver clientes seleccionados"):
            for client_id in selected_client_ids:
                client = get_client_by_id(client_id)
                if client is not None and not client.empty:
                    st.write(f"• {client['name']} ({client['codigo_ag']}) - {client['pais']}")

def show_type_selector(clients_df):
    """Selector por tipo de cliente"""
    
    available_types = get_tipos_cliente()
    client_types_in_db = clients_df['tipo_cliente'].dropna().unique()
    
    # Filtrar solo tipos que existen en la BD
    valid_types = [t for t in available_types if t in client_types_in_db]
    
    if not valid_types:
        st.warning("No hay tipos de cliente disponibles")
        return
    
    selected_type = st.selectbox(
        "Seleccionar tipo de cliente:",
        options=['Todos'] + valid_types,
        key="type_selector"
    )
    
    st.session_state.generator_config['selected_type'] = selected_type if selected_type != 'Todos' else None
    
    # Mostrar estadísticas
    if selected_type and selected_type != 'Todos':
        filtered_clients = clients_df[clients_df['tipo_cliente'] == selected_type]
        if has_country_filter():
            user_country = get_user_country_filter()
            filtered_clients = filtered_clients[filtered_clients['pais'] == user_country]
        
        st.info(f"Clientes del tipo '{selected_type}': {len(filtered_clients)}")
        
        # Mostrar muestra de clientes
        if len(filtered_clients) > 0:
            with st.expander("Ver muestra de clientes"):
                sample_size = min(10, len(filtered_clients))
                for _, client in filtered_clients.head(sample_size).iterrows():
                    st.write(f"• {client['name']} ({client['codigo_ag']}) - {client['pais']}")
                if len(filtered_clients) > sample_size:
                    st.write(f"... y {len(filtered_clients) - sample_size} más")

def show_region_selector(clients_df):
    """Selector por región"""
    
    available_regions = get_regiones()
    client_regions_in_db = clients_df['region'].dropna().unique()
    
    # Filtrar solo regiones que existen en la BD
    valid_regions = [r for r in available_regions if r in client_regions_in_db]
    
    if not valid_regions:
        st.warning("No hay regiones disponibles")
        return
    
    selected_region = st.selectbox(
        "Seleccionar región:",
        options=['Todas'] + valid_regions,
        key="region_selector"
    )
    
    st.session_state.generator_config['selected_region'] = selected_region if selected_region != 'Todas' else None
    
    # Mostrar estadísticas
    if selected_region and selected_region != 'Todas':
        filtered_clients = clients_df[clients_df['region'] == selected_region]
        if has_country_filter():
            user_country = get_user_country_filter()
            filtered_clients = filtered_clients[filtered_clients['pais'] == user_country]
        
        st.info(f"Clientes en la región '{selected_region}': {len(filtered_clients)}")
        
        # Mostrar muestra de clientes
        if len(filtered_clients) > 0:
            with st.expander("Ver muestra de clientes"):
                sample_size = min(10, len(filtered_clients))
                for _, client in filtered_clients.head(sample_size).iterrows():
                    st.write(f"• {client['name']} ({client['codigo_ag']}) - {client['pais']}")
                if len(filtered_clients) > sample_size:
                    st.write(f"... y {len(filtered_clients) - sample_size} más")

def show_country_selector(clients_df):
    """Selector por país"""
    
    # Si el usuario tiene filtro de país, solo mostrar su país
    if has_country_filter():
        user_country = get_user_country_filter()
        st.info(f"Filtro activo: Solo clientes de {user_country}")
        filtered_clients = clients_df[clients_df['pais'] == user_country]
        st.session_state.generator_config['selected_country'] = user_country
        
        st.success(f"Clientes en {user_country}: {len(filtered_clients)}")
        
        # Mostrar muestra de clientes
        if len(filtered_clients) > 0:
            with st.expander("Ver muestra de clientes"):
                sample_size = min(10, len(filtered_clients))
                for _, client in filtered_clients.head(sample_size).iterrows():
                    st.write(f"• {client['name']} ({client['codigo_ag']})")
                if len(filtered_clients) > sample_size:
                    st.write(f"... y {len(filtered_clients) - sample_size} más")
        return
    
    # Usuario sin restricciones - puede elegir cualquier país
    available_countries = get_paises()
    client_countries_in_db = clients_df['pais'].dropna().unique()
    
    # Filtrar solo países que existen en la BD
    valid_countries = [c for c in available_countries if c in client_countries_in_db]
    
    if not valid_countries:
        st.warning("No hay países disponibles")
        return
    
    selected_country = st.selectbox(
        "Seleccionar país:",
        options=['Todos'] + valid_countries,
        key="country_selector"
    )
    
    st.session_state.generator_config['selected_country'] = selected_country if selected_country != 'Todos' else None
    
    # Mostrar estadísticas
    if selected_country and selected_country != 'Todos':
        filtered_clients = clients_df[clients_df['pais'] == selected_country]
        
        st.info(f"Clientes en {selected_country}: {len(filtered_clients)}")
        
        # Mostrar muestra de clientes
        if len(filtered_clients) > 0:
            with st.expander("Ver muestra de clientes"):
                sample_size = min(10, len(filtered_clients))
                for _, client in filtered_clients.head(sample_size).iterrows():
                    st.write(f"• {client['name']} ({client['codigo_ag']})")
                if len(filtered_clients) > sample_size:
                    st.write(f"... y {len(filtered_clients) - sample_size} más")

def show_generation_summary():
    """Muestra el resumen de la configuración y permite generar el preview"""
    
    config = st.session_state.generator_config
    
    # Validar configuración
    if not config['target_years']:
        st.warning("Selecciona al menos un año para continuar")
        return
    
    # Obtener clientes que serán afectados
    target_clients = get_target_clients_from_config(config)
    
    if not target_clients or len(target_clients) == 0:
        st.warning("No hay clientes que coincidan con los criterios seleccionados")
        return
    
    # Mostrar resumen
    st.markdown("#### Resumen de Configuración")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Años seleccionados", len(config['target_years']))
        st.write("Años: " + ", ".join(map(str, sorted(config['target_years']))))
    
    with col2:
        st.metric("Clientes afectados", len(target_clients))
        selection_desc = get_selection_description(config)
        st.write(f"Criterio: {selection_desc}")
    
    with col3:
        total_generations = len(config['target_years']) * len(target_clients)
        st.metric("Total generaciones", total_generations)
        st.write(f"{len(config['target_years'])} años × {len(target_clients)} clientes")
    
    # Botón para generar preview
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("Generar Preview", type="primary", use_container_width=True):
            generate_preview_data(config, target_clients)
    
    with col2:
        if st.button("Limpiar Configuración", use_container_width=True):
            clear_generator_config()
            st.rerun()

def get_target_clients_from_config(config):
    """Obtiene la lista de clientes objetivo basada en la configuración"""
    clients_df = get_clients(use_cache=True)
    
    if clients_df.empty:
        return []
    
    # Aplicar filtro de país del usuario si existe
    if has_country_filter():
        user_country = get_user_country_filter()
        clients_df = clients_df[clients_df['pais'] == user_country]
    
    selection_type = config['selection_type']
    
    if selection_type == 'specific':
        # Clientes específicos
        target_ids = config['selected_clients']
        return [get_client_by_id(client_id) for client_id in target_ids 
                if get_client_by_id(client_id) is not None and not get_client_by_id(client_id).empty]
    
    elif selection_type == 'type':
        # Por tipo de cliente
        if config['selected_type']:
            filtered_df = clients_df[clients_df['tipo_cliente'] == config['selected_type']]
        else:
            filtered_df = clients_df
        
        result = []
        for _, row in filtered_df.iterrows():
            client = get_client_by_id(row['id'])
            if client is not None and not client.empty:
                result.append(client)
        return result
    
    elif selection_type == 'region':
        # Por región
        if config['selected_region']:
            filtered_df = clients_df[clients_df['region'] == config['selected_region']]
        else:
            filtered_df = clients_df
        
        result = []
        for _, row in filtered_df.iterrows():
            client = get_client_by_id(row['id'])
            if client is not None and not client.empty:
                result.append(client)
        return result
    
    elif selection_type == 'country':
        # Por país
        if config['selected_country']:
            filtered_df = clients_df[clients_df['pais'] == config['selected_country']]
        else:
            filtered_df = clients_df
        
        result = []
        for _, row in filtered_df.iterrows():
            client = get_client_by_id(row['id'])
            if client is not None and not client.empty:
                result.append(client)
        return result
    
    return []

def get_selection_description(config):
    """Obtiene una descripción legible del criterio de selección"""
    selection_type = config['selection_type']
    
    if selection_type == 'specific':
        return f"Clientes específicos ({len(config['selected_clients'])})"
    elif selection_type == 'type':
        return f"Tipo: {config['selected_type'] or 'Todos'}"
    elif selection_type == 'region':
        return f"Región: {config['selected_region'] or 'Todas'}"
    elif selection_type == 'country':
        return f"País: {config['selected_country'] or 'Todos'}"
    
    return "No definido"

def generate_preview_data(config, target_clients):
    """Genera los datos de preview para mostrar en la siguiente pestaña"""
    
    with st.spinner("Generando preview de fechas..."):
        preview_data = []
        
        for year in config['target_years']:
            for client in target_clients:
                if client is None or client.empty:
                    continue
                
                try:
                    # Obtener actividades del cliente
                    activities = get_client_activities(client['id'])
                    
                    if activities.empty:
                        continue
                    
                    client_data = {
                        'year': year,
                        'client_id': client['id'],
                        'client_name': client['name'],
                        'client_code': client['codigo_ag'],
                        'client_country': client['pais'],
                        'activities': [],
                        'total_dates': 0
                    }
                    
                    # Generar fechas para cada actividad
                    for _, activity in activities.iterrows():
                        try:
                            start_date = date(year, 1, 1)
                            calculated_dates = calculate_dates_for_frequency(
                                activity['frequency_type'],
                                activity['frequency_config'],
                                start_date=start_date,
                                full_year=True
                            )
                            
                            activity_data = {
                                'name': activity['activity_name'],
                                'frequency_type': activity['frequency_type'],
                                'dates': calculated_dates,
                                'dates_count': len(calculated_dates)
                            }
                            
                            client_data['activities'].append(activity_data)
                            client_data['total_dates'] += len(calculated_dates)
                            
                        except Exception as e:
                            st.error(f"Error generando fechas para {client['name']} - {activity['activity_name']}: {str(e)}")
                    
                    if client_data['activities']:
                        preview_data.append(client_data)
                
                except Exception as e:
                    st.error(f"Error procesando cliente {client['name']}: {str(e)}")
        
        # Guardar datos de preview en session state
        st.session_state.generator_config['preview_data'] = preview_data
        st.session_state.generator_preview_ready = True
        
        st.success(f"Preview generado exitosamente para {len(preview_data)} configuraciones cliente-año")

def show_preview_tab():
    """Muestra la pestaña de preview de fechas"""
    st.subheader("Preview de Fechas a Generar")
    
    if not st.session_state.generator_preview_ready or not st.session_state.generator_config.get('preview_data'):
        st.info("Configura la generación en la pestaña anterior y genera el preview")
        return
    
    preview_data = st.session_state.generator_config['preview_data']
    
    if not preview_data:
        st.warning("No hay datos de preview disponibles")
        return
    
    # Mostrar estadísticas generales
    show_preview_statistics(preview_data)
    
    st.divider()
    
    # Filtros para el preview
    show_preview_filters(preview_data)
    
    st.divider()
    
    # Mostrar tabla de preview
    show_preview_table(preview_data)
    
    st.divider()
    
    # Botones de acción
    show_preview_actions(preview_data)

def show_preview_statistics(preview_data):
    """Muestra estadísticas del preview"""
    
    # Calcular estadísticas
    total_configurations = len(preview_data)
    total_clients = len(set(item['client_id'] for item in preview_data))
    total_years = len(set(item['year'] for item in preview_data))
    total_dates = sum(item['total_dates'] for item in preview_data)
    
    # Mostrar métricas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Configuraciones", total_configurations)
    
    with col2:
        st.metric("Clientes únicos", total_clients)
    
    with col3:
        st.metric("Años", total_years)
    
    with col4:
        st.metric("Total fechas", total_dates)
    
    # Distribución por año
    years_distribution = {}
    for item in preview_data:
        year = item['year']
        if year not in years_distribution:
            years_distribution[year] = {'clients': 0, 'dates': 0}
        years_distribution[year]['clients'] += 1
        years_distribution[year]['dates'] += item['total_dates']
    
    st.markdown("##### Distribución por Año")
    
    dist_data = []
    for year in sorted(years_distribution.keys()):
        dist_data.append({
            'Año': year,
            'Clientes': years_distribution[year]['clients'],
            'Total Fechas': years_distribution[year]['dates'],
            'Promedio por Cliente': round(years_distribution[year]['dates'] / years_distribution[year]['clients'], 1)
        })
    
    st.dataframe(pd.DataFrame(dist_data), use_container_width=True)

def show_preview_filters(preview_data):
    """Muestra filtros para el preview"""
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Filtro por año
        available_years = sorted(set(item['year'] for item in preview_data))
        selected_year = st.selectbox(
            "Filtrar por año:",
            options=['Todos'] + available_years,
            key="preview_year_filter"
        )
    
    with col2:
        # Filtro por país
        available_countries = sorted(set(item['client_country'] for item in preview_data))
        selected_country = st.selectbox(
            "Filtrar por país:",
            options=['Todos'] + available_countries,
            key="preview_country_filter"
        )
    
    with col3:
        # Filtro por número mínimo de fechas
        min_dates = st.number_input(
            "Fechas mínimas:",
            min_value=0,
            max_value=max(item['total_dates'] for item in preview_data),
            value=0,
            key="preview_min_dates_filter"
        )
    
    # Aplicar filtros
    filtered_data = preview_data
    
    if selected_year != 'Todos':
        filtered_data = [item for item in filtered_data if item['year'] == selected_year]
    
    if selected_country != 'Todos':
        filtered_data = [item for item in filtered_data if item['client_country'] == selected_country]
    
    if min_dates > 0:
        filtered_data = [item for item in filtered_data if item['total_dates'] >= min_dates]
    
    st.session_state.filtered_preview_data = filtered_data
    
    if len(filtered_data) != len(preview_data):
        st.info(f"Mostrando {len(filtered_data)} de {len(preview_data)} configuraciones")

def show_preview_table(preview_data):
    """Muestra la tabla detallada del preview"""
    
    # Usar datos filtrados si están disponibles
    data_to_show = st.session_state.get('filtered_preview_data', preview_data)
    
    if not data_to_show:
        st.warning("No hay datos que coincidan con los filtros aplicados")
        return
    
    st.markdown("##### Detalle de Fechas por Cliente y Año")
    
    # Selector de vista
    view_mode = st.radio(
        "Vista:",
        options=['Resumen', 'Detallada'],
        horizontal=True,
        key="preview_view_mode"
    )
    
    if view_mode == 'Resumen':
        show_preview_summary_table(data_to_show)
    else:
        show_preview_detailed_table(data_to_show)

def show_preview_summary_table(data_to_show):
    """Muestra tabla resumen del preview"""
    
    # Preparar datos para la tabla resumen
    summary_data = []
    
    for item in data_to_show:
        activities_summary = []
        for activity in item['activities']:
            activities_summary.append(f"{activity['name']} ({activity['dates_count']})")
        
        summary_data.append({
            'Año': item['year'],
            'Cliente': item['client_name'],
            'Código': item['client_code'],
            'País': item['client_country'],
            'Actividades': len(item['activities']),
            'Total Fechas': item['total_dates'],
            'Detalle Actividades': ', '.join(activities_summary[:3]) + ('...' if len(activities_summary) > 3 else '')
        })
    
    df = pd.DataFrame(summary_data)
    st.dataframe(df, use_container_width=True)

def show_preview_detailed_table(data_to_show):
    """Muestra tabla detallada del preview con fechas específicas"""
    
    # Permitir seleccionar un cliente específico para ver detalle
    client_options = []
    client_mapping = {}
    
    for item in data_to_show:
        key = f"{item['client_name']} ({item['year']})"
        client_options.append(key)
        client_mapping[key] = item
    
    if not client_options:
        st.warning("No hay clientes disponibles para mostrar detalle")
        return
    
    selected_client_key = st.selectbox(
        "Seleccionar cliente para ver detalle:",
        options=client_options,
        key="preview_detail_client"
    )
    
    if selected_client_key:
        item = client_mapping[selected_client_key]
        
        st.markdown(f"#### {item['client_name']} - {item['year']}")
        
        # Mostrar cada actividad
        for activity in item['activities']:
            with st.expander(f"{activity['name']} ({activity['dates_count']} fechas)"):
                if activity['dates']:
                    # Organizar fechas por mes
                    dates_by_month = {}
                    for date_obj in activity['dates']:
                        month_key = date_obj.strftime('%Y-%m')
                        month_name = date_obj.strftime('%B %Y')
                        if month_key not in dates_by_month:
                            dates_by_month[month_key] = {
                                'name': month_name,
                                'dates': []
                            }
                        dates_by_month[month_key]['dates'].append(date_obj.strftime('%d'))
                    
                    # Mostrar por meses
                    for month_key in sorted(dates_by_month.keys()):
                        month_data = dates_by_month[month_key]
                        dates_str = ', '.join(sorted(month_data['dates'], key=int))
                        st.write(f"**{month_data['name']}:** {dates_str}")
                else:
                    st.write("No se generaron fechas para esta actividad")

def show_preview_actions(preview_data):
    """Muestra los botones de acción para el preview"""
    
    st.markdown("##### Acciones")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("Confirmar y Generar", type="primary", use_container_width=True):
            execute_generation(preview_data)
    
    with col2:
        if st.button("Exportar Preview", use_container_width=True):
            export_preview_data(preview_data)
    
    with col3:
        if st.button("Volver a Configurar", use_container_width=True):
            st.session_state.generator_preview_ready = False
            st.rerun()
    
    with col4:
        if st.button("Limpiar Todo", use_container_width=True):
            clear_generator_config()
            st.rerun()

def save_all_calculated_dates(client_id, activity_name, dates_list):
    """Guarda todas las fechas para una actividad específica (no limitado a 4)"""
    if not dates_list:
        print(f"No hay fechas para guardar para actividad {activity_name}")
        return 0

def save_all_calculated_dates_by_year(client_id, activity_name, dates_list, year):
    """Guarda todas las fechas para una actividad específica de un año, preservando otros años"""
    if not dates_list:
        print(f"No hay fechas para guardar para actividad {activity_name} del año {year}")
        return 0
        
    try:
        from database import save_calculated_dates_by_year
        
        # Usar la nueva función de base de datos que preserva otros años
        save_calculated_dates_by_year(client_id, activity_name, dates_list, year)
        
        return len(dates_list)
        
    except Exception as e:
        print(f"Error guardando fechas para {activity_name} del año {year}: {e}")
        return 0
        
    try:
        from database import get_pooled_connection, return_pooled_connection, _db_cache
        from datetime import datetime, date
        
        conn = get_pooled_connection()
        cursor = conn.cursor()
        
        try:
            # Usar transacción para operaciones atómicas
            cursor.execute("BEGIN TRANSACTION")
            
            # Eliminar fechas existentes para esta actividad
            cursor.execute('''
                DELETE FROM calculated_dates 
                WHERE client_id = ? AND activity_name = ?
            ''', (client_id, activity_name))
            
            # Insertar todas las fechas en posiciones secuenciales
            dates_saved = 0
            for position, date_item in enumerate(dates_list, 1):
                if date_item:
                    # Manejo simplificado de conversión de fecha a string
                    try:
                        if hasattr(date_item, 'strftime'):
                            date_str = date_item.strftime('%Y-%m-%d')
                        else:
                            date_str = str(date_item)
                            # Validar que sea un formato de fecha válido
                            if len(date_str) == 10 and date_str.count('-') == 2:
                                pass  # Parece ser YYYY-MM-DD
                            else:
                                print(f"Advertencia: formato de fecha no estándar: {date_str}")
                    except Exception as date_convert_error:
                        print(f"Error convirtiendo fecha: {date_convert_error}")
                        date_str = str(date_item)
                    
                    cursor.execute('''
                        INSERT INTO calculated_dates (client_id, activity_name, date_position, date)
                        VALUES (?, ?, ?, ?)
                    ''', (client_id, activity_name, position, date_str))
                    dates_saved += 1
            
            conn.commit()
            print(f"Guardadas {dates_saved} fechas para {activity_name}")
            
            # Invalidar cache de fechas para este cliente
            _db_cache.invalidate_pattern(f"dates_{client_id}")
            
            return dates_saved
            
        except Exception as e:
            print(f"Error guardando fechas para {activity_name}: {e}")
            conn.rollback()
            raise e
        finally:
            return_pooled_connection(conn)
            
    except ImportError:
        # Fallback a la función original si hay problemas con imports
        print(f"Usando función original para {activity_name}")
        save_calculated_dates(client_id, activity_name, dates_list)
        return min(len(dates_list), 4)

def execute_generation(preview_data):
    """Ejecuta la generación real de fechas en la base de datos"""
    
    with st.spinner("Generando fechas en la base de datos..."):
        success_count = 0
        error_count = 0
        errors = []
        total_dates_saved = 0
        
        progress_bar = st.progress(0)
        total_operations = len(preview_data)
        
        # Contenedor para mostrar información de debug
        debug_info = st.empty()
        
        for i, item in enumerate(preview_data):
            try:
                debug_info.info(f"Procesando: {item['client_name']} ({item['year']}) - {len(item['activities'])} actividades")
                
                # Generar fechas para cada actividad del cliente
                client_dates_saved = 0
                for activity in item['activities']:
                    if activity['dates']:
                        # Preparar lista de fechas para esta actividad específica
                        dates_list = activity['dates']  # Ya son objetos datetime
                        
                        # Debug: mostrar información de la actividad
                        debug_info.info(f"Guardando {len(dates_list)} fechas para {activity['name']} del año {item['year']}")
                        
                        # Usar la nueva función que preserva fechas de otros años
                        dates_saved = save_all_calculated_dates_by_year(item['client_id'], activity['name'], dates_list, item['year'])
                        
                        client_dates_saved += dates_saved
                        total_dates_saved += dates_saved
                
                success_count += 1
                debug_info.success(f"✓ {item['client_name']}: {client_dates_saved} fechas guardadas")
                
            except Exception as e:
                error_count += 1
                error_msg = f"{item['client_name']} ({item['year']}): {str(e)}"
                errors.append(error_msg)
                debug_info.error(f"❌ Error: {error_msg}")
            
            # Actualizar barra de progreso
            progress_bar.progress((i + 1) / total_operations)
        
        # Limpiar información de debug
        debug_info.empty()
        
        # Mostrar resultados
        if success_count > 0:
            st.success(f"Generación completada: {success_count} configuraciones exitosas")
            st.info(f"Total de fechas guardadas en la base de datos: {total_dates_saved}")
            
            # Guardar en historial
            history_entry = {
                'timestamp': datetime.now(),
                'configurations': success_count,
                'errors': error_count,
                'years': sorted(set(item['year'] for item in preview_data)),
                'total_dates': total_dates_saved
            }
            
            if 'generator_history' not in st.session_state:
                st.session_state.generator_history = []
            
            st.session_state.generator_history.append(history_entry)
            
            # Limpiar configuración actual
            clear_generator_config()
        
        if error_count > 0:
            st.error(f"Errores durante la generación: {error_count}")
            with st.expander("Ver errores"):
                for error in errors:
                    st.write(f"• {error}")

def export_preview_data(preview_data):
    """Exporta los datos del preview a un archivo CSV"""
    
    try:
        # Preparar datos para exportación
        export_data = []
        
        for item in preview_data:
            for activity in item['activities']:
                for date_obj in activity['dates']:
                    export_data.append({
                        'Año': item['year'],
                        'Cliente': item['client_name'],
                        'Código Cliente': item['client_code'],
                        'País': item['client_country'],
                        'Actividad': activity['name'],
                        'Fecha': date_obj.strftime('%Y-%m-%d'),
                        'Mes': date_obj.strftime('%B'),
                        'Día': date_obj.strftime('%d')
                    })
        
        df = pd.DataFrame(export_data)
        csv = df.to_csv(index=False)
        
        st.download_button(
            label="Descargar Preview CSV",
            data=csv,
            file_name=f"preview_fechas_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
        
    except Exception as e:
        st.error(f"Error al exportar: {str(e)}")

def show_history_tab():
    """Muestra la pestaña de historial de generaciones"""
    st.subheader("Historial de Generaciones")
    
    if not st.session_state.get('generator_history'):
        st.info("No hay generaciones previas registradas")
        return
    
    history = st.session_state.generator_history
    
    # Mostrar estadísticas del historial
    total_generations = len(history)
    total_configurations = sum(entry['configurations'] for entry in history)
    total_dates_generated = sum(entry['total_dates'] for entry in history)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Generaciones", total_generations)
    
    with col2:
        st.metric("Configuraciones Exitosas", total_configurations)
    
    with col3:
        st.metric("Fechas Generadas", total_dates_generated)
    
    st.divider()
    
    # Tabla de historial
    st.markdown("##### Detalle del Historial")
    
    history_data = []
    for i, entry in enumerate(reversed(history), 1):  # Mostrar más reciente primero
        history_data.append({
            'Orden': i,
            'Fecha/Hora': entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
            'Configuraciones': entry['configurations'],
            'Errores': entry['errors'],
            'Años': ', '.join(map(str, entry['years'])),
            'Total Fechas': entry['total_dates']
        })
    
    df = pd.DataFrame(history_data)
    st.dataframe(df, use_container_width=True)
    
    # Botón para limpiar historial
    if st.button("Limpiar Historial", type="secondary"):
        st.session_state.generator_history = []
        st.rerun()

def clear_generator_config():
    """Limpia la configuración del generador"""
    st.session_state.generator_config = {
        'target_years': [],
        'selection_type': 'specific',
        'selected_clients': [],
        'selected_type': None,
        'selected_region': None,
        'selected_country': None,
        'preview_data': None,
        'generation_complete': False
    }
    st.session_state.generator_preview_ready = False
    if 'filtered_preview_data' in st.session_state:
        del st.session_state.filtered_preview_data