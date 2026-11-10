#!/usr/bin/env bash
# Sobe o DashGen: instala dependencias, compila o frontend e inicia o servidor.
# Uso: ./run.sh    (abrir http://localhost:5000)
set -e
cd "$(dirname "$0")"

echo ">> Backend: instalando dependencias Python..."
pip install -r backend/requirements-dev.txt

echo ">> Frontend: instalando e compilando..."
( cd frontend && npm install && npm run build )

echo ">> Iniciando servidor em http://localhost:5000 (Ctrl+C para parar)"
cd backend && flask --app app:create_app run --port 5000
