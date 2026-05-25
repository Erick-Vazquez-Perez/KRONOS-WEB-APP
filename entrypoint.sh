#!/bin/sh
set -e

echo "[ENTRYPOINT] Iniciando configuración..."

mkdir -p /app/.streamlit

if [ -n "$SQLITECLOUD_CONNECTION_STRING" ]; then
  cat > /app/.streamlit/secrets.toml << EOF
SQLITECLOUD_CONNECTION_STRING = "$SQLITECLOUD_CONNECTION_STRING"
AUTH_PEPPER = "$AUTH_PEPPER"
ADMIN_BOOTSTRAP_PASSWORD = "$ADMIN_BOOTSTRAP_PASSWORD"
KRONOS_ENV = "production"
EOF
  echo "[ENTRYPOINT] secrets.toml generado OK"
else
  echo "[ENTRYPOINT] ERROR: SQLITECLOUD_CONNECTION_STRING no definida"
  exit 1
fi

echo "[ENTRYPOINT] Iniciando Streamlit..."
exec streamlit run main.py \
  --server.port=${PORT:-8501} \
  --server.address=0.0.0.0 \
  --server.headless=true \
  --server.enableCORS=false \
  --server.enableXsrfProtection=false
