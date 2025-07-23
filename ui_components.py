import streamlit as st
import json
import sqlite3
import pandas as pd
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from config import is_read_only_mode
from database import (
    get_clients, get_client_by_id, add_client, update_client, delete_client,
    get_frequency_templates, add_frequency_template, update_frequency_template,
    delete_frequency_template, get_frequency_usage_count,
    get_client_activities, update_client_activity_frequency,
    add_client_activity, delete_client_activity,
    get_calculated_dates, save_calculated_dates, update_calculated_date,
    get_db_connection
)
from date_calculator import recalculate_client_dates
from calendar_utils import create_client_calendar_table, format_frequency_description
from client_constants import get_tipos_cliente, get_regiones
from werfen_styles import get_client_card_html, get_metric_card_html, get_calendar_header_html, get_button_html
import sqlite3

# ========== FUNCIONES DE GALERÍA Y NAVEGACIÓN ==========

def show_clients_gallery():
    """Muestra la galería de clientes"""
    st.header("Clientes Kronos")
    
    # Si se está mostrando el detalle del cliente
    if st.session_state.get('show_client_detail', False) and st.session_state.get('selected_client'):
        show_client_detail()
        return
    
    # Limpiar estados si llegamos aquí
    if 'show_edit_modal' in st.session_state:
        st.session_state.show_edit_modal = False
    if 'show_client_detail' in st.session_state:
        st.session_state.show_client_detail = False
    
    clients = get_clients()
    
    if clients.empty:
        st.info("No hay clientes registrados. Agrega un cliente para comenzar.")
        return
    
    # Fila superior: búsqueda de texto
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_term = st.text_input(
            "Buscar por nombre, código AG, CSR, vendedor, tipo o región:",
            placeholder="Ingresa tu búsqueda...",
            key="client_search",
            help="Busca clientes por cualquiera de sus campos principales"
        )
    
    with col2:
        # Botón para limpiar búsqueda
        if st.button("Limpiar", key="clear_search", help="Limpiar búsqueda"):
            # Eliminar la key del session_state para que se reinicialice
            if "client_search" in st.session_state:
                del st.session_state["client_search"]
            st.rerun()
    
    # Fila inferior: filtros adicionales  
    col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 2, 2, 1])
    
    with col1:
        # Filtro por CSR
        csr_options = ['Todos'] + sorted([csr for csr in clients['csr'].dropna().unique() if csr])
        selected_csr = st.selectbox(
            "Filtrar por CSR:",
            csr_options,
            index=0,  # Siempre empezar con "Todos"
            key="csr_filter"
        )
    
    with col2:
        # Filtro por vendedor
        vendedor_options = ['Todos'] + sorted([vendedor for vendedor in clients['vendedor'].dropna().unique() if vendedor])
        selected_vendedor = st.selectbox(
            "Filtrar por Vendedor:",
            vendedor_options,
            index=0,  # Siempre empezar con "Todos"
            key="vendedor_filter"
        )
    
    with col3:
        # Filtro por tipo de cliente
        tipo_options = ['Todos'] + get_tipos_cliente()
        selected_tipo = st.selectbox(
            "Filtrar por Tipo:",
            tipo_options,
            index=0,  # Siempre empezar con "Todos"
            key="tipo_filter"
        )
    
    with col4:
        # Filtro por región
        region_options = ['Todos'] + get_regiones()
        selected_region = st.selectbox(
            "Filtrar por Región:",
            region_options,
            index=0,  # Siempre empezar con "Todos"
            key="region_filter"
        )
    
    with col5:
        # Ordenar por
        sort_options = ['Nombre A-Z', 'Nombre Z-A', 'Código AG', 'CSR', 'Vendedor', 'Tipo', 'Región']
        sort_by = st.selectbox(
            "Ordenar por:",
            sort_options,
            index=0,  # Siempre empezar con "Nombre A-Z"
            key="sort_filter"
        )
    
    with col6:
        st.write("")  # Espacio para alinear el botón
        if st.button("Limpiar Filtros", key="clear_all_filters", help="Limpiar todos los filtros"):
            # Eliminar todas las keys de los filtros para que se reinicialicen
            filter_keys = ["client_search", "csr_filter", "vendedor_filter", "tipo_filter", "region_filter", "sort_filter"]
            for key in filter_keys:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    # Filtrar clientes basado en los criterios seleccionados
    filtered_clients = clients.copy()
    
    # Aplicar filtro de texto (verificar que no sea None o vacío)
    if search_term and search_term.strip():
        filtered_clients = filtered_clients[
            filtered_clients['name'].str.contains(search_term, case=False, na=False) |
            filtered_clients['codigo_ag'].str.contains(search_term, case=False, na=False) |
            filtered_clients['csr'].str.contains(search_term, case=False, na=False) |
            filtered_clients['vendedor'].str.contains(search_term, case=False, na=False) |
            filtered_clients['tipo_cliente'].str.contains(search_term, case=False, na=False) |
            filtered_clients['region'].str.contains(search_term, case=False, na=False)
        ]
    
    # Aplicar filtro de CSR
    if selected_csr and selected_csr != 'Todos':
        filtered_clients = filtered_clients[filtered_clients['csr'] == selected_csr]
    
    # Aplicar filtro de vendedor
    if selected_vendedor and selected_vendedor != 'Todos':
        filtered_clients = filtered_clients[filtered_clients['vendedor'] == selected_vendedor]
    
    # Aplicar filtro de tipo de cliente
    if selected_tipo and selected_tipo != 'Todos':
        filtered_clients = filtered_clients[filtered_clients['tipo_cliente'] == selected_tipo]
    
    # Aplicar filtro de región
    if selected_region and selected_region != 'Todos':
        filtered_clients = filtered_clients[filtered_clients['region'] == selected_region]
    
    # Aplicar ordenamiento
    if sort_by == 'Nombre A-Z':
        filtered_clients = filtered_clients.sort_values('name', ascending=True)
    elif sort_by == 'Nombre Z-A':
        filtered_clients = filtered_clients.sort_values('name', ascending=False)
    elif sort_by == 'Código AG':
        filtered_clients = filtered_clients.sort_values('codigo_ag', ascending=True, na_position='last')
    elif sort_by == 'CSR':
        filtered_clients = filtered_clients.sort_values('csr', ascending=True, na_position='last')
    elif sort_by == 'Vendedor':
        filtered_clients = filtered_clients.sort_values('vendedor', ascending=True, na_position='last')
    elif sort_by == 'Tipo':
        filtered_clients = filtered_clients.sort_values('tipo_cliente', ascending=True, na_position='last')
    elif sort_by == 'Región':
        filtered_clients = filtered_clients.sort_values('region', ascending=True, na_position='last')
    
    # Verificar si hay resultados
    if filtered_clients.empty:
        st.warning("No se encontraron clientes que coincidan con los filtros seleccionados")
        
        # Mostrar sugerencias para ajustar la búsqueda
        st.info("""
        **Sugerencias:**
        - Intenta con términos de búsqueda más generales
        - Revisa los filtros seleccionados (CSR, Vendedor, Tipo, Región)
        - Usa el botón 'Limpiar Filtros' para resetear todos los filtros
        """)
        return
    
    # Mostrar información de resultados
    total_clients = len(clients)
    shown_clients = len(filtered_clients)
    
    if shown_clients == total_clients:
        st.info(f"Mostrando todos los clientes ({total_clients} total)")
    else:
        pass
        st.info(f"Mostrando {shown_clients} de {total_clients} clientes")
        
        # Mostrar filtros activos
        active_filters = []
        if search_term:
            active_filters.append(f"Texto: '{search_term}'")
        if selected_csr != 'Todos':
            active_filters.append(f"CSR: {selected_csr}")
        if selected_vendedor != 'Todos':
            active_filters.append(f"Vendedor: {selected_vendedor}")
        if sort_by != 'Nombre A-Z':
            active_filters.append(f"Orden: {sort_by}")
        
        if active_filters:
            st.caption(f"Filtros activos: {' • '.join(active_filters)}")
    
    clients_to_show = filtered_clients
    
    # Selector de vista
    col1, col2 = st.columns([1, 3])
    with col1:
        view_mode = st.selectbox(
            "Vista:",
            ["Galería", "Lista"],
            key="view_mode",
            help="Selecciona cómo mostrar los clientes"
        )
    
    st.divider()
    
    # Mostrar clientes según la vista seleccionada
    if view_mode == "Lista":
        show_clients_list_view(clients_to_show)
    else:
        show_clients_gallery_view(clients_to_show)

def get_client_current_month_data(client_id):
    """Obtiene los datos del mes actual para un cliente específico (vista compacta)"""
    dates_df = get_calculated_dates(client_id)
    
    if dates_df.empty:
        return None
    
    # Obtener mes actual
    current_month = datetime.now().month
    
    # Filtrar fechas del mes actual
    month_dates = []
    for _, row in dates_df.iterrows():
        try:
            date_obj = datetime.strptime(row['date'], '%Y-%m-%d')
            if date_obj.month == current_month:
                # Mapear meses al español para formato abreviado
                months_spanish = {
                    1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr', 5: 'May', 6: 'Jun',
                    7: 'Jul', 8: 'Ago', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'
                }
                month_abbr = months_spanish[date_obj.month]
                formatted_date = f"{date_obj.day:02d}-{month_abbr}"
                
                month_dates.append({
                    'activity_name': row['activity_name'],
                    'date': date_obj,
                    'date_position': row['date_position'],
                    'formatted_date': formatted_date
                })
        except:
            continue
    
    if not month_dates:
        return None
    
    # Crear tabla agrupada por actividad - solo fechas del mes actual
    table_data = {}
    
    # Agrupar fechas por actividad y posición, solo para este mes
    for date_info in month_dates:
        activity = date_info['activity_name']
        position = date_info['date_position']
        
        if activity not in table_data:
            table_data[activity] = {}
        
        table_data[activity][position] = date_info['formatted_date']
    
    # Crear DataFrame para la tabla
    table_rows = []
    
    # Determinar cuántas fechas tiene cada actividad en este mes específico
    for activity in sorted(table_data.keys()):
        row = {'Actividad': activity}
        activity_positions = sorted(table_data[activity].keys())
        
        # Agregar columnas para cada posición que existe en este mes
        for i, pos in enumerate(activity_positions, 1):
            fecha_col = f'Fecha {i}'
            row[fecha_col] = table_data[activity][pos]
        
        table_rows.append(row)
    
    if table_rows:
        # Crear DataFrame con índice limpio y resetear índice para evitar filas vacías
        df = pd.DataFrame(table_rows)
        # Filtrar filas que solo tengan 'Actividad' y valores nulos en el resto
        df = df.dropna(subset=[col for col in df.columns if col != 'Actividad'], how='all')
        return df.reset_index(drop=True) if not df.empty else None
    else:
        return None

def show_clients_gallery_view(clients_to_show):
    """Muestra los clientes en vista de galería (tarjetas)"""
    # Mostrar galería de clientes
    cols = st.columns(3)
    
    for idx, (_, client) in enumerate(clients_to_show.iterrows()):
        with cols[idx % 3]:
            with st.container():
                # Usar el HTML personalizado de Werfen
                st.markdown(get_client_card_html(client), unsafe_allow_html=True)
                
                # Mostrar vista del mes actual
                try:
                    current_month_df = get_client_current_month_data(client['id'])
                    if current_month_df is not None and not current_month_df.empty:
                        # Obtener nombre del mes actual
                        months = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                                 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
                        current_month_name = months[datetime.now().month - 1]
                        
                        st.markdown(f"{current_month_name}")
                        # Calcular altura dinámica basada en número de filas
                        num_rows = len(current_month_df)
                        dynamic_height = min(max(num_rows * 35 + 60, 150), 400)  # Altura entre 150 y 400px
                        
                        st.dataframe(
                            current_month_df,
                            use_container_width=True,
                            hide_index=True,
                            height=dynamic_height,
                            column_config={
                                'Actividad': st.column_config.TextColumn(
                                    'Actividad',
                                    width='medium'
                                )
                            }
                        )
                    else:
                        current_month_name = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                                            'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'][datetime.now().month - 1]
                        st.markdown(f"{current_month_name}")
                        st.write("Sin actividades este mes")
                except Exception as e:
                    st.write("Sin calendario configurado")
                
                # Botón para ver detalle
                if st.button(f"Ver Detalle", key=f"detail_{client['id']}"):
                    # Limpiar estados previos
                    for key in ['show_edit_modal', 'edit_name', 'edit_codigo_ag', 'edit_codigo_we', 
                              'edit_csr', 'edit_vendedor', 'edit_calendario_sap']:
                        if key in st.session_state:
                            del st.session_state[key]
                    
                    # Establecer nuevo cliente
                    st.session_state.selected_client = int(client['id'])
                    st.session_state.show_client_detail = True
                    st.rerun()

def show_clients_list_view(clients_to_show):
    """Muestra los clientes en vista de lista (tabla)"""
    if clients_to_show.empty:
        st.info("No hay clientes para mostrar")
        return
    
    # Preparar datos para la tabla
    display_data = []
    for _, client in clients_to_show.iterrows():
        display_data.append({
            'Nombre': client['name'],
            'Código AG': client['codigo_ag'] or 'N/A',
            'Código WE': client['codigo_we'] or 'N/A',
            'CSR': client['csr'] or 'N/A',
            'Vendedor': client['vendedor'] or 'N/A',
            'Tipo Cliente': client.get('tipo_cliente', 'N/A') or 'N/A',
            'Región': client.get('region', 'N/A') or 'N/A',
            'ID': client['id']
        })
    
    # Mostrar tabla
    for i, client_data in enumerate(display_data):
        with st.container():
            col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([3, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1])
            
            with col1:
                st.markdown(f"**{client_data['Nombre']}**")
            
            with col2:
                st.write(f"AG: {client_data['Código AG']}")
            
            with col3:
                st.write(f"WE: {client_data['Código WE']}")
            
            with col4:
                st.write(f"CSR: {client_data['CSR']}")
            
            with col5:
                st.write(f"Vendedor: {client_data['Vendedor']}")
            
            with col6:
                st.write(f"Tipo: {client_data['Tipo Cliente']}")
            
            with col7:
                st.write(f"Región: {client_data['Región']}")
            
            with col8:
                if st.button("Ver", key=f"list_detail_{client_data['ID']}", help="Ver detalle"):
                    # Limpiar estados previos
                    for key in ['show_edit_modal', 'edit_name', 'edit_codigo_ag', 'edit_codigo_we', 
                              'edit_csr', 'edit_vendedor', 'edit_calendario_sap']:
                        if key in st.session_state:
                            del st.session_state[key]
                    
                    # Establecer nuevo cliente
                    st.session_state.selected_client = int(client_data['ID'])
                    st.session_state.show_client_detail = True
                    st.rerun()
            
            # Separador entre filas
            if i < len(display_data) - 1:
                st.divider()

# ========== FUNCIONES DE DETALLE DEL CLIENTE CON EDICIÓN MEJORADA ==========

def show_client_detail():
    """Muestra el detalle de un cliente específico con edición de fechas mejorada"""
    # Validar que existe un cliente seleccionado
    if not st.session_state.get('selected_client'):
        st.error("No hay cliente seleccionado. Regresando a la galería...")
        st.session_state.show_client_detail = False
        st.rerun()
        return
    
    client_id = st.session_state.selected_client
    
    # NO limpiar estados de confirmación aquí, solo claves de botones duplicadas
    # (La limpieza que causaba el problema se ha eliminado)
    
    # Intentar obtener el cliente
    try:
        client = get_client_by_id(client_id)
    except Exception as e:
        st.error(f"Error al obtener datos del cliente: {e}")
        client = None
    
    if client is None or len(client) == 0:
        st.error("Cliente no encontrado. Es posible que haya sido eliminado.")
        
        # Botón para regresar a la galería
        if st.button("← Regresar a la Galería"):
            st.session_state.show_client_detail = False
            st.session_state.selected_client = None
            # Limpiar estados de edición
            for key in list(st.session_state.keys()):
                if key.startswith('edit_client_') or key in ['show_edit_modal']:
                    del st.session_state[key]
            st.rerun()
        return
    
    # Botones de navegación y acciones
    col1, col2, col3 = st.columns([1, 1, 6])
    with col1:
        if st.button("← Regresar"):
            st.session_state.show_client_detail = False
            st.session_state.selected_client = None
            # Limpiar estados de edición
            for key in list(st.session_state.keys()):
                if key.startswith('edit_client_') or key in ['show_edit_modal']:
                    del st.session_state[key]
            st.rerun()
    
    with col2:
        if not is_read_only_mode():
            if st.button("Editar Cliente"):
                st.session_state.show_edit_modal = True
                st.rerun()
        else:
            st.button("Editar Cliente", disabled=True, help="No disponible en modo producción")
    
    # Mostrar modal de edición si está activado
    if st.session_state.get('show_edit_modal', False):
        show_edit_modal_improved(client)  # Usar la función mejorada
        return
    
    st.header(f"Detalle del Cliente: {client['name']}")
    
    # Información del cliente
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        **Nombre:** {client['name']}  
        **Código AG:** {client['codigo_ag'] or 'N/A'}
        """)
    
    with col2:
        st.markdown(f"""
        **Código WE:** {client['codigo_we'] or 'N/A'}  
        **CSR:** {client['csr'] or 'N/A'}
        """)
    
    with col3:
        st.markdown(f"""
        **Vendedor:** {client['vendedor'] or 'N/A'}  
        **Calendario SAP:** {client['calendario_sap'] or 'N/A'}
        """)
    
    st.divider()
    
    # ========== SECCIÓN MEJORADA DE CALENDARIO CON EDICIÓN ==========
    st.subheader("Calendario de Actividades")
    
    # Controles de vista mejorados
    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
    
    with col1:
        # Configurar opciones de vista según el modo
        if is_read_only_mode():
            view_options = ["Vista por Mes", "Año Completo"]
        else:
            view_options = ["Vista por Mes", "Edición por Año", "Año Completo"]
        
        view_type = st.selectbox(
            "Vista del calendario:",
            view_options,
            help="Selecciona cómo quieres ver el calendario",
            key=f"view_type_{client_id}"
        )
    
    with col2:
        if view_type == "Vista por Mes":
            # Selector de mes para vista mensual
            months = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                      'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
            
            selected_month = st.selectbox(
                "Selecciona el mes:",
                months,
                index=datetime.now().month - 1,  # Mes actual como default
                key=f"month_selector_{client_id}"
            )
    
    with col3:
        # Información adicional según la vista
        if view_type == "Vista por Mes":
            st.write("*Vista de solo lectura*")
        elif view_type == "Edición por Año":
            if not is_read_only_mode():
                st.write("*Vista editable*")
        elif view_type == "Año Completo":
            st.write("*Vista completa*")
    
    with col4:
        if not is_read_only_mode():
            if st.button("Recalcular", key=f"recalc_{client_id}"):
                with st.spinner("Recalculando fechas..."):
                    recalculate_client_dates(client_id)
                st.success("Fechas recalculadas")
                st.rerun()
        else:
            st.button("Recalcular", key=f"recalc_{client_id}", disabled=True, help="No disponible en producción")
    
    # Información de estado del calendario
    dates_df = get_calculated_dates(client_id)
    if not dates_df.empty:
        total_dates = len(dates_df)
        activities_count = len(dates_df['activity_name'].unique())
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Fechas", total_dates)
        with col2:
            st.metric("Actividades", activities_count)
        with col3:
            # Próxima fecha
            try:
                future_dates = dates_df[pd.to_datetime(dates_df['date']) > datetime.now()]
                if not future_dates.empty:
                    next_date = future_dates.iloc[0]['date']
                    next_date_obj = datetime.strptime(next_date, '%Y-%m-%d')
                    days_until = (next_date_obj - datetime.now()).days
                    st.metric("Próxima Fecha", f"{days_until} días")
                else:
                    st.metric("Próxima Fecha", "N/A")
            except:
                st.metric("Próxima Fecha", "N/A")
    
    # Mostrar vista según selección
    try:
        if view_type == "Vista por Mes":
            show_monthly_readonly_calendar(client_id, selected_month)
        
        elif view_type == "Edición por Año":
            show_editable_full_year_calendar(client_id)
        
        elif view_type == "Año Completo":
            calendar_df = create_client_calendar_table(client_id, show_full_year=True)
            if not calendar_df.empty:
                st.dataframe(calendar_df, use_container_width=True, hide_index=True)
                
                # Mostrar resumen del año
                try:
                    from calendar_utils import get_client_year_summary
                    summary = get_client_year_summary(client_id)
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total de Fechas", summary['total_fechas'])
                    with col2:
                        st.metric("Actividades", summary['actividades'])
                    with col3:
                        st.metric("Meses con Actividad", summary['meses_con_actividad'])
                    with col4:
                        if summary['proxima_fecha']:
                            next_date = datetime.strptime(summary['proxima_fecha']['fecha'], '%Y-%m-%d')
                            st.metric("Próxima Fecha", next_date.strftime('%d-%b'))
                        else:
                            st.metric("Próxima Fecha", "N/A")
                except:
                    pass
            else:
                st.info("No hay fechas calculadas para mostrar el año completo.")
                
    except Exception as e:
        st.error(f"Error al mostrar el calendario: {e}")
        st.info("Intenta recalcular las fechas o verifica que las actividades estén configuradas correctamente.")
    
    st.divider()
    
    # Sección de configuración de actividades y frecuencias (solo en desarrollo)
    if not is_read_only_mode():
        show_client_activities_section(client_id)
        
        # Sección de acciones rápidas
        st.divider()
        st.subheader("Acciones Rápidas")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if st.button("Exportar Calendario", use_container_width=True, key=f"export_{client_id}"):
                st.info("Funcionalidad de exportar próximamente...")
        
        with col2:
            if st.button("Enviar por Email", use_container_width=True, key=f"email_{client_id}"):
                st.info("Funcionalidad de email próximamente...")
        
        with col3:
            if st.button("Duplicar Configuración", use_container_width=True, key=f"duplicate_{client_id}"):
                st.info("Funcionalidad de duplicar próximamente...")
        
        with col4:
            if st.button("Limpiar Fechas", use_container_width=True, key=f"clear_{client_id}"):
                if st.session_state.get(f'confirm_clear_{client_id}', False):
                    # Ejecutar limpieza
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM calculated_dates WHERE client_id = ?", (client_id,))
                    conn.commit()
                    conn.close()
                    
                    st.success("Fechas eliminadas exitosamente")
                    st.session_state[f'confirm_clear_{client_id}'] = False
                    st.rerun()
                else:
                    st.session_state[f'confirm_clear_{client_id}'] = True
                    st.warning("Presiona nuevamente para confirmar la eliminación de todas las fechas")
                    st.rerun()
        
        with col5:
            # Debug: Mostrar estado actual de confirmación
            confirm_key = f'confirm_delete_{client_id}'
            is_confirmed = st.session_state.get(confirm_key, False)
            
            # Cambiar el estilo del botón si está en modo confirmación
            button_type = "primary" if is_confirmed else "secondary"
            button_text = "CONFIRMAR ELIMINACIÓN" if is_confirmed else "Eliminar Cliente"
            
            if st.button(button_text, use_container_width=True, key=f"delete_client_detail_{client_id}", type=button_type):
                if is_confirmed:
                    # Segunda presión: ejecutar eliminación
                    st.info("Eliminando cliente...")
                    try:
                        if delete_client(client_id):
                            st.success("Cliente eliminado exitosamente")
                            # Limpiar estados específicos del cliente
                            keys_to_delete = [k for k in st.session_state.keys() if str(client_id) in str(k)]
                            for key in keys_to_delete:
                                if key in st.session_state:
                                    del st.session_state[key]
                            
                            # Regresar a la galería
                            st.session_state.show_client_detail = False
                            st.session_state.selected_client = None
                            st.rerun()
                        else:
                            st.error("Error al eliminar el cliente")
                            st.session_state[confirm_key] = False
                    except Exception as e:
                        st.error(f"Error inesperado: {str(e)}")
                        st.session_state[confirm_key] = False
                else:
                    # Primera presión: pedir confirmación
                    st.session_state[confirm_key] = True
                    st.warning("¿Estás seguro? Presiona nuevamente para confirmar la eliminación PERMANENTE del cliente y todos sus datos")
                    st.rerun()
            
            # Mostrar botón de cancelar si está en modo confirmación
            if is_confirmed:
                if st.button("Cancelar", use_container_width=True, key=f"cancel_delete_{client_id}"):
                    st.session_state[confirm_key] = False
                    st.rerun()

# ========== FUNCIONES DE VISTA DE CALENDARIO ==========

def show_monthly_readonly_calendar(client_id, selected_month):
    """Muestra un calendario mensual en formato de tabla simple y compacta"""
    
    dates_df = get_calculated_dates(client_id)
    
    if dates_df.empty:
        st.info("No hay fechas calculadas.")
        return
    
    st.markdown(f"### Calendario de {selected_month}")
    st.write("*Vista de solo lectura - Fechas programadas para este mes*")
    
    # Convertir nombre del mes a número
    months = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
              'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    month_num = months.index(selected_month) + 1
    
    # Filtrar fechas del mes seleccionado
    month_dates = []
    for _, row in dates_df.iterrows():
        try:
            date_obj = datetime.strptime(row['date'], '%Y-%m-%d')
            if date_obj.month == month_num:
                # Mapear días de la semana al español
                days_spanish = {
                    'Monday': 'Lunes',
                    'Tuesday': 'Martes', 
                    'Wednesday': 'Miércoles',
                    'Thursday': 'Jueves',
                    'Friday': 'Viernes',
                    'Saturday': 'Sábado',
                    'Sunday': 'Domingo'
                }
                day_english = date_obj.strftime('%A')
                day_spanish = days_spanish.get(day_english, day_english)
                
                # Mapear meses al español para formato abreviado
                months_spanish = {
                    1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr', 5: 'May', 6: 'Jun',
                    7: 'Jul', 8: 'Ago', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'
                }
                month_abbr = months_spanish[date_obj.month]
                formatted_date = f"{date_obj.day:02d}-{month_abbr}"
                
                month_dates.append({
                    'activity_name': row['activity_name'],
                    'date': date_obj,
                    'date_position': row['date_position'],
                    'formatted_date': formatted_date,
                    'day_name': day_spanish
                })
        except:
            continue
    
    if not month_dates:
        st.info(f"No hay actividades programadas para {selected_month}")
        return
    
    # Mostrar información resumen del mes
    total_dates_month = len(month_dates)
    activities_list = list(set([d['activity_name'] for d in month_dates]))
    activities_count = len(activities_list)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Fechas en el Mes", total_dates_month)
    with col2:
        st.metric("Actividades", activities_count)
    with col3:
        # Próxima fecha del mes
        try:
            future_dates = [d for d in month_dates if d['date'] > datetime.now()]
            if future_dates:
                next_date = min(future_dates, key=lambda x: x['date'])
                days_until = (next_date['date'] - datetime.now()).days
                st.metric("Próxima Fecha", f"{days_until} días")
            else:
                st.metric("Próxima Fecha", "N/A")
        except:
            st.metric("Próxima Fecha", "N/A")
    
    # Crear tabla agrupada por actividad - solo fechas del mes seleccionado
    table_data = {}
    date_details = {}  # Para almacenar detalles de fecha y día
    
    # Agrupar fechas por actividad y posición, solo para este mes
    for date_info in month_dates:
        activity = date_info['activity_name']
        position = date_info['date_position']
        
        if activity not in table_data:
            table_data[activity] = {}
            date_details[activity] = {}
        
        table_data[activity][position] = date_info['formatted_date']
        date_details[activity][position] = date_info['day_name']
    
    # Crear DataFrame para la tabla con fechas y días alternados
    table_rows = []
    
    # Determinar cuántas fechas tiene cada actividad en este mes específico
    for activity in sorted(table_data.keys()):
        row = {'Actividad': activity}
        activity_positions = sorted(table_data[activity].keys())
        
        # Agregar columnas alternando Fecha y Día para cada posición que existe en este mes
        for i, pos in enumerate(activity_positions, 1):
            fecha_col = f'Fecha {i}'
            dia_col = f'Día {i}'
            
            row[fecha_col] = table_data[activity][pos]
            row[dia_col] = date_details[activity][pos]
        
        table_rows.append(row)
    
    if table_rows:
        df_table = pd.DataFrame(table_rows)
        
        # Configurar columnas para mejor visualización
        column_config = {
            'Actividad': st.column_config.TextColumn(
                'Actividad',
                width='medium',
                help='Nombre de la actividad'
            )
        }
        
        # Configurar columnas de fecha y día
        for col in df_table.columns:
            if col.startswith('Fecha'):
                column_config[col] = st.column_config.TextColumn(
                    col,
                    width='small',
                    help=f'Fecha programada'
                )
            elif col.startswith('Día'):
                column_config[col] = st.column_config.TextColumn(
                    col,
                    width='small',
                    help=f'Día de la semana'
                )
        
        # Mostrar tabla
        st.dataframe(
            df_table,
            column_config=column_config,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No hay fechas para mostrar en formato de tabla.")

# ========== FUNCIONES DE EDICIÓN DE FECHAS ==========

def show_inline_editable_calendar(client_id):
    """Muestra una tabla con edición inline usando st.data_editor - Todas las fechas del cliente"""
    
    # En modo de solo lectura, mostrar mensaje y salir
    if is_read_only_mode():
        st.warning("**Edición No Disponible en Producción**")
        st.info("Esta vista de edición está deshabilitada en el entorno de producción.")
        return
    
    dates_df = get_calculated_dates(client_id)
    
    if dates_df.empty:
        st.info("No hay fechas calculadas.")
        return
    
    st.markdown("### Edición Completa de Fechas")
    st.write("*Edita todas las fechas del cliente simultáneamente en la tabla*")
    
    # Mostrar información sobre las fechas
    total_dates = len(dates_df)
    activities_count = len(dates_df['activity_name'].unique())
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Fechas", total_dates)
    with col2:
        st.metric("Actividades", activities_count)
    with col3:
        max_dates_per_activity = dates_df.groupby('activity_name')['date_position'].max().max()
        st.metric("Máx. Fechas/Actividad", max_dates_per_activity)
    
    # Preparar datos para st.data_editor
    edit_df = prepare_calendar_for_editing(dates_df)
    
    if edit_df.empty:
        st.info("No hay datos para mostrar.")
        return
    
    # Configurar columnas editables
    column_config = {}
    for col in edit_df.columns:
        if col != 'Actividad':
            column_config[col] = st.column_config.DateColumn(
                col,
                help=f"Edita la {col.lower()}",
                format="DD/MM/YYYY",
                step=1,
            )
    
    # Editor de datos
    edited_df = st.data_editor(
        edit_df,
        column_config=column_config,
        use_container_width=True,
        num_rows="fixed",
        key=f"calendar_editor_{client_id}"
    )
    
    # Instrucciones de uso
    st.info("""
    **Instrucciones:**
    - Haz clic en cualquier celda de fecha para editarla
    - Puedes añadir nuevas fechas en las columnas vacías
    - Las fechas se organizan por posición (Fecha 1, Fecha 2, etc.)
    - Los cambios se muestran en tiempo real en la parte inferior
    """)
    
    # Detectar cambios y guardar
    if not edit_df.equals(edited_df):
        st.markdown("### Cambios Detectados")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("Guardar Cambios", 
                        key=f"save_inline_{client_id}",
                        type="primary",
                        use_container_width=True):
                save_inline_changes(client_id, edit_df, edited_df)
                st.success("Cambios guardados exitosamente")
                st.rerun()
        
        with col2:
            if st.button("Descartar Cambios",
                        key=f"discard_inline_{client_id}",
                        use_container_width=True):
                st.rerun()
        
        # Mostrar preview de cambios
        show_changes_preview(edit_df, edited_df)
    else:
        st.markdown("### Sin Cambios Pendientes")
        st.info("Edita las fechas en la tabla superior para ver los cambios aquí.")

def show_monthly_editable_calendar(client_id):
    """Muestra un calendario mensual editable con navegación entre meses"""
    
    # En modo de solo lectura, mostrar mensaje y salir
    if is_read_only_mode():
        st.warning("**Edición No Disponible en Producción**")
        st.info("Esta vista de edición está deshabilitada en el entorno de producción.")
        return
    
    dates_df = get_calculated_dates(client_id)
    
    if dates_df.empty:
        st.info("No hay fechas calculadas.")
        return
    
    st.markdown("### Calendario Mensual Editable")
    st.write("*Navega por los meses y edita las fechas de cada uno*")
    
    # Información general
    total_dates = len(dates_df)
    activities_count = len(dates_df['activity_name'].unique())
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total de Fechas", total_dates)
    with col2:
        st.metric("Actividades", activities_count)
    
    # Selector de mes
    months = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
              'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    
    selected_month = st.selectbox(
        "Selecciona el mes:",
        months,
        index=datetime.now().month - 1,  # Mes actual como default
        key=f"month_selector_{client_id}"
    )
    
    month_num = months.index(selected_month) + 1
    
    # Filtrar fechas del mes seleccionado
    month_dates = []
    for _, row in dates_df.iterrows():
        try:
            date_obj = datetime.strptime(row['date'], '%Y-%m-%d')
            if date_obj.month == month_num:
                month_dates.append({
                    'activity_name': row['activity_name'],
                    'date': date_obj.date(),
                    'date_position': row['date_position'],
                    'original_date_str': row['date']
                })
        except:
            continue
    
    if not month_dates:
        st.info(f"No hay actividades programadas para {selected_month}")
        return
    
    # Crear DataFrame para el editor
    activities = {}
    for date_info in month_dates:
        activity = date_info['activity_name']
        if activity not in activities:
            activities[activity] = {}
        activities[activity][date_info['date_position']] = date_info['date']
    
    # Determinar el número máximo de fechas para este mes
    max_dates = max(len(dates) for dates in activities.values()) if activities else 0
    max_dates = max(max_dates, 6)  # Mínimo 6 columnas
    
    # Preparar datos para el editor
    edit_data = []
    for activity, dates in activities.items():
        row_data = {'Actividad': activity}
        for i in range(1, max_dates + 1):
            row_data[f'Fecha {i}'] = dates.get(i, None)
        edit_data.append(row_data)
    
    if not edit_data:
        st.info(f"No hay datos para mostrar en {selected_month}")
        return
    
    edit_df = pd.DataFrame(edit_data)
    
    # Configurar columnas editables
    column_config = {}
    for col in edit_df.columns:
        if col != 'Actividad':
            column_config[col] = st.column_config.DateColumn(
                col,
                help=f"Edita la {col.lower()} para {selected_month}",
                format="DD/MM/YYYY",
                step=1,
            )
    
    # Editor de datos
    edited_df = st.data_editor(
        edit_df,
        column_config=column_config,
        use_container_width=True,
        num_rows="fixed",
        key=f"monthly_calendar_editor_{client_id}_{month_num}"
    )
    
    # Instrucciones específicas para la vista mensual
    st.info(f"""
    **Instrucciones para {selected_month}:**
    - Edita las fechas directamente en la tabla
    - Solo se muestran las fechas del mes seleccionado
    - Cambia de mes usando el selector superior
    - Los cambios se guardan automáticamente
    """)
    
    # Detectar cambios y guardar
    if not edit_df.equals(edited_df):
        st.markdown("### Cambios Detectados")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("Guardar Cambios", 
                        key=f"save_monthly_{client_id}_{month_num}",
                        type="primary",
                        use_container_width=True):
                save_monthly_changes(client_id, edit_df, edited_df, month_num)
                st.success(f"Cambios guardados para {selected_month}")
                st.rerun()
        
        with col2:
            if st.button("Descartar Cambios",
                        key=f"discard_monthly_{client_id}_{month_num}",
                        use_container_width=True):
                st.rerun()
        
        # Mostrar preview de cambios
        show_monthly_changes_preview(edit_df, edited_df, selected_month)
    else:
        st.markdown("### Sin Cambios Pendientes")
        st.info(f"Edita las fechas en la tabla superior para ver los cambios de {selected_month}.")

def show_editable_full_year_calendar(client_id):
    """Muestra un calendario anual editable por meses"""
    
    # En modo de solo lectura, redirigir a vista de solo lectura
    if is_read_only_mode():
        st.warning("**Vista de Edición No Disponible en Producción**")
        st.info("Mostrando vista de solo lectura del calendario completo")
        calendar_df = create_client_calendar_table(client_id, show_full_year=True)
        if not calendar_df.empty:
            st.dataframe(calendar_df, use_container_width=True, hide_index=True)
        else:
            st.info("No hay fechas calculadas para este cliente.")
        return
    
    dates_df = get_calculated_dates(client_id)
    
    if dates_df.empty:
        st.info("No hay fechas calculadas para mostrar el año completo.")
        return
    
    st.markdown("### Calendario Anual Editable")
    
    # Crear tabs por trimestres
    months = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
              'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    
    # Dividir en 4 grupos de 3 meses
    quarters = [
        ("Q1", months[0:3]),    # Enero-Marzo
        ("Q2", months[3:6]),    # Abril-Junio  
        ("Q3", months[6:9]),    # Julio-Septiembre
        ("Q4", months[9:12])    # Octubre-Diciembre
    ]
    
    # Crear tabs por trimestre
    quarter_tabs = st.tabs([f"{q[0]} ({q[1][0][:3]}-{q[1][-1][:3]})" for q in quarters])
    
    for quarter_idx, (quarter_name, quarter_months) in enumerate(quarters):
        with quarter_tabs[quarter_idx]:
            
            # Crear sub-tabs para cada mes del trimestre
            month_tabs = st.tabs(quarter_months)
            
            for month_idx, month in enumerate(quarter_months):
                with month_tabs[month_idx]:
                    month_num = months.index(month) + 1
                    show_editable_month_view(client_id, month_num, month, dates_df)

def show_editable_month_view(client_id, month_num, month_name, dates_df):
    """Muestra la vista editable de un mes específico optimizada en bloques de 4"""
    
    # Filtrar fechas del mes
    month_dates = []
    for _, row in dates_df.iterrows():
        try:
            date_obj = datetime.strptime(row['date'], '%Y-%m-%d')
            if date_obj.month == month_num:
                month_dates.append({
                    'activity': row['activity_name'],
                    'date': date_obj,
                    'position': row['date_position'],
                    'original_date_str': row['date']
                })
        except:
            continue
    
    if not month_dates:
        st.info(f"No hay actividades programadas para {month_name}")
        return
    
    # Agrupar por actividad
    activities = {}
    for date_info in month_dates:
        activity = date_info['activity']
        if activity not in activities:
            activities[activity] = []
        activities[activity].append(date_info)
    
    # Mostrar cada actividad del mes en bloques optimizados
    for activity, dates in activities.items():
        st.markdown(f"**{activity}**")
        
        # Dividir fechas en bloques de 4 para optimizar el espacio
        dates_sorted = sorted(dates, key=lambda x: x['position'])
        
        # Procesar en bloques de 4
        for i in range(0, len(dates_sorted), 4):
            block_dates = dates_sorted[i:i+4]
            
            # Crear 4 columnas para el bloque
            cols = st.columns(4)
            
            for idx, date_info in enumerate(block_dates):
                with cols[idx]:
                    # Contenedor compacto para cada fecha
                    with st.container():
                        st.markdown(f"**Fecha {date_info['position']}**")
                        
                        # Input de fecha más compacto
                        new_date = st.date_input(
                            "",  # Sin label para ahorrar espacio
                            value=date_info['date'].date(),
                            key=f"month_edit_{client_id}_{activity}_{date_info['position']}_{month_num}",
                            help=f"Editar fecha {date_info['position']} para {activity}",
                            format="DD/MM/YYYY"
                        )
                        
                        # Indicador visual de cambio
                        if new_date != date_info['date'].date():
                            st.markdown("*Modificada*")
                        
                        # Botón de guardado compacto
                        if st.button("Guardar", 
                                   key=f"save_month_{client_id}_{activity}_{date_info['position']}_{month_num}",
                                   help="Guardar esta fecha",
                                   use_container_width=True):
                            # Manejo seguro de fechas
                            date_str = new_date.strftime('%Y-%m-%d') if hasattr(new_date, 'strftime') else str(new_date)
                            update_calculated_date(client_id, activity, date_info['position'], date_str)
                            st.success("Actualizada")
                            st.rerun()
            
            # Espaciado entre bloques
            if i + 4 < len(dates_sorted):
                st.markdown("<br>", unsafe_allow_html=True)
        
        # Botón para guardar todas las fechas de la actividad
        st.markdown("---")
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button(f"Guardar todas las fechas de {activity}", 
                        key=f"save_all_{client_id}_{activity}_{month_num}",
                        use_container_width=True):
                changes_made = 0
                for date_info in dates_sorted:
                    # Obtener el valor actual del input
                    input_key = f"month_edit_{client_id}_{activity}_{date_info['position']}_{month_num}"
                    if input_key in st.session_state:
                        new_date = st.session_state[input_key]
                        if new_date != date_info['date'].date():
                            date_str = new_date.strftime('%Y-%m-%d')
                            update_calculated_date(client_id, activity, date_info['position'], date_str)
                            changes_made += 1
                
                if changes_made > 0:
                    st.success(f"{changes_made} fechas actualizadas para {activity}")
                    st.rerun()
                else:
                    st.info("No hay cambios para guardar")
        
        st.markdown("---")

def prepare_calendar_for_editing(dates_df):
    """Prepara los datos del calendario para edición inline - Muestra todas las fechas disponibles"""
    
    if dates_df.empty:
        return pd.DataFrame()
    
    # Crear tabla pivoteada
    activities = dates_df['activity_name'].unique()
    
    # Determinar el número máximo de fechas que tiene cualquier actividad
    max_dates = 0
    for activity in activities:
        activity_dates = dates_df[dates_df['activity_name'] == activity]
        if not activity_dates.empty:
            max_position = activity_dates['date_position'].max()
            max_dates = max(max_dates, max_position)
    
    # Si no hay fechas, crear al menos 12 columnas para permitir agregar fechas
    if max_dates == 0:
        max_dates = 12
    
    # Asegurar que tengamos al menos 12 columnas para fechas (un año completo)
    max_dates = max(max_dates, 12)
    
    # Crear estructura base
    result_data = []
    
    for activity in activities:
        activity_dates = dates_df[dates_df['activity_name'] == activity].sort_values('date_position')
        
        row_data = {'Actividad': activity}
        
        # Agregar todas las fechas disponibles
        for i in range(1, max_dates + 1):
            date_row = activity_dates[activity_dates['date_position'] == i]
            
            if not date_row.empty:
                try:
                    date_obj = datetime.strptime(date_row.iloc[0]['date'], '%Y-%m-%d').date()
                    row_data[f'Fecha {i}'] = date_obj
                except:
                    row_data[f'Fecha {i}'] = None
            else:
                row_data[f'Fecha {i}'] = None
        
        result_data.append(row_data)
    
    return pd.DataFrame(result_data)


def save_inline_changes(client_id, original_df, edited_df):
    """Guarda los cambios realizados en el editor inline - Maneja todas las fechas disponibles"""
    
    for idx, row in edited_df.iterrows():
        activity = row['Actividad']
        
        # Recopilar fechas editadas (buscar todas las columnas de fechas)
        dates_list = []
        i = 1
        while f'Fecha {i}' in row:
            col_name = f'Fecha {i}'
            date_value = row[col_name]
            
            if pd.notna(date_value) and date_value is not None:
                # Manejo más robusto de diferentes tipos de fecha
                try:
                    if hasattr(date_value, 'strftime'):
                        # Es un objeto datetime o date
                        dates_list.append(date_value.strftime('%Y-%m-%d'))
                    elif isinstance(date_value, str):
                        # Es una string, verificar si es una fecha válida
                        if date_value.strip():
                            # Intentar parsear como fecha
                            try:
                                parsed_date = pd.to_datetime(date_value)
                                dates_list.append(parsed_date.strftime('%Y-%m-%d'))
                            except:
                                dates_list.append(date_value)
                        else:
                            dates_list.append(None)
                    else:
                        # Intentar convertir a string y luego a fecha
                        try:
                            date_str = str(date_value)
                            if date_str and date_str != 'nan':
                                parsed_date = pd.to_datetime(date_str)
                                dates_list.append(parsed_date.strftime('%Y-%m-%d'))
                            else:
                                dates_list.append(None)
                        except:
                            dates_list.append(None)
                except Exception as e:
                    print(f"Error procesando fecha en posición {i}: {e}")
                    dates_list.append(None)
            else:
                dates_list.append(None)
            i += 1
        
        # Guardar en la base de datos
        save_calculated_dates(client_id, activity, dates_list)

def save_monthly_changes(client_id, original_df, edited_df, month_num):
    """Guarda los cambios realizados en el editor mensual"""
    
    for idx, row in edited_df.iterrows():
        activity = row['Actividad']
        
        # Recopilar fechas editadas del mes
        dates_list = []
        i = 1
        while f'Fecha {i}' in row:
            col_name = f'Fecha {i}'
            date_value = row[col_name]
            
            if pd.notna(date_value) and date_value is not None:
                # Manejo más robusto de diferentes tipos de fecha
                try:
                    if hasattr(date_value, 'strftime'):
                        dates_list.append(date_value.strftime('%Y-%m-%d'))
                    elif isinstance(date_value, str):
                        if date_value.strip():
                            try:
                                parsed_date = pd.to_datetime(date_value)
                                dates_list.append(parsed_date.strftime('%Y-%m-%d'))
                            except:
                                dates_list.append(date_value)
                        else:
                            dates_list.append(None)
                    else:
                        try:
                            date_str = str(date_value)
                            if date_str and date_str != 'nan':
                                parsed_date = pd.to_datetime(date_str)
                                dates_list.append(parsed_date.strftime('%Y-%m-%d'))
                            else:
                                dates_list.append(None)
                        except:
                            dates_list.append(None)
                except Exception as e:
                    print(f"Error procesando fecha en posición {i}: {e}")
                    dates_list.append(None)
            else:
                dates_list.append(None)
            i += 1
        
        # Guardar en la base de datos
        save_calculated_dates(client_id, activity, dates_list)

def show_monthly_changes_preview(original_df, edited_df, month_name):
    """Muestra un preview de los cambios realizados en el mes específico"""
    
    st.subheader(f"Cambios en {month_name}")
    
    changes_found = False
    
    for idx, (orig_row, edit_row) in enumerate(zip(original_df.iterrows(), edited_df.iterrows())):
        orig_data = orig_row[1]
        edit_data = edit_row[1]
        
        activity = edit_data['Actividad']
        
        # Buscar diferencias
        for col in orig_data.index:
            if col != 'Actividad':
                orig_val = orig_data[col]
                edit_val = edit_data[col]
                
                # Comparar valores (teniendo en cuenta NaT y None)
                if pd.isna(orig_val) and pd.isna(edit_val):
                    continue
                elif pd.isna(orig_val) or pd.isna(edit_val):
                    if not changes_found:
                        changes_found = True
                    
                    # Manejo seguro de fechas
                    if pd.isna(orig_val):
                        orig_str = "Sin fecha"
                    elif hasattr(orig_val, 'strftime'):
                        orig_str = orig_val.strftime('%d/%m/%Y')
                    else:
                        orig_str = str(orig_val)
                    
                    if pd.isna(edit_val):
                        edit_str = "Sin fecha"
                    elif hasattr(edit_val, 'strftime'):
                        edit_str = edit_val.strftime('%d/%m/%Y')
                    else:
                        edit_str = str(edit_val)
                    
                    st.write(f"**{activity}** - {col}: `{orig_str}` → `{edit_str}`")
                
                elif orig_val != edit_val:
                    if not changes_found:
                        changes_found = True
                    
                    # Manejo seguro de fechas para cambios
                    orig_str = orig_val.strftime('%d/%m/%Y') if hasattr(orig_val, 'strftime') else str(orig_val)
                    edit_str = edit_val.strftime('%d/%m/%Y') if hasattr(edit_val, 'strftime') else str(edit_val)
                    
                    st.write(f"**{activity}** - {col}: `{orig_str}` → `{edit_str}`")
    
    if not changes_found:
        st.info(f"No se detectaron cambios para {month_name}.")

def show_changes_preview(original_df, edited_df):
    """Muestra un preview de los cambios realizados"""
    
    st.subheader("Preview de Cambios")
    
    changes_found = False
    
    for idx, (orig_row, edit_row) in enumerate(zip(original_df.iterrows(), edited_df.iterrows())):
        orig_data = orig_row[1]
        edit_data = edit_row[1]
        
        activity = edit_data['Actividad']
        
        # Buscar diferencias
        for col in orig_data.index:
            if col != 'Actividad':
                orig_val = orig_data[col]
                edit_val = edit_data[col]
                
                # Comparar valores (teniendo en cuenta NaT y None)
                if pd.isna(orig_val) and pd.isna(edit_val):
                    continue
                elif pd.isna(orig_val) or pd.isna(edit_val):
                    if not changes_found:
                        changes_found = True
                    
                    # Manejo seguro de fechas
                    if pd.isna(orig_val):
                        orig_str = "Sin fecha"
                    elif hasattr(orig_val, 'strftime'):
                        orig_str = orig_val.strftime('%d/%m/%Y')
                    else:
                        orig_str = str(orig_val)
                    
                    if pd.isna(edit_val):
                        edit_str = "Sin fecha"
                    elif hasattr(edit_val, 'strftime'):
                        edit_str = edit_val.strftime('%d/%m/%Y')
                    else:
                        edit_str = str(edit_val)
                    
                    st.write(f"**{activity}** - {col}: `{orig_str}` → `{edit_str}`")
                
                elif orig_val != edit_val:
                    if not changes_found:
                        changes_found = True
                    
                    # Manejo seguro de fechas para cambios
                    orig_str = orig_val.strftime('%d/%m/%Y') if hasattr(orig_val, 'strftime') else str(orig_val)
                    edit_str = edit_val.strftime('%d/%m/%Y') if hasattr(edit_val, 'strftime') else str(edit_val)
                    
                    st.write(f"**{activity}** - {col}: `{orig_str}` → `{edit_str}`")
    
    if not changes_found:
        st.info("No se detectaron cambios.")

# ========== FUNCIONES DE ACTIVIDADES ==========

def show_client_activities_section(client_id):
    """Muestra la sección de configuración de actividades y frecuencias"""
    # No mostrar nada en modo de solo lectura
    if is_read_only_mode():
        return
    
    st.subheader("Configurar Actividades y Frecuencias")
    
    activities = get_client_activities(client_id)
    frequency_templates = get_frequency_templates()
    
    if not frequency_templates.empty:
        # Mostrar actividades actuales
        if not activities.empty:
            st.write("**Actividades Actuales:**")
            
            for idx, (_, activity) in enumerate(activities.iterrows()):
                col1, col2, col3 = st.columns([3, 3, 1])
                
                with col1:
                    st.write(f"**{activity['activity_name']}**")
                
                with col2:
                    # Selector de frecuencia para cada actividad
                    current_freq_id = activity['frequency_template_id']
                    current_freq_index = 0
                    
                    freq_options = frequency_templates['name'].tolist()
                    freq_ids = frequency_templates['id'].tolist()
                    
                    try:
                        current_freq_index = freq_ids.index(current_freq_id)
                    except ValueError:
                        current_freq_index = 0
                    
                    new_freq = st.selectbox(
                        "Frecuencia:",
                        freq_options,
                        index=current_freq_index,
                        key=f"freq_{activity['activity_name']}_{idx}",
                        disabled=is_read_only_mode(),
                        help="Solo lectura en producción" if is_read_only_mode() else None
                    )
                    
                    # Actualizar frecuencia si cambió (solo en modo edición)
                    if not is_read_only_mode():
                        new_freq_id = freq_ids[freq_options.index(new_freq)]
                        if new_freq_id != current_freq_id:
                            if st.button("Guardar", key=f"save_freq_{idx}", help="Guardar cambio de frecuencia"):
                                if update_client_activity_frequency(client_id, activity['activity_name'], new_freq_id):
                                    st.success(f"Frecuencia actualizada para {activity['activity_name']}")
                                    st.rerun()
                
                with col3:
                    # Botón para eliminar actividad
                    if not is_read_only_mode():
                        if st.button("Eliminar", key=f"delete_{idx}", help="Eliminar actividad"):
                            if delete_client_activity(client_id, activity['activity_name']):
                                st.success(f"Actividad '{activity['activity_name']}' eliminada")
                                st.rerun()
                            else:
                                st.error("Error al eliminar la actividad")
                    else:
                        st.button("Eliminar", key=f"delete_{idx}", disabled=True, help="No disponible en producción")
            
            st.divider()
        
        # Agregar nueva actividad (solo en modo edición)
        if not is_read_only_mode():
            st.write("**Agregar Nueva Actividad:**")
            
            col1, col2, col3 = st.columns([3, 3, 1])
            
            with col1:
                new_activity_name = st.text_input(
                    "Nombre de la actividad:",
                    placeholder="Ej: Inspección de Calidad",
                    key="new_activity_name"
                )
            
            with col2:
                freq_options = frequency_templates['name'].tolist()
                freq_ids = frequency_templates['id'].tolist()
                
                selected_freq = st.selectbox(
                    "Frecuencia:",
                    freq_options,
                    key="new_activity_freq"
                )
            
            with col3:
                if st.button("Agregar", key="add_activity"):
                    if new_activity_name.strip():
                        selected_freq_id = freq_ids[freq_options.index(selected_freq)]
                        if add_client_activity(client_id, new_activity_name.strip(), selected_freq_id):
                            st.success(f"Actividad '{new_activity_name}' agregada")
                            st.rerun()
                    else:
                        st.error("El nombre de la actividad es obligatorio")
        # No mostrar mensaje en modo de solo lectura, simplemente no mostrar la sección

# ========== FUNCIONES DE MODAL DE EDICIÓN ==========

def show_edit_modal_improved(client):
    """Muestra el modal de edición de cliente - Versión mejorada"""
    # Validar que el cliente existe
    if client is None or len(client) == 0 or 'id' not in client:
        st.error("Error: Datos del cliente no válidos")
        st.session_state.show_edit_modal = False
        return
    
    if is_read_only_mode():
        st.header(f"Ver Cliente: {client['name']}")
        st.warning("**MODO SOLO LECTURA** - No se permiten modificaciones en producción")
        
        # Mostrar solo información de lectura
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("Volver"):
                st.session_state.show_edit_modal = False
                st.rerun()
        
        # Tabs de solo lectura
        tab1, tab2, tab3 = st.tabs(["Datos del Cliente", "Actividades y Frecuencias", "Ver Fechas"])
        
        with tab1:
            show_client_data_tab_improved(client)
        
        with tab2:
            show_activities_management_tab(client)
        
        with tab3:
            show_dates_editing_tab(client)
        return
    
    st.header(f"Editar Cliente: {client['name']}")
    
    # Tabs para organizar mejor el contenido
    tab1, tab2, tab3 = st.tabs(["Datos del Cliente", "Actividades y Frecuencias", "Editar Fechas"])
    
    with tab1:
        show_client_data_tab_improved(client)
    
    with tab2:
        show_activities_management_tab(client)
    
    with tab3:
        show_dates_editing_tab(client)

def show_client_data_tab_improved(client):
    """Pestaña de datos del cliente en el modal de edición - Versión mejorada"""
    if is_read_only_mode():
        st.subheader("Información del Cliente (Solo Lectura)")
        st.info("Los campos están deshabilitados en el entorno de producción")
    else:
        st.subheader("Información del Cliente")
    
    # Validar que client no es None y tiene los datos necesarios
    if client is None:
        st.error("Error: No se pudieron cargar los datos del cliente")
        return
    
    # Crear un key único basado en el ID del cliente
    client_id = client.get('id') if hasattr(client, 'get') else client['id']
    key_prefix = f"edit_client_{client_id}"
    
    # Función auxiliar para obtener valores seguros
    def safe_get(field):
        if hasattr(client, 'get'):
            return client.get(field, '') or ''
        else:
            return client[field] if field in client and client[field] is not None else ''
    
    # Verificar si hay un mensaje de éxito en session_state
    if st.session_state.get(f'{key_prefix}_update_success', False):
        st.success("Cliente actualizado exitosamente! Los cambios se han guardado.")
        # Limpiar el flag después de mostrarlo
        st.session_state[f'{key_prefix}_update_success'] = False
    
    # Verificar si hay un mensaje de error en session_state
    if st.session_state.get(f'{key_prefix}_update_error'):
        st.error(f"{st.session_state[f'{key_prefix}_update_error']}")
        # Limpiar el error después de mostrarlo
        del st.session_state[f'{key_prefix}_update_error']
    
    # Obtener datos actualizados del cliente si acabamos de actualizar
    current_client = client
    if st.session_state.get(f'{key_prefix}_just_updated', False):
        # Recargar datos del cliente desde la base de datos
        updated_client = get_client_by_id(client_id)
        if updated_client is not None:
            current_client = updated_client
        st.session_state[f'{key_prefix}_just_updated'] = False
    
    # Mostrar campos editables (o de solo lectura)
    col1, col2, col3 = st.columns(3)
    
    readonly = is_read_only_mode()
    
    with col1:
        name = st.text_input(
            "Nombre del Cliente", 
            value=safe_get('name') if current_client is client else current_client.get('name', ''),
            key=f"{key_prefix}_name_input",
            help="Edita el nombre del cliente" if not readonly else "Solo lectura en producción",
            disabled=readonly
        )
        codigo_ag = st.text_input(
            "Código AG", 
            value=safe_get('codigo_ag') if current_client is client else current_client.get('codigo_ag', ''),
            key=f"{key_prefix}_codigo_ag_input",
            help="Edita el código AG" if not readonly else "Solo lectura en producción",
            disabled=readonly
        )
        codigo_we = st.text_input(
            "Código WE", 
            value=safe_get('codigo_we') if current_client is client else current_client.get('codigo_we', ''),
            key=f"{key_prefix}_codigo_we_input",
            help="Edita el código WE" if not readonly else "Solo lectura en producción",
            disabled=readonly
        )
    
    with col2:
        csr = st.text_input(
            "CSR", 
            value=safe_get('csr') if current_client is client else current_client.get('csr', ''),
            key=f"{key_prefix}_csr_input",
            help="Edita el CSR" if not readonly else "Solo lectura en producción",
            disabled=readonly
        )
        vendedor = st.text_input(
            "Vendedor", 
            value=safe_get('vendedor') if current_client is client else current_client.get('vendedor', ''),
            key=f"{key_prefix}_vendedor_input",
            help="Edita el vendedor" if not readonly else "Solo lectura en producción",
            disabled=readonly
        )
        calendario_sap = st.text_input(
            "Calendario SAP", 
            value=safe_get('calendario_sap') if current_client is client else current_client.get('calendario_sap', ''),
            key=f"{key_prefix}_calendario_sap_input",
            help="Edita el calendario SAP" if not readonly else "Solo lectura en producción",
            disabled=readonly
        )
    
    with col3:
        # Nuevos campos
        tipos_cliente = get_tipos_cliente()
        current_tipo = safe_get('tipo_cliente') if current_client is client else current_client.get('tipo_cliente', 'Otro')
        try:
            tipo_index = tipos_cliente.index(current_tipo)
        except ValueError:
            tipo_index = tipos_cliente.index('Otro')
        
        tipo_cliente = st.selectbox(
            "Tipo de Cliente",
            tipos_cliente,
            index=tipo_index,
            key=f"{key_prefix}_tipo_cliente_input",
            help="Selecciona el tipo de cliente" if not readonly else "Solo lectura en producción",
            disabled=readonly
        )
        
        regiones = get_regiones()
        current_region = safe_get('region') if current_client is client else current_client.get('region', 'Otro')
        try:
            region_index = regiones.index(current_region)
        except ValueError:
            region_index = regiones.index('Otro')
            
        region = st.selectbox(
            "Región",
            regiones,
            index=region_index,
            key=f"{key_prefix}_region_input",
            help="Selecciona la región" if not readonly else "Solo lectura en producción",
            disabled=readonly
        )
    
    # Verificar si hay cambios (solo si no estamos en modo readonly)
    has_changes = False
    if not readonly:
        original_data = current_client if current_client is not client else client
        has_changes = (
            name != (original_data.get('name', '') if hasattr(original_data, 'get') else original_data['name']) or
            codigo_ag != (original_data.get('codigo_ag', '') or '' if hasattr(original_data, 'get') else original_data['codigo_ag'] or '') or
            codigo_we != (original_data.get('codigo_we', '') or '' if hasattr(original_data, 'get') else original_data['codigo_we'] or '') or
            csr != (original_data.get('csr', '') or '' if hasattr(original_data, 'get') else original_data['csr'] or '') or
            vendedor != (original_data.get('vendedor', '') or '' if hasattr(original_data, 'get') else original_data['vendedor'] or '') or
            calendario_sap != (original_data.get('calendario_sap', '') or '' if hasattr(original_data, 'get') else original_data['calendario_sap'] or '') or
            tipo_cliente != (original_data.get('tipo_cliente', 'Otro') if hasattr(original_data, 'get') else original_data.get('tipo_cliente', 'Otro')) or
            region != (original_data.get('region', 'Otro') if hasattr(original_data, 'get') else original_data.get('region', 'Otro'))
        )
    
    # Mostrar indicador de cambios
    if has_changes:
        st.info("**Hay cambios pendientes de guardar**")
        
        # Mostrar los cambios específicos
        with st.expander("Ver detalles de los cambios"):
            def get_original_value(field):
                if hasattr(original_data, 'get'):
                    value = original_data.get(field, '')
                    # Manejar valores por defecto para los nuevos campos
                    if field in ['tipo_cliente', 'region'] and not value:
                        return 'Otro'
                    return value or ''
                else:
                    value = original_data[field] if field in original_data and original_data[field] is not None else ''
                    # Manejar valores por defecto para los nuevos campos
                    if field in ['tipo_cliente', 'region'] and not value:
                        return 'Otro'
                    return value
            
            if name != get_original_value('name'):
                st.write(f"• **Nombre:** '{get_original_value('name')}' → '{name}'")
            if codigo_ag != get_original_value('codigo_ag'):
                st.write(f"• **Código AG:** '{get_original_value('codigo_ag')}' → '{codigo_ag}'")
            if codigo_we != get_original_value('codigo_we'):
                st.write(f"• **Código WE:** '{get_original_value('codigo_we')}' → '{codigo_we}'")
            if csr != get_original_value('csr'):
                st.write(f"• **CSR:** '{get_original_value('csr')}' → '{csr}'")
            if vendedor != get_original_value('vendedor'):
                st.write(f"• **Vendedor:** '{get_original_value('vendedor')}' → '{vendedor}'")
            if calendario_sap != get_original_value('calendario_sap'):
                st.write(f"• **Calendario SAP:** '{get_original_value('calendario_sap')}' → '{calendario_sap}'")
            if tipo_cliente != get_original_value('tipo_cliente'):
                st.write(f"• **Tipo Cliente:** '{get_original_value('tipo_cliente')}' → '{tipo_cliente}'")
            if region != get_original_value('region'):
                st.write(f"• **Región:** '{get_original_value('region')}' → '{region}'")
    
    # Botones de acción (solo en modo edición)
    if not readonly:
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            if st.button("Guardar Información del Cliente", 
                        use_container_width=True, 
                        key=f"{key_prefix}_save_data",
                        disabled=not has_changes):
                if name.strip():
                    try:
                        with st.spinner("Actualizando cliente..."):
                            # Realizar la actualización
                            success = update_client(client_id, name, codigo_ag, codigo_we, csr, vendedor, calendario_sap, tipo_cliente, region)
                        
                        if success:
                            # Establecer flags para mostrar mensaje de éxito y recargar datos
                            st.session_state[f'{key_prefix}_update_success'] = True
                            st.session_state[f'{key_prefix}_just_updated'] = True
                            
                            # Limpiar los inputs para que se recarguen con los nuevos valores
                            input_keys = [f"{key_prefix}_name_input", f"{key_prefix}_codigo_ag_input", 
                                         f"{key_prefix}_codigo_we_input", f"{key_prefix}_csr_input",
                                         f"{key_prefix}_vendedor_input", f"{key_prefix}_calendario_sap_input",
                                         f"{key_prefix}_tipo_cliente_input", f"{key_prefix}_region_input"]
                            
                            for key in input_keys:
                                if key in st.session_state:
                                    del st.session_state[key]
                            
                            # Hacer rerun para mostrar la actualización SIN cerrar el modal
                            st.rerun()
                        else:
                            st.session_state[f'{key_prefix}_update_error'] = "Error al actualizar cliente en la base de datos"
                            st.rerun()
                            
                    except Exception as e:
                        st.session_state[f'{key_prefix}_update_error'] = f"Error al actualizar cliente: {e}"
                        st.rerun()
                else:
                    st.error("El nombre del cliente es obligatorio")
        
        with col2:
            if st.button("Resetear", 
                        use_container_width=True, 
                        key=f"{key_prefix}_reset_data",
                        help="Restaurar valores originales"):
                # Limpiar los keys de input para forzar recarga con valores originales
                input_keys = [f"{key_prefix}_name_input", f"{key_prefix}_codigo_ag_input", 
                             f"{key_prefix}_codigo_we_input", f"{key_prefix}_csr_input",
                             f"{key_prefix}_vendedor_input", f"{key_prefix}_calendario_sap_input",
                             f"{key_prefix}_tipo_cliente_input", f"{key_prefix}_region_input"]
                
                for key in input_keys:
                    if key in st.session_state:
                        del st.session_state[key]
                
                # Limpiar también los flags de actualización
                if f'{key_prefix}_just_updated' in st.session_state:
                    del st.session_state[f'{key_prefix}_just_updated']
                
                st.rerun()
        
        with col3:
            if st.button("Cerrar", 
                        use_container_width=True, 
                        key=f"{key_prefix}_close_modal",
                        help="Cerrar sin guardar cambios"):
                # Limpiar el modal
                st.session_state.show_edit_modal = False
                # Limpiar todos los estados relacionados con la edición
                keys_to_clear = [key for key in st.session_state.keys() if key.startswith(f'{key_prefix}_')]
                for key in keys_to_clear:
                    del st.session_state[key]
                st.rerun()
    else:
        # En modo solo lectura, solo mostrar botón de cerrar
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("Cerrar", 
                        use_container_width=True, 
                        key=f"{key_prefix}_close_readonly"):
                st.session_state.show_edit_modal = False
                st.rerun()

def show_activities_management_tab(client):
    """Pestaña de gestión de actividades en el modal de edición"""
    # En modo de solo lectura, solo mostrar las actividades sin posibilidad de edición
    if is_read_only_mode():
        st.subheader("Actividades del Cliente (Solo Lectura)")
        
        activities = get_client_activities(client['id'])
        if not activities.empty:
            # Mostrar solo información de lectura
            for _, activity in activities.iterrows():
                st.write(f"• **{activity['activity_name']}**")
        else:
            st.info("No hay actividades configuradas para este cliente.")
        return
    
    st.subheader("Gestión de Actividades y Frecuencias")
    
    activities = get_client_activities(client['id'])
    frequency_templates = get_frequency_templates()
    
    if not frequency_templates.empty:
        # Mostrar actividades actuales en una tabla editable
        if not activities.empty:
            st.write("**Actividades del Cliente:**")
            
            for idx, (_, activity) in enumerate(activities.iterrows()):
                with st.container():
                    st.markdown(f"**{activity['activity_name']}**")
                    
                    col1, col2, col3 = st.columns([4, 4, 1])
                    
                    with col1:
                        st.write(f"*Frecuencia actual: {activity['frequency_name']}*")
                        desc = format_frequency_description(activity['frequency_type'], activity['frequency_config'])
                        st.write(f"*Descripción: {desc}*")
                    
                    with col2:
                        # Selector de nueva frecuencia
                        freq_options = frequency_templates['name'].tolist()
                        freq_ids = frequency_templates['id'].tolist()
                        
                        try:
                            current_index = freq_ids.index(activity['frequency_template_id'])
                        except ValueError:
                            current_index = 0
                        
                        new_freq = st.selectbox(
                            "Cambiar a:",
                            freq_options,
                            index=current_index,
                            key=f"modal_freq_{activity['activity_name']}_{idx}"
                        )
                        
                        new_freq_id = freq_ids[freq_options.index(new_freq)]
                        
                        if new_freq_id != activity['frequency_template_id']:
                            if st.button(f"Actualizar", key=f"modal_update_{idx}"):
                                if update_client_activity_frequency(client['id'], activity['activity_name'], new_freq_id):
                                    st.success(f"Frecuencia actualizada para {activity['activity_name']}")
                                    st.rerun()
                    
                    with col3:
                        if st.button("Eliminar", key=f"modal_delete_{idx}", help="Eliminar actividad"):
                            if delete_client_activity(client['id'], activity['activity_name']):
                                st.success(f"Actividad eliminada")
                                st.rerun()
                    
                    st.divider()
        
        # Formulario para agregar nueva actividad
        st.subheader("Agregar Nueva Actividad")
        
        with st.form("add_activity_modal_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_activity_name = st.text_input("Nombre de la actividad:", placeholder="Ej: Control de Inventario")
            
            with col2:
                freq_options = frequency_templates['name'].tolist()
                freq_ids = frequency_templates['id'].tolist()
                
                selected_freq = st.selectbox("Frecuencia:", freq_options)
            
            if st.form_submit_button("Agregar Actividad"):
                if new_activity_name.strip():
                    selected_freq_id = freq_ids[freq_options.index(selected_freq)]
                    if add_client_activity(client['id'], new_activity_name.strip(), selected_freq_id):
                        st.success(f"Actividad '{new_activity_name}' agregada exitosamente")
                        st.rerun()
                else:
                    st.error("El nombre de la actividad es obligatorio")
        
        # Botón para recalcular fechas después de cambios
        if st.button("Recalcular Todas las Fechas", use_container_width=True):
            with st.spinner("Recalculando fechas para todo el año..."):
                recalculate_client_dates(client['id'])
            st.success("Fechas recalculadas con las nuevas frecuencias")
            st.rerun()

def show_dates_editing_tab(client):
    """Pestaña de edición de fechas en el modal de edición"""
    if is_read_only_mode():
        st.subheader("Fechas del Cliente (Solo Lectura)")
        st.info("La edición de fechas está deshabilitada en el entorno de producción")
        
        # Mostrar fechas en modo de solo lectura
        dates_df = get_calculated_dates(client['id'])
        if not dates_df.empty:
            st.dataframe(dates_df, use_container_width=True, hide_index=True)
        else:
            st.info("No hay fechas calculadas para este cliente.")
        return
    
    st.subheader("Edición Manual de Fechas")
    
    dates_df = get_calculated_dates(client['id'])
    
    if not dates_df.empty and 'activity_name' in dates_df.columns:
        activities_list = dates_df['activity_name'].unique()
        
        # Selector de actividad
        selected_activity = st.selectbox(
            "Selecciona la actividad para editar:",
            activities_list,
            key="modal_activity_selector"
        )
        
        if selected_activity:
            st.write(f"**Editando fechas para: {selected_activity}**")
            activity_dates = dates_df[dates_df['activity_name'] == selected_activity].sort_values('date_position')
            
            # Mostrar las primeras 8 fechas en 2 filas de 4
            edited_dates = {}
            
            for row in range(2):
                cols = st.columns(4)
                for col in range(4):
                    position = row * 4 + col + 1
                    if position <= 8:
                        with cols[col]:
                            matching_row = activity_dates[activity_dates['date_position'] == position]
                            
                            if not matching_row.empty:
                                try:
                                    current_date = datetime.strptime(matching_row.iloc[0]['date'], '%Y-%m-%d').date()
                                except:
                                    current_date = datetime.now().date()
                            else:
                                current_date = datetime.now().date()
                            
                            new_date = st.date_input(
                                f"Fecha {position}",
                                value=current_date,
                                key=f"modal_edit_{selected_activity}_{position}",
                                format="DD/MM/YYYY"
                            )
                            # Manejo seguro de fechas
                            if hasattr(new_date, 'strftime'):
                                edited_dates[position] = new_date.strftime('%Y-%m-%d')
                            else:
                                edited_dates[position] = str(new_date)
            
            # Botón para guardar fechas de esta actividad
            if st.button(f"Guardar fechas de {selected_activity}", 
                        key=f"modal_save_{selected_activity}", 
                        use_container_width=True):
                dates_list = [edited_dates[pos] for pos in range(1, 9)]
                save_calculated_dates(client['id'], selected_activity, dates_list)
                st.success(f"Fechas actualizadas para {selected_activity}")
                st.rerun()
    else:
        st.info("No hay fechas calculadas. Ve a la pestaña 'Actividades y Frecuencias' y presiona 'Recalcular Todas las Fechas'.")

# ========== FUNCIONES DE AGREGAR CLIENTE ==========

def show_add_client():
    """Muestra el formulario para agregar un nuevo cliente"""
    if is_read_only_mode():
        st.header("Agregar Nuevo Cliente")
        st.error("**FUNCIÓN NO DISPONIBLE EN PRODUCCIÓN**")
        st.info("Esta función está deshabilitada en el entorno de producción para mantener la integridad de los datos.")
        return
    
    st.header("Agregar Nuevo Cliente")
    
    # Obtener frecuencias disponibles
    frequency_templates = get_frequency_templates()
    
    if frequency_templates.empty:
        st.error("No hay frecuencias disponibles. Por favor, agrega frecuencias primero en 'Administrar Frecuencias'.")
        return
    
    with st.form("add_client_form"):
        st.subheader("Información del Cliente")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            name = st.text_input("Nombre del Cliente *", placeholder="Ingresa el nombre completo")
            codigo_ag = st.text_input("Código AG", placeholder="Código AG")
            codigo_we = st.text_input("Código WE", placeholder="Código WE")
        
        with col2:
            csr = st.text_input("CSR", placeholder="CSR asignado")
            vendedor = st.text_input("Vendedor", placeholder="Vendedor asignado")
            calendario_sap = st.text_input("Calendario SAP", placeholder="Calendario SAP")
        
        with col3:
            # Nuevos campos
            tipos_cliente = get_tipos_cliente()
            tipo_cliente = st.selectbox(
                "Tipo de Cliente *",
                tipos_cliente,
                index=tipos_cliente.index("Otro")
            )
            
            regiones = get_regiones()
            region = st.selectbox(
                "Región *",
                regiones,
                index=regiones.index("Otro")
            )
        
        st.divider()
        st.subheader("Configuración de Actividades")
        st.write("Define las actividades y sus frecuencias para este cliente:")
        
        # Lista de actividades a configurar
        activities_config = []
        
        # Actividades predeterminadas
        default_activities = ["Fecha envío OC", "Fecha Entrega", "Albaranado", "Embarque"]
        
        freq_options = frequency_templates['name'].tolist()
        freq_ids = frequency_templates['id'].tolist()
        
        for i, activity in enumerate(default_activities):
            st.write(f"**{activity}:**")
            col1, col2 = st.columns([2, 3])
            
            with col1:
                selected_freq = st.selectbox(
                    "Frecuencia:",
                    freq_options,
                    key=f"default_freq_{i}",
                    help=f"Selecciona la frecuencia para {activity}"
                )
            
            with col2:
                # Mostrar descripción de la frecuencia seleccionada
                selected_template = frequency_templates[frequency_templates['name'] == selected_freq].iloc[0]
                desc = format_frequency_description(selected_template['frequency_type'], selected_template['frequency_config'])
                st.info(f"{desc}")
            
            selected_freq_id = freq_ids[freq_options.index(selected_freq)]
            activities_config.append((activity, selected_freq_id))
        
        st.divider()
        
        # Actividades adicionales
        st.subheader("Actividades Adicionales (Opcional)")
        
        num_additional = st.number_input("¿Cuántas actividades adicionales quieres agregar?", 
                                        min_value=0, max_value=5, value=0)
        
        for i in range(num_additional):
            st.write(f"**Actividad Adicional {i+1}:**")
            col1, col2, col3 = st.columns([2, 2, 3])
            
            with col1:
                additional_name = st.text_input(
                    "Nombre:",
                    key=f"additional_name_{i}",
                    placeholder="Ej: Control de Calidad"
                )
            
            with col2:
                additional_freq = st.selectbox(
                    "Frecuencia:",
                    freq_options,
                    key=f"additional_freq_{i}"
                )
            
            with col3:
                if additional_name.strip() and additional_freq:
                    selected_template = frequency_templates[frequency_templates['name'] == additional_freq].iloc[0]
                    desc = format_frequency_description(selected_template['frequency_type'], selected_template['frequency_config'])
                    st.info(f"{desc}")
            
            if additional_name.strip():
                additional_freq_id = freq_ids[freq_options.index(additional_freq)]
                activities_config.append((additional_name.strip(), additional_freq_id))
        
        submitted = st.form_submit_button("Crear Cliente con Configuración", use_container_width=True)
        
        if submitted:
            if name.strip():
                with st.spinner("Creando cliente y configurando actividades..."):
                    # Crear cliente
                    client_id = add_client(name.strip(), codigo_ag, codigo_we, csr, vendedor, calendario_sap, tipo_cliente, region)
                    
                    if client_id:
                        # Agregar actividades configuradas
                        for activity_name, freq_id in activities_config:
                            add_client_activity(client_id, activity_name, freq_id)
                        
                        # Calcular fechas basadas en la configuración
                        recalculate_client_dates(client_id)
                        
                        st.success(f"Cliente '{name}' creado exitosamente con {len(activities_config)} actividades configuradas")
                        
                        # Guardar el ID del cliente recién creado en session_state
                        st.session_state.new_client_created = client_id
                        st.session_state.new_client_name = name
                        
                        # Mostrar las fechas calculadas
                        st.subheader("Calendario Generado")
                        calendar_df = create_client_calendar_table(client_id, show_full_year=False)
                        
                        if not calendar_df.empty:
                            st.dataframe(calendar_df, use_container_width=True, hide_index=True)
                            
                            # Mostrar información del año completo
                            try:
                                from calendar_utils import get_client_year_summary
                                summary = get_client_year_summary(client_id)
                                
                                st.info(f"**Resumen del Año:** {summary['total_fechas']} fechas programadas "
                                       f"en {summary['meses_con_actividad']} meses para {summary['actividades']} actividades")
                            except:
                                pass
                        else:
                            st.warning("No se pudieron calcular las fechas. Puedes configurarlas desde el detalle del cliente.")
                            
                    else:
                        st.error("Error al crear el cliente. Revisa los logs.")
            else:
                st.error("El nombre del cliente es obligatorio")
    
    # Mostrar botón para ver detalle solo si se creó un cliente recientemente
    if st.session_state.get('new_client_created'):
        st.divider()
        st.subheader("¡Cliente Creado Exitosamente!")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(f"Ver Detalle de '{st.session_state.get('new_client_name', 'Cliente')}'", 
                        key="view_new_client_detail", 
                        use_container_width=True,
                        type="primary"):
                st.session_state.selected_client = st.session_state.new_client_created
                st.session_state.show_client_detail = True
                # Limpiar el estado de cliente recién creado
                del st.session_state['new_client_created']
                del st.session_state['new_client_name']
                st.rerun()
        
        # Botón para crear otro cliente
        with col1:
            if st.button("Crear Otro", key="create_another_client"):
                # Limpiar el estado de cliente recién creado
                del st.session_state['new_client_created']
                del st.session_state['new_client_name']
                st.rerun()
        
        with col3:
            if st.button("Ver Galería", key="view_gallery_from_add"):
                # Limpiar el estado de cliente recién creado
                del st.session_state['new_client_created']
                del st.session_state['new_client_name']
                st.rerun()

# ========== FUNCIONES DE GESTIÓN DE FRECUENCIAS ==========

def show_manage_frequencies():
    """Muestra la interfaz de administración de frecuencias"""
    if is_read_only_mode():
        st.header("Administrar Frecuencias")
        st.error("**FUNCIÓN NO DISPONIBLE EN PRODUCCIÓN**")
        st.info("Esta función está deshabilitada en el entorno de producción para mantener la integridad de los datos.")
        return
    
    st.header("Administrar Frecuencias")
    
    # Inicializar estados para la edición
    if 'editing_frequency' not in st.session_state:
        st.session_state.editing_frequency = None
    
    # Mostrar frecuencias existentes en tabla editable
    st.subheader("Frecuencias Disponibles")
    
    templates = get_frequency_templates()
    
    if not templates.empty:
        show_frequency_list(templates)
    
    # Solo mostrar el formulario de agregar si no estamos editando
    if st.session_state.editing_frequency is None:
        show_add_frequency_form()

def show_frequency_list(templates):
    """Muestra la lista de frecuencias con opciones de edición"""
    for idx, (_, template) in enumerate(templates.iterrows()):
        with st.container():
            # Verificar si esta frecuencia está siendo editada
            is_editing = st.session_state.editing_frequency == template['id']
            
            if is_editing:
                show_frequency_edit_form(template)
            else:
                show_frequency_view(template)
            
            st.divider()

def show_frequency_view(template):
    """Muestra la vista normal de una frecuencia"""
    col1, col2, col3, col4 = st.columns([3, 4, 2, 2])
    
    with col1:
        st.write(f"**{template['name']}**")
        st.write(f"*{template['description'] or 'Sin descripción'}*")
    
    with col2:
        # Mostrar configuración legible
        config_text = format_frequency_description(template['frequency_type'], template['frequency_config'])
        st.write(f"**Tipo:** {config_text}")
        
        # Mostrar uso
        usage_count = get_frequency_usage_count(template['id'])
        if usage_count > 0:
            st.write(f"**En uso:** {usage_count} actividad(es)")
        else:
            st.write("**Sin uso**")
    
    with col3:
        if not is_read_only_mode():
            if st.button("Editar", key=f"edit_{template['id']}", use_container_width=True):
                st.session_state.editing_frequency = template['id']
                st.rerun()
        else:
            st.button("Editar", key=f"edit_{template['id']}", disabled=True, use_container_width=True, help="No disponible en producción")
    
    with col4:
        if not is_read_only_mode():
            usage_count = get_frequency_usage_count(template['id'])
            if usage_count == 0:
                if st.button("Eliminar", key=f"delete_{template['id']}", use_container_width=True):
                    success, message = delete_frequency_template(template['id'])
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
            else:
                st.button("En uso", key=f"disabled_{template['id']}", 
                        disabled=True, use_container_width=True,
                        help=f"No se puede eliminar porque está siendo usada por {usage_count} actividad(es)")
        else:
            st.button("Eliminar", key=f"delete_{template['id']}", disabled=True, use_container_width=True, help="No disponible en producción")

def show_frequency_edit_form(template):
    """Muestra el formulario de edición de una frecuencia"""
    st.markdown("### Editando Frecuencia")
    
    with st.form(f"edit_frequency_{template['id']}"):
        col1, col2 = st.columns(2)
        
        with col1:
            edit_name = st.text_input("Nombre:", value=template['name'])
            edit_description = st.text_area("Descripción:", value=template['description'] or "")
        
        with col2:
            edit_freq_type = st.selectbox(
                "Tipo de Frecuencia:",
                ["nth_weekday", "specific_days"],
                index=0 if template['frequency_type'] == "nth_weekday" else 1,
                format_func=lambda x: "Día de la semana específico" if x == "nth_weekday" else "Días específicos del mes"
            )
        
        # Configuración específica basada en el tipo
        edit_freq_config = show_frequency_config_inputs(edit_freq_type, template['frequency_config'])
        
        # Botones del formulario
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.form_submit_button("Guardar Cambios", use_container_width=True):
                if edit_name.strip() and edit_freq_config:
                    if update_frequency_template(
                        template['id'], 
                        edit_name.strip(), 
                        edit_freq_type, 
                        edit_freq_config, 
                        edit_description
                    ):
                        st.success(f"Frecuencia '{edit_name}' actualizada exitosamente")
                        st.session_state.editing_frequency = None
                        st.rerun()
                    else:
                        st.error("Error al actualizar la frecuencia")
                else:
                    st.error("Completa todos los campos obligatorios")
        
        with col2:
            if st.form_submit_button("Cancelar", use_container_width=True):
                st.session_state.editing_frequency = None
                st.rerun()
        
        with col3:
            # Información de uso
            usage_count = get_frequency_usage_count(template['id'])
            if usage_count > 0:
                st.info(f"En uso: {usage_count} actividades")

def show_frequency_config_inputs(freq_type, current_config_json):
    """Muestra los inputs de configuración para una frecuencia"""
    try:
        current_config = json.loads(current_config_json)
    except:
        current_config = {}
    
    if freq_type == "nth_weekday":
        col1, col2 = st.columns(2)
        with col1:
            current_weekday = current_config.get('weekday', 0)
            weekday_names = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
            edit_weekday = st.selectbox(
                "Día de la semana:",
                weekday_names,
                index=current_weekday
            )
        with col2:
            current_weeks = current_config.get('weeks', [1])
            edit_weeks = st.multiselect(
                "Semanas del mes:",
                [1, 2, 3, 4],
                default=current_weeks
            )
        
        if edit_weeks:
            weekday_num = weekday_names.index(edit_weekday)
            return json.dumps({"weekday": weekday_num, "weeks": edit_weeks})
        else:
            return ""
    
    elif freq_type == "specific_days":
        current_days = current_config.get('days', [1])
        edit_days = st.multiselect(
            "Días del mes:",
            list(range(1, 32)),
            default=current_days
        )
        
        if edit_days:
            return json.dumps({"days": edit_days})
        else:
            return ""
    
    return ""

def show_add_frequency_form():
    """Muestra el formulario para agregar una nueva frecuencia"""
    st.subheader("Agregar Nueva Frecuencia")
    
    with st.form("add_frequency_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            freq_name = st.text_input("Nombre de la Frecuencia *", placeholder="Ej: 2do Viernes")
            freq_type = st.selectbox(
                "Tipo de Frecuencia",
                ["nth_weekday", "specific_days"],
                format_func=lambda x: "Día de la semana específico" if x == "nth_weekday" else "Días específicos del mes"
            )
        
        with col2:
            description = st.text_area("Descripción", placeholder="Describe cuándo ocurre esta frecuencia")
        
        if freq_type == "nth_weekday":
            col1, col2 = st.columns(2)
            with col1:
                weekday = st.selectbox(
                    "Día de la semana",
                    ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
                )
            with col2:
                weeks = st.multiselect(
                    "Semanas del mes",
                    [1, 2, 3, 4],
                    help="Selecciona qué semanas del mes (1=primera, 2=segunda, etc.)"
                )
            
            if weeks:
                weekday_num = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"].index(weekday)
                freq_config = json.dumps({"weekday": weekday_num, "weeks": weeks})
            else:
                freq_config = ""
        
        elif freq_type == "specific_days":
            days = st.multiselect(
                "Días del mes",
                list(range(1, 32)),
                help="Selecciona los días específicos del mes"
            )
            
            if days:
                freq_config = json.dumps({"days": days})
            else:
                freq_config = ""
        
        submitted = st.form_submit_button("Agregar Frecuencia", use_container_width=True)
        
        if submitted:
            if freq_name.strip() and freq_config:
                if add_frequency_template(freq_name.strip(), freq_type, freq_config, description):
                    st.success(f"Frecuencia '{freq_name}' agregada exitosamente")
                    st.rerun()
                else:
                    st.error("Error al agregar la frecuencia")
            else:
                st.error("Completa todos los campos obligatorios")

# ========== FUNCIONES DE UTILIDAD Y HELPERS ==========

def show_date_editing_section(client_id):
    """Muestra la sección de edición de fechas individuales (versión legacy)"""
    st.subheader("Editar Fechas")
    
    dates_df = get_calculated_dates(client_id)
    
    if not dates_df.empty and 'activity_name' in dates_df.columns:
        activities = dates_df['activity_name'].unique()
        
        selected_activity = st.selectbox("Selecciona actividad para editar:", activities)
        
        if selected_activity:
            activity_dates = dates_df[dates_df['activity_name'] == selected_activity].sort_values('date_position')
            
            st.write(f"**Fechas para {selected_activity}:**")
            
            # Crear formulario de edición para las primeras 12 fechas
            with st.form(f"edit_dates_{selected_activity}"):
                edited_dates = {}
                
                # Mostrar hasta 12 fechas en 3 filas de 4 columnas
                for row in range(3):
                    cols = st.columns(4)
                    for col in range(4):
                        position = row * 4 + col + 1
                        if position <= 12:
                            with cols[col]:
                                matching_row = activity_dates[activity_dates['date_position'] == position]
                                
                                if not matching_row.empty:
                                    try:
                                        original_date = datetime.strptime(matching_row.iloc[0]['date'], '%Y-%m-%d').date()
                                    except:
                                        original_date = datetime.now().date()
                                else:
                                    original_date = datetime.now().date()
                                
                                new_date = st.date_input(
                                    f"Fecha {position}:",
                                    value=original_date,
                                    key=f"date_{position}_{selected_activity}",
                                    format="DD/MM/YYYY"
                                )
                                # Manejo seguro de fechas
                                if hasattr(new_date, 'strftime'):
                                    edited_dates[position] = new_date.strftime('%Y-%m-%d')
                                else:
                                    edited_dates[position] = str(new_date)
                
                if st.form_submit_button("Guardar Cambios"):
                    # Guardar todas las fechas editadas
                    dates_list = [edited_dates[pos] for pos in range(1, 13)]
                    save_calculated_dates(client_id, selected_activity, dates_list)
                    
                    st.success("Fechas actualizadas exitosamente")
                    st.rerun()
    else:
        st.info("No hay actividades configuradas para editar fechas.")

def format_client_info_card(client):
    """Formatea la información del cliente en una tarjeta"""
    return f"""
    <div style="border: 1px solid #ddd; padding: 15px; border-radius: 10px; margin-bottom: 15px; background-color: #f9f9f9;">
        <h4 style="margin: 0 0 10px 0; color: #2c3e50;">{client['name']}</h4>
        <p style="margin: 5px 0; font-size: 14px;"><strong>Código AG:</strong> {client['codigo_ag'] or 'N/A'}</p>
        <p style="margin: 5px 0; font-size: 14px;"><strong>CSR:</strong> {client['csr'] or 'N/A'}</p>
        <p style="margin: 5px 0; font-size: 14px;"><strong>Vendedor:</strong> {client['vendedor'] or 'N/A'}</p>
    </div>
    """

def clear_client_selection_state():
    """Limpia los estados relacionados con la selección de cliente"""
    keys_to_clear = [
        'show_client_detail', 'selected_client', 'show_edit_modal',
        'edit_name', 'edit_codigo_ag', 'edit_codigo_we', 
        'edit_csr', 'edit_vendedor', 'edit_calendario_sap'
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    # Limpiar también keys que empiecen con 'edit_client_'
    for key in list(st.session_state.keys()):
        if key.startswith('edit_client_'):
            del st.session_state[key]

def show_success_message(message, duration=3):
    """Muestra un mensaje de éxito temporal"""
    success_placeholder = st.empty()
    success_placeholder.success(message)
    
    # Programar limpieza del mensaje (esto es conceptual, streamlit no tiene timers)
    # En la práctica, el mensaje se limpia con st.rerun()

def show_error_message(message):
    """Muestra un mensaje de error"""
    st.error(f"{message}")

def show_info_message(message):
    """Muestra un mensaje informativo"""
    st.info(f"ℹ{message}")

def show_warning_message(message):
    """Muestra un mensaje de advertencia"""
    st.warning(f"{message}")

# ========== FUNCIONES DE VALIDACIÓN ==========

def validate_client_data(name, codigo_ag="", codigo_we="", csr="", vendedor="", calendario_sap=""):
    """Valida los datos del cliente antes de guardar"""
    errors = []
    
    if not name or not name.strip():
        errors.append("El nombre del cliente es obligatorio")
    
    if len(name) > 100:
        errors.append("El nombre del cliente no puede exceder 100 caracteres")
    
    # Validaciones adicionales si es necesario
    if codigo_ag and len(codigo_ag) > 20:
        errors.append("El código AG no puede exceder 20 caracteres")
    
    if codigo_we and len(codigo_we) > 20:
        errors.append("El código WE no puede exceder 20 caracteres")
    
    return errors

def validate_activity_name(activity_name, client_id=None):
    """Valida el nombre de una actividad"""
    errors = []
    
    if not activity_name or not activity_name.strip():
        errors.append("El nombre de la actividad es obligatorio")
    
    if len(activity_name) > 100:
        errors.append("El nombre de la actividad no puede exceder 100 caracteres")
    
    # Verificar duplicados si se proporciona client_id
    if client_id and activity_name.strip():
        activities = get_client_activities(client_id)
        if not activities.empty:
            existing_names = activities['activity_name'].str.lower().tolist()
            if activity_name.strip().lower() in existing_names:
                errors.append(f"Ya existe una actividad llamada '{activity_name.strip()}'")
    
    return errors

def validate_frequency_data(name, frequency_type, frequency_config, description=""):
    """Valida los datos de una frecuencia"""
    errors = []
    
    if not name or not name.strip():
        errors.append("El nombre de la frecuencia es obligatorio")
    
    if not frequency_type:
        errors.append("El tipo de frecuencia es obligatorio")
    
    if not frequency_config:
        errors.append("La configuración de frecuencia es obligatoria")
    
    # Validar formato JSON de la configuración
    try:
        config_dict = json.loads(frequency_config)
        
        if frequency_type == "nth_weekday":
            if 'weekday' not in config_dict or 'weeks' not in config_dict:
                errors.append("Configuración de día de semana incompleta")
            elif not isinstance(config_dict['weeks'], list) or len(config_dict['weeks']) == 0:
                errors.append("Debe seleccionar al menos una semana")
        
        elif frequency_type == "specific_days":
            if 'days' not in config_dict:
                errors.append("Configuración de días específicos incompleta")
            elif not isinstance(config_dict['days'], list) or len(config_dict['days']) == 0:
                errors.append("Debe seleccionar al menos un día")
        
    except json.JSONDecodeError:
        errors.append("Formato de configuración inválido")
    
    return errors

# ========== FUNCIONES DE EXPORTACIÓN Y UTILIDADES AVANZADAS ==========

def export_client_calendar(client_id, format_type="csv"):
    """Exporta el calendario de un cliente (funcionalidad futura)"""
    # Esta función se puede implementar más adelante
    dates_df = get_calculated_dates(client_id)
    
    if dates_df.empty:
        return None
    
    # Preparar datos para exportación
    export_data = prepare_calendar_for_export(dates_df)
    
    if format_type == "csv":
        return export_data.to_csv(index=False)
    elif format_type == "excel":
        # Requiere openpyxl o xlsxwriter
        return export_data.to_excel(index=False)
    else:
        return None

def prepare_calendar_for_export(dates_df):
    """Prepara los datos del calendario para exportación"""
    # Convertir a formato más legible para exportar
    export_data = []
    
    activities = dates_df['activity_name'].unique()
    
    for activity in activities:
        activity_dates = dates_df[dates_df['activity_name'] == activity].sort_values('date_position')
        
        for _, row in activity_dates.iterrows():
            export_data.append({
                'Actividad': activity,
                'Posición': row['date_position'],
                'Fecha': row['date'],
                'Personalizada': 'Sí' if row.get('is_custom', False) else 'No'
            })
    
    return pd.DataFrame(export_data)

def duplicate_client_configuration(source_client_id, target_client_id):
    """Duplica la configuración de actividades de un cliente a otro (funcionalidad futura)"""
    try:
        # Obtener actividades del cliente origen
        source_activities = get_client_activities(source_client_id)
        
        if source_activities.empty:
            return False, "El cliente origen no tiene actividades configuradas"
        
        # Copiar actividades al cliente destino
        for _, activity in source_activities.iterrows():
            add_client_activity(
                target_client_id, 
                activity['activity_name'], 
                activity['frequency_template_id']
            )
        
        # Recalcular fechas para el cliente destino
        recalculate_client_dates(target_client_id)
        
        return True, f"Configuración duplicada exitosamente. {len(source_activities)} actividades copiadas."
        
    except Exception as e:
        return False, f"Error al duplicar configuración: {e}"

def get_calendar_statistics(client_id):
    """Obtiene estadísticas del calendario de un cliente"""
    dates_df = get_calculated_dates(client_id)
    
    if dates_df.empty:
        return {
            'total_dates': 0,
            'activities_count': 0,
            'dates_this_month': 0,
            'dates_next_month': 0,
            'custom_dates': 0
        }
    
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year
    
    # Contar fechas del mes actual
    dates_this_month = 0
    dates_next_month = 0
    custom_dates = 0
    
    for _, row in dates_df.iterrows():
        try:
            date_obj = datetime.strptime(row['date'], '%Y-%m-%d')
            
            if date_obj.year == current_year and date_obj.month == current_month:
                dates_this_month += 1
            
            next_month = current_month + 1 if current_month < 12 else 1
            next_year = current_year if current_month < 12 else current_year + 1
            
            if date_obj.year == next_year and date_obj.month == next_month:
                dates_next_month += 1
            
            if row.get('is_custom', False):
                custom_dates += 1
                
        except:
            continue
    
    return {
        'total_dates': len(dates_df),
        'activities_count': len(dates_df['activity_name'].unique()),
        'dates_this_month': dates_this_month,
        'dates_next_month': dates_next_month,
        'custom_dates': custom_dates
    }