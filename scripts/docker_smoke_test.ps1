<#
.SYNOPSIS
Builds the Docker image, starts a temporary container, then checks /health.

.EXAMPLE
.\scripts\docker_smoke_test.ps1 -ImageTag smoke

.EXAMPLE
.\scripts\docker_smoke_test.ps1 -ImageTag latest -SkipBuild
#>

[CmdletBinding()]
param(
    [string]$ImageName = "ml-inference-api",
    [string]$ImageTag = "smoke",
    [string]$ContainerName = "mlops-api-smoke",
    [int]$Port = 8000,
    [int]$TimeoutSeconds = 90,
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"

function Remove-SmokeContainer {
    param([string]$Name)
    $existing = docker ps -aq --filter "name=^/$Name$"
    if ($existing) {
        docker rm -f $Name | Out-Null
    }
}

$image = "${ImageName}:${ImageTag}"
$healthUrl = "http://127.0.0.1:$Port/health"

try {
    if (-not $SkipBuild) {
        docker build `
            -t $image `
            --build-arg APP_VERSION=$ImageTag `
            --build-arg VCS_REF=local-smoke `
            .
    }

    Remove-SmokeContainer -Name $ContainerName

    docker run -d `
        --name $ContainerName `
        -p "${Port}:8000" `
        $image | Out-Null

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        try {
            $response = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 5
            if ($response.status -eq "ok") {
                Write-Host "Docker smoke test OK: $healthUrl"
                exit 0
            }
        }
        catch {
            Start-Sleep -Seconds 3
        }
    } while ((Get-Date) -lt $deadline)

    docker logs $ContainerName
    throw "Docker smoke test failed: /health did not return status=ok within $TimeoutSeconds seconds."
}
finally {
    Remove-SmokeContainer -Name $ContainerName
}
