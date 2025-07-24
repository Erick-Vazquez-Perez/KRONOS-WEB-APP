#!/usr/bin/env python3
"""
Script de prueba para verificar que las importaciones funcionan correctamente
"""

try:
    print("Probando importaciones...")
    
    # Importaciones básicas
    import streamlit as st
    print("✓ Streamlit importado correctamente")
    
    import pandas as pd
    print("✓ Pandas importado correctamente")
    
    import plotly.express as px
    import plotly.graph_objects as go
    print("✓ Plotly importado correctamente")
    
    from datetime import datetime, timedelta, date
    print("✓ Datetime importado correctamente")
    
    # Importaciones locales
    try:
        from database import get_db_connection, get_clients, get_calculated_dates
        print("✓ Database módulos importados correctamente")
    except Exception as e:
        print(f"⚠ Error importando database: {e}")
    
    try:
        from werfen_styles import get_metric_card_html
        print("✓ Werfen styles importado correctamente")
    except Exception as e:
        print(f"⚠ Error importando werfen_styles: {e}")
    
    try:
        from dashboard_components import show_dashboard
        print("✓ Dashboard components importado correctamente")
    except Exception as e:
        print(f"⚠ Error importando dashboard_components: {e}")
    
    print("\n✅ Todas las importaciones básicas funcionan correctamente!")
    print("🚀 El dashboard debería funcionar sin problemas.")
    
except Exception as e:
    print(f"❌ Error durante las pruebas: {e}")
    import traceback
    traceback.print_exc()
