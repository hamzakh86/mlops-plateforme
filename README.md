# 🚀 Plateforme MLOps pour Déploiement IA

Bienvenue dans le dépôt principal du projet de stage **Plateforme MLOps**. Ce projet vise à construire une infrastructure complète permettant l'entraînement, le suivi, l'empaquetage (Docker), et le déploiement (Kubernetes) de modèles de Machine Learning.

## 🎯 Architecture - Semaine 1 (Socle ML)
La première phase du projet consiste à établir les fondations du cycle de vie MLOps :
- **Python & venv** : Isolation des dépendances.
- **Git** : Versionnement du code source.
- **Scikit-Learn** : Création du modèle d'Intelligence Artificielle (PoC : Classification Iris).
- **MLflow Tracking** : Enregistrement centralisé des hyperparamètres, des métriques de performance, et des artefacts (fichiers du modèle).

---

## 🛠️ Installation et Configuration

### 1. Prérequis
- Python 3.11+ installé sur votre machine.
- Git.

### 2. Création de l'environnement virtuel
Ouvrez un terminal (PowerShell) à la racine du projet et exécutez :
```powershell
# Création de l'environnement
python -m venv venv

# Activation (Windows PowerShell)
.\venv\Scripts\Activate.ps1
```

### 3. Installation des dépendances
Une fois l'environnement activé, installez les bibliothèques requises :
```powershell
pip install -r requirements.txt
```

---

## 🧠 Exécution de l'Entraînement

Pour simuler le travail d'un Data Scientist et entraîner le modèle, exécutez le script principal :
```powershell
python src/train.py
```

Vous pouvez également modifier les hyperparamètres du modèle en ligne de commande :
```powershell
python src/train.py --n_estimators 150 --max_depth 5
```
*Le script est structuré selon les standards de l'industrie (Type Hinting, Logging, Docstrings) et gère automatiquement l'injection des données vers la base MLflow.*

---

## 📊 Visualisation des Résultats (MLflow UI)

MLflow enregistre toutes les expériences dans une base de données locale (`mlflow.db`). Pour visualiser les résultats et comparer les différents entraînements, lancez le serveur UI :

```powershell
mlflow ui --backend-store-uri sqlite:///mlflow.db
```
Ouvrez ensuite votre navigateur à l'adresse suivante : **http://127.0.0.1:5000**

Vous y trouverez l'expérience `Iris_Classification` contenant :
- Les paramètres utilisés (`n_estimators`, `max_depth`).
- Les métriques calculées (`accuracy`, `precision`, `recall`, `f1_score`).
- Le modèle sérialisé et prêt à être déployé (Semaine 2).
