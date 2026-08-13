import json
import os
import numpy as np
import pandas as pd
from typing import Dict, Any

BASELINE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "drift_baseline.json")

def save_baseline_stats(df: pd.DataFrame, feature_cols: list, file_path: str = BASELINE_PATH):
    """Calcule et sauvegarde les statistiques de référence (moyenne, std, min, max) pour la détection de drift."""
    stats = {}
    for col in feature_cols:
        stats[col] = {
            "mean": float(df[col].mean()),
            "std": float(df[col].std()),
            "min": float(df[col].min()),
            "max": float(df[col].max())
        }
    
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    print(f"Statistiques de référence pour le Data Drift sauvegardées dans : {file_path}")


def detect_data_drift(current_df: pd.DataFrame, file_path: str = BASELINE_PATH, threshold: float = 2.5) -> Dict[str, Any]:
    """Détecte la dérive statistique des données d'inférence par rapport aux statistiques d'entraînement.
    
    Returns:
        dict avec score global de drift, statut (normal/drift_detected) et détails par feature.
    """
    if not os.path.exists(file_path):
        return {
            "drift_detected": False,
            "drift_score": 0.0,
            "message": "Fichier de référence baseline non trouvé.",
            "details": {}
        }
    
    with open(file_path, "r", encoding="utf-8") as f:
        baseline_stats = json.load(f)
    
    details = {}
    max_z_scores = []
    
    for col, base in baseline_stats.items():
        if col in current_df.columns:
            val = current_df[col].mean()
            std = base["std"] if base["std"] > 0 else 1.0
            # Score de déviation Z-score
            z_score = abs(val - base["mean"]) / std
            is_drifted = z_score > threshold
            max_z_scores.append(z_score)
            
            details[col] = {
                "observed_mean": round(float(val), 2),
                "baseline_mean": round(base["mean"], 2),
                "z_score": round(float(z_score), 2),
                "drift": bool(is_drifted)
            }
    
    global_drift_score = round(float(np.max(max_z_scores)), 2) if max_z_scores else 0.0
    drift_detected = global_drift_score > threshold
    
    return {
        "drift_detected": drift_detected,
        "drift_score": global_drift_score,
        "status": "DRIFT_DETECTED" if drift_detected else "NORMAL",
        "threshold": threshold,
        "details": details
    }
