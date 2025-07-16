import streamlit as st
import json
from datetime import datetime
from database import (
    get_clients, get_client_by_id, add_client, update_client,
    get_frequency_templates, add_frequency_template, update_frequency_template,
    delete_frequency_template, get_frequency_usage_count,
    get_client_activities, update_client_activity_frequency,
    add_client_activity, delete_client_activity,
    get_calculated_dates, save_calculated_dates
)
from date_calculator import recalculate_client_dates
from calendar_utils import create_client_calendar_table, format_frequency_description

def show_clients_gallery():
    """Muestra la galería de clientes"""
    st.header("Galería de Clientes")
    
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
    
    # Mostrar galería de clientes
    cols = st.columns(3)
    
    for idx, (_, client) in enumerate(clients.iterrows()):
        with cols[idx % 3]:
            with st.container():
                st.markdown(f"""
                <div style="border: 1px solid #ddd; padding: 15px; border-radius: 10px; margin-bottom: 15px; background-color: #f9f9f9;">
                    <h4 style="margin: 0 0 10px 0; color: #2c3e50;">{client['name']}</h4>
                    <p style="margin: 5px 0; font-size: 14px;"><strong>Código AG:</strong> {client['codigo_ag'] or 'N/A'}</p>
                    <p style="margin: 5px 0; font-size: 14px;"><strong>CSR:</strong> {client['csr'] or 'N/A'}</p>
                    <p style="margin: 5px 0; font-size: 14px;"><strong>Vendedor:</strong> {client['vendedor'] or 'N/A'}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Mostrar mini tabla de calendario
                try:
                    calendar_df = create_client_calendar_table(client['id'], show_full_year=False)
                    if not calendar_df.empty:
                        st.dataframe(
                            calendar_df,
                            use_container_width=True,
                            hide_index=True,
                            height=150
                        )
                    else:
                        st.write("Sin calendario configurado")
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

def show_client_detail():
    """Muestra el detalle de un cliente específico"""
    # Validar que existe un cliente seleccionado
    if not st.session_state.get('selected_client'):
        st.error("No hay cliente seleccionado. Regresando a la galería...")
        st.session_state.show_client_detail = False
        st.rerun()
        return
    
    client_id = st.session_state.selected_client
    
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
    
    # Botón para regresar
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
        if st.button("Editar"):
            st.session_state.show_edit_modal = True
            st.rerun()
    
    # Mostrar modal de edición si está activado
    if st.session_state.get('show_edit_modal', False):
        show_edit_modal(client)
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
    
    # Sección de configuración de actividades y frecuencias
    show_client_activities_section(client_id)
    
    st.divider()
    
    # Calendario completo
    st.subheader("Calendario de Actividades")
    
    # Controles de vista
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        view_type = st.selectbox(
            "Vista del calendario:",
            ["Año Completo", "Vista Compacta", "Por Mes"],
            help="Selecciona cómo quieres ver el calendario"
        )
    
    with col2:
        if view_type == "Por Mes":
            from calendar_utils import get_available_months
            available_months = get_available_months(client_id)
            
            if available_months:
                month_options = [f"{month['month_name']}" for month in available_months]
                month_keys = [month['month_key'] for month in available_months]
                
                selected_month_idx = st.selectbox(
                    "Selecciona el mes:",
                    range(len(month_options)),
                    format_func=lambda x: month_options[x]
                )
                selected_month = month_keys[selected_month_idx]
            else:
                st.info("No hay meses disponibles")
                selected_month = None
        else:
            selected_month = None
    
    with col3:
        if st.button("Recalcular Fechas"):
            with st.spinner("Recalculando fechas para todo el año..."):
                recalculate_client_dates(client_id)
            st.success("Fechas recalculadas exitosamente")
            st.rerun()
    
    # Mostrar calendario según la vista seleccionada
    try:
        if view_type == "Año Completo":
            calendar_df = create_client_calendar_table(client_id, show_full_year=True)
            if not calendar_df.empty:
                st.dataframe(calendar_df, use_container_width=True, hide_index=True)
                
                # Mostrar resumen del año
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
            else:
                st.info("No hay fechas calculadas para mostrar el año completo.")
        
        elif view_type == "Vista Compacta":
            calendar_df = create_client_calendar_table(client_id, show_full_year=False)
            if not calendar_df.empty:
                st.dataframe(calendar_df, use_container_width=True, hide_index=True)
            else:
                st.info("No hay fechas calculadas para la vista compacta.")
        
        elif view_type == "Por Mes" and selected_month:
            from calendar_utils import create_monthly_calendar_view
            monthly_df = create_monthly_calendar_view(client_id, selected_month)
            if not monthly_df.empty:
                st.dataframe(monthly_df, use_container_width=True, hide_index=True)
            else:
                st.info(f"No hay actividades programadas para el mes seleccionado.")
        
        # Edición de fechas (solo para vista compacta)
        if view_type == "Vista Compacta":
            show_date_editing_section(client_id)
            
    except Exception as e:
        st.error(f"Error al mostrar el calendario: {e}")
        st.info("Intenta recalcular las fechas o verifica que las actividades estén configuradas correctamente.")

def show_client_activities_section(client_id):
    """Muestra la sección de configuración de actividades y frecuencias"""
    st.subheader("⚙️ Configurar Actividades y Frecuencias")
    
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
                        key=f"freq_{activity['activity_name']}_{idx}"
                    )
                    
                    # Actualizar frecuencia si cambió
                    new_freq_id = freq_ids[freq_options.index(new_freq)]
                    if new_freq_id != current_freq_id:
                        if st.button(key=f"save_freq_{idx}", help="Guardar cambio de frecuencia"):
                            if update_client_activity_frequency(client_id, activity['activity_name'], new_freq_id):
                                st.success(f"Frecuencia actualizada para {activity['activity_name']}")
                                st.rerun()
                
                with col3:
                    # Botón para eliminar actividad
                    if st.button( key=f"delete_{idx}", help="Eliminar actividad"):
                        if delete_client_activity(client_id, activity['activity_name']):
                            st.success(f"Actividad {activity['activity_name']} eliminada")
                            st.rerun()
            
            st.divider()
        
        # Agregar nueva actividad
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

def show_date_editing_section(client_id):
    """Muestra la sección de edición de fechas individuales"""
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
                                    key=f"date_{position}_{selected_activity}"
                                )
                                edited_dates[position] = new_date.strftime('%Y-%m-%d')
                
                if st.form_submit_button("Guardar Cambios"):
                    # Guardar todas las fechas editadas
                    dates_list = [edited_dates[pos] for pos in range(1, 13)]
                    save_calculated_dates(client_id, selected_activity, dates_list)
                    
                    st.success("Fechas actualizadas exitosamente")
                    st.rerun()
    else:
        st.info("No hay actividades configuradas para editar fechas.")

def show_edit_modal(client):
    """Muestra el modal de edición de cliente"""
    # Validar que el cliente existe - usando len() para pandas Series
    if client is None or len(client) == 0 or 'id' not in client:
        st.error("Error: Datos del cliente no válidos")
        st.session_state.show_edit_modal = False
        return
    
    st.header(f"Editar Cliente: {client['name']}")
    
    # Botón para cerrar modal
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("Cerrar", use_container_width=True, key="close_modal"):
            st.session_state.show_edit_modal = False
            # Limpiar estados de los campos de edición específicos del cliente
            key_prefix = f"edit_client_{client['id']}"
            keys_to_clear = [
                f"{key_prefix}_name", f"{key_prefix}_codigo_ag", f"{key_prefix}_codigo_we", 
                f"{key_prefix}_csr", f"{key_prefix}_vendedor", f"{key_prefix}_calendario_sap"
            ]
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    # Tabs para organizar mejor el contenido
    tab1, tab2, tab3 = st.tabs(["Datos del Cliente"])
    
    with tab1:
        show_client_data_tab(client)

def show_client_data_tab(client):
    """Pestaña de datos del cliente en el modal de edición"""
    st.subheader("Información del Cliente")
    
    # Crear un key único basado en el ID del cliente para evitar conflictos
    key_prefix = f"edit_client_{client['id']}"
    
    # Mostrar campos editables directamente sin session_state complejo
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input(
            "Nombre del Cliente", 
            value=client['name'],
            key=f"{key_prefix}_name_input",
            help="Edita el nombre del cliente"
        )
        codigo_ag = st.text_input(
            "Código AG", 
            value=client['codigo_ag'] or "",
            key=f"{key_prefix}_codigo_ag_input",
            help="Edita el código AG"
        )
        codigo_we = st.text_input(
            "Código WE", 
            value=client['codigo_we'] or "",
            key=f"{key_prefix}_codigo_we_input",
            help="Edita el código WE"
        )
    
    with col2:
        csr = st.text_input(
            "CSR", 
            value=client['csr'] or "",
            key=f"{key_prefix}_csr_input",
            help="Edita el CSR"
        )
        vendedor = st.text_input(
            "Vendedor", 
            value=client['vendedor'] or "",
            key=f"{key_prefix}_vendedor_input",
            help="Edita el vendedor"
        )
        calendario_sap = st.text_input(
            "Calendario SAP", 
            value=client['calendario_sap'] or "",
            key=f"{key_prefix}_calendario_sap_input",
            help="Edita el calendario SAP"
        )
    
    # Verificar si hay cambios
    has_changes = (
        name != client['name'] or
        codigo_ag != (client['codigo_ag'] or "") or
        codigo_we != (client['codigo_we'] or "") or
        csr != (client['csr'] or "") or
        vendedor != (client['vendedor'] or "") or
        calendario_sap != (client['calendario_sap'] or "")
    )
    
    # Mostrar indicador de cambios
    if has_changes:
        st.info("**Hay cambios pendientes de guardar**")
        
        # Mostrar los cambios específicos
        changes_list = []
        if name != client['name']:
            changes_list.append(f"Nombre: '{client['name']}' → '{name}'")
        if codigo_ag != (client['codigo_ag'] or ""):
            changes_list.append(f"Código AG: '{client['codigo_ag'] or ''}' → '{codigo_ag}'")
        if codigo_we != (client['codigo_we'] or ""):
            changes_list.append(f"Código WE: '{client['codigo_we'] or ''}' → '{codigo_we}'")
        if csr != (client['csr'] or ""):
            changes_list.append(f"CSR: '{client['csr'] or ''}' → '{csr}'")
        if vendedor != (client['vendedor'] or ""):
            changes_list.append(f"Vendedor: '{client['vendedor'] or ''}' → '{vendedor}'")
        if calendario_sap != (client['calendario_sap'] or ""):
            changes_list.append(f"Calendario SAP: '{client['calendario_sap'] or ''}' → '{calendario_sap}'")
        
        with st.expander("Ver detalles de los cambios"):
            for change in changes_list:
                st.write(f"• {change}")
    
    # Botón para guardar cambios
    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("Guardar Información del Cliente", 
                    use_container_width=True, 
                    key=f"{key_prefix}_save_data",
                    disabled=not has_changes):
            if name.strip():
                try:
                    # Debug: mostrar qué se va a actualizar
                    st.write("Actualizando cliente...")
                    st.write(f"ID: {client['id']}")
                    st.write(f"Datos nuevos: {name}, {codigo_ag}, {codigo_we}, {csr}, {vendedor}, {calendario_sap}")
                    
                    # Realizar la actualización
                    success = update_client(client['id'], name, codigo_ag, codigo_we, csr, vendedor, calendario_sap)
                    
                    if success:
                        st.success("Cliente actualizado exitosamente en la base de datos")
                        
                        # Esperar un momento para que el usuario vea el mensaje
                        import time
                        time.sleep(1)
                        
                        # Limpiar estados y cerrar modal
                        st.session_state.show_edit_modal = False
                        
                        # Limpiar todos los keys relacionados con este cliente
                        keys_to_clear = []
                        for key in list(st.session_state.keys()):
                            if key.startswith(f"edit_client_{client['id']}"):
                                keys_to_clear.append(key)
                        
                        for key in keys_to_clear:
                            del st.session_state[key]
                        
                        st.rerun()
                    else:
                        st.error("Error al actualizar cliente en la base de datos")
                        st.write("Revisa los logs de la consola para más detalles")
                        
                except Exception as e:
                    st.error(f"Error al actualizar cliente: {e}")
                    import traceback
                    st.code(traceback.format_exc())
            else:
                st.error("El nombre del cliente es obligatorio")
    
    with col2:
        if st.button("Resetear", 
                    use_container_width=True, 
                    key=f"{key_prefix}_reset_data",
                    help="Restaurar valores originales"):
            # Forzar recarga limpiando los keys de input
            for key in list(st.session_state.keys()):
                if key.startswith(f"{key_prefix}_") and key.endswith("_input"):
                    del st.session_state[key]
            st.rerun()

def show_activities_management_tab(client):
    """Pestaña de gestión de actividades en el modal de edición"""
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
                            if st.button(f"💾 Actualizar", key=f"modal_update_{idx}"):
                                if update_client_activity_frequency(client['id'], activity['activity_name'], new_freq_id):
                                    st.success(f"Frecuencia actualizada para {activity['activity_name']}")
                                    st.rerun()
                    
                    with col3:
                        if st.button("🗑️", key=f"modal_delete_{idx}", help="Eliminar actividad"):
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
            
            if st.form_submit_button("➕ Agregar Actividad"):
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
                                key=f"modal_edit_{selected_activity}_{position}"
                            )
                            edited_dates[position] = new_date.strftime('%Y-%m-%d')
            
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

def show_add_client():
    """Muestra el formulario para agregar un nuevo cliente"""
    st.header("Agregar Nuevo Cliente")
    
    # Obtener frecuencias disponibles
    frequency_templates = get_frequency_templates()
    
    if frequency_templates.empty:
        st.error("No hay frecuencias disponibles. Por favor, agrega frecuencias primero en 'Administrar Frecuencias'.")
        return
    
    with st.form("add_client_form"):
        st.subheader("📋 Información del Cliente")
        
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Nombre del Cliente *", placeholder="Ingresa el nombre completo")
            codigo_ag = st.text_input("Código AG", placeholder="Código AG")
            codigo_we = st.text_input("Código WE", placeholder="Código WE")
        
        with col2:
            csr = st.text_input("CSR", placeholder="CSR asignado")
            vendedor = st.text_input("Vendedor", placeholder="Vendedor asignado")
            calendario_sap = st.text_input("Calendario SAP", placeholder="Calendario SAP")
        
        st.divider()
        st.subheader("⚙️ Configuración de Actividades")
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
                st.info(f"📅 {desc}")
            
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
                    client_id = add_client(name.strip(), codigo_ag, codigo_we, csr, vendedor, calendario_sap)
                    
                    if client_id:
                        # Agregar actividades configuradas
                        for activity_name, freq_id in activities_config:
                            add_client_activity(client_id, activity_name, freq_id)
                        
                        # Calcular fechas basadas en la configuración
                        recalculate_client_dates(client_id)
                        
                        st.success(f"Cliente '{name}' creado exitosamente con {len(activities_config)} actividades configuradas")
                        
                        # Mostrar las fechas calculadas
                        st.subheader("Calendario Generado")
                        calendar_df = create_client_calendar_table(client_id, show_full_year=False)
                        
                        if not calendar_df.empty:
                            st.dataframe(calendar_df, use_container_width=True, hide_index=True)
                            
                            # Mostrar información del año completo
                            from calendar_utils import get_client_year_summary
                            summary = get_client_year_summary(client_id)
                            
                            st.info(f"**Resumen del Año:** {summary['total_fechas']} fechas programadas "
                                   f"en {summary['meses_con_actividad']} meses para {summary['actividades']} actividades")
                        else:
                            st.warning("No se pudieron calcular las fechas. Puedes configurarlas desde el detalle del cliente.")
                        
                        st.balloons()
                        
                        # Botón para ir al detalle del cliente
                        if st.button("📋 Ver Detalle del Cliente"):
                            st.session_state.selected_client = client_id
                            st.session_state.show_client_detail = True
                            st.rerun()
                            
                    else:
                        st.error("Error al crear el cliente. Revisa los logs.")
            else:
                st.error("El nombre del cliente es obligatorio")

def show_manage_frequencies():
    """Muestra la interfaz de administración de frecuencias"""
    st.header("⚙️ Administrar Frecuencias")
    
    # Inicializar estados para la edición
    if 'editing_frequency' not in st.session_state:
        st.session_state.editing_frequency = None
    
    # Mostrar frecuencias existentes en tabla editable
    st.subheader("📋 Frecuencias Disponibles")
    
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
        if st.button("Editar", key=f"edit_{template['id']}", use_container_width=True):
            st.session_state.editing_frequency = template['id']
            st.rerun()
    
    with col4:
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
            if st.form_submit_button("❌ Cancelar", use_container_width=True):
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