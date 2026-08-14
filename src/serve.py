"""
src/serve.py
─────────────
API FastAPI — Plateforme MLOps (ITGate Group)

Expose :
  GET  /health   → Vérification santé (Kubernetes probes)
  GET  /metrics  → Métriques Prometheus
  POST /token    → Authentification JWT
  GET  /history  → Historique des requêtes (DB)
  POST /predict  → Prédiction Iris (modèle Scikit-Learn via MLflow)
  POST /ask      → Système RAG Questions/Réponses (LangChain + Groq + FAISS)
  POST /extract  → Extraction intelligente de documents
  POST /classify → Classification de documents
"""

import logging
import os
import time
from pathlib import Path
import mlflow
import mlflow.sklearn
import pandas as pd
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from typing import List
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy.orm import Session

from src.monitoring import LLM_REQUEST_DURATION_SECONDS, LLM_REQUESTS_TOTAL, DATA_DRIFT_SCORE
from src.drift import detect_data_drift
from src.rag_engine import RAGEngine
from src.database import init_db, get_db
from src.models import User, ApiRequestLog
from src.auth import get_current_user, authenticate_user, create_access_token, get_password_hash

# ─── Charger les variables d'environnement (.env) ─────────────────────────────
load_dotenv()

# ─── Logger ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ─── Configuration ────────────────────────────────────────────────────────────
MLFLOW_TRACKING_URI   = os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")
EXPERIMENT_NAME       = os.getenv("MLFLOW_EXPERIMENT_NAME", "ITGate_Revenue_Forecast")
REGISTERED_MODEL_NAME = os.getenv("REGISTERED_MODEL_NAME", "ITGate_Revenue_Model")
MODEL_STAGE           = os.getenv("MODEL_STAGE", "Production")
MODEL_ARTIFACT_PATH   = os.getenv("MODEL_ARTIFACT_PATH", "random_forest_ts_model")
RAG_EXPERIMENT_NAME   = os.getenv("RAG_EXPERIMENT_NAME", "RAG_Document_QA")
DEFAULT_ADMIN_USER    = os.getenv("DEFAULT_ADMIN_USER", "admin")
DEFAULT_ADMIN_PASS    = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin")
BASE_DIR              = Path(__file__).resolve().parents[1]
FRONTEND_DIR          = BASE_DIR / "frontend"
FRONTEND_DIST_DIR     = FRONTEND_DIR / "dist"

# ─── Singletons globaux ───────────────────────────────────────────────────────
_model      = None
_model_info = {}
_rag_engine = RAGEngine()

# ─── Schémas Pydantic ─────────────────────────────────────────────────────────
class RevenueFeatures(BaseModel):
    num_engineers: int = Field(..., description="Nombre d'ingénieurs ITGate", json_schema_extra={"example": 45})
    active_projects: int = Field(..., description="Nombre de projets en cours", json_schema_extra={"example": 16})
    avg_contract_value: float = Field(..., description="Valeur moyenne du contrat (TND)", json_schema_extra={"example": 4800.0})
    lag_1: float = Field(..., description="Revenu (M-1)", json_schema_extra={"example": 72500.0})
    lag_2: float = Field(..., description="Revenu (M-2)", json_schema_extra={"example": 68000.0})
    lag_3: float = Field(..., description="Revenu (M-3)", json_schema_extra={"example": 65400.0})

class PredictRequest(BaseModel):
    data: List[RevenueFeatures] = Field(..., min_length=1, description="Historique des revenus pour prédire le mois suivant.")

class PredictResponse(BaseModel):
    predictions:  List[float]
    model_run_id: str
    duration_ms:  float

class AskRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=5,
        description="La question à poser aux documents.",
        json_schema_extra={"example": "Combien de jours de congé annuel ont les employés ?"},
    )

class AskResponse(BaseModel):
    answer:     str
    sources:    List[str]
    run_id:     str
    duration_ms: float
    fallback:   bool = False

# ─── Chargement du modèle (Model Registry en priorité, fallback dernier run) ──
def _load_best_model() -> None:
    global _model, _model_info
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    logger.info(f"Connexion à MLflow Tracking URI : {MLFLOW_TRACKING_URI}")
    
    # 1. Tentative de chargement depuis le MLflow Model Registry (Stage Production)
    try:
        registry_uri = f"models:/{REGISTERED_MODEL_NAME}/{MODEL_STAGE}"
        logger.info(f"Tentative de chargement depuis le Model Registry : {registry_uri}")
        _model = mlflow.sklearn.load_model(registry_uri)
        
        client = mlflow.MlflowClient()
        latest_versions = client.get_latest_versions(REGISTERED_MODEL_NAME, stages=[MODEL_STAGE])
        version_info = latest_versions[0] if latest_versions else None
        
        _model_info = {
            "source":      "Model Registry",
            "model_name":  REGISTERED_MODEL_NAME,
            "stage":       MODEL_STAGE,
            "version":     version_info.version if version_info else "1",
            "run_id":      version_info.run_id if version_info else "registry",
            "status":      "Production Ready",
        }
        logger.info(f"✅ Modèle chargé avec succès depuis le Registry ({REGISTERED_MODEL_NAME} v{_model_info['version']} [{MODEL_STAGE}])")
        return
    except Exception as e:
        logger.warning(f"⚠️ Model Registry non disponible ({e}). Fallback vers le dernier Run de l'expérience...")

    # 2. Fallback : Chargement du dernier run de l'expérience
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
    logger.info(f"Chargement du modèle depuis le Run : {model_uri}")
    _model = mlflow.sklearn.load_model(model_uri)
    _model_info = {
        "source":     "Experiment Run",
        "run_id":     run_id,
        "r2":         run.get("metrics.r2", "N/A"),
        "rmse":       run.get("metrics.rmse", "N/A"),
        "experiment": EXPERIMENT_NAME,
        "stage":      "Latest_Run_Fallback"
    }
    logger.info(f"Modèle chargé avec succès depuis le run. run_id={run_id} | R2={_model_info.get('r2')}")

# ─── Lifespan ─────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Démarrage de l'API — Initialisation de la DB...")
    init_db()
    
    # Créer un admin par défaut si aucun user n'existe
    db_gen = get_db()
    db = next(db_gen)
    if not db.query(User).filter(User.username == DEFAULT_ADMIN_USER).first():
        logger.info(f"Création de l'utilisateur admin par défaut ({DEFAULT_ADMIN_USER}).")
        admin = User(username=DEFAULT_ADMIN_USER, hashed_password=get_password_hash(DEFAULT_ADMIN_PASS))
        db.add(admin)
        db.commit()
    db.close()

    logger.info("Chargement des modèles ML...")
    _load_best_model()

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
        "- **Système RAG** (LangChain + Groq + FAISS)\n"
        "- **IA métier** : Extraction et Classification de documents\n\n"
        "Produit final d'un pipeline MLOps complet (Docker + Kubernetes)."
    ),
    version="4.0.0",
    lifespan=lifespan,
)

# ─── Monitoring Prometheus ─────────────────────────────────────────────────────
Instrumentator().instrument(app).expose(app)

# ─── CORS et Sécurité ───────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

# ─── Routes Publiques ─────────────────────────────────────────────────────────

if FRONTEND_DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST_DIR / "assets"), name="frontend-assets")

@app.get("/logo.png", include_in_schema=False)
def get_logo():
    logo_dist = FRONTEND_DIST_DIR / "logo.png"
    if logo_dist.exists():
        return FileResponse(logo_dist)
    logo_pub = FRONTEND_DIR / "public" / "logo.png"
    if logo_pub.exists():
        return FileResponse(logo_pub)
    raise HTTPException(status_code=404, detail="Logo non trouvé")

@app.get("/", include_in_schema=False)
def web_dashboard():
    index_path = FRONTEND_DIST_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Interface React non disponible. Lancez : npm --prefix frontend run build",
        )
    return FileResponse(index_path)

@app.get("/health", tags=["Système"])
def health_check():
    return {
        "status":       "ok",
        "model_loaded": _model is not None,
        "model_info":   _model_info,
        "rag_loaded":   _rag_engine.is_loaded,
        "rag_info":     _rag_engine.run_info,
    }

@app.get("/health/live", tags=["Système"])
def liveness_check():
    """Liveness probe pour Kubernetes : vérifie que le serveur HTTP répond."""
    return {"status": "alive"}

@app.get("/health/ready", tags=["Système"])
def readiness_check():
    """Readiness probe pour Kubernetes : vérifie que le modèle ML est chargé."""
    if _model is None:
        raise HTTPException(status_code=503, detail="Modèle ML non prêt")
    return {"status": "ready", "model_info": _model_info}

@app.get("/model/info", tags=["Système"])
def get_model_info():
    """Retourne les métadonnées détaillées du modèle en production."""
    return {
        "model_loaded": _model is not None,
        "model_info": _model_info,
        "features": ["num_engineers", "active_projects", "avg_contract_value", "lag_1", "lag_2", "lag_3"],
        "target": "revenue",
        "model_type": "RandomForestRegressor_Multivariate",
        "tracking_uri": MLFLOW_TRACKING_URI,
    }

@app.post("/token", tags=["Auth"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# ─── Utilitaires DB ───────────────────────────────────────────────────────────
def log_request(db: Session, user_id: int, endpoint: str, req_status: str, detail: str, duration_ms: float):
    log = ApiRequestLog(
        user_id=user_id,
        endpoint=endpoint,
        status=req_status,
        detail=detail,
        duration_ms=duration_ms
    )
    db.add(log)
    db.commit()

@app.get("/history", tags=["Système"])
def get_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    logs = db.query(ApiRequestLog).order_by(ApiRequestLog.created_at.desc()).limit(20).all()
    return [{
        "endpoint": l.endpoint,
        "status": l.status,
        "detail": l.detail,
        "duration_ms": l.duration_ms,
        "at": l.created_at.strftime("%H:%M:%S"),
        "error": l.status == "Erreur"
    } for l in logs]

# ─── Routes Sécurisées (Inférence & IA) ───────────────────────────────────────

@app.post("/predict", response_model=PredictResponse, tags=["Inférence ML"])
def predict(request: PredictRequest, req: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if _model is None:
        raise HTTPException(status_code=503, detail="Le modèle n'est pas encore chargé.")
    start = time.perf_counter()
    try:
        df          = pd.DataFrame([item.model_dump() for item in request.data])
        predictions = _model.predict(df)
        results     = [float(p) for p in predictions]
        
        # Calcul du Data Drift
        drift_report = detect_data_drift(df)
        DATA_DRIFT_SCORE.set(drift_report["drift_score"])
        
        duration_ms = (time.perf_counter() - start) * 1000
        log_request(db, current_user.id, "/predict", "OK", "Termine", duration_ms)
        return PredictResponse(predictions=results, model_run_id=_model_info.get("run_id", "inconnu"), duration_ms=round(duration_ms, 2))
    except Exception as e:
        log_request(db, current_user.id, "/predict", "Erreur", str(e), 0)
        raise HTTPException(status_code=422, detail=f"Erreur de prédiction : {str(e)}")


@app.get("/drift", tags=["Monitoring & Data Quality"])
def get_drift_status(current_user: User = Depends(get_current_user)):
    """Retourne le rapport de dérive statistique des données (Data Drift)."""
    # Échantillon de test fictif récent si aucune prédiction récente
    dummy_data = pd.DataFrame([{
        "num_engineers": 45,
        "active_projects": 16,
        "avg_contract_value": 4800.0,
        "lag_1": 72500.0,
        "lag_2": 68000.0,
        "lag_3": 65400.0
    }])
    report = detect_data_drift(dummy_data)
    DATA_DRIFT_SCORE.set(report["drift_score"])
    return report


@app.post("/ask", response_model=AskResponse, tags=["RAG"])
def ask(request: AskRequest, req: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not _rag_engine.is_loaded:
        raise HTTPException(status_code=503, detail="Moteur RAG non disponible.")
    start = time.perf_counter()
    try:
        result = _rag_engine.ask(request.question)
    except Exception as e:
        LLM_REQUESTS_TOTAL.labels(endpoint="ask", status="error").inc()
        log_request(db, current_user.id, "/ask", "Erreur", str(e), 0)
        raise HTTPException(status_code=500, detail=f"Erreur du moteur RAG : {str(e)}")
        
    duration_ms = (time.perf_counter() - start) * 1000
    LLM_REQUEST_DURATION_SECONDS.labels(endpoint="ask").observe(duration_ms / 1000)
    
    fallback = result.get("fallback", False)
    req_status = "Fallback" if fallback else "OK"
    LLM_REQUESTS_TOTAL.labels(endpoint="ask", status="fallback" if fallback else "success").inc()
    log_request(db, current_user.id, "/ask", req_status, f"{duration_ms:.2f} ms", duration_ms)
    
    return AskResponse(
        answer=result["answer"],
        sources=result["sources"],
        run_id=_rag_engine.run_info.get("run_id", "inconnu"),
        duration_ms=round(duration_ms, 2),
        fallback=fallback,
    )

class ClassifyRequest(BaseModel):
    text: str = Field(..., min_length=10)
    categories: List[str] = Field(..., min_length=2)

class ExtractRequest(BaseModel):
    text: str = Field(..., min_length=10)


from src.nlp_engine import DocumentClassifier, DocumentExtractor
_classifier = DocumentClassifier()
_extractor = DocumentExtractor()


@app.post("/extract", tags=["Extraction"])
async def extract_document(request: ExtractRequest, req: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    start = time.perf_counter()
    result = _extractor.extract(request.text)
    duration_ms = (time.perf_counter() - start) * 1000
    LLM_REQUEST_DURATION_SECONDS.labels(endpoint="extract").observe(duration_ms / 1000)
    
    fallback = _extractor.last_error is not None
    req_status = "Fallback" if fallback else "OK"
    LLM_REQUESTS_TOTAL.labels(endpoint="extract", status="fallback" if fallback else "success").inc()
    log_request(db, current_user.id, "/extract", req_status, f"{duration_ms:.2f} ms", duration_ms)
    
    return {"extracted_data": result, "duration_ms": round(duration_ms, 2), "fallback": fallback}


@app.post("/classify", tags=["Classification"])
async def classify_document(request: ClassifyRequest, req: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    start = time.perf_counter()
    category = _classifier.classify(request.text, request.categories)
    duration_ms = (time.perf_counter() - start) * 1000
    LLM_REQUEST_DURATION_SECONDS.labels(endpoint="classify").observe(duration_ms / 1000)
    
    fallback = _classifier.last_error is not None
    req_status = "Fallback" if fallback else "OK"
    LLM_REQUESTS_TOTAL.labels(endpoint="classify", status="fallback" if fallback else "success").inc()
    log_request(db, current_user.id, "/classify", req_status, f"{duration_ms:.2f} ms", duration_ms)
    
    return {"category": category, "duration_ms": round(duration_ms, 2), "fallback": fallback}
