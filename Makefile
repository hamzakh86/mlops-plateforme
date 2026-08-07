# ============================================================
#  Makefile — Plateforme MLOps (ITGate)
#  Raccourcis pour les commandes les plus utilisées du projet.
#  Usage: make <cible>   ex: make train   make serve   make docker-build
# ============================================================

# Variables
PYTHON      = venv/Scripts/python
PIP         = venv/Scripts/pip
UVICORN     = venv/Scripts/uvicorn
IMAGE_NAME  = ml-inference-api
PORT        = 8000
DB_URI      = sqlite:///mlflow.db

# ── Environnement ───────────────────────────────────────────
.PHONY: install
install:  ## Installe les dépendances Python dans le venv
	$(PIP) install -r requirements.txt

.PHONY: venv
venv:  ## Crée l'environnement virtuel Python
	python -m venv venv

# ── Semaine 1 : Entraînement & Tracking ────────────────────
.PHONY: train
train:  ## Lance le pipeline d'entraînement (paramètres par défaut)
	$(PYTHON) src/train.py

.PHONY: train-custom
train-custom:  ## Lance un entraînement avec des paramètres personnalisés
	$(PYTHON) src/train.py --n_estimators 200 --max_depth 5 --run_name "RF_n200_d5"

.PHONY: mlflow-ui
mlflow-ui:  ## Démarre l'interface web MLflow
	$(UVICORN) mlflow ui --backend-store-uri $(DB_URI)

# ── Semaine 2 : API & Docker ────────────────────────────────
.PHONY: serve
serve:  ## Démarre l'API d'inférence FastAPI en local
	$(UVICORN) src.serve:app --host 127.0.0.1 --port $(PORT) --reload

.PHONY: docker-build
docker-build:  ## Construit l'image Docker de l'API
	docker build -t $(IMAGE_NAME):latest .

.PHONY: docker-run
docker-run:  ## Lance un conteneur Docker de l'API
	docker run -p $(PORT):8000 --name ml-api $(IMAGE_NAME):latest

.PHONY: docker-stop
docker-stop:  ## Arrête et supprime le conteneur Docker
	docker stop ml-api ; docker rm ml-api

# ── Kubernetes ──────────────────────────────────────────────
.PHONY: k8s-deploy
k8s-deploy:  ## Déploie tous les manifestes Kubernetes
	kubectl apply -f k8s/configmap.yaml
	kubectl apply -f k8s/deployment.yaml
	kubectl apply -f k8s/service.yaml
	kubectl apply -f k8s/hpa.yaml

.PHONY: k8s-status
k8s-status:  ## Affiche l'état du déploiement Kubernetes
	kubectl get pods,svc,hpa -l app=ml-inference

.PHONY: k8s-delete
k8s-delete:  ## Supprime le déploiement Kubernetes
	kubectl delete -f k8s/

# ── RAG (Local) ─────────────────────────────────────────────
.PHONY: train-rag
train-rag:  ## Lance l'ingestion des documents pour le système RAG
	$(PYTHON) src/train_rag.py --run-name "RAG_Local_Ingestion"

# ── Tests & Qualité ─────────────────────────────────────────
.PHONY: test
test:  ## Lance tous les tests unitaires et d'intégration
	venv/Scripts/pytest tests/ -v

# ── Utilitaires ─────────────────────────────────────────────
.PHONY: help
help:  ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
