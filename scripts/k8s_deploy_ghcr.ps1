<#
.SYNOPSIS
Deploy the MLOps API to Kubernetes using an image published in GHCR.

.EXAMPLE
.\scripts\k8s_deploy_ghcr.ps1 -ImageRegistry ghcr.io/owner/repo -ImageTag abc1234
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ImageRegistry,

    [Parameter(Mandatory = $true)]
    [string]$ImageTag,

    [string]$Python = "venv\Scripts\python",
    [string]$PatchOutput = "k8s\deployment-ghcr.local.yaml"
)

$ErrorActionPreference = "Stop"

if ($ImageRegistry -match "[<>]" -or $ImageTag -match "[<>]") {
    throw "Replace placeholders with real values. Example: -ImageRegistry ghcr.io/my-user/my-repo -ImageTag abc1234"
}

& $Python scripts/render_k8s_ghcr_patch.py --registry $ImageRegistry --tag $ImageTag --output $PatchOutput

kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml
kubectl patch deployment ml-inference-deployment --patch-file $PatchOutput

kubectl get pods,svc,hpa -l app=ml-inference
