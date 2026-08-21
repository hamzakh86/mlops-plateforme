# Synthèse de Soutenance : Plateforme MLOps pour Déploiement IA

**Stagiaire :** Hamza Khaled
**Encadrant :** Achraf Chehab
**Contexte :** Programme de stages d'été 2026 — ITGate Group

---

## 🎯 Objectif du Projet
Concevoir et développer une **plateforme MLOps de bout en bout** permettant l'entraînement, le suivi, le déploiement automatisé et le monitoring de modèles d'Intelligence Artificielle (ML classique, NLP, RAG). L'objectif est de fournir une solution scalable, conteneurisée et prête pour la production, démontrant le savoir-faire technologique d'ITGate Group.

## 🛠️ Architecture Technologique
La plateforme repose sur une architecture moderne en 5 couches :
1. **Machine Learning & Tracking** : `Scikit-Learn` (modèle de base Iris) et `MLflow` (historisation, registre de modèles).
2. **Backend & IA Métier** : API `FastAPI` asynchrone exposant les prédictions ML, le RAG (Retrieval-Augmented Generation avec `FAISS` et `Groq`) et l'extraction/classification de documents Zero-Shot.
3. **Frontend de Pilotage** : Console d'administration web développée en `React` (Vite) offrant une interface moderne et dynamique pour l'interaction utilisateur et l'observabilité.
4. **Orchestration & Déploiement** : Conteneurisation via `Docker` (Multi-stage) et déploiement orchestré via `Kubernetes` (Deployment, Services, HPA).
5. **CI/CD & Monitoring** : Pipeline automatisé `GitHub Actions` (Build, Test, Push GHCR) et supervision technique/métier avec `Prometheus` et `Grafana`.

## ✨ Fonctionnalités Clés
- **Inférence ML Temps Réel** : Consommation du dernier modèle validé dans MLflow via l'API.
- **RAG Local/Cloud Hybride** : Recherche documentaire sur les données internes de l'entreprise (Embeddings locaux) générée avec l'API Groq, incluant une logique de fallback en cas d'erreur.
- **IA Documentaire** : Extraction d'entités structurées et classification de documents sans entraînement préalable (Zero-Shot).
- **Auto-Scaling (HPA)** : Adaptation automatique du nombre de Pods Kubernetes selon la charge.
- **Dashboard d'Observabilité** : Métriques HTTP classiques et métriques IA dédiées (latence LLM, fallbacks, nombre de documents récupérés).

## 🚀 Réalisations et Valeur Ajoutée
- **Complétude** : Le cycle complet du MLOps a été couvert, depuis la préparation des données jusqu'au monitoring en production.
- **Robustesse** : Implémentation d'une gestion fine des erreurs, avec *graceful degradation* (fallback) pour l'API LLM afin de garantir un service continu.
- **Ergonomie** : Une interface utilisateur unifiée, claire et esthétique, indispensable pour démontrer l'outil aux parties prenantes non techniques.
- **Prêt pour le Déploiement** : Tous les artefacts (manifestes K8s, scripts, dashboards JSON) sont versionnés, validés par la CI/CD et prêts à être déployés sur un vrai cluster de production.

## 🔮 Perspectives
La prochaine évolution naturelle de cette plateforme serait l'ajout d'une base de données persistante (`PostgreSQL`) pour le traçage fin des requêtes des utilisateurs, ainsi que la migration vers un moteur LLM 100% on-premise sur GPU pour garantir une indépendance cloud totale.
