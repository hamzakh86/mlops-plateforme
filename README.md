# 🚀 Plateforme MLOps pour Déploiement IA

> Projet de Stage — **ITGate Group**
> Construction d'une plateforme complète d'entraînement, de suivi, de conteneurisation et de déploiement de modèles de Machine Learning.

---

## 🗺️ Roadmap du Projet

| Semaine | Thème | Statut |
|---|---|---|
| **Semaine 1** | Cadrage, environnement, MLflow, FastAPI, Docker, Kubernetes local | ✅ Terminé |
| **Semaine 2** | Cas IA métiers : RAG local, extraction intelligente, classification de documents | 🔄 En cours |
| Semaine 3 | Monitoring (Prometheus / Grafana), métriques applicatives, dashboard | 🔜 À venir |
| Semaine 4 | CI/CD, automatisation du build, tests et déploiement | 🔜 À venir |

### Avancement actuel

Aujourd'hui, **lundi 10/08/2026**, correspond au **Jour 6** du stage.

Le weekend du **08/08/2026** et du **09/08/2026** est compté comme une pause et n'est pas inclus dans les jours de travail.

Statut actuel du Jour 6 : **en cours**. Aucun travail technique n'a encore été réalisé aujourd'hui.

Objectif du Jour 6 :
- Commencer le développement réel des endpoints métiers `/extract` et `/classify`.
- Ajouter les tests unitaires et d'intégration associés.
- Préparer la transition vers le monitoring Prometheus / Grafana.

---

## 🏗️ Architecture du Projet

```
Platforme MLOps/
│
├── src/
│   ├── train.py          # Pipeline d'entraînement ML + MLflow Tracking
│   ├── train_rag.py      # Pipeline d'ingestion RAG + index FAISS
│   ├── rag_engine.py     # Moteur RAG local avec Ollama
│   ├── nlp_engine.py     # Classification et extraction de documents
│   └── serve.py          # API FastAPI : prédiction, RAG, extraction, classification
│
├── k8s/
│   ├── configmap.yaml    # Variables de configuration Kubernetes
│   ├── deployment.yaml   # Déploiement des pods de l'API
│   ├── service.yaml      # Exposition réseau de l'API (LoadBalancer)
│   └── hpa.yaml          # Auto-Scaling automatique (2 à 8 répliques)
│
├── tests/                # Tests unitaires et tests API
├── data/
│   ├── raw/              # Documents bruts pour le RAG
│   └── processed/        # Index FAISS généré
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
- Docker Desktop
- Kubernetes activé dans Docker Desktop

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
| IA / RAG | Ollama + FAISS | Modèle LLM local et Vector Store |
| Monitoring | Prometheus + Grafana | *(Semaine 3)* |

---

## 🤖 Semaine 2 — Système RAG (Retrieval-Augmented Generation)

La plateforme intègre un système de questions/réponses documentaire basé sur vos propres données, fonctionnant **100% en local** (aucune clé API requise).

### 1. Ingestion des documents (Création de l'index FAISS)
Placez vos documents `.txt` dans le dossier `data/raw/` puis lancez :
```powershell
make train-rag
# ou
python src/train_rag.py --run-name "RAG_Local_Ingestion"
```
Cela va découper les documents, calculer les embeddings (avec `sentence-transformers`) et sauvegarder l'index vectoriel dans MLflow.

### 2. Poser des questions via l'API
L'API intègre un endpoint `/ask` pour interroger vos documents (assurez-vous qu'Ollama est installé et le modèle `phi3:mini` téléchargé).
```bash
curl -X POST "http://127.0.0.1:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "Quels sont les horaires de travail de lentreprise ?"}'
```
L'API retournera une réponse générée par l'IA locale, ainsi que les sources (fichiers) utilisées pour générer cette réponse.

---

## 🧾 IA Métier — Extraction et Classification

La plateforme prépare également deux endpoints métiers pour traiter des documents texte :

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
  "duration_ms": 950.42
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
  "duration_ms": 870.15
}
```

---

## 👤 Auteur
Projet de stage réalisé à **ITGate Group**. www.itgate-group.com
