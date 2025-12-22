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
    }

    /* ========== OCULTAR ELEMENTOS DEL HEADER DE STREAMLIT ========== */
    /* Ocultar botones de Deploy y menú de opciones, pero mantener el botón de sidebar */
    header[data-testid="stHeader"] button[kind="header"] {
        display: none !important;
    }
    
    header[data-testid="stHeader"] > div > div:nth-child(2) {
        display: none !important;
    }

    /* ========== ESTILOS BÁSICOS DE BOTONES ========== */
    /* Botones básicos con colores Werfen - Especificidad alta */
    .stApp .stButton > button,
    div[data-testid="stAppViewContainer"] .stButton > button {
        background: var(--werfen-blue) !important;
        color: white !important;
        border: 2px solid var(--werfen-blue) !important;
        border-radius: 8px !important;
        padding: 0.6rem 1.2rem !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 4px rgba(6, 3, 141, 0.2) !important;
        min-height: 42px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-decoration: none !important;
        line-height: 1.2 !important;
    }
    
    .stApp .stButton > button:hover,
    div[data-testid="stAppViewContainer"] .stButton > button:hover {
        background: white !important;
        color: var(--werfen-blue) !important;
        border-color: var(--werfen-blue) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 8px rgba(6, 3, 141, 0.3) !important;
    }
    
    .stApp .stButton > button:active,
    div[data-testid="stAppViewContainer"] .stButton > button:active {
        background: var(--werfen-blue-dark) !important;
        color: white !important;
        border-color: var(--werfen-blue-dark) !important;
        transform: translateY(0px) !important;
        box-shadow: 0 1px 2px rgba(6, 3, 141, 0.2) !important;
    }
    
    .stApp .stButton > button:focus,
    div[data-testid="stAppViewContainer"] .stButton > button:focus {
        outline: 2px solid rgba(6, 3, 141, 0.3) !important;
        outline-offset: 2px !important;
    }
    
    .stApp .stButton > button:disabled,
    div[data-testid="stAppViewContainer"] .stButton > button:disabled {
        background: #e0e0e0 !important;
        color: #999 !important;
        border-color: #ddd !important;
        cursor: not-allowed !important;
        transform: none !important;
        box-shadow: none !important;
        opacity: 0.6 !important;
    }
    /* ========== ESTILOS PARA BOTONES ESPECÍFICOS ========== */
    /* Botones de tipo "primary" - Mantener el estilo azul → blanco */
    .stApp .stButton > button[kind="primary"],
    .stApp .stButton > button[data-testid="baseButton-primary"] {
        background: var(--werfen-blue) !important;
        color: white !important;
        border-color: var(--werfen-blue) !important;
    }
    
    .stApp .stButton > button[kind="primary"]:hover,
    .stApp .stButton > button[data-testid="baseButton-primary"]:hover {
        background: white !important;
        color: var(--werfen-blue) !important;
        border-color: var(--werfen-blue) !important;
    }
    
    /* Botones de tipo "secondary" - Mantener el estilo azul → blanco */
    .stApp .stButton > button[kind="secondary"],
    .stApp .stButton > button[data-testid="baseButton-secondary"] {
        background: var(--werfen-blue) !important;
        color: white !important;
        border: 2px solid var(--werfen-blue) !important;
    }
    
    .stApp .stButton > button[kind="secondary"]:hover,
    .stApp .stButton > button[data-testid="baseButton-secondary"]:hover {
        background: white !important;
        color: var(--werfen-blue) !important;
    }
    
    /* Estilos de espaciado para contenedores de botones */
    .stButton {
        margin: 0.25rem 0 !important;
    }
    
    /* Botones en columnas */
    div[data-testid="column"] .stButton > button {
        width: 100% !important;
    }
    
    /* ========== HEADER Y NAVEGACIÓN ========== */
    .main-header {
        background: linear-gradient(135deg, var(--werfen-blue) 0%, var(--werfen-blue-light) 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(6, 3, 141, 0.1);
    }

    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
    }

    /* ========== SIDEBAR ========== */
    .css-1d391kg {
        background-color: var(--werfen-gray);
        border-right: 3px solid var(--werfen-blue);
    }

    /* Espaciado mejorado en sidebar */
    div[data-testid="stSidebar"] hr {
        margin: 25px 0 !important;
        border: 1px solid var(--werfen-orange) !important;
        border-radius: 2px !important;
        background: linear-gradient(90deg, var(--werfen-blue) 0%, var(--werfen-orange) 100%) !important;
        height: 2px !important;
    }
    
    /* Títulos de sección personalizados en sidebar */
    div[data-testid="stSidebar"] h3 {
        color: var(--werfen-blue) !important;
        font-weight: 800 !important;
        margin: 25px 0 20px 0 !important;
        font-size: 18px !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        text-align: center !important;
        padding: 10px 0 !important;
        border-bottom: 2px solid var(--werfen-orange) !important;
        background: linear-gradient(135deg, var(--werfen-gray) 0%, var(--werfen-white) 100%) !important;
        border-radius: 8px !important;
    }
    
    /* Estilo para contenedores de botones en sidebar */
    .stButton {
        margin-bottom: 12px !important;
    }

    /* ========== TARJETAS DE CLIENTE ========== */
    .client-card {
        border: 2px solid var(--werfen-gray-dark);
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        background: linear-gradient(135deg, white 0%, var(--werfen-gray) 100%);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }

    .client-card:before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, var(--werfen-blue) 0%, var(--werfen-orange) 100%);
    }

    .client-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.15);
        border-color: var(--werfen-blue);
    }

    .client-card h4 {
        color: var(--werfen-blue);
        margin: 0 0 0.8rem 0;
        font-size: 1.3rem;
        font-weight: 700;
    }

    .client-card p {
        margin: 0.3rem 0;
        font-size: 0.9rem;
        color: #333;
    }

    .client-card strong {
        color: var(--werfen-blue);
        font-weight: 600;
    }

    /* ========== FILTROS Y SELECTORES ========== */
    .stSelectbox > div > div {
        border: 2px solid var(--werfen-gray-dark);
        border-radius: 8px;
        transition: border-color 0.3s ease;
    }

    .stSelectbox > div > div:focus-within {
        border-color: var(--werfen-blue);
        box-shadow: 0 0 0 2px rgba(6, 3, 141, 0.1);
    }

    .stTextInput > div > div > input {
        border: 2px solid var(--werfen-gray-dark);
        border-radius: 8px;
        transition: border-color 0.3s ease;
    }

    .stTextInput > div > div > input:focus {
        border-color: var(--werfen-blue);
        box-shadow: 0 0 0 2px rgba(6, 3, 141, 0.1);
    }

    /* ========== MÉTRICAS Y ESTADÍSTICAS ========== */
    .metric-card {
        background: linear-gradient(135deg, var(--werfen-blue) 0%, var(--werfen-blue-light) 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(6, 3, 141, 0.2);
        margin-bottom: 1rem;
    }

    .metric-card h3 {
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
    }

    .metric-card p {
        margin: 0.5rem 0 0 0;
        font-size: 0.9rem;
        opacity: 0.9;
    }

    /* ========== ESTILIZADO DE MÉTRICAS NATIVAS DE STREAMLIT ========== */
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, white 0%, var(--werfen-gray) 100%);
        border: 2px solid var(--werfen-gray-dark);
        border-left: 4px solid var(--werfen-blue);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    div[data-testid="metric-container"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(6, 3, 141, 0.15);
        border-left-color: var(--werfen-orange);
    }

    div[data-testid="metric-container"] > div {
        color: var(--werfen-blue) !important;
    }

    div[data-testid="metric-container"] > div > div[data-testid="metric-label"] {
        font-size: 0.9rem !important;
        color: #666 !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        margin-bottom: 0.5rem !important;
    }

    div[data-testid="metric-container"] > div > div[data-testid="metric-value"] {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        color: var(--werfen-blue) !important;
        line-height: 1 !important;
    }

    div[data-testid="metric-container"] > div > div[data-testid="metric-delta"] {
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        padding: 0.2rem 0.5rem !important;
        border-radius: 20px !important;
        margin-top: 0.5rem !important;
    }

    div[data-testid="metric-container"] > div > div[data-testid="metric-delta"][data-state="positive"] {
        background-color: rgba(46, 125, 50, 0.1) !important;
        color: #2e7d32 !important;
    }

    div[data-testid="metric-container"] > div > div[data-testid="metric-delta"][data-state="negative"] {
        background-color: rgba(211, 47, 47, 0.1) !important;
        color: #d32f2f !important;
    }

    /* ========== MÉTRICAS WERFEN PERSONALIZADAS ========== */
    .werfen-metric {
        background: linear-gradient(135deg, white 0%, var(--werfen-gray) 100%);
        border: 2px solid var(--werfen-gray-dark);
        border-left: 4px solid var(--werfen-blue);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
        position: relative;
    }

    .werfen-metric:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(6, 3, 141, 0.15);
        border-left-color: var(--werfen-orange);
    }

    .werfen-metric .metric-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
    }

    .werfen-metric .metric-label {
        font-size: 0.9rem;
        color: #666;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .werfen-metric .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--werfen-blue);
        line-height: 1;
    }

    .werfen-metric .metric-delta {
        font-size: 0.8rem;
        font-weight: 600;
        padding: 0.2rem 0.5rem;
        border-radius: 20px;
        margin-top: 0.5rem;
    }

    .werfen-metric .metric-delta.positive {
        background-color: rgba(46, 125, 50, 0.1);
        color: #2e7d32;
    }

    .werfen-metric .metric-delta.negative {
        background-color: rgba(211, 47, 47, 0.1);
        color: #d32f2f;
    }

    .werfen-metric .metric-help {
        background-color: var(--werfen-gray);
        border-radius: 50%;
        width: 20px;
        height: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.8rem;
        color: #666;
        cursor: help;
    }

    /* ========== BOTONES WERFEN PERSONALIZADOS ========== */
    .werfen-button-container {
        margin: 0.5rem 0;
    }

    .werfen-button-container.full-width {
        width: 100%;
    }

    .werfen-button {
        border: 2px solid transparent;
        border-radius: 8px;
        padding: 0.8rem 1.5rem;
        font-weight: 600;
        font-size: 0.9rem;
        cursor: pointer;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    .werfen-button.primary {
        background: linear-gradient(45deg, var(--werfen-blue) 0%, var(--werfen-blue-light) 100%);
        color: white;
        border-color: var(--werfen-blue);
    }

    .werfen-button.primary:hover:not(.disabled) {
        background: white !important;
        color: var(--werfen-blue) !important;
        border-color: var(--werfen-blue) !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(6, 3, 141, 0.3);
    }

    .werfen-button.secondary {
        background: linear-gradient(45deg, var(--werfen-orange) 0%, var(--werfen-orange-light) 100%);
        color: white;
        border-color: var(--werfen-orange);
    }

    .werfen-button.secondary:hover:not(.disabled) {
        background: white !important;
        color: var(--werfen-orange) !important;
        border-color: var(--werfen-orange) !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(232, 119, 33, 0.3);
    }

    .werfen-button.outline {
        background: transparent;
        border: 2px solid var(--werfen-blue);
        color: var(--werfen-blue);
    }

    .werfen-button.outline:hover:not(.disabled) {
        background: var(--werfen-blue);
        color: white;
        transform: translateY(-2px);
    }

    .werfen-button.disabled {
        opacity: 0.6;
        cursor: not-allowed;
        transform: none !important;
        box-shadow: none !important;
    }

    .werfen-button.full-width {
        width: 100%;
    }

    /* ========== ALERTAS Y MENSAJES ========== */
    .stAlert > div {
        border-radius: 8px;
        border-left: 4px solid var(--werfen-orange);
    }

    .stSuccess > div {
        background-color: rgba(232, 119, 33, 0.1);
        border-left-color: var(--werfen-orange);
    }

    .stInfo > div {
        background-color: rgba(6, 3, 141, 0.1);
        border-left-color: var(--werfen-blue);
    }

    /* ========== TABLAS ========== */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    .stDataFrame thead th {
        background: linear-gradient(135deg, var(--werfen-blue) 0%, var(--werfen-blue-light) 100%);
        color: white;
        font-weight: 600;
        padding: 1rem;
    }

    .stDataFrame tbody tr:nth-child(even) {
        background-color: var(--werfen-gray);
    }

    .stDataFrame tbody tr:hover {
        background-color: rgba(6, 3, 141, 0.05);
    }

    /* ========== FORMULARIOS ========== */
    .form-container {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border: 1px solid var(--werfen-gray-dark);
        margin-bottom: 1rem;
    }

    .form-container h3 {
        color: var(--werfen-blue);
        margin-bottom: 1.5rem;
        font-weight: 700;
        border-bottom: 2px solid var(--werfen-orange);
        padding-bottom: 0.5rem;
    }

    /* ========== TABS ========== */
    .stTabs > div > div > div > div {
        color: var(--werfen-blue);
        font-weight: 600;
    }

    .stTabs > div > div > div > div[aria-selected="true"] {
        color: var(--werfen-orange);
        border-bottom-color: var(--werfen-orange);
    }

    /* ========== CALENDARIO ========== */
    .calendar-container {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border: 1px solid var(--werfen-gray-dark);
    }

    .calendar-header {
        background: linear-gradient(135deg, var(--werfen-blue) 0%, var(--werfen-orange) 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: 700;
    }

    /* ========== LOGO Y BRANDING ========== */
    .werfen-logo {
        text-align: center;
        margin-bottom: 2rem;
    }

    .werfen-logo h1 {
        font-family: 'Verdana', sans-serif;
        color: var(--werfen-blue);
        font-size: 3rem;
        font-weight: 800;
        margin: 0;
    }

    .werfen-subtitle {
        color: var(--werfen-blue);
        font-size: 1.1rem;
        font-weight: 500;
        text-align: center;
        margin-bottom: 2rem;
    }

    /* ========== ANIMACIONES ========== */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .fade-in-up {
        animation: fadeInUp 0.6s ease-out;
    }

    /* ========== RESPONSIVE ========== */
    @media (max-width: 768px) {
        .client-card {
            padding: 1rem;
        }
        
        .werfen-logo h1 {
            font-family: 'Verdana', sans-serif;
            color: var(--werfen-blue);
            font-size: 2rem;
        }
        
        .main-header h1 {
            font-size: 1.8rem;
        }
    }

    /* ========== SIDEBAR PERSONALIZADO ========== */
    .css-1d391kg .css-1v0mbdj {
        border-top: 3px solid var(--werfen-orange);
    }

    /* ========== FOOTER ========== */
    .werfen-footer {
        text-align: center;
        padding: 2rem;
        margin-top: 3rem;
        border-top: 1px solid var(--werfen-gray-dark);
        color: var(--werfen-blue);
        font-size: 0.9rem;
    }

    /* ========== OCULTAR BOTÓN FULLSCREEN DE IMÁGENES ========== */
    [data-testid="StyledFullScreenButton"],
    [data-testid="stImageFullScreenButton"],
    button[title="View fullscreen"] {
        display: none !important;
    }
    
    /* Ocultar overlay de fullscreen */
    [data-testid="imageFullScreenOverlay"] {
        display: none !important;
    }
    </style>
    
    <script>
    // Forzar reestilizado después de que Streamlit cargue
    setTimeout(function() {
        const buttons = document.querySelectorAll('div[data-testid="stSidebar"] .stButton > button');
        buttons.forEach(button => {
            // Forzar estilos directamente
            button.style.cssText = `
                all: unset !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                width: 100% !important;
                height: 55px !important;
                margin: 10px 0 !important;
                padding: 15px 20px !important;
                border-radius: 12px !important;
                border: 2px solid #e0e0e0 !important;
                background: linear-gradient(135deg, #ffffff 0%, #f5f5f5 100%) !important;
                color: #06038D !important;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
                font-weight: 700 !important;
                font-size: 16px !important;
                text-align: center !important;
                cursor: pointer !important;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
                box-shadow: 0 4px 8px rgba(6, 3, 141, 0.2) !important;
                box-sizing: border-box !important;
                letter-spacing: 0.8px !important;
            `;
            
            // Agregar eventos de hover
            button.addEventListener('mouseenter', function() {
                if (!this.disabled) {
                    this.style.background = 'linear-gradient(135deg, #06038D 0%, #1a17a3 100%)';
                    this.style.color = '#ffffff';
                    this.style.borderColor = '#06038D';
                    this.style.transform = 'translateY(-4px)';
                    this.style.boxShadow = '0 12px 30px rgba(6, 3, 141, 0.4)';
                }
            });
            
            button.addEventListener('mouseleave', function() {
                if (!this.disabled && !this.closest('.nav-active')) {
                    this.style.background = 'linear-gradient(135deg, #ffffff 0%, #f5f5f5 100%)';
                    this.style.color = '#06038D';
                    this.style.borderColor = '#e0e0e0';
                    this.style.transform = 'translateY(0px)';
                    this.style.boxShadow = '0 4px 8px rgba(6, 3, 141, 0.2)';
                }
            });
        });
        
        // Aplicar estilos a botones activos
        const activeButtons = document.querySelectorAll('.nav-active .stButton > button');
        activeButtons.forEach(button => {
            button.style.background = 'linear-gradient(135deg, #E87721 0%, #ff8c3d 100%)';
            button.style.color = '#ffffff';
            button.style.borderColor = '#E87721';
            button.style.boxShadow = '0 8px 20px rgba(232, 119, 33, 0.3)';
            button.style.transform = 'translateY(-2px)';
        });
    }, 200);
    
    // Re-aplicar estilos cada vez que Streamlit re-renderiza
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList') {
                setTimeout(function() {
                    const buttons = document.querySelectorAll('div[data-testid="stSidebar"] .stButton > button');
                    buttons.forEach(button => {
                        if (!button.hasAttribute('data-styled')) {
                            button.style.cssText = `
                                all: unset !important;
                                display: flex !important;
                                align-items: center !important;
                                justify-content: center !important;
                                width: 100% !important;
                                height: 55px !important;
                                margin: 10px 0 !important;
                                padding: 15px 20px !important;
                                border-radius: 12px !important;
                                border: 2px solid #e0e0e0 !important;
                                background: linear-gradient(135deg, #ffffff 0%, #f5f5f5 100%) !important;
                                color: #06038D !important;
                                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
                                font-weight: 700 !important;
                                font-size: 16px !important;
                                text-align: center !important;
                                cursor: pointer !important;
                                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
                                box-shadow: 0 4px 8px rgba(6, 3, 141, 0.2) !important;
                                box-sizing: border-box !important;
                                letter-spacing: 0.8px !important;
                            `;
                            button.setAttribute('data-styled', 'true');
                        }
                    });
                }, 100);
            }
        });
    });
    
    // Observar cambios en la sidebar
    setTimeout(function() {
        const sidebar = document.querySelector('div[data-testid="stSidebar"]');
        if (sidebar) {
            observer.observe(sidebar, { childList: true, subtree: true });
        }
    }, 500);
    </script>
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
    return f"""
    <div class="client-card fade-in-up">
        <h4>{client['name']}</h4>
        <p><strong>Código AG:</strong> {client['codigo_ag'] or 'N/A'}</p>
        <p><strong>CSR:</strong> {client['csr'] or 'N/A'}</p>
        <p><strong>Vendedor:</strong> {client['vendedor'] or 'N/A'}</p>
        <p><strong>Tipo:</strong> {client.get('tipo_cliente', 'N/A') or 'N/A'}</p>
        <p><strong>Región:</strong> {client.get('region', 'N/A') or 'N/A'}</p>
    </div>
    """

def get_metric_card_html(title, value, subtitle="", color="#1f77b4"):
    """Genera HTML para tarjetas de métricas con el mismo estilo que las tarjetas de clientes"""
    return f"""
    <div class="client-card fade-in-up" style="text-align: center;">
        <h3 style="color: {color}; margin: 0 0 15px 0; font-size: 2.5em; font-weight: bold;">{value}</h3>
        <h4 style="color: var(--werfen-blue); margin: 0 0 8px 0; font-size: 1.1rem; font-weight: 600;">{title}</h4>
        {f'<p style="margin: 0; font-size: 0.9rem; color: #666;">{subtitle}</p>' if subtitle else ''}
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
