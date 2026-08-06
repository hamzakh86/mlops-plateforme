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

# ─────────────────────────────────────────────────────────────────
# Stage 2 : Runtime — image finale légère (sans outils de build)
# ─────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Métadonnées de l'image
LABEL maintainer="Plateforme MLOps - Stage ITGate"
LABEL version="2.0.0"

# Bonnes pratiques de sécurité : ne pas exécuter en tant que root
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

WORKDIR /app

# Copier les packages installés depuis le stage builder
COPY --from=builder /install /usr/local

# Copier le code source
COPY src/ ./src/

# Copier les artefacts MLflow nécessaires au chargement du modèle
COPY mlflow.db .
COPY mlruns/ ./mlruns/

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
