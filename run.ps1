# ============================================================
#  run.ps1 — Helper PowerShell pour Windows (Alternative à make)
#  Usage:
#    .\run.ps1 register-model
#    .\run.ps1 notebook
#    .\run.ps1 train
#    .\run.ps1 serve
#    .\run.ps1 test
#    .\run.ps1 mlflow-ui
# ============================================================

param (
    [Parameter(Position=0)]
    [string]$Target = "help"
)

$Python = ".\venv\Scripts\python.exe"
$Uvicorn = ".\venv\Scripts\uvicorn.exe"
$Pytest = ".\venv\Scripts\pytest.exe"

switch ($Target.ToLower()) {
    "register-model" {
        Write-Host "🏛️ Entraînement et enregistrement dans MLflow Model Registry..." -ForegroundColor Cyan
        & $Python src/train.py --register --promote
    }
    "notebook" {
        Write-Host "📓 Démarrage du Notebook Jupyter ITGate..." -ForegroundColor Cyan
        & $Python -m notebook notebooks/demo_itgate.ipynb
    }
    "train" {
        Write-Host "🧠 Lancement de l'entraînement MLflow..." -ForegroundColor Cyan
        & $Python src/train.py
    }
    "serve" {
        Write-Host "🚀 Démarrage de l'API FastAPI..." -ForegroundColor Cyan
        & $Uvicorn src.serve:app --host 127.0.0.1 --port 8000 --reload
    }
    "test" {
        Write-Host "🧪 Lancement des tests pytest..." -ForegroundColor Cyan
        & $Pytest tests/ -v
    }
    "mlflow-ui" {
        Write-Host "📊 Démarrage de MLflow UI..." -ForegroundColor Cyan
        & $Python -m mlflow ui --backend-store-uri sqlite:///mlflow.db
    }
    "train-rag" {
        Write-Host "🤖 Ingestion RAG des documents..." -ForegroundColor Cyan
        & $Python src/train_rag.py --run-name "RAG_Local_Ingestion"
    }
    "frontend-dev" {
        Write-Host "⚛️ Démarrage de la console React..." -ForegroundColor Cyan
        npm --prefix frontend run dev
    }
    default {
        Write-Host "Usage: .\run.ps1 <cible>" -ForegroundColor Yellow
        Write-Host "Cibles disponibles :"
        Write-Host "  register-model : Entraîne et enregistre le modèle dans le Model Registry" -ForegroundColor Green
        Write-Host "  notebook       : Ouvre le notebook Jupyter de soutenance" -ForegroundColor Green
        Write-Host "  train          : Entraîne le modèle RandomForest" -ForegroundColor Green
        Write-Host "  serve          : Démarre l'API FastAPI sur http://127.0.0.1:8000" -ForegroundColor Green
        Write-Host "  test           : Exécute les 39 tests unitaires" -ForegroundColor Green
        Write-Host "  mlflow-ui      : Lance l'interface MLflow sur http://127.0.0.1:5000" -ForegroundColor Green
        Write-Host "  train-rag      : Réindexe les documents pour le RAG" -ForegroundColor Green
        Write-Host "  frontend-dev   : Démarre le frontend React en développement" -ForegroundColor Green
    }
}
