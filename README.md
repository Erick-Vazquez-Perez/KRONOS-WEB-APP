# KRONOS 2.0 - Sistema de Gestión de Calendarios

Sistema web desarrollado para Werfen que permite gestionar calendarios de clientes con autenticación basada en roles y base de datos en la nube.

## 🚀 Características

### ✅ **Sistema de Autenticación**
- **Login persistente** - No se pierde la sesión al hacer refresh
- **Dos tipos de usuario:**
  - `kronosuser` - Solo lectura (visualización)
  - `kronosadmin` - Permisos completos (edición)
- **Interfaz mejorada** con logo corporativo

### ✅ **Base de Datos en la Nube**
- **SQLiteCloud** - Base de datos centralizada
- **Sincronización automática** entre desarrollo y producción
- **Sin problemas de versiones** - mismos datos en todos lados

### ✅ **Optimizaciones de Rendimiento**
- **Cache inteligente** - Consultas repetitivas optimizadas
- **Sin warnings** - Logs limpios
- **Navegación fluida** entre páginas

## 👥 Usuarios del Sistema

| Usuario | Contraseña | Permisos |
|---------|------------|----------|
| `kronosuser` | `KronosUser2024!` | Solo lectura |
| `kronosadmin` | `KronosAdmin2024!` | Administrador completo |

## 🛠️ Configuración para Desarrollo

1. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Variables de entorno** (archivo `.env`):
   ```env
   KRONOS_ENV=development
   LOCAL_DEVELOPMENT=true
   SQLITECLOUD_CONNECTION_STRING=sqlitecloud://cdjydgzlhk.g5.sqlite.cloud:8860/client_calendar.db?apikey=umCTRDGxAR2FUkNbpDOihf47bM4bQR3tRKJ53qFzL7A
   ```

3. **Ejecutar aplicación:**
   ```bash
   streamlit run main.py
   ```

## ☁️ Configuración para Producción (Streamlit Cloud)

1. **En Streamlit Cloud → Settings → Secrets**, agregar:
   ```toml
   SQLITECLOUD_CONNECTION_STRING = "sqlitecloud://cdjydgzlhk.g5.sqlite.cloud:8860/client_calendar.db?apikey=umCTRDGxAR2FUkNbpDOihf47bM4bQR3tRKJ53qFzL7A"
   ```

2. **Variables automáticas** (se detectan solas):
   - `STREAMLIT_CLOUD=true`
   - `STREAMLIT_SERVER_PORT=8501`

## 📁 Estructura del Proyecto

```
KRONOS 2.0/
├── main.py                 # Aplicación principal
├── auth_system.py          # Sistema de autenticación
├── config.py              # Configuración de entornos
├── database.py            # Funciones de base de datos
├── ui_components.py       # Componentes de interfaz
├── dashboard_components.py # Dashboard
├── werfen_styles.py       # Estilos corporativos
├── requirements.txt       # Dependencias
├── logo.png              # Logo corporativo
├── favicon.ico           # Icono de la app
└── .streamlit/
    └── secrets.toml       # Configuración local
```

## 🔒 Seguridad

- **Contraseñas hasheadas** con SHA256
- **Sesiones persistentes** pero con expiración (8 horas)
- **Verificación de permisos** en cada acción
- **Conexión segura** a SQLiteCloud

## 📊 Funcionalidades por Rol

### 📋 **Usuario (kronosuser)**
- ✅ Ver dashboard con métricas
- ✅ Ver galería de clientes
- ✅ Ver detalles de cada cliente
- ✅ Exportar datos
- ❌ No puede agregar/editar/eliminar

### ⚙️ **Administrador (kronosadmin)**
- ✅ Todas las funciones de usuario
- ✅ Agregar nuevos clientes
- ✅ Editar clientes existentes
- ✅ Gestionar frecuencias
- ✅ Modificar actividades
- ✅ Ver información de debug

## 🎨 Mejoras de Interfaz

- **Login moderno** con gradiente y logo corporativo
- **Sin emojis** en interfaz profesional
- **Información de usuario** al final de la sidebar
- **Navegación intuitiva** basada en permisos
- **Mensajes claros** de estado y errores

## 🚧 Funciones Próximamente

- Exportación avanzada a Excel/PDF
- Notificaciones por email
- Métricas avanzadas
- Gestión de usuarios desde la interfaz

---

**Desarrollado para Werfen** | **KRONOS 2.0** | **2025**
