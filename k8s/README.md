# Déploiement Kubernetes

Ce dossier contient les manifestes nécessaires pour déployer l'API MLOps sur un cluster Kubernetes local, par exemple Docker Desktop Kubernetes ou Minikube.

## Ressources

| Fichier | Rôle |
|---|---|
| `configmap.yaml` | Configuration non sensible de l'API |
| `groq-api-key.template.yaml` | Exemple de Secret Kubernetes pour `GROQ_API_KEY` |
| `deployment.yaml` | Déploiement de l'API FastAPI |
| `deployment-ghcr.yaml` | Patch pour utiliser une image publiée dans GitHub Container Registry |
| `service.yaml` | Exposition réseau de l'API |
| `hpa.yaml` | Autoscaling horizontal |

## Créer le Secret Groq

Ne pas committer une vraie clé API.

Option recommandée :

```powershell
kubectl create secret generic groq-api-secret --from-literal=GROQ_API_KEY="<votre-cle-groq>"
```

Option template :

```powershell
copy k8s/groq-api-key.template.yaml k8s/groq-api-key.local.yaml
# Modifier k8s/groq-api-key.local.yaml avec la vraie clé
kubectl apply -f k8s/groq-api-key.local.yaml
```

Le fichier local contenant la vraie clé doit rester non versionné.

## Déployer

```powershell
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml
```

Ou :

```powershell
make k8s-deploy
```

## Déployer une image publiée dans GHCR

Après publication de l'image par la CI, générez le patch local avec l'image réelle :

```powershell
make k8s-render-ghcr-patch IMAGE_REGISTRY=ghcr.io/<owner>/<repo> IMAGE_TAG=<tag>
```

Le fichier généré `k8s/deployment-ghcr.local.yaml` reste non versionné. Pour déployer en une seule commande :

```powershell
make k8s-deploy-ghcr IMAGE_REGISTRY=ghcr.io/<owner>/<repo> IMAGE_TAG=<tag>
```

Sur Windows sans `make`, utilisez :

```powershell
.\scripts\k8s_deploy_ghcr.ps1 -ImageRegistry ghcr.io/owner/repo -ImageTag tag
```

Pour un cluster privé, configurez d'abord un `imagePullSecret` si le package GHCR n'est pas public.

## Vérifier

```powershell
kubectl get pods,svc,hpa -l app=ml-inference
kubectl describe deployment ml-inference-deployment
kubectl logs -l app=ml-inference --tail=100
```

## Monitoring

Le service expose les annotations Prometheus :

```yaml
prometheus.io/scrape: "true"
prometheus.io/path: "/metrics"
prometheus.io/port: "8000"
```

Ces annotations peuvent être utilisées par une installation Prometheus dans le cluster pour découvrir automatiquement l'API.
