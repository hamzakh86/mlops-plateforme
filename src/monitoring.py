"""
src/monitoring.py
─────────────────
Métriques Prometheus métier pour les endpoints IA.
"""

from prometheus_client import Counter, Histogram, Gauge


LLM_REQUESTS_TOTAL = Counter(
    "mlops_llm_requests_total",
    "Nombre d'appels aux fonctionnalités LLM par endpoint et statut.",
    ["endpoint", "status"],
)

LLM_FALLBACKS_TOTAL = Counter(
    "mlops_llm_fallbacks_total",
    "Nombre de réponses fallback déclenchées après erreur LLM.",
    ["endpoint", "reason"],
)

LLM_REQUEST_DURATION_SECONDS = Histogram(
    "mlops_llm_request_duration_seconds",
    "Durée des appels aux fonctionnalités LLM.",
    ["endpoint"],
)

RAG_RETRIEVED_DOCUMENTS = Histogram(
    "mlops_rag_retrieved_documents",
    "Nombre de documents récupérés par requête RAG.",
    buckets=(0, 1, 2, 3, 4, 5, 8, 10),
)

DATA_DRIFT_SCORE = Gauge(
    "mlops_data_drift_score",
    "Score de dérive statistique des données d'entrée (Z-score max).",
)
