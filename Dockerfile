# ─────────────────────────────────────────────────────────────────
# Stage 1 : Builder — installe les dépendances Python
# L'idée du multi-stage build : séparer "l'atelier" du "livrable"
# pour avoir une image finale ultra-légère.
# ─────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# On installe d'abord les dépendances dans un dossier isolé (--prefix)
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ────────────────────────────────────────────────────────────────
# Stage 2 : Frontend — construit l'interface React
# ────────────────────────────────────────────────────────────────
FROM node:22-slim AS frontend-builder

WORKDIR /frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ────────────────────────────────────────────────────────────────
# Stage 3 : Runtime — image finale légère (sans outils de build)
# ────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Métadonnées de l'image, renseignées par la CI ou par Makefile
ARG APP_VERSION=dev
ARG VCS_REF=local
ARG BUILD_DATE=unknown

LABEL maintainer="Plateforme MLOps - Stage ITGate"
LABEL version="${APP_VERSION}"
LABEL org.opencontainers.image.title="MLOps Platform API"
LABEL org.opencontainers.image.description="FastAPI inference API with MLflow, RAG, Groq fallback and Prometheus metrics"
LABEL org.opencontainers.image.version="${APP_VERSION}"
LABEL org.opencontainers.image.revision="${VCS_REF}"
LABEL org.opencontainers.image.created="${BUILD_DATE}"

# Bonnes pratiques de sécurité : ne pas exécuter en tant que root
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

WORKDIR /app

# Copier les packages installés depuis le stage builder
COPY --from=builder /install /usr/local

# Copier le code source
COPY src/ ./src/
COPY --from=frontend-builder /frontend/dist ./frontend/dist

# Créer les répertoires pour les artefacts MLflow
RUN mkdir -p /app/mlruns && chown -R appuser:appgroup /app/mlruns

# Copier les artefacts MLflow si disponibles (optionnel pour CI)
COPY --chown=appuser:appgroup mlflow.db . 2>/dev/null || true
COPY --chown=appuser:appgroup mlruns/ ./mlruns/ 2>/dev/null || true

# Changer le propriétaire des fichiers
RUN chown -R appuser:appgroup /app

# Basculer vers l'utilisateur non-root
USER appuser

# Exposer le port de l'API
EXPOSE 8000

# Healthcheck natif Docker : vérifie que l'API répond bien toutes les 30s
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Point d'entrée : démarrer Uvicorn en mode production
CMD ["uvicorn", "src.serve:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
