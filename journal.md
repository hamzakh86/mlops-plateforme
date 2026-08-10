# Daily Progress Journal - MLOps Platform

Ce fichier sert de journal de bord pour tracer l'avancement quotidien du projet de stage.

---

### Jour 1 — 03/08/2026
**Résumé de la journée :**
- Prise de connaissance du sujet de stage (Plateforme MLOps pour déploiement IA).
- Étude préliminaire des technologies demandées (Docker, Kubernetes, MLflow, FastAPI).
- Ébauche de l'architecture globale du projet.

---

### Jour 2 — 04/08/2026
**Résumé de la journée :**
- Finalisation et amélioration du cahier des charges.
- Étude du cycle de vie d'un projet Machine Learning en environnement MLOps.
- Préparation de l'environnement de développement (VS Code, installation de Python, Git).

---

### Jour 3 — 05/08/2026
**Résumé de la journée :**
- Choix du dataset "Iris" comme modèle *baseline* pour construire l'infrastructure MLOps sans complexité métier initiale.
- Mise en place de l'environnement virtuel (`venv`) et du fichier `requirements.txt`.
- Développement du script d'entraînement ML (`src/train.py`).
- Intégration de **MLflow** pour le tracking automatique des hyperparamètres, métriques et modèles.

---

### Jour 4 — 06/08/2026
**Résumé de la journée :**
- Étude de FastAPI pour la création du backend.
- Développement de l'API d'inférence (`src/serve.py`) connectée directement au registre MLflow.
- Tests locaux de l'API via l'interface Swagger UI (`/docs`) et validation des prédictions en temps réel.
- Création du premier `README.md` avec la roadmap.

---

### Jour 5 — 07/08/2026
**Résumé de la journée :**
- **Dockerisation** : Création d'un `Dockerfile` multi-stage pour empaqueter l'API de manière légère et sécurisée (utilisateur non-root).
- Création d'un `Makefile` pour automatiser les commandes du projet (`make train`, `make serve`, `make docker-build`).
- Intégration de la librairie Prometheus Instrumentator dans l'API en prévision du monitoring.
- **Orchestration Kubernetes** : Rédaction des manifestes YAML (`deployment.yaml`, `service.yaml`, `configmap.yaml`, `hpa.yaml`).
- Configuration de l'auto-scaling (HPA) pour garantir la scalabilité de l'API.
- Restructuration du projet pour préparer la suite (création des dossiers `data/raw`, `data/processed`, `notebooks`, `tests`).
- Ajout des routes stubs (`/extract`, `/classify`, `/ask`) dans FastAPI pour s'aligner avec les futurs besoins IA métier.
- **Architecture NLP** : Conception de l'architecture pour le système RAG (Retrieval-Augmented Generation).
- **Problème d'API Google** : Rencontre d'une erreur d'authentification (`401 UNAUTHENTICATED`) avec les clés OAuth/Gemini.
- **Pivot vers du 100% Local** : Migration de l'architecture vers une solution locale pour garantir la résilience et l'indépendance de la plateforme.
- **Ingestion RAG** : Développement du pipeline d'ingestion RAG (`src/train_rag.py`) en utilisant `sentence-transformers` (all-MiniLM-L6-v2) pour les embeddings et FAISS pour l'indexation.
- **Moteur RAG** : Développement du moteur d'inférence RAG (`src/rag_engine.py`) utilisant le LLM local `phi3:mini` via **Ollama**.
- **Tests** : Création des tests unitaires et d'intégration (`tests/test_train.py`, `tests/test_api.py`, `tests/test_rag.py`).
- **Automatisation** : Mise à jour du `Makefile` et du `README.md` pour intégrer les commandes du système RAG.

---

### Pause weekend — 08/08/2026 et 09/08/2026
**Résumé :**
- Pause de samedi et dimanche.
- Aucun jour de stage comptabilisé.

---

### Jour 6 — 10/08/2026
**Résumé de la journée :**
- **Développement des endpoints métiers** : implémentation complète de `/extract` (extraction structurée de données) et `/classify` (classification zero-shot), avec `src/nlp_engine.py` (`DocumentClassifier`, `DocumentExtractor`).
- **Validation renforcée** : ajout d'un schéma Pydantic (`ExtractionSchema`) pour fiabiliser le parsing JSON du LLM, et d'un garde-fou sur `/classify` rejetant toute catégorie hallucinée hors de la liste fournie par l'utilisateur.
- **Tests unitaires et d'intégration** : 19 tests créés (`tests/test_nlp_engine.py`, extension de `tests/test_api.py`), tous mockés pour rester compatibles CI/CD sans dépendance à un LLM réel. Résolution de deux problèmes de configuration pytest (`ModuleNotFoundError: src` via `pytest.ini` + `pythonpath`, puis erreur de fixture `client` non injectée).
- **Pivot d'architecture LLM — Ollama → Groq** : tests de latence sur le poste de développement (Intel i5-1035G1, sans GPU dédié) ont confirmé qu'Ollama/`phi3:mini` en CPU-only était trop lent pour un usage confortable en développement et en démo. Décision de migrer vers **Groq** (API cloud, tier gratuit, modèles Llama open-source), après une brève exploration de xAI Grok (écarté : pas de tier gratuit garanti selon la documentation officielle, framing peu adapté au budget d'un projet de stage).
  - Création de `src/llm_provider.py` : fabrique centralisée pour l'instanciation du LLM, utilisée par `rag_engine.py` et `nlp_engine.py`.
  - Mise à jour de `.env.example`, `.gitignore`, `README.md` et suppression des dépendances Ollama (`langchain-ollama` → `langchain-groq`).
  - **Impact sur l'architecture** : la plateforme n'est plus "100% locale" — la génération de réponses (RAG, extraction, classification) dépend désormais de l'API Groq. Les embeddings et l'index FAISS restent locaux. Ce compromis est documenté et assumé : latence/fiabilité en développement priorisées sur l'indépendance totale vis-à-vis du cloud.
- **Validation en conditions réelles (post-mocks)** : tests manuels des 3 endpoints Groq via l'API démarrée localement.
  - `/extract` → 261 ms, extraction exacte (montant, date, fournisseur).
  - `/classify` → 146 ms, catégorie correcte.
  - `/ask` (RAG complet) → réponse cohérente et sourcée.
  - Gain de latence confirmé face à Ollama/CPU : facteur ~5 à 10x.
- **Sécurité** : détection d'une clé API Google (Gemini, architecture abandonnée au Jour 5) laissée en clair dans un ancien `.env` — révocation recommandée par précaution. Une clé Groq a également été régénérée après exposition accidentelle en cours de développement. Vérification de l'historique Git (`git log --all --full-history -- .env`) à finaliser.

**Écart par rapport à l'objectif initial du Jour 6 :** l'objectif prévoyait de "commencer" le développement de `/extract` et `/classify`. Les deux endpoints sont en réalité terminés, testés (mocks + conditions réelles) et fonctionnels — l'avancement dépasse la planification initiale.

**Point à valider avec l'encadrant :** le pivot Ollama → Groq modifie la promesse d'indépendance "100% locale" du cahier des charges initial. Compromis à faire valider formellement.

---

**Objectifs du Jour 7 :**
- Étoffer le corpus de documents RAG (actuellement 1 document, 11 chunks) pour des tests plus représentatifs.
- Entamer la phase de monitoring (Prometheus + Grafana), prévue en Semaine 3.
- Réfléchir à une stratégie de fallback/gestion d'erreur en cas d'indisponibilité ou de quota dépassé sur l'API Groq.