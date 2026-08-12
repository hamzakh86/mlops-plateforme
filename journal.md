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

---

### Jour 7 — 11/08/2026
**Résumé de la journée :**
- **Élargissement du corpus RAG** : ajout de deux nouveaux documents internes dans `data/raw/` :
  - `mlops_platform_architecture.txt` : architecture de la plateforme, composants, stratégie de déploiement.
  - `security_and_operations_policy.txt` : monitoring, gestion d'incidents LLM, sécurité des secrets.
- **Réingestion RAG** : régénération de l'index FAISS avec le corpus élargi.
  - Corpus final : 3 documents.
  - Découpage final : 21 chunks.
  - Run MLflow : `a673d7f0c93747419640c4c44623a7ac`.
- **Correction de cohérence documentaire** : mise à jour des références techniques restantes après le pivot Ollama/Gemini vers **Groq + FAISS**.
- **Monitoring métier Prometheus** : ajout de `src/monitoring.py` avec des métriques dédiées :
  - `mlops_llm_requests_total` pour suivre les appels IA par endpoint et statut.
  - `mlops_llm_fallbacks_total` pour mesurer les indisponibilités/quota Groq.
  - `mlops_llm_request_duration_seconds` pour mesurer la latence des endpoints IA.
  - `mlops_rag_retrieved_documents` pour observer le nombre de documents récupérés par FAISS.
- **Fallback Groq** : implémentation d'une stratégie de dégradation contrôlée.
  - `/ask` conserve la recherche FAISS locale et retourne les sources pertinentes même si Groq échoue.
  - `/extract` retourne une structure stable avec champs `null` en cas d'erreur LLM.
  - `/classify` retourne `Erreur_Classification` en cas d'erreur LLM.
  - Les endpoints exposent désormais un champ `fallback` pour rendre l'état visible côté client.
- **Robustesse applicative** : initialisation lazy des chaînes LLM dans `DocumentClassifier` et `DocumentExtractor`, afin d'éviter qu'une clé Groq absente bloque l'import de l'application ou les tests.
- **Tests** :
  - Correction de la fixture FastAPI pour neutraliser explicitement le lifespan MLflow/RAG pendant les tests.
  - Correction du test RAG qui mockait encore `ChatOllama` au lieu du provider Groq centralisé.
  - Ajout d'un test de fallback RAG lorsque le LLM échoue.
  - Validation : `23 passed` sur les tests API/NLP/RAG, puis `4 passed` sur les tests du pipeline d'entraînement.
- **Correction Docker** : suppression d'un caractère parasite au début du `Dockerfile` qui pouvait casser le build.

**Résultat du Jour 7 :** la plateforme dispose maintenant d'un corpus RAG plus représentatif, d'une base de monitoring métier exploitable par Prometheus/Grafana, et d'une stratégie de fallback claire pour limiter l'impact d'une indisponibilité Groq.

**Objectifs proposés pour le Jour 8 :**
- Régénérer l'index RAG avec le corpus élargi (`make train-rag`) et valider quelques questions de démonstration.
- Ajouter une configuration Prometheus/Grafana locale (`monitoring/prometheus.yml`, dashboard Grafana JSON ou documentation de dashboard).
- Préparer une courte note pour l'encadrant sur le compromis Groq cloud vs indépendance locale.

---

### Jour 8 — 11/08/2026
**Résumé de la journée :**
- **Observabilité & Monitoring** : Ajout de la stack Docker Compose (`docker-compose.monitoring.yml`), configuration Prometheus (`monitoring/prometheus.yml`) et provisioning Grafana avec dashboard de supervision des métriques HTTP, latence et fallbacks.
- **Démonstration & CI/CD** : Création du script de trafic de démonstration (`scripts/generate_demo_traffic.py`), mise en place du workflow GitHub Actions (`.github/workflows/ci.yml`), versionnement des images Docker et publication sur GitHub Container Registry (`ghcr.io`).
- **Durcissement Kubernetes & Scripts Windows** : Sécurisation des clés via Secrets Kubernetes (`k8s/groq-api-secret`), scripts PowerShell pour Windows (`scripts/k8s_deploy_ghcr.ps1` et `scripts/docker_smoke_test.ps1`) et checklist de soutenance (`docs/windows-demo-checklist.md`).
- **Console Web React & Packaging Docker** : Développement de la console web en React (`frontend/`), intégration dans l'image Docker multi-stage (Node 22 + Python 3.11) et service des assets statiques via FastAPI.

**Résultat du Jour 8 :** La plateforme est dotée d'une observabilité Grafana/Prometheus complète, d'une console React professionnelle, d'une intégration CI/CD avec GHCR et de manifestes Kubernetes prêts pour la production.

---

### Jour 9 — 12/08/2026
**Résumé de la journée :**
- **Persistance & Base de données (SQLite + SQLAlchemy)** : Création de la couche d'accès aux données dans `src/database.py` et `src/models.py` (tables `User` et `ApiRequestLog`). Historisation de chaque appel API via la route `/history` et affichage persistant dans le dashboard React.
- **Sécurisation par Authentification JWT** : Implémentation du système d'authentification OAuth2 avec JSON Web Tokens (`src/auth.py`). Protection de tous les endpoints de prédiction/RAG/nlp avec dépendances de sécurité `Depends(get_current_user)`. Utilisation de `pbkdf2_sha256` pour le hachage sécurisé des mots de passe.
- **Branding ITGate & Redesign de l'Interface** :
  - Intégration du logo officiel **ITGate Group** (`logo.png`) dans le header de l'application et la page de connexion.
  - Refonte complète de la page de login avec un design *glassmorphism* haut de gamme (fond animé bleu/teal, carte semi-transparente avec flou, effets de survol et halo lumineux).
  - Ajout du bouton et du flux de **Déconnexion (Logout)** dans la barre latérale pour purger le token JWT et rediriger l'utilisateur.
- **Évaluation de la Qualité RAG (Ragas)** : Développement du script `scripts/evaluate_rag.py` permettant de calculer les métriques de fidélité et de pertinence des réponses du RAG via la bibliothèque `ragas`. Ajout de la commande `make evaluate-rag`.
- **GitOps & Continuous Deployment (ArgoCD)** : Rédaction du manifeste Kubernetes ArgoCD `k8s/argocd/application.yaml` afin de piloter le déploiement continu du cluster depuis le dépôt Git.
- **Observabilité & Monitoring** : Mise à jour de la configuration Prometheus (`monitoring/prometheus.yml`) avec le target `host.docker.internal:8000` pour scraper les métriques en environnement local et conteneurisé.

**Résultat :** La plateforme MLOps ITGate est désormais complète, hautement sécurisée (JWT + DB), dotée d'une identité visuelle professionnelle et prête pour la démonstration en réunion.
