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
IMAGE_TAG   = dev
IMAGE_REGISTRY = ghcr.io/your-github-user
K8S_GHCR_PATCH = k8s/deployment-ghcr.local.yaml
PORT        = 8000
DB_URI      = sqlite:///mlflow.db
FRONTEND_DIR = frontend

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

.PHONY: register-model
register-model:  ## Entraîne et enregistre le modèle dans le MLflow Model Registry
	$(PYTHON) src/train.py --register --promote

.PHONY: notebook
notebook:  ## Démarre le notebook Jupyter de démonstration ITGate
	$(PYTHON) -m jupyter notebook notebooks/demo_itgate.ipynb

.PHONY: mlflow-ui
mlflow-ui:  ## Démarre l'interface web MLflow
	$(UVICORN) mlflow ui --backend-store-uri $(DB_URI)

# ── Semaine 2 : API & Docker ────────────────────────────────
.PHONY: serve
serve:  ## Démarre l'API d'inférence FastAPI en local
	$(UVICORN) src.serve:app --host 127.0.0.1 --port $(PORT) --reload

.PHONY: frontend-install
frontend-install:  ## Installe les dépendances React
	npm --prefix $(FRONTEND_DIR) install

.PHONY: frontend-dev
frontend-dev:  ## Démarre l'interface React en développement
	npm --prefix $(FRONTEND_DIR) run dev

.PHONY: frontend-build
frontend-build:  ## Compile l'interface React pour FastAPI/Docker
	npm --prefix $(FRONTEND_DIR) run build

.PHONY: docker-build
docker-build:  ## Construit l'image Docker de l'API
	docker build -t $(IMAGE_NAME):latest .

.PHONY: docker-build-versioned
docker-build-versioned:  ## Construit l'image Docker avec tags latest + IMAGE_TAG
	docker build -t $(IMAGE_NAME):latest -t $(IMAGE_NAME):$(IMAGE_TAG) --build-arg APP_VERSION=$(IMAGE_TAG) --build-arg VCS_REF=$(IMAGE_TAG) .

.PHONY: docker-tag-versioned
docker-tag-versioned:  ## Tag l'image locale pour un registry Docker
	docker tag $(IMAGE_NAME):$(IMAGE_TAG) $(IMAGE_REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)
	docker tag $(IMAGE_NAME):$(IMAGE_TAG) $(IMAGE_REGISTRY)/$(IMAGE_NAME):latest

.PHONY: docker-push-versioned
docker-push-versioned: docker-tag-versioned  ## Pousse l'image versionnée vers IMAGE_REGISTRY
	docker push $(IMAGE_REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)
	docker push $(IMAGE_REGISTRY)/$(IMAGE_NAME):latest

.PHONY: docker-smoke
docker-smoke:  ## Build puis vérifie l'image Docker via /health
	powershell -ExecutionPolicy Bypass -File scripts/docker_smoke_test.ps1 -ImageName $(IMAGE_NAME) -ImageTag smoke

.PHONY: docker-run
docker-run:  ## Lance un conteneur Docker de l'API
	docker run -p $(PORT):8000 --name ml-api $(IMAGE_NAME):latest

.PHONY: docker-stop
docker-stop:  ## Arrête et supprime le conteneur Docker
	docker stop ml-api ; docker rm ml-api

# ── Monitoring local ────────────────────────────────────────
.PHONY: monitoring-up
monitoring-up:  ## Lance API + Prometheus + Grafana avec Docker Compose
	docker compose -f docker-compose.monitoring.yml up --build -d

.PHONY: monitoring-down
monitoring-down:  ## Arrête la stack de monitoring locale
	docker compose -f docker-compose.monitoring.yml down

.PHONY: monitoring-logs
monitoring-logs:  ## Affiche les logs de la stack de monitoring
	docker compose -f docker-compose.monitoring.yml logs -f

.PHONY: monitoring-status
monitoring-status:  ## Affiche l'état des services de monitoring
	docker compose -f docker-compose.monitoring.yml ps

.PHONY: demo-traffic
demo-traffic:  ## Génère du trafic API pour alimenter Prometheus/Grafana
	$(PYTHON) scripts/generate_demo_traffic.py --rounds 5 --delay 1

.PHONY: demo-traffic-lite
demo-traffic-lite:  ## Génère du trafic sans appels LLM (/health + /predict)
	$(PYTHON) scripts/generate_demo_traffic.py --rounds 5 --delay 1 --skip-llm

.PHONY: smoke-api
smoke-api:  ## Vérifie rapidement les endpoints principaux de l'API
	$(PYTHON) scripts/smoke_api.py

.PHONY: smoke-api-lite
smoke-api-lite:  ## Vérifie l'API sans appeler Groq (/health + /predict)
	$(PYTHON) scripts/smoke_api.py --skip-llm

# ── Kubernetes ──────────────────────────────────────────────
.PHONY: k8s-deploy
k8s-deploy:  ## Déploie tous les manifestes Kubernetes
	kubectl apply -f k8s/configmap.yaml
	kubectl apply -f k8s/deployment.yaml
	kubectl apply -f k8s/service.yaml
	kubectl apply -f k8s/hpa.yaml

.PHONY: k8s-deploy-ghcr
k8s-deploy-ghcr: k8s-render-ghcr-patch k8s-deploy  ## Applique le patch Kubernetes pour utiliser une image GHCR
	kubectl patch deployment ml-inference-deployment --patch-file $(K8S_GHCR_PATCH)

.PHONY: k8s-render-ghcr-patch
k8s-render-ghcr-patch:  ## Génère le patch Kubernetes GHCR local depuis IMAGE_REGISTRY et IMAGE_TAG
	$(PYTHON) scripts/render_k8s_ghcr_patch.py --registry $(IMAGE_REGISTRY) --tag $(IMAGE_TAG) --output $(K8S_GHCR_PATCH)

.PHONY: k8s-create-groq-secret
k8s-create-groq-secret:  ## Crée le Secret Kubernetes Groq depuis la variable GROQ_API_KEY du shell
	kubectl create secret generic groq-api-secret --from-literal=GROQ_API_KEY="$(GROQ_API_KEY)" --dry-run=client -o yaml | kubectl apply -f -

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

.PHONY: validate-artifacts
validate-artifacts:  ## Valide les artefacts de déploiement, monitoring et démonstration
	venv/Scripts/pytest tests/test_project_artifacts.py -v

.PHONY: ci-local
ci-local:  ## Lance localement les validations principales de la CI
	npm run build --prefix $(FRONTEND_DIR)
	venv/Scripts/pytest tests/ -v
	docker build -t $(IMAGE_NAME):ci --build-arg APP_VERSION=ci --build-arg VCS_REF=local-ci .

# ── Utilitaires ─────────────────────────────────────────────
.PHONY: help
help:  ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
