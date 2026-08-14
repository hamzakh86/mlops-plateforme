# 🚀 Guide de Présentation — Plateforme MLOps ITGate Group (V3)
*Document de synthèse préparé pour la soutenance / réunion d'avancement avec l'encadrant.*

---

## 📑 Sommaire
1. [Qu'est-ce que le MLOps & Idée Générale du Projet](#1--quest-ce-que-le-mlops--idée-générale-du-projet)
2. [Architecture Globale & Stack Technologique](#2-️-architecture-globale--stack-technologique)
3. [Structure du Code & Rôle de Chaque Fichier/Dossier](#3--structure-du-code--rôle-de-chaque-dossier--fichier)
4. [Rôle Détaillé des Outils Clés](#4-️-rôle-détaillé-des-outils-clés)
5. [Logique de Fonctionnement de Bout en Bout (Workflows)](#5--logique-de-fonctionnement-de-bout-en-bout-workflows)
6. [Guide de Démonstration Pas-à-Pas pour la Réunion](#6--guide-de-démonstration-pas-à-pas-pour-la-réunion)

---

## 1. 🎯 Qu'est-ce que le MLOps & Idée Générale du Projet

### A. Définition du MLOps
Le terme **MLOps** (*Machine Learning Operations*) est la fusion du **Machine Learning** et des pratiques **DevOps**.
> **Définition clé à retenir :** C'est l'ensemble des méthodes, outils et pratiques d'ingénierie logicielle permettant de concevoir, tester, déployer, sécuriser, automatiser et surveiller des modèles de Machine Learning en production de manière reproductible et fiable.

### B. Problématiques résolues par le MLOps
- **Le syndrome du "Ça marche sur mon notebook" :** Un script d'entraînement isolé ne sait pas gérer la charge, l'authentification ni les pannes.
- **La dégradation silencieuse (*Data Drift*) :** En production, les données réelles évoluent avec le temps (ex: inflation, nouveaux profils de clients). Sans monitoring, un modèle délivre de mauvaises prédictions sans que personne ne s'en rende compte.
- **Le manque de traçabilité :** Difficulté à savoir quelle version de données ou quels hyperparamètres ont produit le modèle actuellement en production.
- **La complexité du déploiement :** Nécessité d'automatiser la mise en production sans interruption de service.

### C. Buts & Objectifs de notre plateforme ITGate Group
1. **Résoudre un cas d'usage métier réel ITGate :**
   - 📈 **Prévision du Chiffre d'Affaires (CA)** via Séries Temporelles Multi-variées (intégrant le nombre d'ingénieurs, les projets actifs et la valeur moyenne des contrats).
2. **Fournir des capacités d'IA Générative Documentaire :**
   - 🤖 **Moteur RAG (*Retrieval-Augmented Generation*)** pour interroger les documents internes et politiques de l'entreprise.
   - 🧾 **Traitement Intelligent de Documents** : Extraction automatique de données (factures, devis) et classification textuelle.
3. **Assurer une observabilité et une sécurité de niveau production :**
   - Détection en temps réel du **Data Drift** (Z-Score).
   - Authentification sécurisée par **JWT** et persistance de l'historique sous **SQLite/SQLAlchemy**.
   - Monitoring temps réel avec **Prometheus & Grafana**.
   - Déploiement moderne conteneurisé (**Docker**, **Kubernetes**, **ArgoCD**).

### D. Utilisateurs cibles (Personas)
- **Data Scientists / ML Engineers :** Expérimentent, entraînent et comparent les modèles sur MLflow.
- **DevOps / Ingénieurs Cloud :** Déploient, scalent et monitorent l'infrastructure (K8s, Docker, CI/CD).
- **Direction / Décisionnaires ITGate :** Visualisent les prévisions financières et l'état de l'activité sur le tableau de bord React.
- **Collaborateurs internes :** Interrogent la base de connaissances documentaire de l'entreprise.

---

## 2. 🏗️ Architecture Globale & Stack Technologique

### Schéma d'Architecture
```
                       +-----------------------------------+
                       |      UTILISATEUR / FRONTEND       |
                       |  React Dashboard (Port 5173/8000) |
                       +-----------------+-----------------+
                                         |
                                         | Authentification JWT (OAuth2)
                                         v
+-----------------------------------------------------------------------------------+
|                            API GATEWAY / FASTAPI (Port 8000)                      |
|  - Sécurité & Tokens JWT (auth.py)                                                |
|  - Persistance Historique SQLite / SQLAlchemy (models.py, database.py)           |
|  - Instrumentateur Prometheus & Métriques Métier (monitoring.py)                  |
+---------------------+-------------------+-------------------+---------------------+
                      |                   |                   |
        +-------------+     +-------------+     +-------------+
        |                   |                   |             |
        v                   v                   v             v
+---------------+   +---------------+   +---------------+   +-------------------+
| PREDICTION CA |   |  DATA DRIFT   |   |   RAG ENGINE  |   |    NLP ENGINE     |
| RandomForest  |   |  Z-Score Max  |   | FAISS (Local) |   | (Classification & |
|  Multi-varié  |   | Baseline JSON |   |  + Groq LLM   |   |    Extraction)    |
+-------+-------+   +---------------+   +-------+-------+   +---------+---------+
        |                                       |                     |
        | Modèle versionné                      | Chunks & Embeddings | LLM Cloud
        v                                       v                     v
+---------------+                       +---------------+     +-----------------+
| MLflow Server |                       |  data/raw/    |     | API Cloud Groq  |
|  (Port 5000)  |                       |  Corpus ITGate|     |  (Llama3 Fast)  |
+---------------+                       +---------------+     +-----------------+
        ^
        | Collecte des métriques (/metrics)
+-------+-------------------------------+
| OBSERVABILITÉ & INFRASTRUCTURE        |
| - Prometheus (9090) : Scrape métriques|
| - Grafana (3000) : Dashboard visuel   |
| - Docker & Kubernetes (K8s)           |
| - ArgoCD : Déploiement GitOps         |
+---------------------------------------+
```

---

## 3. 📁 Structure du Code & Rôle de Chaque Dossier / Fichier

```text
mlops-plateforme/
│
├── data/                               # Données du projet
│   ├── raw/                            # Données brutes (CSV de CA multi-varié, fichiers TXT ITGate)
│   ├── processed/                      # Données transformées/nettoyées
│   └── drift_baseline.json             # Profil statistique de référence (moyenne/écart-type d'entraînement)
│
├── src/                                # Code source backend (Cœur logique)
│   ├── __init__.py                     # Package Python
│   ├── train.py                        # Pipeline d'entraînement du modèle de CA (RandomForest + MLflow)
│   ├── train_rag.py                    # Pipeline d'indexation documentaire (Embeddings locaux + FAISS)
│   ├── serve.py                        # Serveur d'inférence FastAPI (endpoints /predict, /ask, /drift, etc.)
│   ├── drift.py                        # Détecteur statistique de Data Drift (calcul Z-score sur les requêtes)
│   ├── rag_engine.py                   # Moteur RAG : recherche vectorielle FAISS + génération Groq
│   ├── nlp_engine.py                   # Extraction structurée et Classification zero-shot
│   ├── llm_provider.py                 # Fabrique centralisée pour instancier le LLM Groq
│   ├── auth.py                         # Authentification OAuth2 + JWT (hachage mots de passe pbkdf2)
│   ├── database.py                     # Connexion SQLAlchemy à la base SQLite
│   ├── models.py                       # Modèles de base de données (User, ApiRequestLog)
│   └── monitoring.py                   # Définition des métriques Prometheus métier (drift, fallbacks, latence)
│
├── frontend/                           # Application Web React (Vite + Glassmorphism UI)
│   ├── src/                            # Composants React (Dashboard, Formulaires, Graphiques SVG)
│   ├── package.json                    # Dépendances Node.js du frontend
│   └── dist/                           # Build de production compilé (servi directement par FastAPI)
│
├── k8s/                                # Manifestes Kubernetes pour le déploiement
│   ├── deployment.yaml                 # Déploiement des pods FastAPI
│   ├── service.yaml                    # Exposition réseau interne/externe (LoadBalancer/NodePort)
│   ├── configmap.yaml                  # Variables d'environnement non sensibles
│   ├── hpa.yaml                        # Horizontal Pod Autoscaler (scaling automatique selon CPU)
│   └── argocd/application.yaml         # Définition de l'application GitOps ArgoCD
│
├── monitoring/                         # Configuration de la stack d'observabilité
│   ├── prometheus.yml                  # Configuration du scraper Prometheus (collecte sur /metrics)
│   └── grafana/dashboards/             # Dashboard JSON pré-configuré pour visualiser les métriques
│
├── .github/workflows/ci.yml            # Pipeline CI/CD GitHub Actions (tests auto, build Docker, push GHCR)
├── Dockerfile                          # Build multi-stage optimisé (Node.js pour React + Python pour l'API)
├── docker-compose.monitoring.yml       # Lancement simultané de l'API, Prometheus et Grafana
├── Makefile                            # Raccourcis de commandes CLI (make train, make serve, make monitoring-up)
├── requirements.txt                    # Dépendances Python du projet
└── .env                                # Clés secrètes et variables d'environnement (JWT secret, Groq Key)
```

---

## 4. ⚙️ Rôle Détaillé des Outils Clés

| Outil | Rôle précis dans la plateforme | Pourquoi on l'utilise ? |
|---|---|---|
| **MLflow** | **Expérimentation & Versionnement de Modèles** | Historise chaque entraînement ($R^2$, $MAE$, hyperparamètres), sauvegarde le modèle binaire (`model.pkl`) et permet de recharger la version exacte voulue en production. |
| **FastAPI / Swagger** | **Framework API REST & Documentation** | API ultra-rapide et asynchrone. **Swagger UI (`/docs`)** génère automatiquement une interface interactive pour tester tous les endpoints en direct. |
| **Docker** | **Conteneurisation Multi-Stage** | Isole le backend Python et le frontend React dans une image légère et portable. Élimine tout problème d'incompatibilité d'environnement. |
| **Kubernetes (K8s)** | **Orchestration de Conteneurs** | Gère la haute disponibilité : redémarrage automatique en cas de panne (*self-healing*), répartition de charge (*Service*) et mise à l'échelle automatique (*HPA*). |
| **ArgoCD (GitOps)** | **Déploiement Continu Déclaratif** | Synchronise automatiquement l'état du cluster Kubernetes avec les manifestes stockés dans le dépôt Git. |
| **Prometheus** | **Collecte de Métriques Temps Réel** | Scrape régulièrement l'endpoint `/metrics` de l'API pour mesurer le trafic, les temps de réponse, les erreurs et le score de **Data Drift**. |
| **Grafana** | **Tableau de Bord de Supervision** | Transforme les métriques brutes de Prometheus en graphiques visuels et lisibles (santé de l'API, charge, dérive statistique). |
| **Groq** | **Inférence LLM Cloud Ultra-Rapide** | Exécute des modèles LLM open-source (Llama 3) avec une latence exceptionnelle (~150ms) pour la synthèse RAG et l'extraction de données. |
| **GitHub Actions (CI/CD)** | **Intégration Continue** | Lance automatiquement les tests (`pytest`), valide les artefacts, construit l'image Docker et la publie sur le registre GitHub (`ghcr.io`) à chaque commit. |

---

## 5. 🔄 Logique de Fonctionnement de Bout en Bout (Workflows)

### Flux A : Prévision de Chiffre d'Affaires & Détection de Data Drift
1. **Entraînement (`train.py`)** :
   - Chargement du dataset financier `data/raw/itgate_revenue_multivariate.csv`.
   - Création des features temporelles de lag ($M-1, M-2, M-3$) et variables business (Ingénieurs, Projets, Contrats).
   - Entraînement d'un `RandomForestRegressor`, enregistrement du run dans **MLflow** et calcul de la baseline de référence sauvegardée dans `data/drift_baseline.json`.
2. **Inférence (`POST /predict`)** :
   - L'utilisateur transmet les paramètres du mois via l'API ou le formulaire React.
   - Le modèle calcule et retourne la prévision financière pour le mois suivant ($M+1$).
3. **Contrôle Qualité des Données (`drift.py`)** :
   - À chaque prédiction, le Z-score des données entrantes est calculé par rapport à la baseline d'entraînement.
   - Si un Z-score dépasse le seuil critique (ex: $> 3$), un statut **"Drift Détecté"** est levé.
   - La métrique Prometheus `mlops_data_drift_score` est mise à jour immédiatement.

### Flux B : Moteur Documentaire RAG & Fallback
1. **Indexation (`train_rag.py`)** :
   - Découpage des documents textuels internes (`data/raw/*.txt`) en segments (*chunks*).
   - Calcul des vecteurs d'embeddings via le modèle local `sentence-transformers` et création d'un index vectoriel **FAISS**.
2. **Question/Réponse (`POST /ask`)** :
   - L'utilisateur pose une question métier sur ITGate.
   - FAISS recherche localement les 3 extraits les plus pertinents.
   - Le LLM Groq rédige une réponse précise en citant ses sources.
   - **Mécanisme de Fallback :** Si la connexion internet ou Groq est indisponible, l'API ne plante pas : elle retourne directement les documents bruts trouvés localement par FAISS.

---

## 6. 🚀 Guide de Démonstration Pas-à-Pas pour la Réunion

Voici le plan idéal à dérouler devant votre encadrant :

```text
[1. Connexion & Sécurité]
  └── Montrer la page de Login Glassmorphism (Branding ITGate)
  └── Connexion avec admin / admin (Validation du JWT)

[2. Métier ITGate : Prévision du CA]
  └── Remplir les 6 paramètres (Ingénieurs, Projets, Contrats, Lags CA)
  └── Cliquer sur "Prédire le Chiffre d'Affaires"
  └── Montrer la prévision chiffrée et la courbe interactive SVG (pointillé vert M+1)

[3. Innovation MLOps : Démonstration du Data Drift en direct]
  └── Entrer une valeur anormale (ex: 500 ingénieurs au lieu de 40)
  └── Montrer le badge qui passe au rouge : "⚠️ Dérive détectée (Data Drift)"
  └── Expliquer que cela alerte l'équipe sur la nécessité de réentraîner le modèle

[4. Moteur IA Générative (RAG)]
  └── Poser une question interne sur ITGate (ex: "Quels sont les domaines d'activité d'ITGate ?")
  └── Montrer la réponse instantanée et la liste des sources documentaires

[5. Observabilité & DevOps]
  └── Ouvrir Swagger UI (http://127.0.0.1:8000/docs) pour montrer l'API standardisée
  └── Ouvrir MLflow (http://127.0.0.1:5000) pour montrer l'historique des modèles
  └── Ouvrir Grafana (http://127.0.0.1:3000) pour prouver le monitoring en temps réel
```
