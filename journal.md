# Daily Progress Journal - MLOps Platform

Ce fichier sert de journal de bord pour tracer l'avancement quotidien du projet de stage.

---

### Jour 1 — 01/08/2026
**Résumé de la journée :**
- Prise de connaissance du sujet de stage (Plateforme MLOps pour déploiement IA).
- Étude préliminaire des technologies demandées (Docker, Kubernetes, MLflow, FastAPI).
- Ébauche de l'architecture globale du projet.

---

### Jour 2 — 02/08/2026
**Résumé de la journée :**
- Finalisation et amélioration du cahier des charges.
- Étude du cycle de vie d'un projet Machine Learning en environnement MLOps.
- Préparation de l'environnement de développement (VS Code, installation de Python, Git).

---

### Jour 3 — 03/08/2026
**Résumé de la journée :**
- Choix du dataset "Iris" comme modèle *baseline* pour construire l'infrastructure MLOps sans complexité métier initiale.
- Mise en place de l'environnement virtuel (`venv`) et du fichier `requirements.txt`.
- Développement du script d'entraînement ML (`src/train.py`).
- Intégration de **MLflow** pour le tracking automatique des hyperparamètres, métriques et modèles.

---

### Jour 4 — 04/08/2026
**Résumé de la journée :**
- Étude de FastAPI pour la création du backend.
- Développement de l'API d'inférence (`src/serve.py`) connectée directement au registre MLflow.
- Tests locaux de l'API via l'interface Swagger UI (`/docs`) et validation des prédictions en temps réel.
- Création du premier `README.md` avec la roadmap.

---

### Jour 5 — 05/08/2026
**Résumé de la journée :**
- **Dockerisation** : Création d'un `Dockerfile` multi-stage pour empaqueter l'API de manière légère et sécurisée (utilisateur non-root).
- Création d'un `Makefile` pour automatiser les commandes du projet (`make train`, `make serve`, `make docker-build`).
- Intégration de la librairie Prometheus Instrumentator dans l'API en prévision du monitoring.

---

### Jour 6 (Aujourd'hui) — 06/08/2026
**Résumé de la journée :**
- **Orchestration Kubernetes** : Rédaction des manifestes YAML (`deployment.yaml`, `service.yaml`, `configmap.yaml`, `hpa.yaml`).
- Configuration de l'auto-scaling (HPA) pour garantir la scalabilité de l'API.
- Restructuration du projet pour préparer la suite (création des dossiers `data/raw`, `data/processed`, `notebooks`, `tests`).
- Ajout des routes stubs (`/extract`, `/classify`, `/ask`) dans FastAPI pour s'aligner parfaitement avec les besoins de la Phase 7.
- Validation des Semaines 1 et 2 du cahier des charges.

---

**Prochaine étape :**
- Remplacer le modèle baseline (Iris) par les modèles IA métiers (NLP : Extraction Intelligente, Classification de documents, Système RAG).

---

### Jour 7 — 07/08/2026
**Résumé de la journée :**
- **Architecture NLP** : Conception de l'architecture pour le système RAG (Retrieval-Augmented Generation).
- **Problème d'API Google** : Rencontre d'une erreur d'authentification (`401 UNAUTHENTICATED`) avec les clés OAuth/Gemini.
- **Pivot vers du 100% Local** : Migration de l'architecture vers une solution locale pour garantir la résilience et l'indépendance de la plateforme.
- **Ingestion RAG** : Développement du pipeline d'ingestion RAG (`src/train_rag.py`) en utilisant `sentence-transformers` (all-MiniLM-L6-v2) pour les embeddings et FAISS pour l'indexation.
- **Moteur RAG** : Développement du moteur d'inférence RAG (`src/rag_engine.py`) utilisant le LLM local `phi3:mini` via **Ollama**.
- **Tests** : Création des tests unitaires et d'intégration (`tests/test_train.py`, `tests/test_api.py`, `tests/test_rag.py`).
- **Automatisation** : Mise à jour du `Makefile` et du `README.md` pour intégrer les commandes du système RAG.

---

**Prochaine étape :**
- Développer les fonctionnalités de classification de documents et d'extraction de données structurées.
- Intégrer la stack de Monitoring (Prometheus + Grafana).
