# Risques, Limites et Perspectives d'Amélioration

Bien que la plateforme MLOps actuelle réponde au cahier des charges et propose une base solide pour le déploiement de modèles ML et d'IA, certains choix architecturaux et techniques comportent des limites qu'il convient d'identifier pour une mise en production réelle.

## 1. Risques et Limites Actuelles

### Dépendance au Cloud (API Groq)
- **Constat** : Le système RAG, la classification et l'extraction dépendent de l'API externe Groq.
- **Risque** : Latence réseau, indisponibilité de l'API (outage) ou dépassement de quota, ce qui pourrait paralyser les fonctionnalités IA métier. De plus, l'envoi de documents sensibles vers une API cloud peut poser des problèmes de confidentialité (RGPD).
- **Atténuation actuelle** : Une logique de *fallback* a été implémentée pour permettre à la recherche locale FAISS de fonctionner même si Groq est indisponible. 

### Sécurité et Authentification
- **Constat** : L'API FastAPI et le dashboard React ne sont protégés par aucune authentification (OAuth2, JWT).
- **Risque** : Accès non autorisé aux endpoints, ce qui pourrait entraîner des fuites de données ou une sur-utilisation frauduleuse de l'API.

### Stockage des Données (Statelessness)
- **Constat** : Les requêtes (questions posées, extractions effectuées) ne sont pas persistées en base de données. L'historique ("Activité récente") n'existe que dans le cache du navigateur (React state).
- **Risque** : Impossibilité d'auditer l'utilisation passée de l'API de manière fine hors des métriques agrégées de Prometheus.

## 2. Perspectives d'Amélioration

### IA 100% Locale (On-Premise)
Pour répondre aux contraintes de sécurité stricte, l'objectif à moyen terme serait de revenir à une architecture **100% locale** (comme initié au Jour 5 avec Ollama) en utilisant des serveurs dotés d'accélérateurs matériels (GPU dédiés). Cela permettrait de :
- Garantir la confidentialité absolue des documents d'entreprise.
- Éliminer la dépendance réseau.

### Implémentation d'une Base de Données (PostgreSQL)
L'ajout d'une base de données relationnelle permettrait de :
- Sauvegarder l'historique des requêtes RAG et des extractions.
- Gérer un système d'utilisateurs et de rôles (RBAC).
- Associer le feedback utilisateur (pouce en l'air/bas) sur les réponses du RAG pour affiner l'évaluation du modèle.

### Évaluation Continue du RAG (RAGAs)
Intégrer un framework d'évaluation spécifique au RAG (comme *Ragas* ou *TruLens*) dans la CI/CD pour mesurer objectivement la pertinence (Relevance), la fidélité (Faithfulness) et l'exactitude des sources récupérées par FAISS.

### Déploiement Cloud Native (GitOps)
Mettre en place un outil comme **ArgoCD** ou **Flux** pour synchroniser automatiquement les manifestes Kubernetes (`k8s/`) depuis le dépôt Git vers le cluster, remplaçant ainsi les scripts de déploiement manuels (`make k8s-deploy-ghcr`) par un véritable pipeline GitOps.
