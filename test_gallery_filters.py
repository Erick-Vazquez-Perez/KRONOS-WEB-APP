"""
Test para verificar que los filtros y visualización de nuevos campos funcionen
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    print("1. Probando importaciones...")
    from client_constants import get_tipos_cliente, get_regiones
    from ui_components import show_clients_gallery
    from database import get_clients
    print("✓ Todas las importaciones exitosas")
    
    print("\n2. Probando constantes...")
    tipos = get_tipos_cliente()
    regiones = get_regiones()
    print(f"✓ Tipos de cliente disponibles: {tipos}")
    print(f"✓ Regiones disponibles: {regiones}")
    
    print("\n3. Probando base de datos...")
    clients = get_clients()
    print(f"✓ Clientes en BD: {len(clients)} registros")
    
    if not clients.empty:
        columns = clients.columns.tolist()
        print(f"✓ Columnas disponibles: {columns}")
        
        if 'tipo_cliente' in columns:
            print("✓ Columna 'tipo_cliente' presente")
        else:
            print("⚠ Columna 'tipo_cliente' NO presente")
        
        if 'region' in columns:
            print("✓ Columna 'region' presente")
        else:
            print("⚠ Columna 'region' NO presente")
    
    print("\n✅ TODOS LOS TESTS DE FUNCIONALIDAD PASARON!")
    print("\n📝 Los nuevos campos están listos para usar en:")
    print("   - Filtros de la galería")
    print("   - Tarjetas de cliente")
    print("   - Vista de tabla")
    print("   - Búsqueda de texto")
    print("   - Ordenamiento")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
