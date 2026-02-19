"""
Interfaz de usuario para la generación de calendarios
"""

import streamlit as st
import os
import tempfile
from datetime import datetime
from calendar_generator import (
    CalendarGenerator, 
    get_clients_by_type, 
    get_available_client_types,
    get_available_sap_calendar_codes,
    get_clients_by_sap_calendar
)
from database import get_clients, get_client_activities, get_frequency_template_by_id
from auth_system import get_user_country_filter, has_country_filter
import base64
import pandas as pd

def get_client_real_frequencies_table(client_id, client_name):
    """
    Obtiene las frecuencias reales del cliente y las muestra en una tabla
    """
    try:
        activities_df = get_client_activities(client_id)
        if activities_df.empty:
            st.warning(f"No se encontraron actividades para {client_name}")
            return
        
        frequencies_data = []
        for _, activity in activities_df.iterrows():
            activity_name = activity['activity_name']
            frequency_template_id = activity['frequency_template_id']
            
            # Obtener detalles de la frecuencia
            frequency_template = get_frequency_template_by_id(frequency_template_id)
            if frequency_template is not None:
                frequency_name = frequency_template['name'] if 'name' in frequency_template else 'N/A'
                frequencies_data.append({
                    'Actividad': activity_name,
                    'Frecuencia': frequency_name
                })
        
        if frequencies_data:
            st.markdown(f"**📋 Frecuencias de {client_name}:**")
            df_freq = pd.DataFrame(frequencies_data)
            st.dataframe(df_freq, use_container_width=True, hide_index=True)
        else:
            st.info(f"No se encontraron frecuencias configuradas para {client_name}")
            
    except Exception as e:
        st.error(f"Error obteniendo frecuencias para {client_name}: {str(e)}")

def show_multiple_clients_frequencies(clients, max_clients_to_show=5):
    """
    Muestra las frecuencias de múltiples clientes en un formato compacto
    """
    if not clients:
        return
    
    # Limitar número de clientes a mostrar para evitar sobrecargar la interfaz
    clients_to_show = clients[:max_clients_to_show]
    remaining_clients = len(clients) - len(clients_to_show)
    
    st.markdown("**Frecuencias de Clientes Seleccionados:**")
    
    for client in clients_to_show:
        client_id = client.get('id')
        client_name = client.get('nombre_cliente', 'Cliente')
        
        if client_id:
            with st.expander(f"{client_name} (ID: {client_id})", expanded=False):
                get_client_real_frequencies_table(client_id, client_name)
        else:
            st.warning(f"Cliente {client_name} no tiene ID válido")
    
    if remaining_clients > 0:
        st.info(f"Se muestran los primeros {max_clients_to_show} clientes. Hay {remaining_clients} clientes adicionales seleccionados.")

def show_calendar_generator():
    """
    Interfaz principal para la generación de calendarios
    """
    st.header("Generador de Cartas Calendario")
    st.markdown("*Genera cartas calendario personalizadas para clientes en formato Word*")
    
    # Verificar si existe la plantilla
    template_path = "CF PLANTILLA CALENDARIO 2025.docx"
    if not os.path.exists(template_path):
        st.error(f"Plantilla de calendario no encontrada: {template_path}")
        st.info("Por favor, asegúrate de que el archivo de plantilla esté en la carpeta raíz de la aplicación.")
        return
    
    # Filtro de país del usuario
    country_filter = None
    
    # Si el usuario tiene un filtro de país fijo (como GLCOUser)
    if has_country_filter():
        country_filter = get_user_country_filter()
        st.info(f"Vista filtrada: Generando calendarios para clientes de **{country_filter}**")
    
    # Configuración de generación
    st.subheader("Configuración de Generación")
    
    # Fila con 3 columnas para incluir el filtro de país
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Selector de modo de generación
        generation_mode = st.radio(
            "Modo de generación:",
            ["Cliente individual", "Por tipo de cliente", "Por código calendario SAP", "Todos los clientes"],
            help="Selecciona cómo quieres generar los calendarios"
        )
    
    with col2:
        # Año de generación
        current_year = datetime.now().year
        selected_year = st.selectbox(
            "Año del calendario:",
            [current_year, current_year + 1, current_year + 2],
            index=1 if current_year < 2025 else 0,
            help="Selecciona el año para el cual generar los calendarios"
        )
    
    with col3:
        # Filtro de país (solo si no tiene filtro fijo)
        if not has_country_filter():
            from client_constants import get_paises
            paises_options = ['Todos los países'] + get_paises()
            selected_country = st.selectbox(
                "Filtrar por país:",
                paises_options,
                index=0,
                key="calendar_country_filter",
                help="Selecciona un país para filtrar los clientes"
            )
            
            if selected_country != 'Todos los países':
                country_filter = selected_country
                st.info(f"Filtrando: **{country_filter}**")
        else:
            # Mostrar el país filtrado como información
            st.metric("País filtrado", country_filter)
    
    # Mostrar información sobre el método usado
    st.info("**Fechas desde Base de Datos**: Se usarán únicamente las fechas almacenadas en la base de datos. Si no existen fechas para el año seleccionado, no se generará calendario.")
    
    st.divider()
    
    # Selección de clientes según el modo
    selected_clients = []
    
    if generation_mode == "Cliente individual":
        selected_clients = show_individual_client_selection(country_filter)
    elif generation_mode == "Por tipo de cliente":
        selected_clients = show_client_type_selection(country_filter)
    elif generation_mode == "Por código calendario SAP":
        selected_clients = show_sap_calendar_selection(country_filter)
    elif generation_mode == "Todos los clientes":
        selected_clients = show_all_clients_selection(country_filter)
    
    # Mostrar resumen de selección
    if selected_clients:
        st.subheader("Resumen de Selección")
        
        col1, col2 = st.columns(2)
        with col1:
            st.success(f"Se generarán **{len(selected_clients)}** calendarios")
        with col2:
            st.info(f"**Año {selected_year}**: Solo fechas desde base de datos")
        
        # Mostrar lista de clientes seleccionados
        with st.expander("Ver clientes seleccionados con frecuencias reales", expanded=False):
            for client in selected_clients:
                frecuencia_info = client.get('frecuencia', 'N/A')
                st.write(f"- **{client['nombre_cliente']}** ({client.get('tipo_cliente', 'N/A')}) - {client.get('pais', 'N/A')}")
                
                # Mostrar frecuencias reales en línea
                client_id = client.get('id')
                if client_id:
                    try:
                        activities_df = get_client_activities(client_id)
                        if not activities_df.empty:
                            freq_list = []
                            for _, activity in activities_df.iterrows():
                                activity_name = activity['activity_name']
                                frequency_template_id = activity['frequency_template_id']
                                frequency_template = get_frequency_template_by_id(frequency_template_id)
                                if frequency_template is not None:
                                    frequency_name = frequency_template['name'] if 'name' in frequency_template else 'N/A'
                                    freq_list.append(f"{activity_name}: {frequency_name}")
                            
                            if freq_list:
                                st.markdown(f"*{'; '.join(freq_list)}*")
                        else:
                            st.markdown(f"*Sin frecuencias configuradas*")
                    except Exception as e:
                        st.markdown(f"*Error obteniendo frecuencias*")
                else:
                    st.markdown(f"*Cliente sin ID válido*")
        
        st.divider()
        
        # Botón de generación
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Generar Cartas", type="primary", use_container_width=True):
                generate_calendars(selected_clients, selected_year, template_path)
    else:
        st.warning("No hay clientes seleccionados para generar Cartas.")

def show_individual_client_selection(country_filter=None):
    """
    Interfaz para selección de cliente individual
    """
    st.subheader("Selección de Cliente Individual")
    
    # Obtener todos los clientes
    all_clients = get_clients_by_type(country_filter=country_filter)
    
    if not all_clients:
        st.warning("No hay clientes disponibles.")
        return []
    
    # Buscador de clientes
    search_term = st.text_input(
        "Buscar cliente:",
        placeholder="Escribe el nombre del cliente...",
        help="Busca por nombre del cliente"
    )
    
    # Filtrar clientes según búsqueda
    if search_term:
        filtered_clients = [
            client for client in all_clients 
            if search_term.lower() in client.get('nombre_cliente', '').lower()
        ]
    else:
        filtered_clients = all_clients
    
    if filtered_clients:
        # Selector de cliente
        client_options = [f"{client['nombre_cliente']} ({client.get('pais', 'N/A')})" for client in filtered_clients]
        selected_index = st.selectbox(
            "Seleccionar cliente:",
            range(len(client_options)),
            format_func=lambda x: client_options[x],
            help="Selecciona el cliente para generar su calendario"
        )
        
        selected_client = filtered_clients[selected_index]
        
        # Mostrar información del cliente
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("País", selected_client.get('pais', 'N/A'))
        with col2:
            st.metric("Tipo", selected_client.get('tipo_cliente', 'N/A'))
        with col3:
            st.metric("Frecuencia", selected_client.get('frecuencia', 'N/A'))
        
        # Mostrar frecuencias reales del cliente
        client_id = selected_client.get('id')
        if client_id:
            st.divider()
            get_client_real_frequencies_table(client_id, selected_client.get('nombre_cliente', 'Cliente'))
        
        return [selected_client]
    else:
        if search_term:
            st.warning(f"No se encontraron clientes que coincidan con '{search_term}'.")
        return []

def show_client_type_selection(country_filter=None):
    """
    Interfaz para selección por tipo de cliente
    """
    st.subheader("Selección por Tipo de Cliente")
    
    # Obtener tipos disponibles
    available_types = get_available_client_types()
    
    if not available_types:
        st.warning("No hay tipos de cliente disponibles.")
        return []
    
    # Selector de tipo
    selected_type = st.selectbox(
        "Tipo de cliente:",
        ["Todos"] + available_types,
        help="Selecciona el tipo de cliente para filtrar"
    )
    
    # Obtener clientes del tipo seleccionado
    if selected_type == "Todos":
        clients = get_clients_by_type(country_filter=country_filter)
    else:
        clients = get_clients_by_type(tipo_cliente=selected_type, country_filter=country_filter)
    
    if clients:
        st.success(f"Se encontraron **{len(clients)}** clientes del tipo '{selected_type}'")
        
        # Mostrar distribución por país
        if not country_filter:
            countries = {}
            for client in clients:
                country = client.get('pais', 'N/A')
                countries[country] = countries.get(country, 0) + 1
            
            if countries:
                st.write("**Distribución por país:**")
                for country, count in countries.items():
                    st.write(f"- {country}: {count} clientes")
        
        # Mostrar frecuencias de algunos clientes
        st.divider()
        show_multiple_clients_frequencies(clients, max_clients_to_show=3)
        
        return clients
    else:
        st.warning(f"No se encontraron clientes del tipo '{selected_type}'.")
        return []

def show_sap_calendar_selection(country_filter=None):
    """
    Interfaz para selección por código de calendario SAP
    """
    st.subheader("Selección por Código de Calendario SAP")
    
    # Obtener códigos SAP disponibles
    available_sap_codes = get_available_sap_calendar_codes()
    
    if not available_sap_codes:
        st.warning("No hay códigos de calendario SAP disponibles.")
        return []
    
    # Selector de código SAP
    selected_sap_code = st.selectbox(
        "Código de calendario SAP:",
        ["Todos"] + available_sap_codes,
        help="Selecciona el código de calendario SAP para filtrar clientes"
    )
    
    # Obtener clientes con el código SAP seleccionado
    if selected_sap_code == "Todos":
        clients = get_clients_by_sap_calendar(country_filter=country_filter)
    else:
        clients = get_clients_by_sap_calendar(sap_calendar_code=selected_sap_code, country_filter=country_filter)
    
    if clients:
        st.success(f"Se encontraron **{len(clients)}** clientes con código SAP '{selected_sap_code}'")
        
        # Mostrar distribución por tipo de cliente
        col1, col2 = st.columns(2)
        
        with col1:
            types = {}
            for client in clients:
                client_type = client.get('tipo_cliente', 'N/A')
                types[client_type] = types.get(client_type, 0) + 1
            
            st.write("**Distribución por tipo:**")
            for client_type, count in types.items():
                st.write(f"- {client_type}: {count} clientes")
        
        with col2:
            # Mostrar distribución por país (solo si no hay filtro)
            if not country_filter:
                countries = {}
                for client in clients:
                    country = client.get('pais', 'N/A')
                    countries[country] = countries.get(country, 0) + 1
                
                st.write("**Distribución por país:**")
                for country, count in countries.items():
                    st.write(f"- {country}: {count} clientes")
            else:
                st.write(f"**País filtrado:** {country_filter}")
        
        # Mostrar lista de clientes seleccionados
        with st.expander("Ver clientes seleccionados", expanded=False):
            for client in clients:
                st.write(f"- **{client['nombre_cliente']}** - Tipo: {client.get('tipo_cliente', 'N/A')} - País: {client.get('pais', 'N/A')} - Código SAP: {client.get('calendario_sap', 'N/A')}")
        
        # Mostrar frecuencias de algunos clientes
        st.divider()
        show_multiple_clients_frequencies(clients, max_clients_to_show=3)
        
        return clients
    else:
        st.warning(f"No se encontraron clientes con código SAP '{selected_sap_code}'.")
        return []

def show_all_clients_selection(country_filter=None):
    """
    Interfaz para selección de todos los clientes
    """
    st.subheader("Todos los Clientes")
    
    clients = get_clients_by_type(country_filter=country_filter)
    
    if clients:
        st.success(f"Se generarán calendarios para **{len(clients)}** clientes")
        
        # Mostrar estadísticas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Distribución por tipo
            types = {}
            for client in clients:
                client_type = client.get('tipo_cliente', 'N/A')
                types[client_type] = types.get(client_type, 0) + 1
            
            st.write("**Por tipo:**")
            for client_type, count in types.items():
                st.write(f"- {client_type}: {count}")
        
        with col2:
            # Distribución por país (solo si no hay filtro)
            if not country_filter:
                countries = {}
                for client in clients:
                    country = client.get('pais', 'N/A')
                    countries[country] = countries.get(country, 0) + 1
                
                st.write("**Por país:**")
                for country, count in countries.items():
                    st.write(f"- {country}: {count}")
            else:
                st.write(f"**País filtrado:**")
                st.write(f"- {country_filter}: {len(clients)}")
        
        with col3:
            # Distribución por frecuencia
            frequencies = {}
            for client in clients:
                freq = client.get('frecuencia', 'N/A')
                frequencies[freq] = frequencies.get(freq, 0) + 1
            
            st.write("**Por frecuencia:**")
            for freq, count in frequencies.items():
                st.write(f"- {freq}: {count}")
        
        # Mostrar frecuencias reales de algunos clientes
        st.divider()
        show_multiple_clients_frequencies(clients, max_clients_to_show=5)
        
        return clients
    else:
        st.warning("No hay clientes disponibles.")
        return []

def get_sap_folder_name(calendario_sap):
    """
    Obtiene el nombre de carpeta según el código de calendario SAP
    """
    if not calendario_sap or calendario_sap.strip() == '' or calendario_sap.strip() == '0' or calendario_sap.strip().lower() == 'n/a':
        return "Sin calendario"
    return calendario_sap.strip()

def generate_calendars(clients, year, template_path):
    """
    Genera los calendarios para los clientes seleccionados
    Organiza los archivos en carpetas por código de calendario SAP
    """
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Crear directorio temporal
        temp_dir = tempfile.mkdtemp()
        
        # Inicializar generador
        generator = CalendarGenerator(template_path)
        
        # Diccionario para almacenar archivos con su ruta relativa en el ZIP
        generated_files_with_folders = []  # Lista de tuplas (ruta_archivo, carpeta_sap)
        total_clients = len(clients)
        
        for i, client in enumerate(clients):
            try:
                # Actualizar progreso
                progress = (i + 1) / total_clients
                progress_bar.progress(progress)
                status_text.text(f"Generando calendario para {client.get('nombre_cliente', 'Cliente')} ({i+1}/{total_clients})")
                
                # Obtener código de calendario SAP para la carpeta
                calendario_sap = client.get('calendario_sap', '') or client.get('sap_calendar', '') or ''
                folder_name = get_sap_folder_name(calendario_sap)
                
                # Crear subcarpeta si no existe
                folder_path = os.path.join(temp_dir, folder_name)
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)
                
                # Generar documento en la subcarpeta correspondiente
                client_data = dict(client)
                safe_client_name = client.get('nombre_cliente', 'Cliente').replace('/', '_').replace('\\', '_')
                output_path = generator.generate_document(client_data, 
                    output_path=os.path.join(folder_path, f"CF {safe_client_name} CALENDARIO {year}.docx"),
                    year=year)
                
                if os.path.exists(output_path):
                    generated_files_with_folders.append((output_path, folder_name))
                
            except Exception as e:
                st.error(f"Error generando calendario para {client.get('nombre_cliente', 'Cliente')}: {str(e)}")
                continue
        
        # Crear ZIP si hay múltiples archivos
        if generated_files_with_folders:
            if len(generated_files_with_folders) == 1:
                # Un solo archivo - descarga directa (sin carpeta)
                status_text.text("Preparando descarga...")
                
                with open(generated_files_with_folders[0][0], "rb") as file:
                    file_data = file.read()
                
                st.success(f"Carta generada exitosamente!")
                st.download_button(
                    label="Descargar Carta",
                    data=file_data,
                    file_name=os.path.basename(generated_files_with_folders[0][0]),
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            else:
                # Múltiples archivos - crear ZIP con carpetas
                status_text.text("Creando archivo ZIP con carpetas...")
                
                zip_path = generator.create_zip_from_files_with_folders(generated_files_with_folders)
                
                with open(zip_path, "rb") as zip_file:
                    zip_data = zip_file.read()
                
                # Contar carpetas únicas
                unique_folders = set(f[1] for f in generated_files_with_folders)
                
                st.success(f"Se generaron {len(generated_files_with_folders)} cartas en {len(unique_folders)} carpetas!")
                st.download_button(
                    label="Descargar Cartas (ZIP)",
                    data=zip_data,
                    file_name=f"Cartas_GL_{year}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                    mime="application/zip"
                )
        else:
            st.error("No se pudieron generar calendarios.")
        
        progress_bar.progress(1.0)
        status_text.text("Completado!")
        
    except Exception as e:
        st.error(f"Error durante la generación: {str(e)}")
        progress_bar.empty()
        status_text.empty()

def get_file_download_link(file_path, link_text="Descargar"):
    """
    Crea un enlace de descarga para un archivo
    """
    with open(file_path, "rb") as f:
        data = f.read()
    
    b64_data = base64.b64encode(data).decode()
    file_name = os.path.basename(file_path)
    
    href = f'<a href="data:application/octet-stream;base64,{b64_data}" download="{file_name}">{link_text}</a>'
    return href