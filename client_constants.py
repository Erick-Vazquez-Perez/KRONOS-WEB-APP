"""
Constantes para los campos de cliente
"""

# Tipos de cliente disponibles
TIPOS_CLIENTE = [
    "Integrador",
    "Distribuidor", 
    "Directo",
    "Clinica",
    "Laboratorio",
    "Hospital",
    "Fundación",
    "Otro"
]

# Regiones disponibles
REGIONES = [
    "Norte",
    "Centro", 
    "Occidente",
    "Cuentas Institucionales",
    "Bogotá",
    "Medellín",
    "Cali",
    "Costa",
    "Otro"
]

# Países disponibles
PAISES = [
    "Colombia",
    "México",
    "Otro"
]

def get_tipos_cliente():
    """Retorna la lista de tipos de cliente disponibles"""
    return TIPOS_CLIENTE.copy()

def get_regiones():
    """Retorna la lista de regiones disponibles"""
    return REGIONES.copy()

def get_paises():
    """Retorna la lista de países disponibles"""
    return PAISES.copy()
