# Daily Progress Journal - MLOps Platform

Ce fichier sert de journal de bord pour tracer l'avancement quotidien/hebdomadaire du projet de stage.

---

### Semaines 1 & 2 — Finalisation de la base MLOps

**Objectifs de la période :** 
Cadrage du projet, création du socle Machine Learning, empaquetage (Docker) et orchestration (Kubernetes).

**Actions réalisées :**
- Choix du dataset **Iris** comme cas d'usage ML initial. *Justification : L'objectif de ces premières semaines est de construire et valider la plateforme MLOps (l'infrastructure), et non de complexifier le modèle IA.*
- Initialisation du projet : Git, `requirements.txt`, `.gitignore`, `Makefile`.
- Développement de `src/train.py` : Entraînement d'un modèle RandomForest avec tracking automatique des métriques et paramètres via **MLflow**.
- Développement de `src/serve.py` : Création d'une API REST avec **FastAPI** pour servir le modèle MLflow. Ajout des endpoints stubs (`/extract`, `/classify`, `/ask`) pour préparer la Phase 7.
- **Docker** : Création d'un `Dockerfile` multi-stage, sécurisé et optimisé.
- **Kubernetes** : Rédaction des manifestes (`deployment.yaml`, `service.yaml`, `configmap.yaml`, `hpa.yaml`) pour l'auto-scaling et la haute disponibilité.
- Structuration des dossiers data (`data/raw`, `data/processed`), `notebooks` et `tests`.

**Livrables obtenus :**
Le pipeline MLOps est fonctionnel de bout en bout en local (Entraînement ➔ Tracking ➔ Conteneur ➔ API K8s). Dépôt GitHub à jour avec un `README.md` complet.

**Prochaines étapes (Semaine 3) :**
- Remplacer le modèle baseline (Iris) par les modèles NLP métiers (Document Classification, RAG, Extraction).
- Brancher Prometheus et Grafana pour le monitoring de l'API.
