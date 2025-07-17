# Sistema de Múltiples Bases de Datos - Kronos

## Descripción

Kronos ahora maneja automáticamente diferentes bases de datos según el entorno de ejecución:

- **🚀 Producción (PRD)**: `client_calendar.db`
- **🔧 Desarrollo (DEV)**: `client_calendar_dev.db`  
- **🧪 Pruebas (TEST)**: `client_calendar_test.db`

## Detección Automática de Entorno

El sistema detecta automáticamente el entorno basándose en:

1. **Variable de entorno `KRONOS_ENV`**
2. **Plataformas de despliegue** (Streamlit Cloud, Heroku, Render, etc.)
3. **Archivos locales** (`.env`, `requirements-dev.txt`)
4. **Nombre del host** (localhost, DESKTOP-, LAPTOP-)

## Configuración Manual

### Archivo .env

Crea un archivo `.env` en la raíz del proyecto:

```bash
# Forzar entorno específico
KRONOS_ENV=development
```

### Variable de Entorno del Sistema

```bash
# Windows
set KRONOS_ENV=development

# Linux/Mac
export KRONOS_ENV=development
```

## Migración de Datos

### Script de Migración

Usa el script `migrate_database.py` para gestionar datos:

```bash
python migrate_database.py
```

**Opciones disponibles:**

1. **📊 Mostrar información** - Ver estado de todas las bases de datos
2. **🔄 Migrar PRD → DEV** - Copiar datos de producción a desarrollo (seguro)
3. **⚠️ Migrar DEV → PRD** - Copiar datos de desarrollo a producción (¡cuidado!)
4. **🛡️ Crear backup** - Respaldar cualquier base de datos
5. **❌ Salir**

### Flujo Recomendado

```bash
# 1. Copiar datos de producción a desarrollo
python migrate_database.py
# Seleccionar opción 2

# 2. Trabajar en desarrollo
streamlit run main.py
# Automáticamente usará client_calendar_dev.db

# 3. Cuando esté listo, migrar a producción
python migrate_database.py
# Seleccionar opción 3 (¡con cuidado!)
```

## Verificación del Entorno

### En la Aplicación

- **Desarrollo**: Título muestra "Kronos Web App 🔧 DEV"
- **Producción**: Título muestra "Kronos Web App"
- **Panel de desarrollo**: Expandible con información técnica

### En Logs

Al iniciar la aplicación verás:

```
[KRONOS] Inicializando base de datos: client_calendar_dev.db
[KRONOS] Entorno: development
[KRONOS] Descripción: Base de datos de desarrollo
```

## Casos de Uso

### Desarrollo Local

```bash
# Trabajar en desarrollo sin afectar producción
KRONOS_ENV=development streamlit run main.py
```

### Pruebas

```bash
# Usar base de datos temporal para pruebas
KRONOS_ENV=testing streamlit run main.py
```

### Producción

```bash
# Usar base de datos de producción
KRONOS_ENV=production streamlit run main.py
```

## Seguridad

### Archivos Protegidos (.gitignore)

```gitignore
# Bases de datos
*.db
client_calendar*.db

# Variables de entorno
.env
.env.local
```

### Backups Automáticos

- Se crean automáticamente antes de migraciones
- Formato: `client_calendar.db.backup_YYYYMMDD_HHMMSS`
- Incluyen timestamp para identificación

## Comandos Útiles

### Ver Estado Actual

```python
from config import get_db_config
config = get_db_config()
print(f"Entorno: {config.get_environment()}")
print(f"Base de datos: {config.get_database_path()}")
```

### Cambiar Entorno Manualmente

```python
import os
os.environ['KRONOS_ENV'] = 'development'
# Reiniciar la aplicación
```

### Crear Backup Manual

```python
from migrate_database import backup_database
backup_database('client_calendar.db')
```

## Troubleshooting

### Problema: Base de datos no encontrada

**Solución**: Ejecutar migración PRD → DEV

```bash
python migrate_database.py
# Opción 2
```

### Problema: Entorno incorrecto

**Solución**: Verificar variables de entorno

```bash
echo $KRONOS_ENV  # Linux/Mac
echo %KRONOS_ENV% # Windows
```

### Problema: Datos perdidos después de commit

**Solución**: Las bases de datos están en `.gitignore`, usar migración

```bash
# Recuperar desde backup o migrar desde producción
python migrate_database.py
```

## Estructura de Archivos

```
kronos/
├── client_calendar.db          # Producción (no en git)
├── client_calendar_dev.db      # Desarrollo (no en git)
├── client_calendar_test.db     # Pruebas (no en git)
├── config.py                   # Configuración de entornos
├── migrate_database.py         # Script de migración
├── .env                        # Variables locales (no en git)
├── .env.example               # Plantilla de configuración
├── .gitignore                 # Archivos excluidos
└── README_DATABASE.md         # Esta documentación
```

## Mejores Prácticas

1. **🔄 Migra datos antes de desarrollar**: Usa siempre datos actualizados
2. **🛡️ Haz backups**: Antes de cambios importantes
3. **🧪 Prueba en desarrollo**: Nunca desarrolles directo en producción
4. **📋 Documenta cambios**: Especialmente en estructuras de BD
5. **⚠️ Migra con cuidado**: DEV → PRD solo cuando estés seguro
