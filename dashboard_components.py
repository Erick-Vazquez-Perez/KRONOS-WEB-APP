import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
from database import get_db_connection, get_clients, get_calculated_dates
from werfen_styles import get_metric_card_html
import calendar
from anomaly_detector import get_comprehensive_anomalies, get_holidays_for_month, get_incomplete_weeks_info

def get_tomorrow_oc_clients():
    """Obtiene clientes con fecha OC para mañana (o lunes si hoy es viernes)"""
    today = datetime.now().date()
    
    # Si hoy es viernes (4), mañana debe ser lunes (agregar 3 días)
    if today.weekday() == 4:  # Viernes
        target_date = today + timedelta(days=3)  # Lunes
    else:
        target_date = today + timedelta(days=1)  # Mañana normal
    
    conn = get_db_connection()
    query = """
    SELECT c.name, c.codigo_ag, c.codigo_we, c.csr, c.vendedor, cd.date, c.tipo_cliente, c.region
    FROM clients c
    JOIN calculated_dates cd ON c.id = cd.client_id
    WHERE cd.activity_name = 'Fecha Envío OC' 
    AND date(cd.date) = ?
    ORDER BY c.name
    """
    
    df = pd.read_sql_query(query, conn, params=(target_date.strftime('%Y-%m-%d'),))
    conn.close()
    
    return df

def get_delivery_anomalies():
    """Obtiene clientes donde la fecha de albaranado es mayor que la de entrega - solo del mes actual"""
    conn = get_db_connection()
    
    # Obtener primer y último día del mes actual
    today = datetime.now().date()
    first_day = today.replace(day=1)
    if today.month == 12:
        last_day = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        last_day = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
    
    query = """
    SELECT 
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
    conn.close()
    
    return df

def get_monthly_oc_data(year, month):
    """Obtiene los datos de fechas OC para un mes específico"""
    conn = get_db_connection()
    
    # Crear las fechas de inicio y fin del mes
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
    
    query = """
    SELECT 
        cd.date,
        COUNT(*) as cantidad_oc
    FROM calculated_dates cd
    JOIN clients c ON c.id = cd.client_id
    WHERE cd.activity_name = 'Fecha Envío OC' 
    AND date(cd.date) >= ? AND date(cd.date) <= ?
    GROUP BY date(cd.date)
    ORDER BY date(cd.date)
    """
    
    df = pd.read_sql_query(query, conn, params=(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
    conn.close()
    
    # Convertir fecha a datetime para mejor manejo
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        df['day'] = df['date'].dt.day
    
    return df

def get_activity_counts():
    """Obtiene el conteo de fechas por tipo de actividad"""
    conn = get_db_connection()
    
    query = """
    SELECT 
        cd.activity_name,
        COUNT(*) as total_fechas,
        COUNT(DISTINCT cd.client_id) as clientes_con_actividad
    FROM calculated_dates cd
    JOIN clients c ON c.id = cd.client_id
    GROUP BY cd.activity_name
    ORDER BY total_fechas DESC
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    return df

def create_oc_line_chart(monthly_data, selected_month_name):
    """Crea el gráfico de línea para las fechas OC del mes"""
    if monthly_data.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No hay datos de fechas OC para este mes",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False,
            font=dict(size=14, color="#666666")
        )
        fig.update_layout(
            title=f"Fechas OC en {selected_month_name}",
            xaxis_title="Día del mes",
            yaxis_title="Cantidad de fechas OC",
            height=400,
            showlegend=False
        )
        return fig
    
    fig = go.Figure()
    
    # Línea principal
    fig.add_trace(go.Scatter(
        x=monthly_data['day'],
        y=monthly_data['cantidad_oc'],
        mode='lines+markers',
        name='Fechas OC',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=8, color='#1f77b4'),
        hovertemplate='<b>Día %{x}</b><br>Fechas OC: %{y}<extra></extra>'
    ))
    
    # Área bajo la curva
    fig.add_trace(go.Scatter(
        x=monthly_data['day'],
        y=monthly_data['cantidad_oc'],
        fill='tozeroy',
        mode='none',
        name='Área',
        fillcolor='rgba(31, 119, 180, 0.1)',
        showlegend=False
    ))
    
    fig.update_layout(
        title=" ",
        xaxis_title="Día del mes",
        yaxis_title="Cantidad de fechas OC",
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
    st.header("Dashboard Kronos")
    st.markdown("*Vista general de las actividades y fechas programadas*")
    
    # ========== SELECTOR DE MES ==========
    col1, col2, col3 = st.columns([2, 2, 4])
    
    with col1:
        current_year = datetime.now().year
        years = list(range(current_year - 1, current_year + 2))
        selected_year = st.selectbox("Año:", years, index=1, key="dashboard_year")
    
    with col2:
        months = [
            'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
            'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
        ]
        current_month_idx = datetime.now().month - 1
        selected_month_name = st.selectbox("Mes:", months, index=current_month_idx, key="dashboard_month")
        selected_month = months.index(selected_month_name) + 1
    
    st.markdown("---")
    
    # ========== TABLAS DE ALERTAS (PRIMERA SECCIÓN) ==========
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Fechas OC de Mañana")
        
        # Obtener clientes con fecha OC de mañana
        tomorrow_oc_clients = get_tomorrow_oc_clients()
        
        if not tomorrow_oc_clients.empty:
            st.info(f"**{len(tomorrow_oc_clients)} clientes** tienen fecha OC mañana")
            
            # Mostrar la tabla de clientes
            display_df = tomorrow_oc_clients.copy()
            display_df['date'] = pd.to_datetime(display_df['date']).dt.strftime('%d/%m/%Y')
            display_df = display_df.rename(columns={
                'name': 'Cliente',
                'codigo_ag': 'Cód. AG',
                'csr': 'CSR',
                'date': 'Fecha OC'
            })
            
            # Seleccionar columnas clave para mostrar
            key_columns = ['Cliente', 'Cód. AG', 'CSR', 'Fecha OC']
            display_df = display_df[key_columns]
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.success("No hay fechas OC programadas para mañana")
    
    with col2:
        st.subheader("Anomalías y Alertas del Mes")
        
        # Obtener el mes y año actual
        current_date = datetime.now()
        current_year = current_date.year
        current_month = current_date.month
        current_month_name = current_date.strftime('%B')
        
        # Obtener anomalías completas
        anomalies = get_comprehensive_anomalies(current_year, current_month)
        
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
                    
                    st.warning(f"**{len(incomplete_anomalies)} clientes** pueden verse afectados por semanas incompletas")
                    
                    display_df = incomplete_anomalies.copy()
                    display_df['fecha_albaranado'] = pd.to_datetime(display_df['fecha_albaranado']).dt.strftime('%d/%m/%Y')
                    display_df = display_df.rename(columns={
                        'name': 'Cliente',
                        'codigo_ag': 'Cód. AG',
                        'csr': 'CSR',
                        'frequency_name': 'Frecuencia',
                        'fecha_albaranado': 'Fecha Albaranado',
                        'weekday_from_frequency': 'Día Afectado',
                        'reason': 'Motivo'
                    })
                    
                    key_columns = ['Cliente', 'Cód. AG', 'Frecuencia', 'Fecha Albaranado', 'Día Afectado', 'Motivo']
                    display_df = display_df[key_columns]
                    
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                else:
                    st.success("No hay clientes afectados por semanas incompletas")
            
            # Tab 2: Anomalías por días festivos
            with tab2:
                holiday_anomalies = anomalies['holiday_anomalies']
                if not holiday_anomalies.empty:
                    # Mostrar festivos del mes
                    holidays = get_holidays_for_month(current_year, current_month)
                    if holidays:
                        holiday_text = ", ".join([f"{h[0].strftime('%d/%m')} ({h[1]})" for h in holidays])
                        st.info(f"**Festivos en {current_month_name}:** {holiday_text}")
                    
                    st.warning(f"**{len(holiday_anomalies)} clientes** con albaranado en días festivos")
                    
                    display_df = holiday_anomalies.copy()
                    display_df['fecha_albaranado'] = pd.to_datetime(display_df['fecha_albaranado']).dt.strftime('%d/%m/%Y')
                    display_df = display_df.rename(columns={
                        'name': 'Cliente',
                        'codigo_ag': 'Cód. AG',
                        'csr': 'CSR',
                        'fecha_albaranado': 'Fecha Albaranado',
                        'holiday_description': 'Festivo',
                        'reason': 'Motivo'
                    })
                    
                    key_columns = ['Cliente', 'Cód. AG', 'Fecha Albaranado', 'Festivo', 'Motivo']
                    display_df = display_df[key_columns]
                    
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                else:
                    st.success("No hay clientes con albaranado en días festivos")
            
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
            st.success(f"No se detectaron anomalías para {current_month_name} {current_year}")
        
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
    st.subheader("Métricas Generales")
    
    # Obtener datos para las métricas
    activity_counts = get_activity_counts()
    
    # Crear diccionario de métricas
    metrics = {}
    for _, row in activity_counts.iterrows():
        metrics[row['activity_name']] = {
            'total': row['total_fechas'],
            'clientes': row['clientes_con_actividad']
        }
    
    # Mostrar tarjetas de métricas (solo 3 columnas)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        oc_total = metrics.get('Fecha Envío OC', {}).get('total', 0)
        oc_clientes = metrics.get('Fecha Envío OC', {}).get('clientes', 0)
        st.markdown(get_metric_card_html(
            "Fechas OC", 
            str(oc_total), 
            f"{oc_clientes} clientes",
            "#1f77b4"
        ), unsafe_allow_html=True)
    
    with col2:
        alb_total = metrics.get('Albaranado', {}).get('total', 0)
        alb_clientes = metrics.get('Albaranado', {}).get('clientes', 0)
        st.markdown(get_metric_card_html(
            "Albaranados", 
            str(alb_total), 
            f"{alb_clientes} clientes",
            "#ff7f0e"
        ), unsafe_allow_html=True)
    
    with col3:
        ent_total = metrics.get('Fecha Entrega', {}).get('total', 0)
        ent_clientes = metrics.get('Fecha Entrega', {}).get('clientes', 0)
        st.markdown(get_metric_card_html(
            "Entregas", 
            str(ent_total), 
            f"{ent_clientes} clientes",
            "#2ca02c"
        ), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ========== SELECTOR Y GRÁFICO DE FECHAS OC ==========
    st.subheader("Análisis de Fechas OC por Mes")
    
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
    
    if selected_date < current_month_date:
        chart_subtitle = f"Fechas OC del mes vencido ({chart_month_name} {chart_year})"
    elif selected_date > current_month_date:
        chart_subtitle = f"Fechas OC del mes próximo ({chart_month_name} {chart_year})"
    else:
        chart_subtitle = f"Fechas OC del mes actual ({chart_month_name} {chart_year})"
    
    st.subheader(chart_subtitle)
    
    # Obtener datos del mes seleccionado para la gráfica
    monthly_data = get_monthly_oc_data(chart_year, chart_month)
    
    if not monthly_data.empty:
        total_oc_month = monthly_data['cantidad_oc'].sum()
        st.info(f"**{total_oc_month} fechas OC** programadas en {chart_month_name} {chart_year}")
        
        # Mostrar gráfico de línea del mes
        line_chart = create_oc_line_chart(monthly_data, chart_month_name)
        st.plotly_chart(line_chart, use_container_width=True)
        
    else:
        st.success(f"No hay fechas OC programadas para {chart_month_name} {chart_year}")
    
    st.markdown("---")
    
    

