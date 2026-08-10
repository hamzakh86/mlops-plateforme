---

## 🛠️ Installation et Configuration

### Prérequis
- Python **3.11+**
- Git
- Docker Desktop
- Kubernetes activé dans Docker Desktop
- Une clé API **Groq** gratuite (voir section RAG ci-dessous)

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
| IA / RAG | Groq (cloud) + FAISS | LLM rapide (API gratuite) et Vector Store local |
| Monitoring | Prometheus + Grafana | *(Semaine 3)* |

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

### 2. Poser des questions via l'API
L'API intègre un endpoint `/ask` pour interroger vos documents (assurez-vous que `GROQ_API_KEY` est configuré dans votre `.env`).
```bash
curl -X POST "http://127.0.0.1:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "Quels sont les horaires de travail de lentreprise ?"}'
```
L'API retournera une réponse générée par Groq, ainsi que les sources (fichiers) utilisées pour générer cette réponse.

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

## 👤 Auteur
Projet de stage réalisé à **ITGate Group**. www.itgate-group.com