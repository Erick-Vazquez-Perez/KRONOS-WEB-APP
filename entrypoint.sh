#!/bin/sh
# Genera secrets.toml en runtime a partir de variables de entorno de Railway.
# El archivo solo existe dentro del contenedor — nunca se versiona.
mkdir -p /app/.streamlit

if [ -n "$SQLITECLOUD_CONNECTION_STRING" ]; then
  cat > /app/.streamlit/secrets.toml << EOF
SQLITECLOUD_CONNECTION_STRING = "$SQLITECLOUD_CONNECTION_STRING"
EOF
  echo "[ENTRYPOINT] secrets.toml generado correctamente"
else
  echo "[ENTRYPOINT] ADVERTENCIA: SQLITECLOUD_CONNECTION_STRING no definida"
fi

exec streamlit run main.py \
  --server.port=8501 \
  --server.address=0.0.0.0 \
  --server.headless=true \
  --server.enableCORS=false \
  --server.enableXsrfProtection=false
