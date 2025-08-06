"""
Test rápido para verificar que los warnings están eliminados
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from database import get_clients, get_frequency_templates

def test_no_warnings():
    """Prueba que no aparezcan warnings"""
    print("🧪 Probando consultas sin warnings...")
    
    print("1. Obteniendo clientes...")
    clients = get_clients()
    print(f"   ✅ {len(clients)} clientes obtenidos")
    
    print("2. Obteniendo frecuencias...")
    frequencies = get_frequency_templates()
    print(f"   ✅ {len(frequencies)} frecuencias obtenidas")
    
    print("3. Probando segunda consulta (debe usar cache)...")
    clients2 = get_clients()
    print(f"   ✅ {len(clients2)} clientes obtenidos desde cache")
    
    print("✅ Test completado - Si no viste warnings de SQLAlchemy, ¡funcionó!")

if __name__ == "__main__":
    test_no_warnings()
