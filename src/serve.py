"""
src/serve.py
─────────────
API FastAPI — Plateforme MLOps (ITGate Group)

Expose :
  GET  /health   → Vérification santé (Kubernetes probes)
  GET  /metrics  → Métriques Prometheus
  POST /predict  → Prédiction Iris (modèle Scikit-Learn via MLflow)
  POST /ask      → Système RAG Questions/Réponses (LangChain + Gemini)
  POST /extract  → [WIP] Extraction intelligente de documents (Phase 12)
  POST /classify → [WIP] Classification de documents (Phase 13)
"""

import logging
import os
import time
import mlflow
import mlflow.sklearn
import pandas as pd
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from prometheus_fastapi_instrumentator import Instrumentator

from src.rag_engine import RAGEngine

# ─── Charger les variables d'environnement (.env) ─────────────────────────────
load_dotenv()

# ─── Logger ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ─── Configuration ────────────────────────────────────────────────────────────
MLFLOW_TRACKING_URI  = os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")
EXPERIMENT_NAME      = os.getenv("MLFLOW_EXPERIMENT_NAME", "Iris_Classification")
MODEL_ARTIFACT_PATH  = os.getenv("MODEL_ARTIFACT_PATH", "random_forest_model")
RAG_EXPERIMENT_NAME  = os.getenv("RAG_EXPERIMENT_NAME", "RAG_Document_QA")

# ─── Singletons globaux ───────────────────────────────────────────────────────
_model      = None
_model_info = {}
_rag_engine = RAGEngine()

# ─── Schémas Pydantic ─────────────────────────────────────────────────────────
class IrisFeatures(BaseModel):
    sepal_length: float = Field(..., gt=0, description="Longueur du sépale en cm", example=5.1)
    sepal_width:  float = Field(..., gt=0, description="Largeur du sépale en cm",  example=3.5)
    petal_length: float = Field(..., gt=0, description="Longueur du pétale en cm", example=1.4)
    petal_width:  float = Field(..., gt=0, description="Largeur du pétale en cm",  example=0.2)

class PredictRequest(BaseModel):
    data: List[IrisFeatures] = Field(..., min_length=1, description="Liste de mesures Iris à classifier.")

class PredictResponse(BaseModel):
    predictions:  List[str]
    model_run_id: str
    duration_ms:  float

class AskRequest(BaseModel):
    question: str = Field(..., min_length=5, description="La question à poser aux documents.", example="Combien de jours de congé annuel ont les employés ?")

class AskResponse(BaseModel):
    answer:     str
    sources:    List[str]
    run_id:     str
    duration_ms: float

# ─── Chargement du modèle Iris ────────────────────────────────────────────────
def _load_best_model() -> None:
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

# ─── Lifespan ─────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Démarrage de l'API — Chargement des modèles ML...")

    # 1. Charger le modèle Iris (toujours)
    _load_best_model()

    # 2. Charger le moteur RAG (optionnel — si l'expérience existe)
    try:
        rag_info = _rag_engine.load_from_mlflow(MLFLOW_TRACKING_URI, RAG_EXPERIMENT_NAME)
        logger.info(f"Moteur RAG chargé. run_id={rag_info['run_id']} | chunks={rag_info['num_chunks']}")
    except RuntimeError as e:
        logger.warning(f"⚠️  Moteur RAG non disponible (lancez train_rag.py) : {e}")

    yield
    logger.info("Arrêt de l'API — Libération des ressources.")

# ─── Application FastAPI ───────────────────────────────────────────────────────
app = FastAPI(
    title="🚀 MLOps — Plateforme IA (ITGate Group)",
    description=(
        "API complète de la Plateforme MLOps incluant :\n"
        "- **Inférence ML** (RandomForest + MLflow)\n"
        "- **Système RAG** (LangChain + Gemini + FAISS)\n"
        "- **Endpoints WIP** : Extraction et Classification de documents\n\n"
        "Produit final d'un pipeline MLOps complet (Docker + Kubernetes)."
    ),
    version="3.0.0",
    lifespan=lifespan,
)

# ─── Monitoring Prometheus ─────────────────────────────────────────────────────
Instrumentator().instrument(app).expose(app)

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/health", tags=["Système"])
def health_check():
    """Vérifie l'état de l'API et des modèles (Kubernetes probes)."""
    return {
        "status":       "ok",
        "model_loaded": _model is not None,
        "model_info":   _model_info,
        "rag_loaded":   _rag_engine.is_loaded,
        "rag_info":     _rag_engine.run_info,
    }

@app.post("/predict", response_model=PredictResponse, tags=["Inférence ML"])
def predict(request: PredictRequest, req: Request):
    """Effectue une classification sur les données Iris fournies."""
    if _model is None:
        raise HTTPException(status_code=503, detail="Le modèle n'est pas encore chargé.")
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
    logger.info(f"Prédiction : {labels} | {duration_ms:.2f}ms | {req.client.host}")
    return PredictResponse(
        predictions  = labels,
        model_run_id = _model_info.get("run_id", "inconnu"),
        duration_ms  = round(duration_ms, 2),
    )

@app.post("/ask", response_model=AskResponse, tags=["RAG"])
def ask(request: AskRequest, req: Request):
    """
    Pose une question aux documents de l'entreprise.
    Le système RAG (Gemini + FAISS) cherche la réponse dans les documents ingérés.
    """
    if not _rag_engine.is_loaded:
        raise HTTPException(
            status_code=503,
            detail="Le moteur RAG n'est pas disponible. Lancez d'abord : python src/train_rag.py"
        )
    start = time.perf_counter()
    try:
        result = _rag_engine.ask(request.question)
    except Exception as e:
        logger.error(f"Erreur RAG : {e}")
        raise HTTPException(status_code=500, detail=f"Erreur du moteur RAG : {str(e)}")
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(f"RAG : {duration_ms:.2f}ms | client={req.client.host}")
    return AskResponse(
        answer      = result["answer"],
        sources     = result["sources"],
        run_id      = _rag_engine.run_info.get("run_id", "inconnu"),
        duration_ms = round(duration_ms, 2),
    )

class ClassifyRequest(BaseModel):
    text: str = Field(..., min_length=10, description="Le texte du document à classifier.")
    categories: List[str] = Field(..., min_length=2, description="Liste des catégories possibles.")

class ExtractRequest(BaseModel):
    text: str = Field(..., min_length=10, description="Le texte du document dont on veut extraire les informations.")


# ─── Initialisation des moteurs NLP ────────────────────────────────────────────
from src.nlp_engine import DocumentClassifier, DocumentExtractor
_classifier = DocumentClassifier()
_extractor = DocumentExtractor()


@app.post("/extract", tags=["Extraction"])
async def extract_document(request: ExtractRequest, req: Request):
    """Extraction intelligente d'entités d'un document avec Ollama."""
    start = time.perf_counter()
    result = _extractor.extract(request.text)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(f"Extraction : {duration_ms:.2f}ms | client={req.client.host}")
    return {
        "extracted_data": result,
        "duration_ms": round(duration_ms, 2)
    }

@app.post("/classify", tags=["Classification"])
async def classify_document(request: ClassifyRequest, req: Request):
    """Classification de documents Zero-Shot avec Ollama."""
    start = time.perf_counter()
    category = _classifier.classify(request.text, request.categories)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(f"Classification : {category} | {duration_ms:.2f}ms | client={req.client.host}")
    return {
        "category": category,
        "duration_ms": round(duration_ms, 2)
    }
