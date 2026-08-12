# Checklist de soutenance Windows - Plateforme MLOps

Ce guide sert de déroulé rapide pour présenter le projet depuis PowerShell, sans dépendre de `make`.

## 1. Préparation

Activer l'environnement :

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Vérifier les artefacts :

```powershell
venv\Scripts\pytest tests\test_project_artifacts.py -v
```

Vérifier tous les tests :

```powershell
venv\Scripts\pytest tests\ -v
```

## 2. Entraînement et MLflow

Lancer un entraînement :

```powershell
python src/train.py --run_name "demo_soutenance"
```

Ouvrir MLflow :

```powershell
mlflow ui --backend-store-uri sqlite:///mlflow.db
```

À montrer :

- tracking des runs ;
- métriques du modèle Iris ;
- artefact du modèle sauvegardé.

## 3. API FastAPI

Démarrer l'API :

```powershell
uvicorn src.serve:app --host 127.0.0.1 --port 8000 --reload
```

Ouvrir :

```text
http://127.0.0.1:8000/docs
```

Smoke test local sans Groq :

```powershell
python scripts/smoke_api.py --skip-llm
```

Smoke test complet si `GROQ_API_KEY` est configurée :

```powershell
python scripts/smoke_api.py
```

À montrer :

- `/health` pour l'état modèle/RAG ;
- `/predict` pour l'inférence ML ;
- `/ask` pour le RAG ;
- `/extract` et `/classify` pour les endpoints IA métier.

## 4. Docker

Vérifier l'image Docker si Docker Desktop est démarré :

```powershell
.\scripts\docker_smoke_test.ps1 -ImageTag smoke
```

À expliquer :

- build multi-stage ;
- utilisateur non-root ;
- healthcheck Docker ;
- labels OCI pour tracer version, commit et date de build.

## 5. Monitoring

Démarrer la stack Prometheus/Grafana :

```powershell
docker compose -f docker-compose.monitoring.yml up --build -d
```

Générer du trafic sans Groq :

```powershell
python scripts/generate_demo_traffic.py --rounds 5 --delay 1 --skip-llm
```

Générer du trafic complet :

```powershell
python scripts/generate_demo_traffic.py --rounds 5 --delay 1
```

Ouvrir :

```text
Prometheus : http://127.0.0.1:9090
Grafana    : http://127.0.0.1:3000
Login      : admin / admin
```

À montrer :

- débit HTTP ;
- latence p95 ;
- fallbacks LLM ;
- documents récupérés par le RAG.

Arrêter la stack :

```powershell
docker compose -f docker-compose.monitoring.yml down
```

## 6. Kubernetes local

Créer le Secret Groq si nécessaire :

```powershell
kubectl create secret generic groq-api-secret --from-literal=GROQ_API_KEY="$env:GROQ_API_KEY" --dry-run=client -o yaml | kubectl apply -f -
```

Déployer les manifestes :

```powershell
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml
kubectl get pods,svc,hpa -l app=ml-inference
```

## 7. Kubernetes avec image GHCR

Générer et appliquer le patch GHCR :

```powershell
.\scripts\k8s_deploy_ghcr.ps1 -ImageRegistry ghcr.io/owner/repo -ImageTag tag
```

Remplacer `owner`, `repo` et `tag` par les valeurs réelles publiées par GitHub Actions.

## 8. Fallback Groq

Pour démontrer la résilience :

1. mettre temporairement une clé Groq invalide dans `.env` ;
2. redémarrer l'API ;
3. appeler `/ask`, `/extract` ou `/classify`.

Résultat attendu :

- l'API répond encore ;
- le champ `fallback` vaut `true` ;
- Prometheus/Grafana affichent l'incident.

## 9. Message de conclusion

La plateforme couvre le cycle MLOps complet : entraînement, tracking, API, Docker, Kubernetes, RAG, endpoints IA métier, monitoring, fallback et CI/CD. Le point fort est l'industrialisation progressive : chaque brique est testée, documentée et observable.
