# Guide de démonstration - Plateforme MLOps

## Objectif de la démo

Montrer une plateforme MLOps complète capable de :

- entraîner et tracker un modèle ML avec MLflow ;
- exposer une API d'inférence avec FastAPI ;
- interroger un corpus documentaire avec RAG ;
- extraire et classifier des documents avec un LLM ;
- superviser l'API avec Prometheus et Grafana ;
- gérer proprement une indisponibilité Groq.

## Préparation

Vérifier que l'environnement est prêt :

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Pour une soutenance sur Windows sans `make`, utilisez aussi la checklist dédiée :

```text
docs/windows-demo-checklist.md
```

Vérifier que `.env` contient :

```text
MLFLOW_TRACKING_URI=sqlite:///mlflow.db
MLFLOW_EXPERIMENT_NAME=Iris_Classification
RAG_EXPERIMENT_NAME=RAG_Document_QA
GROQ_API_KEY=<clé personnelle>
GROQ_MODEL=llama-3.1-8b-instant
```

## Scénario 1 - Validation MLflow

Lancer un entraînement :

```powershell
make train
```

Ouvrir MLflow :

```powershell
mlflow ui --backend-store-uri sqlite:///mlflow.db
```

À montrer :

- le run d'entraînement ;
- les hyperparamètres ;
- l'accuracy ;
- l'artefact du modèle.

## Scénario 2 - API FastAPI

Démarrer l'API :

```powershell
make serve
```

Ouvrir :

```text
Interface web : http://127.0.0.1:8000/
Swagger UI    : http://127.0.0.1:8000/docs
```

Vérifier rapidement les endpoints :

```powershell
make smoke-api
```

Sans Groq :

```powershell
make smoke-api-lite
```

À montrer :

- l'interface web de pilotage centralise les tests et les liens outils ;
- `/health` indique si le modèle ML et le RAG sont chargés ;
- `/predict` retourne une classe Iris ;
- `/ask` retourne une réponse sourcée ;
- `/extract` retourne un JSON structuré ;
- `/classify` retourne une catégorie.

## Scénario 3 - Monitoring

Démarrer Docker Desktop, puis :

```powershell
make monitoring-up
```

Générer du trafic :

```powershell
make demo-traffic
```

Ouvrir :

```text
Prometheus : http://127.0.0.1:9090
Grafana    : http://127.0.0.1:3000
Login      : admin / admin
```

À montrer dans Grafana :

- débit des requêtes HTTP ;
- latence p95 des endpoints IA ;
- nombre de fallbacks LLM ;
- activité du RAG.

## Scénario 4 - Fallback Groq

Objectif : montrer que la plateforme reste stable si Groq est indisponible.

Option simple :

1. Arrêter l'API.
2. Remplacer temporairement `GROQ_API_KEY` par une valeur invalide dans `.env`.
3. Redémarrer l'API.
4. Appeler `/ask`, `/extract` ou `/classify`.

Résultat attendu :

- l'API ne casse pas brutalement ;
- la réponse contient `fallback: true` ;
- les métriques Prometheus enregistrent le fallback.

## Questions de démo utiles

RAG :

```text
Quels sont les horaires de travail chez ITGate Group ?
Comment la plateforme MLOps est-elle déployée ?
Que se passe-t-il si Groq est indisponible ?
Quelles métriques sont utilisées pour superviser les endpoints IA ?
```

Classification :

```text
Rapport technique décrivant la supervision Prometheus, Grafana et les stratégies de fallback LLM.
Catégories : Facture, CV, Contrat, Rapport
```

Extraction :

```text
Facture ITGate Group du 10/08/2026. Montant total: 1250.50 TND.
```

## Conclusion orale possible

Cette plateforme montre une chaîne MLOps complète : entraînement, tracking, API, conteneurisation, orchestration, RAG, monitoring et CI/CD. Le point important est que les fonctionnalités IA sont observables et disposent d'une stratégie de fallback, ce qui rend le système plus fiable pour une démonstration et plus proche d'un usage industriel.
