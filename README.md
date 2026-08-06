# 🚀 Plateforme MLOps pour Déploiement IA

> Projet de Stage — **ITGate Group**
> Construction d'une plateforme complète d'entraînement, de suivi, de conteneurisation et de déploiement de modèles de Machine Learning.

---

## 🗺️ Roadmap du Projet

| Semaine | Thème | Statut |
|---|---|---|
| **Semaine 1** | Cadrage, environnement, MLflow, premier entraînement | ✅ Terminé |
| **Semaine 2** | Docker, Kubernetes local, API d'inférence FastAPI | ✅ Terminé |
| Semaine 3 | Monitoring (Prometheus / Grafana), CI/CD | 🔜 À venir |
| Semaine 4 | Système RAG, Extraction intelligente, API IA avancée | 🔜 À venir |

---

## 🏗️ Architecture du Projet

```
Platforme MLOps/
│
├── src/
│   ├── train.py          # Pipeline d'entraînement ML + MLflow Tracking
│   └── serve.py          # API d'inférence FastAPI (Serveur de prédictions)
│
├── k8s/
│   ├── configmap.yaml    # Variables de configuration Kubernetes
│   ├── deployment.yaml   # Déploiement des pods de l'API
│   ├── service.yaml      # Exposition réseau de l'API (LoadBalancer)
│   └── hpa.yaml          # Auto-Scaling automatique (2 à 8 répliques)
│
├── Dockerfile            # Recette de construction de l'image Docker (multi-stage)
├── .dockerignore         # Fichiers exclus de l'image Docker
├── .env.example          # Modèle de configuration des variables d'environnement
├── Makefile              # Raccourcis de commandes (train, serve, docker, k8s)
├── requirements.txt      # Dépendances Python
└── README.md             # Ce fichier
```

---

## 🛠️ Installation et Configuration

### Prérequis
- Python **3.11+**
- Git
- Docker Desktop (pour la Semaine 2)
- Kubernetes activé dans Docker Desktop (pour la Semaine 2)

### 1. Cloner le dépôt
```powershell
git clone <url-de-votre-repo>
cd "Platforme MLOps"
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

### 4. Configurer les variables d'environnement (optionnel)
```powershell
copy .env.example .env
# Éditez .env selon vos besoins
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
- **Swagger UI** (documentation interactive) → **http://127.0.0.1:8000/docs**
- **Health check** → **http://127.0.0.1:8000/health**

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

# Lancer un conteneur
docker run -p 8000:8000 --name ml-api ml-inference-api:latest

# Vérifier que l'API répond
curl http://localhost:8000/health
```

### Déployer sur Kubernetes (local)
```powershell
# Appliquer tous les manifestes dans l'ordre
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml

# Vérifier l'état du déploiement
kubectl get pods,svc,hpa -l app=ml-inference
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
| Monitoring | Prometheus + Grafana | *(Semaine 3)* |

---

## 👤 Auteur
Projet de stage réalisé à **ITGate Group**. www.itgate-group.com
