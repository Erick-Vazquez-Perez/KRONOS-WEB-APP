import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
from database import get_db_connection, get_clients, get_calculated_dates
from werfen_styles import get_metric_card_html
import calendar

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
    WHERE cd.activity_name = 'Fecha envío OC' 
    AND date(cd.date) = ?
    ORDER BY c.name
    """
    
    df = pd.read_sql_query(query, conn, params=(target_date.strftime('%Y-%m-%d'),))
    conn.close()
    
    return df, target_date

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
    WHERE cd.activity_name = 'Fecha envío OC' 
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
        st.subheader("Fechas OC Próximas")
        tomorrow_clients, target_date = get_tomorrow_oc_clients()
        
        # Formatear la fecha objetivo
        date_label = "Mañana" if target_date == datetime.now().date() + timedelta(days=1) else "Lunes"
        
        if not tomorrow_clients.empty:
            st.info(f"**{len(tomorrow_clients)} clientes** tienen fecha OC para {date_label} ({target_date.strftime('%d/%m/%Y')})")
            
            # Mostrar tabla
            display_df = tomorrow_clients.copy()
            display_df['date'] = pd.to_datetime(display_df['date']).dt.strftime('%d/%m/%Y')
            display_df = display_df.rename(columns={
                'name': 'Cliente',
                'codigo_ag': 'Cód. AG',
                'codigo_we': 'Cód. WE',
                'csr': 'CSR',
                'vendedor': 'Vendedor',
                'date': 'Fecha OC',
                'tipo_cliente': 'Tipo',
                'region': 'Región'
            })
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    'Cliente': st.column_config.TextColumn(width='medium'),
                    'Cód. AG': st.column_config.TextColumn(width='small'),
                    'Cód. WE': st.column_config.TextColumn(width='small'),
                    'CSR': st.column_config.TextColumn(width='small'),
                    'Vendedor': st.column_config.TextColumn(width='medium'),
                    'Fecha OC': st.column_config.TextColumn(width='small'),
                    'Tipo': st.column_config.TextColumn(width='small'),
                    'Región': st.column_config.TextColumn(width='small')
                }
            )
        else:
            st.success(f"No hay fechas OC programadas para {date_label}")
    
    with col2:
        st.subheader("Anomalías de fechas del mes")
        delivery_anomalies = get_delivery_anomalies()
        
        if not delivery_anomalies.empty:
            current_month_name = datetime.now().strftime('%B')
            st.warning(f"**{len(delivery_anomalies)} registros** con fecha de albaranado posterior a entrega en {current_month_name}")
            
            # Mostrar tabla
            display_df = delivery_anomalies.copy()
            display_df['fecha_albaranado'] = pd.to_datetime(display_df['fecha_albaranado']).dt.strftime('%d/%m/%Y')
            display_df['fecha_entrega'] = pd.to_datetime(display_df['fecha_entrega']).dt.strftime('%d/%m/%Y')
            display_df = display_df.rename(columns={
                'name': 'Cliente',
                'codigo_ag': 'Cód. AG',
                'csr': 'CSR',
                'vendedor': 'Vendedor',
                'fecha_albaranado': 'Albaranado',
                'fecha_entrega': 'Entrega',
                'pos_albaranado': 'Pos.',
                'tipo_cliente': 'Tipo',
                'region': 'Región'
            })
            
            # Seleccionar solo las columnas más importantes para evitar sobrecarga
            key_columns = ['Cliente', 'Cód. AG', 'CSR', 'Albaranado', 'Entrega', 'Pos.']
            display_df = display_df[key_columns]
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    'Cliente': st.column_config.TextColumn(width='medium'),
                    'Cód. AG': st.column_config.TextColumn(width='small'),
                    'CSR': st.column_config.TextColumn(width='small'),
                    'Albaranado': st.column_config.TextColumn(width='small'),
                    'Entrega': st.column_config.TextColumn(width='small'),
                    'Pos.': st.column_config.NumberColumn(width='small')
                }
            )
        else:
            st.success("No se detectaron anomalías en las fechas del mes actual")
    
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
        oc_total = metrics.get('Fecha envío OC', {}).get('total', 0)
        oc_clientes = metrics.get('Fecha envío OC', {}).get('clientes', 0)
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
    
    # ========== GRÁFICO DE LÍNEA ==========
    st.subheader(f"Fechas OC en {selected_month_name} {selected_year}")
    
    monthly_data = get_monthly_oc_data(selected_year, selected_month)
    chart = create_oc_line_chart(monthly_data, selected_month_name)
    st.plotly_chart(chart, use_container_width=True)
    
    st.markdown("---")
    
    

