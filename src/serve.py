import logging
import os
import time
import mlflow
import mlflow.sklearn
import pandas as pd
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List
from prometheus_fastapi_instrumentator import Instrumentator

# ─── Logger ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ─── Configuration (lecture depuis les variables d'environnement, avec fallback local) ────
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")
EXPERIMENT_NAME     = os.getenv("MLFLOW_EXPERIMENT_NAME", "Iris_Classification")
MODEL_ARTIFACT_PATH = os.getenv("MODEL_ARTIFACT_PATH", "random_forest_model")

# ─── Modèle chargé en mémoire (singleton) ────────────────────────────────────
_model      = None
_model_info = {}

# ─── Schémas Pydantic (équivalent TypeScript Interfaces) ─────────────────────
class IrisFeatures(BaseModel):
    sepal_length: float = Field(..., gt=0, description="Longueur du sépale en cm", example=5.1)
    sepal_width:  float = Field(..., gt=0, description="Largeur du sépale en cm",  example=3.5)
    petal_length: float = Field(..., gt=0, description="Longueur du pétale en cm", example=1.4)
    petal_width:  float = Field(..., gt=0, description="Largeur du pétale en cm",  example=0.2)

class PredictRequest(BaseModel):
    data: List[IrisFeatures] = Field(..., min_length=1, description="Liste de mesures Iris à classifier.")

class PredictResponse(BaseModel):
    predictions: List[str]
    model_run_id: str
    duration_ms: float

# ─── Chargement du modèle (au démarrage de l'application) ─────────────────────
def _load_best_model() -> None:
    """Charge le dernier modèle enregistré dans l'expérience MLflow cible."""
    global _model, _model_info
    
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    logger.info(f"Connexion à MLflow Tracking URI : {MLFLOW_TRACKING_URI}")
    
    experiment = mlflow.get_experiment_by_name(EXPERIMENT_NAME)
    if not experiment:
        raise RuntimeError(f"L'expérience MLflow '{EXPERIMENT_NAME}' est introuvable.")
    
    runs = mlflow.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=["start_time DESC"],
        max_results=1
    )
    if runs.empty:
        raise RuntimeError(f"Aucun run trouvé dans l'expérience '{EXPERIMENT_NAME}'.")
    
    run = runs.iloc[0]
    run_id    = run["run_id"]
    model_uri = f"runs:/{run_id}/{MODEL_ARTIFACT_PATH}"
    
    logger.info(f"Chargement du modèle depuis : {model_uri}")
    _model = mlflow.sklearn.load_model(model_uri)
    _model_info = {
        "run_id":     run_id,
        "accuracy":   run.get("metrics.accuracy", "N/A"),
        "experiment": EXPERIMENT_NAME,
    }
    logger.info(f"Modèle chargé avec succès. run_id={run_id} | accuracy={_model_info['accuracy']}")

# ─── Lifespan (remplacement moderne de @app.on_event) ─────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gère le cycle de vie de l'application : chargement et libération du modèle."""
    logger.info("Démarrage de l'API — Chargement du modèle ML...")
    _load_best_model()
    yield
    logger.info("Arrêt de l'API — Libération des ressources.")

# ─── Application FastAPI ───────────────────────────────────────────────────────
app = FastAPI(
    title="🚀 MLOps — API d'Inférence Iris",
    description=(
        "API de prédiction de l'espèce d'Iris entraînée avec Scikit-Learn "
        "et trackée avec MLflow. Produit final d'un pipeline MLOps complet."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

# ─── Monitoring Prometheus ─────────────────────────────────────────────────────
Instrumentator().instrument(app).expose(app)

# CORS : autorise l'accès depuis le futur frontend web (Semaine 3)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/health", tags=["Système"])
def health_check():
    """Vérifie l'état de l'API et du modèle (utilisé par les probes Kubernetes)."""
    return {
        "status":       "ok",
        "model_loaded": _model is not None,
        "model_info":   _model_info,
    }

@app.post("/predict", response_model=PredictResponse, tags=["Inférence"])
def predict(request: PredictRequest, req: Request):
    """Effectue une classification sur les données Iris fournies."""
    if _model is None:
        raise HTTPException(status_code=503, detail="Le modèle n'est pas encore chargé. Réessayez dans un instant.")
    
    start = time.perf_counter()
    
    IRIS_CLASSES = {0: "setosa", 1: "versicolor", 2: "virginica"}
    
    try:
        df          = pd.DataFrame([item.model_dump() for item in request.data])
        predictions = _model.predict(df)
        labels      = [IRIS_CLASSES[int(p)] for p in predictions]
    except Exception as e:
        logger.error(f"Erreur lors de la prédiction : {e}")
        raise HTTPException(status_code=422, detail=f"Erreur de prédiction : {str(e)}")
    
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(f"Prédiction effectuée en {duration_ms:.2f}ms | résultats={labels} | client={req.client.host}")
    
    return PredictResponse(
        predictions  = labels,
        model_run_id = _model_info.get("run_id", "inconnu"),
        duration_ms  = round(duration_ms, 2),
    )
