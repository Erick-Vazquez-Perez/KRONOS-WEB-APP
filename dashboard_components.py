import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
from database import (
    get_db_connection, get_clients, get_calculated_dates,
    get_cache_stats, get_database_statistics, optimize_database,
    clear_cache, get_clients_summary
)
from werfen_styles import get_metric_card_html
import calendar
from anomaly_detector import get_comprehensive_anomalies, get_holidays_for_month, get_incomplete_weeks_info
from auth_system import get_user_country_filter, has_country_filter, auth_system
from client_constants import get_paises


@st.cache_data(ttl=90, show_spinner=False)
def _cached_query_df(query: str, params: tuple):
    """Cache ligero para DataFrames del dashboard (reduce roundtrips a BDD en reruns)."""
    conn = get_db_connection()
    try:
        return pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()

def get_tomorrow_oc_clients(country_filter=None):
    """Obtiene clientes con fecha OC para mañana (o lunes si hoy es viernes) - Versión optimizada con filtro por país"""
    today = datetime.now().date()
    
    # Si hoy es viernes (4), mañana debe ser lunes (agregar 3 días)
    if today.weekday() == 4:  # Viernes
        target_date = today + timedelta(days=3)  # Lunes
    else:
        target_date = today + timedelta(days=1)  # Mañana normal
    
    # Construir query con filtro de país opcional
    if country_filter:
        query = """
        SELECT c.name, c.codigo_ag, c.codigo_we, c.csr, c.vendedor, cd.date, c.tipo_cliente, c.region, c.calendario_sap, c.pais
        FROM clients c
        JOIN calculated_dates cd ON c.id = cd.client_id
        WHERE cd.activity_id = 1
        AND date(cd.date) = ?
        AND c.pais = ?
        ORDER BY c.name
        """
        df = _cached_query_df(query, (target_date.strftime('%Y-%m-%d'), country_filter))
    else:
        query = """
        SELECT c.name, c.codigo_ag, c.codigo_we, c.csr, c.vendedor, cd.date, c.tipo_cliente, c.region, c.calendario_sap, c.pais
        FROM clients c
        JOIN calculated_dates cd ON c.id = cd.client_id
        WHERE cd.activity_id = 1
        AND date(cd.date) = ?
        ORDER BY c.name
        """
        df = _cached_query_df(query, (target_date.strftime('%Y-%m-%d'),))
    
    return df

def get_delivery_anomalies(country_filter=None):
    """Obtiene clientes donde la fecha de albaranado es mayor que la de entrega - solo del mes actual con filtro por país"""
    
    # Obtener primer y último día del mes actual
    today = datetime.now().date()
    first_day = today.replace(day=1)
    if today.month == 12:
        last_day = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        last_day = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
    
    # Construir query con filtro de país opcional e incluir información de calendario SAP
    if country_filter:
        query = """
        SELECT 
            c.name, 
            c.codigo_ag, 
            c.codigo_we, 
            c.csr, 
            c.vendedor,
            c.tipo_cliente,
            c.region,
            c.pais,
            c.calendario_sap,
            ft_alb.name as frequency_name_albaranado,
            ft_alb.description as frequency_description_albaranado,
            ft_alb.calendario_sap_code as calendario_sap_code_albaranado,
            ft_alb.frequency_type as frequency_type_albaranado,
            ft_alb.frequency_config as frequency_config_albaranado,
            alb.date as fecha_albaranado,
            ent.date as fecha_entrega,
            alb.date_position as pos_albaranado,
            ent.date_position as pos_entrega
        FROM clients c
        JOIN calculated_dates alb ON c.id = alb.client_id AND alb.activity_id = 2
        JOIN calculated_dates ent ON c.id = ent.client_id AND ent.activity_id = 3
                                    AND alb.date_position = ent.date_position
        LEFT JOIN client_activities ca_alb ON c.id = ca_alb.client_id AND ca_alb.activity_id = 2
        LEFT JOIN frequency_templates ft_alb ON ca_alb.frequency_template_id = ft_alb.id
        WHERE date(alb.date) > date(ent.date)
        AND c.pais = ?
        AND (
            (date(alb.date) >= ? AND date(alb.date) <= ?) OR
            (date(ent.date) >= ? AND date(ent.date) <= ?)
        )
        ORDER BY c.name, alb.date_position
        """
        df = _cached_query_df(query, (
            country_filter,
            first_day.strftime('%Y-%m-%d'), last_day.strftime('%Y-%m-%d'),
            first_day.strftime('%Y-%m-%d'), last_day.strftime('%Y-%m-%d')
        ))
    else:
        query = """
        SELECT 
            c.name, 
            c.codigo_ag, 
            c.codigo_we, 
            c.csr, 
            c.vendedor,
            c.tipo_cliente,
            c.region,
            c.pais,
            c.calendario_sap,
            ft_alb.name as frequency_name_albaranado,
            ft_alb.description as frequency_description_albaranado,
            ft_alb.calendario_sap_code as calendario_sap_code_albaranado,
            ft_alb.frequency_type as frequency_type_albaranado,
            ft_alb.frequency_config as frequency_config_albaranado,
            alb.date as fecha_albaranado,
            ent.date as fecha_entrega,
            alb.date_position as pos_albaranado,
            ent.date_position as pos_entrega
        FROM clients c
        JOIN calculated_dates alb ON c.id = alb.client_id AND alb.activity_id = 2
        JOIN calculated_dates ent ON c.id = ent.client_id AND ent.activity_id = 3
                                    AND alb.date_position = ent.date_position
        LEFT JOIN client_activities ca_alb ON c.id = ca_alb.client_id AND ca_alb.activity_id = 2
        LEFT JOIN frequency_templates ft_alb ON ca_alb.frequency_template_id = ft_alb.id
        WHERE date(alb.date) > date(ent.date)
        AND (
            (date(alb.date) >= ? AND date(alb.date) <= ?) OR
            (date(ent.date) >= ? AND date(ent.date) <= ?)
        )
        ORDER BY c.name, alb.date_position
        """
        df = _cached_query_df(query, (
            first_day.strftime('%Y-%m-%d'), last_day.strftime('%Y-%m-%d'),
            first_day.strftime('%Y-%m-%d'), last_day.strftime('%Y-%m-%d')
        ))
    
    # Agregar información formateada de calendario SAP para anomalías de entrega
    if not df.empty:
        # Importar la función para formatear la descripción de frecuencia
        from calendar_utils import format_frequency_description
        
        # Formatear la descripción de frecuencia usando la función utilitaria
        df['formatted_frequency_description'] = df.apply(
            lambda row: format_frequency_description(row['frequency_type_albaranado'], row['frequency_config_albaranado'])
            if pd.notna(row['frequency_type_albaranado']) and pd.notna(row['frequency_config_albaranado'])
            else row.get('frequency_description_albaranado', ''),
            axis=1
        )
        
        # Crear la descripción completa del calendario SAP con frecuencia
        df['calendario_sap_full'] = df.apply(
            lambda row: f"{row['calendario_sap_code_albaranado']} - {row['formatted_frequency_description']}" 
            if pd.notna(row['calendario_sap_code_albaranado']) and row['calendario_sap_code_albaranado'] != '0' 
            else row['formatted_frequency_description'],
            axis=1
        )
    
    return df

def get_monthly_delivery_data(year, month, country_filter=None):
    """Obtiene los datos de fechas de Entrega para un mes específico con filtro por país"""
    
    # Crear las fechas de inicio y fin del mes
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
    
    # Construir query con filtro de país opcional
    if country_filter:
        query = """
        SELECT 
            cd.date,
            COUNT(*) as cantidad_entregas
        FROM calculated_dates cd
        JOIN clients c ON c.id = cd.client_id
        WHERE cd.activity_id = 3
        AND date(cd.date) >= ? AND date(cd.date) <= ?
        AND c.pais = ?
        GROUP BY date(cd.date)
        ORDER BY date(cd.date)
        """
        df = _cached_query_df(query, (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), country_filter))
    else:
        query = """
        SELECT 
            cd.date,
            COUNT(*) as cantidad_entregas
        FROM calculated_dates cd
        JOIN clients c ON c.id = cd.client_id
        WHERE cd.activity_id = 3
        AND date(cd.date) >= ? AND date(cd.date) <= ?
        GROUP BY date(cd.date)
        ORDER BY date(cd.date)
        """
        df = _cached_query_df(query, (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
    
    # Convertir fecha a datetime para mejor manejo
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        df['day'] = df['date'].dt.day
    
    return df

def get_activity_counts(country_filter=None):
    """Obtiene el conteo de fechas por tipo de actividad con filtro por país"""
    
    # Construir query con filtro de país opcional
    if country_filter:
        query = """
        SELECT 
            COALESCE(ac.name, cd.activity_name) as activity_name,
            COUNT(*) as total_fechas,
            COUNT(DISTINCT cd.client_id) as clientes_con_actividad
        FROM calculated_dates cd
        JOIN clients c ON c.id = cd.client_id
        LEFT JOIN activities_catalog ac ON ac.id = cd.activity_id
        WHERE c.pais = ?
        GROUP BY COALESCE(ac.name, cd.activity_name)
        ORDER BY total_fechas DESC
        """
        df = _cached_query_df(query, (country_filter,))
    else:
        query = """
        SELECT 
            COALESCE(ac.name, cd.activity_name) as activity_name,
            COUNT(*) as total_fechas,
            COUNT(DISTINCT cd.client_id) as clientes_con_actividad
        FROM calculated_dates cd
        JOIN clients c ON c.id = cd.client_id
        LEFT JOIN activities_catalog ac ON ac.id = cd.activity_id
        GROUP BY COALESCE(ac.name, cd.activity_name)
        ORDER BY total_fechas DESC
        """
        df = _cached_query_df(query, tuple())
    
    return df

def get_total_clients_count(country_filter=None):
    """Obtiene el total de clientes en el sistema con filtro por país"""
    
    # Construir query con filtro de país opcional
    if country_filter:
        query = """
        SELECT COUNT(*) as total_clientes
        FROM clients
        WHERE pais = ?
        """
        result = _cached_query_df(query, (country_filter,))
    else:
        query = """
        SELECT COUNT(*) as total_clientes
        FROM clients
        """
        result = _cached_query_df(query, tuple())
    
    total = result['total_clientes'].iloc[0] if not result.empty else 0
    return total

def create_delivery_line_chart(monthly_data, selected_month_name):
    """Crea el gráfico de línea para las fechas de Entrega del mes"""
    if monthly_data.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No hay datos de fechas de Entrega para este mes",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False,
            font=dict(size=14, color="#666666")
        )
        fig.update_layout(
            title=f"Fechas de Entrega en {selected_month_name}",
            xaxis_title="Día del mes",
            yaxis_title="Cantidad de fechas de Entrega",
            height=400,
            showlegend=False
        )
        return fig
    
    fig = go.Figure()
    
    # Línea principal
    fig.add_trace(go.Scatter(
        x=monthly_data['day'],
        y=monthly_data['cantidad_entregas'],
        mode='lines+markers',
        name='Fechas Entrega',
        line=dict(color='#2ca02c', width=3),
        marker=dict(size=8, color='#2ca02c'),
        hovertemplate='<b>Día %{x}</b><br>Fechas Entrega: %{y}<extra></extra>'
    ))
    
    # Área bajo la curva
    fig.add_trace(go.Scatter(
        x=monthly_data['day'],
        y=monthly_data['cantidad_entregas'],
        fill='tozeroy',
        mode='none',
        name='Área',
        fillcolor='rgba(44, 160, 44, 0.1)',
        showlegend=False
    ))
    
    fig.update_layout(
        title=" ",
        xaxis_title="Día del mes",
        yaxis_title="Cantidad de fechas de Entrega",
        height=400,
        hovermode='x unified',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Arial", size=12),
        title_font=dict(size=16, color='#2E4057'),
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)',
            zeroline=False
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)',
            zeroline=False
        )
    )
    
    return fig

def show_dashboard():
    """Función principal del dashboard"""
    st.header("Dashboard Green Logistics")
    st.markdown("*Vista general de las actividades y fechas programadas*")
    
    # ========== SELECTOR DE PAÍS PARA ADMINISTRADORES ==========
    
    # Determinar el filtro de país a usar
    dashboard_country_filter = None
    
    # Si el usuario tiene un filtro de país fijo (como GLCOUser)
    if has_country_filter():
        dashboard_country_filter = get_user_country_filter()
        st.info(f"Vista filtrada: Dashboard de **{dashboard_country_filter}**")
    
    # Si es administrador, mostrar selector de país
    elif auth_system.is_admin():
        st.subheader("Configuración del Dashboard")
        
        col1, col2 = st.columns([2, 4])
        with col1:
            paises_options = ['Todos los países'] + get_paises()
            selected_country = st.selectbox(
                "Filtrar dashboard por país:",
                paises_options,
                index=0,
                key="dashboard_country_filter",
                help="Selecciona un país para filtrar todos los datos del dashboard"
            )
            
            if selected_country != 'Todos los países':
                dashboard_country_filter = selected_country
        
        with col2:
            if dashboard_country_filter:
                st.success(f"Mostrando datos de: **{dashboard_country_filter}**")
            else:
                st.info("Mostrando datos de **todos los países**")
        
        st.divider()
    
    # Para otros usuarios (glmxuser), no hay selector pero tampoco filtro fijo
    else:
        # glmxuser ve todos los países pero sin selector
        pass
    
    # ========== TABLAS DE ALERTAS (PRIMERA SECCIÓN) ==========
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Fechas OC de Mañana")
        
        # Obtener clientes con fecha OC de mañana
        tomorrow_oc_clients = get_tomorrow_oc_clients(dashboard_country_filter)
        
        if not tomorrow_oc_clients.empty:
            st.info(f"**{len(tomorrow_oc_clients)} clientes** tienen fecha OC mañana")
            
            # Mostrar la tabla de clientes
            display_df = tomorrow_oc_clients.copy()
            display_df['date'] = pd.to_datetime(display_df['date']).dt.strftime('%d/%m/%Y')
            display_df = display_df.rename(columns={
                'name': 'Cliente',
                'codigo_ag': 'Cód. AG',
                'codigo_we': 'Cód. WE',
                'csr': 'CSR',
                'vendedor': 'Vendedor',
                'calendario_sap': 'Cal. SAP',
                'date': 'Fecha OC',
                'pais': 'País'
            })
            
            # Seleccionar columnas clave para mostrar
            if dashboard_country_filter:
                # Si hay filtro de país, no mostrar la columna país (todos son del mismo país)
                key_columns = ['Cliente', 'Cód. AG', 'Cód. WE', 'CSR', 'Vendedor', 'Cal. SAP', 'Fecha OC']
            else:
                # Si no hay filtro, mostrar la columna país
                key_columns = ['Cliente', 'Cód. AG', 'Cód. WE', 'CSR', 'Vendedor', 'Cal. SAP', 'País', 'Fecha OC']
            
            display_df = display_df[key_columns]
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            country_text = f" en {dashboard_country_filter}" if dashboard_country_filter else ""
            st.success(f"No hay fechas OC programadas para mañana{country_text}")
    
    with col2:
        anomaly_suffix = f" - {dashboard_country_filter}" if dashboard_country_filter else ""
        st.subheader(f"Anomalías y Alertas del Mes{anomaly_suffix}")
        
        # Obtener el mes y año actual
        current_date = datetime.now()
        current_year = current_date.year
        current_month = current_date.month
        current_month_name = current_date.strftime('%B')
        
        # Obtener anomalías completas
        anomalies = get_comprehensive_anomalies(current_year, current_month, dashboard_country_filter)
        
        # Contar total de anomalías (sin incluir delivery_anomalies)
        total_anomalies = (
            len(anomalies['incomplete_week_anomalies']) +
            len(anomalies['holiday_anomalies'])
        )
        
        if total_anomalies > 0:
            
            # Crear tabs para diferentes tipos de anomalías
            tab1, tab2, tab3 = st.tabs([
                "Semanas incompletas", 
                "Días festivos",
                "Resumen"
            ])
            
            with tab1:
                incomplete_anomalies = anomalies['incomplete_week_anomalies']
                if not incomplete_anomalies.empty:
                    # Mostrar información sobre el mes
                    week_info = get_incomplete_weeks_info(current_year, current_month)
                    
                    if week_info['affected_weekdays']:
                        st.info(f"**{current_month_name}** tiene semanas incompletas que afectan: {', '.join(week_info['affected_weekdays'])}")
                    
                    country_info = f" en {dashboard_country_filter}" if dashboard_country_filter else ""
                    st.warning(f"**{len(incomplete_anomalies)} clientes**{country_info} pueden verse afectados por semanas incompletas")
                    
                    display_df = incomplete_anomalies.copy()
                    display_df['fecha_albaranado'] = pd.to_datetime(display_df['fecha_albaranado']).dt.strftime('%d/%m/%Y')
                    display_df = display_df.rename(columns={
                        'name': 'Cliente',
                        'codigo_ag': 'Cód. AG',
                        'codigo_we': 'Cód. WE',
                        'csr': 'CSR',
                        'calendario_sap_full': 'Calendario SAP',
                        'frequency_name': 'Frecuencia',
                        'fecha_albaranado': 'Fecha Albaranado',
                        'weekday_from_frequency': 'Día Afectado',
                        'reason': 'Motivo'
                    })
                    
                    key_columns = ['Cliente', 'Cód. AG', 'Cód. WE', 'Calendario SAP', 'Fecha Albaranado', 'Día Afectado', 'Motivo']
                    display_df = display_df[key_columns]
                    
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                else:
                    country_info = f" en {dashboard_country_filter}" if dashboard_country_filter else ""
                    st.success(f"No hay clientes{country_info} afectados por semanas incompletas")
            
            # Tab 2: Anomalías por días festivos
            with tab2:
                holiday_anomalies = anomalies['holiday_anomalies']
                if not holiday_anomalies.empty:
                    # Mostrar festivos del mes
                    holidays = get_holidays_for_month(current_year, current_month)
                    if holidays:
                        holiday_text = ", ".join([f"{h[0].strftime('%d/%m')} ({h[1]})" for h in holidays])
                        st.info(f"**Festivos en {current_month_name}:** {holiday_text}")
                    
                    country_info = f" en {dashboard_country_filter}" if dashboard_country_filter else ""
                    st.warning(f"**{len(holiday_anomalies)} clientes**{country_info} con albaranado en días festivos")
                    
                    display_df = holiday_anomalies.copy()
                    display_df['fecha_albaranado'] = pd.to_datetime(display_df['fecha_albaranado']).dt.strftime('%d/%m/%Y')
                    display_df = display_df.rename(columns={
                        'name': 'Cliente',
                        'codigo_ag': 'Cód. AG',
                        'codigo_we': 'Cód. WE',
                        'csr': 'CSR',
                        'calendario_sap_full': 'Calendario SAP',
                        'fecha_albaranado': 'Fecha Albaranado',
                        'holiday_description': 'Festivo',
                        'reason': 'Motivo'
                    })
                    
                    key_columns = ['Cliente', 'Cód. AG', 'Cód. WE', 'Calendario SAP', 'Fecha Albaranado', 'Festivo', 'Motivo']
                    display_df = display_df[key_columns]
                    
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                else:
                    country_info = f" en {dashboard_country_filter}" if dashboard_country_filter else ""
                    st.success(f"No hay clientes{country_info} con albaranado en días festivos")
            
            # Tab 3: Resumen
            with tab3:
                col_a, col_b = st.columns(2)
                
                with col_a:
                    st.metric(
                        "Semanas incompletas",
                        len(anomalies['incomplete_week_anomalies']),
                        delta=None
                    )
                
                with col_b:
                    st.metric(
                        "Días festivos",
                        len(anomalies['holiday_anomalies']),
                        delta=None
                    )
                
                st.markdown(f"**Total de clientes únicos afectados:** {anomalies['total_affected_clients']}")
                
        else:
            country_info = f" en {dashboard_country_filter}" if dashboard_country_filter else ""
            st.success(f"No se detectaron anomalías{country_info} para {current_month_name} {current_year}")
        
        # Botón para gestión de festivos (solo en desarrollo)
        from config import is_development
        if is_development():
            with st.expander("Configuración de Festivos y Análisis"):
                from holiday_manager import show_current_month_analysis, manage_holidays_interface
                
                tab_analysis, tab_config = st.tabs(["Análisis del Mes", "Gestionar Festivos"])
                
                with tab_analysis:
                    show_current_month_analysis()
                
                with tab_config:
                    manage_holidays_interface()
    
    st.markdown("---")
    
    # ========== TARJETAS DE MÉTRICAS ==========
    country_suffix = f" - {dashboard_country_filter}" if dashboard_country_filter else ""
    st.subheader(f"Métricas Generales{country_suffix}")
    
    # Obtener datos para las métricas
    activity_counts = get_activity_counts(dashboard_country_filter)
    total_clients = get_total_clients_count(dashboard_country_filter)
    
    # Crear diccionario de métricas
    metrics = {}
    for _, row in activity_counts.iterrows():
        metrics[row['activity_name']] = {
            'total': row['total_fechas'],
            'clientes': row['clientes_con_actividad']
        }
    
    # Mostrar tarjetas de métricas (4 columnas incluyendo total de clientes)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Primera métrica: Total de Clientes
        country_label = f"{dashboard_country_filter}" if dashboard_country_filter else "sistema"
        st.markdown(get_metric_card_html(
            "Total Clientes", 
            str(total_clients), 
            f"en {country_label}",
            "#9467bd"
        ), unsafe_allow_html=True)
    
    with col2:
        oc_total = metrics.get('Fecha Envío OC', {}).get('total', 0)
        oc_clientes = metrics.get('Fecha Envío OC', {}).get('clientes', 0)
        st.markdown(get_metric_card_html(
            "Fechas OC", 
            str(oc_total), 
            f"{oc_clientes} clientes",
            "#1f77b4"
        ), unsafe_allow_html=True)
    
    with col3:
        alb_total = metrics.get('Albaranado', {}).get('total', 0)
        alb_clientes = metrics.get('Albaranado', {}).get('clientes', 0)
        st.markdown(get_metric_card_html(
            "Albaranados", 
            str(alb_total), 
            f"{alb_clientes} clientes",
            "#ff7f0e"
        ), unsafe_allow_html=True)
    
    with col4:
        ent_total = metrics.get('Fecha Entrega', {}).get('total', 0)
        ent_clientes = metrics.get('Fecha Entrega', {}).get('clientes', 0)
        st.markdown(get_metric_card_html(
            "Entregas", 
            str(ent_total), 
            f"{ent_clientes} clientes",
            "#2ca02c"
        ), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ========== SELECTOR Y GRÁFICO DE FECHAS DE ENTREGA ==========
    analysis_suffix = f" - {dashboard_country_filter}" if dashboard_country_filter else ""
    st.subheader(f"Análisis de Fechas de Entrega por Mes{analysis_suffix}")
    
    # Selector de año y mes
    col_year, col_month = st.columns(2)
    
    with col_year:
        chart_year = st.selectbox(
            "Seleccionar Año:",
            options=[2024, 2025, 2026],
            index=1,  # 2025 por defecto
            key="chart_year_selector"
        )
    
    with col_month:
        chart_month = st.selectbox(
            "Seleccionar Mes:",
            options=list(range(1, 13)),
            format_func=lambda x: calendar.month_name[x],
            index=datetime.now().month - 1,  # Mes actual por defecto
            key="chart_month_selector"
        )
    
    chart_month_name = calendar.month_name[chart_month]
    
    # Determinar si el mes seleccionado es pasado, presente o futuro
    current_date = datetime.now()
    selected_date = date(chart_year, chart_month, 1)
    current_month_date = date(current_date.year, current_date.month, 1)
    
    country_text = f" ({dashboard_country_filter})" if dashboard_country_filter else ""
    
    if selected_date < current_month_date:
        chart_subtitle = f"Fechas de Entrega del mes vencido ({chart_month_name} {chart_year}){country_text}"
    elif selected_date > current_month_date:
        chart_subtitle = f"Fechas de Entrega del mes próximo ({chart_month_name} {chart_year}){country_text}"
    else:
        chart_subtitle = f"Fechas de Entrega del mes actual ({chart_month_name} {chart_year}){country_text}"
    
    st.subheader(chart_subtitle)
    
    # Obtener datos del mes seleccionado para la gráfica
    monthly_data = get_monthly_delivery_data(chart_year, chart_month, dashboard_country_filter)
    
    if not monthly_data.empty:
        total_delivery_month = monthly_data['cantidad_entregas'].sum()
        country_info = f" en {dashboard_country_filter}" if dashboard_country_filter else ""
        st.info(f"**{total_delivery_month} fechas de Entrega** programadas en {chart_month_name} {chart_year}{country_info}")
        
        # Mostrar gráfico de línea del mes
        line_chart = create_delivery_line_chart(monthly_data, chart_month_name)
        st.plotly_chart(line_chart, use_container_width=True)
        
    else:
        country_info = f" en {dashboard_country_filter}" if dashboard_country_filter else ""
        st.success(f"No hay fechas de Entrega programadas para {chart_month_name} {chart_year}{country_info}")
    
    st.markdown("---")

def show_performance_dashboard():
    """Muestra un dashboard de rendimiento de la base de datos y cache"""
    st.subheader("Estadísticas de Rendimiento del Sistema")
    
    # Obtener estadísticas
    db_stats = get_database_statistics()
    cache_stats = get_cache_stats()
    
    # Mostrar métricas principales en columnas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Clientes Totales",
            value=db_stats.get('clients_count', 0)
        )
    
    with col2:
        st.metric(
            label="Actividades Totales", 
            value=db_stats.get('client_activities_count', 0)
        )
    
    with col3:
        st.metric(
            label="Fechas Calculadas",
            value=db_stats.get('calculated_dates_count', 0)
        )
    
    with col4:
        st.metric(
            label="Plantillas de Frecuencia",
            value=db_stats.get('frequency_templates_count', 0)
        )
    
    # Estadísticas de cache
    st.subheader("Rendimiento del Cache")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        hit_rate = cache_stats.get('hit_rate', 0)
        color = "normal"
        if hit_rate >= 80:
            color = "normal" 
        elif hit_rate >= 60:
            color = "normal"
        else:
            color = "inverse"
            
        st.metric(
            label="Hit Rate del Cache",
            value=f"{hit_rate:.1f}%"
        )
    
    with col2:
        st.metric(
            label="Cache Hits",
            value=cache_stats.get('hits', 0)
        )
    
    with col3:
        st.metric(
            label="Cache Misses", 
            value=cache_stats.get('misses', 0)
        )
    
    with col4:
        st.metric(
            label="Items en Cache",
            value=cache_stats.get('cached_items', 0)
        )
    
    # Controles de administración
    st.subheader("Administración del Sistema")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Limpiar Cache Completo", type="secondary"):
            clear_cache()
            st.success("Cache limpiado exitosamente")
            st.rerun()
    
    with col2:
        if st.button("Optimizar Base de Datos", type="secondary"):
            if optimize_database():
                st.success("Base de datos optimizada exitosamente")
            else:
                st.error("Error al optimizar la base de datos")
    
    with col3:
        if st.button("Actualizar Estadísticas", type="primary"):
            st.rerun()
    
    # Información adicional
    st.subheader("Información del Sistema")
    
    info_text = f"""
    **Estado del Cache:**
    - El cache está funcionando con un hit rate del {cache_stats.get('hit_rate', 0):.1f}%
    - {'Rendimiento excelente' if cache_stats.get('hit_rate', 0) >= 80 else 'Rendimiento normal' if cache_stats.get('hit_rate', 0) >= 60 else 'Rendimiento bajo - considere limpiar cache'}
    
    **Recomendaciones:**
    - Hit rate > 80%: Excelente rendimiento
    - Hit rate 60-80%: Rendimiento normal
    - Hit rate < 60%: Considere limpiar cache o revisar patrones de consulta
    
    **Optimizaciones Activas:**
    - Connection pooling habilitado
    - Índices de base de datos creados
    - Cache inteligente con TTL
    - Invalidación automática de cache
    """
    
    st.info(info_text)

def show_system_health():
    """Muestra una vista rápida del estado del sistema"""
    # Función deshabilitada - no mostrar información de rendimiento
    pass
    
    

