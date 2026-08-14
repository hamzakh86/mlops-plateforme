# 🚀 Plateforme MLOps — ITGate Group (V3 Production Ready & Model Registry)

Plateforme MLOps de bout en bout développée dans le cadre du projet de stage **ITGate Group** (Août 2026). Elle intègre la prévision du Chiffre d'Affaires par Séries Temporelles Multi-variées, l'inférence en temps réel, un moteur RAG (IA générative sur documents), la détection de Data Drift, la gestion de cycle de vie via **MLflow Model Registry (Stage Production)**, un Notebook de soutenance, la sécurité JWT, l'observabilité Prometheus/Grafana et le déploiement GitOps (ArgoCD / Kubernetes).

---

## 🌟 Nouvelles Fonctionnalités V3.1 (Mise en Production)
- 🏛️ **MLflow Model Registry (Production Stage)** : Gestion du cycle de vie du modèle (`ITGate_Revenue_Model`). Le serveur d'inférence charge en priorité le modèle promu en `Production`, avec fallback automatique.
- 📓 **Notebook Jupyter de Soutenance (`notebooks/demo_itgate.ipynb`)** : Analyse E2E avec graphiques de série temporelle, comparaison CA Réel vs Prédictions, Feature Importance et simulation de Data Drift.
- 🩺 **Probes Kubernetes Séparées** : Endpoints dédiés `/health/live` (Liveness) et `/health/ready` (Readiness) pour une orchestration Kubernetes sans faux positifs.
- ℹ️ **Métadonnées Modèle (`GET /model/info`)** : Exposition des métadonnées du modèle actif en production.
- 🔁 **CI/CD Alignée** : Pipeline GitHub Actions aligné sur l'expérience `ITGate_Revenue_Forecast`.

---

## 🌟 Nouvelles Fonctionnalités V3 (Jour 11)
- 📈 **Prévision du CA ITGate (Time Series Multi-varié)** : Modèle `RandomForestRegressor` entraîné sur les variables métier (ingénieurs, projets, contrats, lags temporels). Dataset dédié : `data/raw/itgate_revenue_multivariate.csv`.
- 🔬 **Détection de Data Drift** : Module `src/drift.py` calculant la dérive statistique (Z-score) par rapport au profil de référence d'entraînement. Métrique Prometheus `mlops_data_drift_score` exposée sur `/metrics`. Endpoint dédié : `GET /drift`.
- 📊 **Interface Web Avancée** : Graphique Séries Temporelles (SVG interactif) dans le Dashboard React + Widget Data Drift en temps réel + Formulaire multi-varié (6 paramètres métier ITGate).

---

## 🌟 Fonctionnalités V2 (Jours 9-10)
- 🔐 **Sécurité JWT** : Authentification par jeton OAuth2/JWT. Identifiants par défaut configurables via `.env`.
- 🗄️ **Base de Données & Historique** : Persistance SQLite + SQLAlchemy pour l'historique complet des requêtes API.
- 🎨 **Branding ITGate & UI Glassmorphism** : Interface React modernisée avec le logo officiel ITGate Group, fond animé et flux de déconnexion.
- 📊 **Évaluation RAG (Ragas)** : Script d'évaluation automatique de la fidélité et pertinence des réponses IA (`make evaluate-rag`).
- 🔄 **GitOps ArgoCD** : Manifeste Kubernetes automatisé (`k8s/argocd/application.yaml`).

---

## 🛠️ Installation et Configuration

### Prérequis
- Python **3.11+**
- Node.js **22+** et npm (pour l'interface React)
- Git
- Docker Desktop
- Kubernetes activé dans Docker Desktop
- Une clé API **Groq** gratuite (voir section RAG ci-dessous)

### 1. Cloner le dépôt
```powershell
git clone https://github.com/hamzakh86/mlops-plateforme.git
cd "mlops-plateforme"
```

### 2. Créer et activer l'environnement virtuel Python
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Installer les dépendances
```powershell
pip install -r requirements.txt
```

### 4. Configurer les variables d'environnement
```powershell
copy .env.example .env
# Éditez .env et renseignez votre GROQ_API_KEY (voir console.groq.com)
```

---

## 🧠 Semaine 1 — Entraînement & MLflow Tracking

### Lancer un entraînement
```powershell
# Avec les paramètres par défaut (100 arbres)
python src/train.py

# Avec des hyperparamètres personnalisés
python src/train.py --n_estimators 200 --max_depth 5 --run_name "RF_n200_d5"
```

**Arguments disponibles :**

| Argument | Type | Défaut | Description |
|---|---|---|---|
| `--n_estimators` | int | 100 | Nombre d'arbres dans la forêt |
| `--max_depth` | int | None | Profondeur maximale de l'arbre |
| `--run_name` | str | "RandomForest_Iris" | Nom du Run dans MLflow |

### Visualiser les résultats (MLflow UI)
```powershell
mlflow ui --backend-store-uri sqlite:///mlflow.db
```
Ouvrez **http://127.0.0.1:5000** dans votre navigateur.

---

## 🐋 Semaine 2 — API, Docker & Kubernetes

### Démarrer l'API d'inférence en local
```powershell
uvicorn src.serve:app --host 127.0.0.1 --port 8000 --reload
```
- **Interface web de pilotage** → **http://127.0.0.1:8000/**
- **Swagger UI** (documentation interactive) → **http://127.0.0.1:8000/docs**
- **Health check** → **http://127.0.0.1:8000/health**

### Interface web de pilotage

La plateforme inclut une interface web React complète. En développement, lancez l'API puis le frontend :

```powershell
uvicorn src.serve:app --host 127.0.0.1 --port 8000 --reload
npm install --prefix frontend
npm run dev --prefix frontend
```

Ouvrez **http://127.0.0.1:5173**.

Pour servir l'interface directement par FastAPI sur **http://127.0.0.1:8000/** :

```powershell
npm run build --prefix frontend
uvicorn src.serve:app --host 127.0.0.1 --port 8000 --reload
```

L'interface permet de :

- visualiser l'état de l'API, du modèle MLflow et du moteur RAG ;
- naviguer entre Dashboard, Inférence ML, IA documents, Observabilité et Déploiement ;
- tester une prédiction Iris via `/predict` ;
- poser une question documentaire via `/ask` ;
- tester l'extraction `/extract` et la classification `/classify` ;
- suivre l'activité récente des appels API ;
- ouvrir rapidement Swagger, MLflow, Prometheus et Grafana.

### Exemple de requête de prédiction
```bash
curl -X POST "http://127.0.0.1:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"data": [{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}]}'
```

**Réponse attendue :**
```json
{
  "predictions": ["setosa"],
  "model_run_id": "dbbbd02ee924...",
  "duration_ms": 1.24
}
```

### Construire et exécuter avec Docker
```powershell
# Construire l'image (multi-stage build)
docker build -t ml-inference-api:latest .

# Construire une image versionnée localement
make docker-build-versioned IMAGE_TAG=v0.1.0

# Alternative PowerShell si `make` n'est pas installé : utilisez directement `docker build`.

# Publier une image versionnée vers un registry Docker
make docker-push-versioned IMAGE_TAG=v0.1.0 IMAGE_REGISTRY=ghcr.io/<votre-utilisateur>

# Lancer un conteneur
docker run -p 8000:8000 --name ml-api ml-inference-api:latest

# Vérifier que l'API répond
curl http://localhost:8000/health
```

Smoke test Docker complet sous PowerShell (build, run temporaire, vérification `/health`, nettoyage) :

```powershell
.\scripts\docker_smoke_test.ps1 -ImageTag smoke
```

### Déployer sur Kubernetes (local)
```powershell
# Créer le secret Groq si les endpoints IA doivent fonctionner dans Kubernetes
$env:GROQ_API_KEY="<votre-cle-groq>"
make k8s-create-groq-secret

# Appliquer tous les manifestes dans l'ordre
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml

# Vérifier l'état du déploiement
kubectl get pods,svc,hpa -l app=ml-inference
```

Le dossier `k8s/` contient un `README.md` dédié avec le détail des ressources, la gestion du Secret Groq et les annotations Prometheus.

Pour utiliser une image publiée dans GitHub Container Registry, adaptez `k8s/deployment-ghcr.yaml` avec votre owner/repo/tag puis lancez :

```powershell
make k8s-deploy-ghcr IMAGE_REGISTRY=ghcr.io/<owner>/<repo> IMAGE_TAG=<tag>
```

Sur Windows sans `make`, utilisez le script PowerShell natif :

```powershell
.\scripts\k8s_deploy_ghcr.ps1 -ImageRegistry ghcr.io/owner/repo -ImageTag tag
```

---

## 📦 Stack Technologique

| Couche | Technologie | Rôle |
|---|---|---|
| Machine Learning | Scikit-Learn | Création et évaluation du modèle |
| Tracking | MLflow | Historisation des expériences |
| API | FastAPI + Uvicorn | Serveur d'inférence web |
| Conteneurisation | Docker | Empaquetage de l'application |
| Orchestration | Kubernetes | Déploiement, scaling, résilience |
| IA / RAG | Groq (cloud) + FAISS | LLM rapide (API gratuite) et Vector Store local |
| Monitoring | Prometheus + Grafana | Métriques HTTP + métriques métier IA |

---

## 🤖 Semaine 2 — Système RAG (Retrieval-Augmented Generation)

La plateforme intègre un système de questions/réponses documentaire basé sur vos propres données. Les **embeddings et l'index vectoriel FAISS restent 100% locaux** ; la génération de réponses est effectuée via l'API cloud **Groq** (tier gratuit), choisie après tests de performance — l'alternative locale (Ollama) s'est avérée trop lente sur un poste de développement sans GPU dédié.

> ⚠️ Nécessite une clé API Groq gratuite. Créez un compte sur [console.groq.com](https://console.groq.com) et renseignez `GROQ_API_KEY` dans votre `.env` (voir `.env.example`).

### 1. Ingestion des documents (Création de l'index FAISS)
Placez vos documents `.txt` dans le dossier `data/raw/` puis lancez :
```powershell
make train-rag
# ou
python src/train_rag.py --run-name "RAG_Local_Ingestion"
```
Cela va découper les documents, calculer les embeddings localement (avec `sentence-transformers`) et sauvegarder l'index vectoriel dans MLflow.

Le corpus d'exemple contient maintenant plusieurs documents internes :
- `data/raw/itgate_company_document.txt`
- `data/raw/mlops_platform_architecture.txt`
- `data/raw/security_and_operations_policy.txt`

### 2. Poser des questions via l'API
L'API intègre un endpoint `/ask` pour interroger vos documents (assurez-vous que `GROQ_API_KEY` est configuré dans votre `.env`).
```bash
curl -X POST "http://127.0.0.1:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "Quels sont les horaires de travail de lentreprise ?"}'
```
L'API retournera une réponse générée par Groq, ainsi que les sources (fichiers) utilisées pour générer cette réponse.

Si Groq est indisponible ou si le quota API est dépassé, le RAG applique un fallback : la recherche FAISS locale continue, les sources pertinentes sont retournées, et le champ `fallback` indique que la génération LLM n'a pas pu être utilisée.

---

## 🧾 IA Métier — Extraction et Classification

La plateforme intègre deux endpoints métiers pour traiter des documents texte, tous deux propulsés par l'API Groq :

| Endpoint | Rôle |
|---|---|
| `POST /extract` | Extraire des informations structurées d'un document |
| `POST /classify` | Classifier un document parmi des catégories données |

### Exemple : extraction intelligente

```bash
curl -X POST "http://127.0.0.1:8000/extract" \
  -H "Content-Type: application/json" \
  -d '{"text": "Facture ITGate Group du 10/08/2026. Montant total: 1250.50 TND."}'
```

**Réponse attendue :**
```json
{
  "extracted_data": {
    "montant_total": 1250.5,
    "date": "2026-08-10",
    "fournisseur": "ITGate Group"
  },
  "duration_ms": 261.13
}
```

### Exemple : classification de document

```bash
curl -X POST "http://127.0.0.1:8000/classify" \
  -H "Content-Type: application/json" \
  -d '{"text": "Facture ITGate Group du 10/08/2026. Montant total: 1250.50 TND.", "categories": ["Facture", "CV", "Contrat", "Rapport"]}'
```

**Réponse attendue :**
```json
{
  "category": "Facture",
  "duration_ms": 146.43
}
```

---

## 📈 Monitoring Prometheus

L'API expose les métriques Prometheus sur :

```text
http://127.0.0.1:8000/metrics
```

En plus des métriques HTTP générées automatiquement par `prometheus-fastapi-instrumentator`, la plateforme expose des métriques métier pour les fonctionnalités IA :

| Métrique | Rôle |
|---|---|
| `mlops_llm_requests_total` | Nombre d'appels IA par endpoint et statut (`success`, `fallback`, `error`) |
| `mlops_llm_fallbacks_total` | Nombre de fallbacks déclenchés après erreur LLM |
| `mlops_llm_request_duration_seconds` | Latence des endpoints IA |
| `mlops_rag_retrieved_documents` | Nombre de documents récupérés par FAISS pour une requête RAG |

Ces métriques préparent l'intégration Grafana : latence par endpoint, taux de fallback Groq et activité du moteur RAG.

### Stack locale Prometheus + Grafana

Une configuration Docker Compose dédiée permet de lancer l'API, Prometheus et Grafana :

```powershell
make monitoring-up
# ou
docker compose -f docker-compose.monitoring.yml up --build -d
```

Services exposés :

| Service | URL | Usage |
|---|---|---|
| API FastAPI | http://127.0.0.1:8000/docs | Tester les endpoints |
| Prometheus | http://127.0.0.1:9090 | Vérifier les targets et requêter les métriques |
| Grafana | http://127.0.0.1:3000 | Visualiser le dashboard |

Identifiants Grafana par défaut :

```text
admin / admin
```

Le dashboard `MLOps Platform Monitoring` est provisionné automatiquement depuis `monitoring/grafana/dashboards/mlops-platform.json`.

Commandes utiles :

```powershell
make monitoring-status
make monitoring-logs
make monitoring-down
```

### Générer du trafic de démonstration

Après le démarrage de l'API, vous pouvez générer quelques requêtes pour alimenter Prometheus et Grafana :

```powershell
make demo-traffic
```

Sans appeler Groq :

```powershell
make demo-traffic-lite
```

Une note d'architecture courte est disponible dans `docs/architecture-monitoring-fallback.md`.

---

## 🧪 Démonstration et Smoke Tests

Des payloads prêts à l'emploi sont disponibles dans `examples/`.

Vérifier rapidement l'API démarrée :

```powershell
make smoke-api
```

Sans appels Groq :

```powershell
make smoke-api-lite
```

Le déroulé complet de démonstration est documenté dans `docs/demo-guide.md`.

Pour une démo Windows sans `make`, utilisez :

```text
docs/windows-demo-checklist.md
```

---

## 🔁 CI/CD

Le dépôt contient une base GitHub Actions dans `.github/workflows/ci.yml`.

À chaque push sur `main`/`master` et à chaque pull request, la CI :

- installe les dépendances Python ;
- valide les artefacts de déploiement, monitoring et démonstration ;
- lance les tests unitaires et d'intégration ;
- prépare un modèle MLflow minimal pour le build ;
- vérifie que l'image Docker de l'API se construit correctement avec les tags `ci` et SHA court du commit ;
- ajoute des métadonnées OCI à l'image (`version`, `revision`, `created`).
- publie l'image vers GitHub Container Registry sur les pushes `main`/`master`.

Validation locale équivalente :

```powershell
make ci-local
```

Valider uniquement les artefacts de déploiement, monitoring et démonstration :

```powershell
make validate-artifacts
```

Vérifier localement l'image Docker si Docker Desktop est démarré :

```powershell
.\scripts\docker_smoke_test.ps1 -ImageTag smoke
```

---

## 👤 Auteur
Projet de stage réalisé à **ITGate Group**. www.itgate-group.com
