"""
Estilos CSS personalizados para la aplicación GREEN LOGISTICS - Werfen
Colores corporativos Werfen: Azul #06038D, Naranja #E87721
"""

def get_custom_css():
    """Retorna el CSS personalizado para la aplicación"""
    return """
    <style>
    /* ========== VARIABLES DE COLOR WERFEN ========== */
    :root {
        --werfen-blue: #06038D;
        --werfen-orange: #E87721;
        --werfen-blue-light: #1a17a3;
        --werfen-blue-dark: #040269;
        --werfen-orange-light: #ff8c3d;
        --werfen-orange-dark: #c66619;
        --werfen-gray: #f5f5f5;
        --werfen-gray-dark: #e0e0e0;
        --werfen-white: #ffffff;
        --werfen-text-gray: #6b7280;
        --card-shadow: 0 2px 8px rgba(6,3,141,0.10);
        --card-shadow-hover: 0 6px 18px rgba(6,3,141,0.18);
        --border-radius: 8px;
    }

    /* ========== HEADER DE STREAMLIT: SIN FONDO, CONTENIDO FLOTANTE ========== */
    header[data-testid="stHeader"] {
        background: transparent !important;
        border-bottom: none !important;
        box-shadow: none !important;
    }
    /* Ocultar botones de Deploy, Share y similares */
    header[data-testid="stHeader"] button[kind="header"],
    header[data-testid="stHeader"] a[kind="header"],
    [data-testid="stDeployButton"] {
        display: none !important;
    }
    /* Re-mostrar únicamente los 3 botones de opciones del toolbar */
    [data-testid="stToolbarActions"] button[kind="header"],
    [data-testid="stToolbarActions"] a[kind="header"] {
        display: inline-flex !important;
    }
    /* Subir el contenido eliminando el padding que Streamlit reserva para el header */
    .block-container,
    div[data-testid="block-container"],
    section[data-testid="stMain"] .block-container,
    div[data-testid="stAppViewContainer"] section[data-testid="stMain"] > div > div {
        padding-top: 1rem !important;
        margin-top: 0 !important;
    }

    /* ========== SIDEBAR — ESTILOS PREDETERMINADOS DE STREAMLIT ========== */
    /* Separador en sidebar */
    div[data-testid="stSidebar"] hr {
        margin: 14px 0 !important;
        border: none !important;
        border-top: 1px solid var(--werfen-gray-dark) !important;
        background: none !important;
        height: 1px !important;
    }

    /* Títulos h3 dentro del sidebar */
    div[data-testid="stSidebar"] h3 {
        color: var(--werfen-blue) !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        margin: 14px 0 6px 0 !important;
    }

    /* Botones del sidebar con acento azul Werfen */
    div[data-testid="stSidebar"] .stButton > button {
        border-radius: var(--border-radius) !important;
    }

    /* Espaciado de botones global */
    .stButton {
        margin: 0.2rem 0 !important;
    }

    /* ========== BOTONES PRINCIPALES (área de contenido) ========== */
    .stApp .stButton > button,
    div[data-testid="stAppViewContainer"] .stButton > button {
        background: var(--werfen-blue) !important;
        color: white !important;
        border: 2px solid var(--werfen-blue) !important;
        border-radius: var(--border-radius) !important;
        padding: 0.5rem 1.2rem !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
        box-shadow: var(--card-shadow) !important;
        min-height: 40px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        line-height: 1.2 !important;
    }
    .stApp .stButton > button:hover,
    div[data-testid="stAppViewContainer"] .stButton > button:hover {
        background: white !important;
        color: var(--werfen-blue) !important;
        border-color: var(--werfen-blue) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(6,3,141,0.2) !important;
    }
    .stApp .stButton > button:active,
    div[data-testid="stAppViewContainer"] .stButton > button:active {
        background: var(--werfen-blue-dark) !important;
        color: white !important;
        transform: translateY(0) !important;
        box-shadow: var(--card-shadow) !important;
    }
    .stApp .stButton > button:disabled,
    div[data-testid="stAppViewContainer"] .stButton > button:disabled {
        background: #e0e0e0 !important;
        color: #999 !important;
        border-color: #ddd !important;
        cursor: not-allowed !important;
        transform: none !important;
        box-shadow: none !important;
        opacity: 0.7 !important;
    }

    /* Botones en columnas */
    div[data-testid="column"] .stButton > button {
        width: 100% !important;
    }

    /* ========== TARJETAS DE CLIENTE ========== */
    .client-card {
        background: var(--werfen-white);
        border: 1px solid #e8e8f0;
        border-top: 3px solid var(--werfen-blue);
        border-radius: var(--border-radius);
        padding: 1.1rem 1.25rem;
        margin-bottom: 0.75rem;
        box-shadow: var(--card-shadow);
        transition: box-shadow 0.22s ease, border-top-color 0.22s ease;
        position: relative;
    }

    .client-card:hover {
        box-shadow: 0 4px 12px rgba(6,3,141,0.12);
        border-top-color: var(--werfen-orange);
    }

    .client-card h4 {
        color: var(--werfen-blue);
        margin: 0 0 0.6rem 0;
        font-size: 1rem;
        font-weight: 700;
    }

    .client-card p {
        margin: 0.15rem 0;
        font-size: 0.82rem;
        color: var(--werfen-text-gray);
    }

    .client-card strong {
        color: #374151;
        font-weight: 600;
    }

    /* ========== BADGES / PILLS ========== */
    .werfen-badge {
        display: inline-block;
        padding: 2px 9px;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.2px;
    }
    .werfen-badge-orange {
        background: var(--werfen-orange);
        color: white;
    }
    .werfen-badge-blue {
        background: rgba(6,3,141,0.1);
        color: var(--werfen-blue);
    }
    .werfen-badge-gray {
        background: #e8e8f0;
        color: #374151;
    }

    /* ========== FILTROS Y SELECTORES (área de contenido) ========== */
    .stApp .stSelectbox > div > div {
        border: 1px solid var(--werfen-gray-dark);
        border-radius: var(--border-radius);
        transition: border-color 0.2s ease;
    }
    .stApp .stSelectbox > div > div:focus-within {
        border-color: var(--werfen-blue) !important;
        box-shadow: 0 0 0 2px rgba(6,3,141,0.1) !important;
    }
    .stApp .stTextInput > div > div > input {
        border: 1px solid var(--werfen-gray-dark);
        border-radius: var(--border-radius);
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }
    .stApp .stTextInput > div > div > input:focus {
        border-color: var(--werfen-blue) !important;
        box-shadow: 0 0 0 2px rgba(6,3,141,0.1) !important;
    }
    .stApp .stMultiSelect > div > div {
        border: 1px solid var(--werfen-gray-dark);
        border-radius: var(--border-radius);
    }
    .stApp .stMultiSelect > div > div:focus-within {
        border-color: var(--werfen-blue) !important;
        box-shadow: 0 0 0 2px rgba(6,3,141,0.1) !important;
    }
    .stApp .stMultiSelect span[data-baseweb="tag"] {
        background: rgba(6,3,141,0.1) !important;
        color: var(--werfen-blue) !important;
        border-radius: 4px !important;
    }

    /* ========== MÉTRICAS NATIVAS DE STREAMLIT ========== */
    div[data-testid="metric-container"] {
        background: var(--werfen-white);
        border: 1px solid #e8e8f0;
        border-radius: var(--border-radius);
        padding: 1.1rem 1.25rem 1rem;
        margin-bottom: 0.75rem;
        box-shadow: var(--card-shadow);
        position: relative;
        overflow: hidden;
        transition: box-shadow 0.22s ease;
    }
    div[data-testid="metric-container"]::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: var(--werfen-orange);
    }
    div[data-testid="metric-container"]:hover {
        box-shadow: var(--card-shadow-hover);
    }
    div[data-testid="metric-container"] > div > div[data-testid="metric-label"] {
        font-size: 0.78rem !important;
        color: var(--werfen-text-gray) !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    div[data-testid="metric-container"] > div > div[data-testid="metric-value"] {
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        color: var(--werfen-blue) !important;
        line-height: 1.1 !important;
    }
    div[data-testid="metric-container"] > div > div[data-testid="metric-delta"][data-state="positive"] {
        background-color: rgba(46,125,50,0.1) !important;
        color: #2e7d32 !important;
        border-radius: 4px !important;
        padding: 2px 6px !important;
    }
    div[data-testid="metric-container"] > div > div[data-testid="metric-delta"][data-state="negative"] {
        background-color: rgba(211,47,47,0.1) !important;
        color: #d32f2f !important;
        border-radius: 4px !important;
        padding: 2px 6px !important;
    }

    /* ========== MÉTRICAS WERFEN PERSONALIZADAS ========== */
    .werfen-metric {
        background: var(--werfen-white);
        border: 1px solid #e8e8f0;
        border-radius: var(--border-radius);
        padding: 1.1rem 1.25rem;
        margin-bottom: 0.75rem;
        box-shadow: var(--card-shadow);
        position: relative;
        overflow: hidden;
        transition: box-shadow 0.22s ease;
    }
    .werfen-metric::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: var(--werfen-orange);
    }
    .werfen-metric:hover {
        box-shadow: var(--card-shadow-hover);
    }
    .werfen-metric .metric-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .werfen-metric .metric-label {
        font-size: 0.78rem;
        color: var(--werfen-text-gray);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .werfen-metric .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: var(--werfen-blue);
        line-height: 1.1;
        margin-top: 0.35rem;
    }
    .werfen-metric .metric-delta {
        font-size: 0.76rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 20px;
        margin-top: 0.35rem;
        display: inline-block;
    }
    .werfen-metric .metric-delta.positive {
        background-color: rgba(46,125,50,0.1);
        color: #2e7d32;
    }
    .werfen-metric .metric-delta.negative {
        background-color: rgba(211,47,47,0.1);
        color: #d32f2f;
    }
    .werfen-metric .metric-help {
        width: 18px; height: 18px;
        border-radius: 50%;
        background: var(--werfen-gray);
        display: flex; align-items: center; justify-content: center;
        font-size: 0.74rem;
        color: var(--werfen-text-gray);
        cursor: help;
    }

    /* ========== BOTONES WERFEN PERSONALIZADOS (HTML buttons) ========== */
    .werfen-button-container {
        margin: 0.4rem 0;
    }
    .werfen-button-container.full-width { width: 100%; }

    .werfen-button {
        border: 2px solid transparent;
        border-radius: var(--border-radius);
        padding: 0.65rem 1.4rem;
        font-weight: 600;
        font-size: 0.88rem;
        cursor: pointer;
        transition: all 0.2s ease;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    .werfen-button.primary {
        background: var(--werfen-blue);
        color: white;
        border-color: var(--werfen-blue);
    }
    .werfen-button.primary:hover:not(.disabled) {
        background: white;
        color: var(--werfen-blue);
        border-color: var(--werfen-blue);
        box-shadow: 0 4px 10px rgba(6,3,141,0.2);
    }
    .werfen-button.secondary {
        background: var(--werfen-orange);
        color: white;
        border-color: var(--werfen-orange);
    }
    .werfen-button.secondary:hover:not(.disabled) {
        background: white;
        color: var(--werfen-orange);
        border-color: var(--werfen-orange);
    }
    .werfen-button.outline {
        background: transparent;
        border: 2px solid var(--werfen-blue);
        color: var(--werfen-blue);
    }
    .werfen-button.outline:hover:not(.disabled) {
        background: var(--werfen-blue);
        color: white;
    }
    .werfen-button.disabled {
        opacity: 0.6;
        cursor: not-allowed;
    }
    .werfen-button.full-width { width: 100%; }

    /* ========== ALERTAS ========== */
    .stAlert > div {
        border-radius: var(--border-radius);
    }
    .stInfo > div {
        border-left-color: var(--werfen-blue) !important;
    }

    /* ========== TABLAS ========== */
    .stDataFrame {
        border-radius: var(--border-radius);
        overflow: hidden;
        box-shadow: var(--card-shadow);
    }
    .stDataFrame tbody tr:hover {
        background-color: rgba(6,3,141,0.04) !important;
    }

    /* ========== TABS ========== */
    .stTabs [data-baseweb="tab"] {
        color: var(--werfen-text-gray);
        font-weight: 500;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: var(--werfen-blue) !important;
        border-bottom-color: var(--werfen-orange) !important;
        font-weight: 700;
    }

    /* ========== CALENDARIO ========== */
    .calendar-container {
        background: white;
        border-radius: var(--border-radius);
        padding: 1.25rem;
        box-shadow: var(--card-shadow);
        border: 1px solid #e8e8f0;
    }
    .calendar-header {
        background: linear-gradient(135deg, var(--werfen-blue) 0%, var(--werfen-orange) 100%);
        color: white;
        padding: 0.9rem 1rem;
        border-radius: var(--border-radius);
        text-align: center;
        margin-bottom: 1rem;
        font-weight: 700;
    }

    /* ========== LOGO Y BRANDING ========== */
    .werfen-logo {
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .werfen-logo h1 {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        color: var(--werfen-blue);
        font-size: 2.5rem;
        font-weight: 800;
        margin: 0;
    }
    .werfen-subtitle {
        color: var(--werfen-blue);
        font-size: 1rem;
        font-weight: 500;
        text-align: center;
        margin-bottom: 1.5rem;
    }

    /* ========== FORMULARIOS ========== */
    .form-container {
        background: white;
        padding: 1.5rem;
        border-radius: var(--border-radius);
        box-shadow: var(--card-shadow);
        border: 1px solid #e8e8f0;
        border-top: 3px solid var(--werfen-blue);
        margin-bottom: 1rem;
    }
    .form-container h3 {
        color: var(--werfen-blue);
        margin-bottom: 1.25rem;
        font-weight: 700;
        border-bottom: 2px solid var(--werfen-orange);
        padding-bottom: 0.4rem;
    }

    /* ========== FOOTER ========== */
    .werfen-footer {
        text-align: center;
        padding: 0.25rem 0;
        margin-top: 0.5rem;
        border-top: 1px solid var(--werfen-gray-dark);
        color: var(--werfen-blue);
        font-size: 0.85rem;
        line-height: 1.2;
    }
    .werfen-footer p { margin: 0; }

    /* ========== OCULTAR BOTÓN FULLSCREEN DE IMÁGENES ========== */
    [data-testid="StyledFullScreenButton"],
    [data-testid="stImageFullScreenButton"],
    button[title="View fullscreen"],
    [data-testid="imageFullScreenOverlay"] {
        display: none !important;
    }

    /* ========== LOADER / SPINNER ========== */
    div[data-testid="stStatusWidget"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
    }
    div[data-testid="stStatusWidget"] > div:first-child {
        display: none !important;
    }
    div[data-testid="stStatusWidget"]::before {
        content: '' !important;
        display: block !important;
        width: 32px !important;
        height: 32px !important;
        border: 3px solid rgba(6,3,141,0.12) !important;
        border-top: 3px solid #06038D !important;
        border-right: 3px solid #E87721 !important;
        border-radius: 50% !important;
        animation: werfen-spin 0.8s linear infinite !important;
    }
    div[data-testid="stStatusWidget"]::after {
        display: none !important;
    }
    @keyframes werfen-spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    .stSpinner > div {
        border-top-color: #06038D !important;
        border-right-color: #E87721 !important;
    }
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #06038D 0%, #E87721 100%) !important;
    }
    .stProgress > div > div {
        background-color: rgba(6,3,141,0.1) !important;
    }

    /* ========== ANIMACIONES ========== */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(14px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    .fade-in-up { animation: fadeInUp 0.4s ease-out; }

    /* ========== RESPONSIVE ========== */
    @media (max-width: 768px) {
        .client-card { padding: 0.9rem; }
        div[data-testid="metric-container"] > div > div[data-testid="metric-value"] {
            font-size: 1.8rem !important;
        }
    }
    </style>
    """

def get_werfen_header():
    """Retorna el header personalizado de Werfen"""
    return """
    <div class="werfen-logo fade-in-up">
        <h1>Green Logistics</h1>
    </div>
    """

def get_client_card_html(client):
    """Genera HTML personalizado para tarjetas de cliente"""
    tipo  = (client.get('tipo_cliente') or '').strip()
    pais  = (client.get('pais') or '').strip()
    tipo_badge = (
        f'<span class="werfen-badge werfen-badge-orange" style="font-size:0.7rem;">{tipo}</span>'
        if tipo else ''
    )
    pais_badge = (
        f'<span class="werfen-badge werfen-badge-blue" style="font-size:0.7rem;margin-left:4px;">{pais}</span>'
        if pais else ''
    )
    return f"""
    <div class="client-card fade-in-up">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0.55rem;">
            <h4 style="margin:0;flex:1;padding-right:8px;">{client['name']}</h4>
            <div style="white-space:nowrap;flex-shrink:0;">{tipo_badge}{pais_badge}</div>
        </div>
        <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:2px 12px;">
            <p><strong>AG:</strong> {client.get('codigo_ag') or 'N/A'}</p>
            <p><strong>WE:</strong> {client.get('codigo_we') or 'N/A'}</p>
            <p><strong>CSR:</strong> {client.get('csr') or 'N/A'}</p>
            <p><strong>Vendedor:</strong> {client.get('vendedor') or 'N/A'}</p>
            <p><strong>Cal. SAP:</strong> {(client.get('calendario_sap') or '').strip() or 'N/A'}</p>
            <p><strong>Región:</strong> {client.get('region') or 'N/A'}</p>
            <p><strong>Estado:</strong> {client.get('estado') or 'N/A'}</p>
            <p><strong>Ciudad:</strong> {client.get('ciudad') or 'N/A'}</p>
        </div>
    </div>
    """

def get_metric_card_html(title, value, subtitle="", color="#06038D"):
    """Genera HTML para tarjetas KPI con barra naranja, número grande azul y etiqueta gris"""
    subtitle_html = (
        f'<div style="font-size:0.76rem;color:#6b7280;margin-top:3px;">{subtitle}</div>'
        if subtitle else ''
    )
    return f"""
    <div style="background:#fff;border:1px solid #e8e8f0;border-radius:8px;padding:1.1rem 1.25rem;
                box-shadow:0 2px 8px rgba(6,3,141,0.10);position:relative;overflow:hidden;
                text-align:center;margin-bottom:0.75rem;">
        <div style="position:absolute;top:0;left:0;right:0;height:3px;background:#E87721;"></div>
        <div style="font-size:2.3rem;font-weight:700;color:#06038D;line-height:1.1;">{value}</div>
        <div style="font-size:0.76rem;font-weight:600;color:#6b7280;text-transform:uppercase;
                    letter-spacing:0.5px;margin-top:0.4rem;">{title}</div>
        {subtitle_html}
    </div>
    """

def get_calendar_header_html(month_name):
    """Genera HTML para header de calendario"""
    return f"""
    <div class="calendar-header fade-in-up">
        📅 Calendario de {month_name}
    </div>
    """

def get_werfen_footer():
    """Retorna el footer personalizado"""
    return """
    <div class="werfen-footer">
        <p>Green Logistics Web App - Shipment Consolidation | Werfen México Customer Service</p>
    </div>
    """

def get_metric_html(label, value, delta=None, help_text=None):
    """Genera HTML para una métrica con estilo Werfen"""
    delta_html = ""
    if delta is not None:
        delta_class = "positive" if delta >= 0 else "negative"
        delta_icon = "↗" if delta >= 0 else "↘"
        delta_html = f'<div class="metric-delta {delta_class}">{delta_icon} {delta}</div>'
    
    help_html = ""
    if help_text:
        help_html = f'<div class="metric-help" title="{help_text}">ℹ</div>'
    
    return f"""
    <div class="werfen-metric">
        <div class="metric-header">
            <span class="metric-label">{label}</span>
            {help_html}
        </div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """

def get_button_html(text, button_type="primary", disabled=False, full_width=False, onclick=""):
    """Genera HTML para un botón con estilo Werfen"""
    disabled_class = " disabled" if disabled else ""
    width_class = " full-width" if full_width else ""
    onclick_attr = f'onclick="{onclick}"' if onclick else ""
    
    return f"""
    <div class="werfen-button-container{width_class}">
        <button class="werfen-button {button_type}{disabled_class}" 
                {'disabled' if disabled else ''} {onclick_attr}>
            {text}
        </button>
    </div>
    """

def get_form_container_html(title, content):
    """Genera HTML para un contenedor de formulario con estilo Werfen"""
    return f"""
    <div class="form-container fade-in-up">
        <h3>{title}</h3>
        {content}
    </div>
    """
