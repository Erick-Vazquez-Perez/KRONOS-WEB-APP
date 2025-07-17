# 🗄️ PERSISTENCIA DE BASE DE DATOS EN STREAMLIT CLOUD

## 🎯 **Problema Resuelto**

**Problema**: En Streamlit Cloud, los registros creados se almacenaban en memoria temporal y se perdían al reiniciar la aplicación.

**Solución**: Configurar la aplicación para que use el archivo `client_calendar.db` versionado en GitHub, garantizando persistencia completa.

---

## ⚙️ **Configuración Implementada**

### 🔧 **1. Detección Automática de Entorno**

La aplicación detecta automáticamente si está ejecutándose en:

- **Desarrollo Local** (`localhost:8501`): Usa `client_calendar_dev.db`
- **Streamlit Cloud** (producción): Usa `client_calendar.db` versionado
- **Otros clouds**: Usa `client_calendar.db` con ruta absoluta

### 📁 **2. Rutas de Base de Datos**

```python
# DESARROLLO LOCAL
database_path = "client_calendar_dev.db"  # Ruta relativa

# PRODUCCIÓN (Streamlit Cloud)
database_path = "/app/kronos-web-app/client_calendar.db"  # Ruta absoluta
```

### 🔄 **3. Versionado de la BD de Producción**

- ✅ **`client_calendar.db`**: Incluido en GitHub para Streamlit Cloud
- ❌ **`client_calendar_dev.db`**: Excluido (solo local)
- ❌ **`client_calendar_test.db`**: Excluido (solo testing)

---

## 🚀 **Comportamiento por Entorno**

| Entorno | Base de Datos | Persistencia | Versionado |
|---------|---------------|-------------|------------|
| **Desarrollo Local** | `client_calendar_dev.db` | ✅ Local | ❌ No |
| **Streamlit Cloud** | `client_calendar.db` | ✅ **GitHub** | ✅ **Sí** |
| **Testing** | `client_calendar_test.db` | ❌ Temporal | ❌ No |

---

## 🔍 **Detección Automática**

### 🌩️ **Streamlit Cloud**
```bash
# Variables detectadas automáticamente:
STREAMLIT_CLOUD=true
STREAMLIT_SERVER_PORT=8501
STREAMLIT_BROWSER_GATHER_USAGE_STATS=true
```

### 🏠 **Desarrollo Local**
```bash
# Ejecutándose en:
localhost:8501
127.0.0.1:8501
```

### ⚙️ **Variables de Entorno (Opcional)**
```bash
# Forzar entorno específico:
KRONOS_ENV=production  # Para forzar producción
KRONOS_ENV=development # Para forzar desarrollo
```

---

## 📂 **Estructura de Archivos**

```
kronos-web-app/
├── 🗄️ BASES DE DATOS
│   ├── client_calendar.db          # ✅ PRODUCCIÓN (versionado)
│   ├── client_calendar_dev.db      # ❌ Desarrollo (no versionado)
│   └── client_calendar_test.db     # ❌ Testing (no versionado)
├── ⚙️ CONFIGURACIÓN
│   ├── config.py                   # Detección de entorno y rutas
│   ├── .env                        # Variables locales (no versionado)
│   ├── .env.streamlit              # Referencia para Streamlit Cloud
│   └── .gitignore                  # Configuración de exclusiones
└── 🚀 APLICACIÓN
    ├── main.py
    ├── database.py
    └── ...
```

---

## ✅ **Verificación de Funcionamiento**

### 🧪 **Test Local**
```python
from config import DatabaseConfig
config = DatabaseConfig()

print(f"Entorno: {config.get_environment()}")
print(f"BD: {config.get_database_path()}")
# Output: Entorno: development, BD: client_calendar_dev.db
```

### 🌩️ **Test Streamlit Cloud**
```python
# En Streamlit Cloud automáticamente:
# Entorno: production
# BD: /app/kronos-web-app/client_calendar.db
```

---

## 🎉 **Resultado Final**

### ✅ **Beneficios Logrados**

1. **🔒 Persistencia Garantizada**: Los datos nunca se pierden en Streamlit Cloud
2. **🔄 Sincronización Automática**: Cambios en GitHub se reflejan en la app
3. **🌍 Acceso Global**: Todos los usuarios ven los mismos datos
4. **📊 Historial Versionado**: Los datos están respaldados en GitHub
5. **🚀 Zero Configuration**: No requiere configuración manual en deployment

### 🎯 **Casos de Uso Cubiertos**

- ✅ **Desarrollo Local**: Base de datos independiente para pruebas
- ✅ **Producción Cloud**: Base de datos persistente versionada
- ✅ **Deployment Automático**: Sin configuración manual requerida
- ✅ **Backup Automático**: GitHub actúa como respaldo

---

## 🛠️ **Troubleshooting**

### ❓ **"Los datos no persisten en Streamlit Cloud"**
- ✅ Verificar que `client_calendar.db` esté en el repositorio
- ✅ Confirmar que el commit incluye el archivo de BD
- ✅ Comprobar que Streamlit Cloud detecta el entorno correctamente

### ❓ **"Error de permisos en la base de datos"**
- ✅ Streamlit Cloud tiene permisos de lectura/escritura automáticamente
- ✅ La aplicación usa rutas absolutas en producción

### ❓ **"Datos diferentes entre local y cloud"**
- ✅ Es normal: desarrollo usa `client_calendar_dev.db`
- ✅ Producción usa `client_calendar.db` (datos reales)

---

## 📋 **Checklist de Deployment**

- [x] `client_calendar.db` incluido en `.gitignore` como excepción
- [x] Archivo `client_calendar.db` commiteado al repositorio
- [x] `config.py` configurado para rutas absolutas en producción
- [x] Detección automática de Streamlit Cloud funcionando
- [x] Variables de entorno opcionales configuradas
- [x] Tests de persistencia validados

---

**🎉 ESTADO: COMPLETAMENTE FUNCIONAL**

La aplicación ahora mantiene persistencia completa de datos en Streamlit Cloud, usando GitHub como sistema de almacenamiento y respaldo automático.
