# DashGen: imagem unica (frontend compilado + backend Flask servido por gunicorn).
# Estagio 1: compila o frontend React.
FROM node:20-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Estagio 2: runtime Python.
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install -r backend/requirements.txt
COPY backend/ backend/
COPY --from=frontend /app/frontend/dist frontend/dist
RUN useradd --create-home dashgen && mkdir -p /app/backend/data/configs && chown -R dashgen /app/backend/data
USER dashgen
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD python -c "import os,urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:' + os.environ.get('PORT', '8000') + '/api/health', timeout=4).status == 200 else 1)"
# Um unico worker com threads: as sessoes ficam na memoria do processo (ver README).
# A porta vem de $PORT quando a hospedagem a define (Render, Koyeb etc.); localmente, 8000.
CMD ["sh", "-c", "exec gunicorn --chdir backend -b 0.0.0.0:${PORT:-8000} -w 1 --threads 8 --timeout 120 wsgi:app"]
