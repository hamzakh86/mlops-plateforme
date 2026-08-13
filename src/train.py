import argparse
import logging
import os
import mlflow
import mlflow.sklearn
import pandas as pd
import numpy as np
from typing import Tuple
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from numpy import ndarray
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.drift import save_baseline_stats

# ─── Logger ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ─── Configuration ─────────────────────────────────────────────────────────────
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")
EXPERIMENT_NAME     = os.getenv("MLFLOW_EXPERIMENT_NAME", "ITGate_Revenue_Forecast")
RANDOM_STATE        = int(os.getenv("RANDOM_STATE", "42"))
DATA_PATH           = "data/raw/itgate_revenue_multivariate.csv"


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Script d'entraînement MLOps — Time Series Multi-varié ITGate.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--n_estimators", type=int, default=100,
                        help="Nombre d'arbres dans la forêt aléatoire.")
    parser.add_argument("--max_depth", type=int, default=10,
                        help="Profondeur maximale de chaque arbre.")
    parser.add_argument("--lags", type=int, default=3,
                        help="Nombre de lags temporels du chiffre d'affaires.")
    parser.add_argument("--run_name", type=str, default="RF_Multivariate_Revenue",
                        help="Nom du Run MLflow.")
    return parser.parse_args()


def prepare_data(lags: int) -> Tuple[ndarray, ndarray, ndarray, ndarray, list, pd.DataFrame]:
    logger.info(f"Chargement du dataset multi-varié ITGate depuis {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)
    
    # Création des Lags sur le revenu
    for i in range(1, lags + 1):
        df[f"lag_{i}"] = df["revenue"].shift(i)
    
    df = df.dropna().reset_index(drop=True)
    
    feature_cols = ["num_engineers", "active_projects", "avg_contract_value"] + [f"lag_{i}" for i in range(1, lags + 1)]
    X = df[feature_cols].values
    y = df["revenue"].values
    
    # Sauvegarde des statistiques de référence pour le Data Drift
    save_baseline_stats(df, feature_cols)
    
    test_size = 12
    X_train, X_test = X[:-test_size], X[-test_size:]
    y_train, y_test = y[:-test_size], y[-test_size:]

    logger.info(f"Données prêtes — Features: {feature_cols} | Train: {X_train.shape[0]} | Test: {X_test.shape[0]}")
    return X_train, X_test, y_train, y_test, feature_cols, df


def compute_metrics(y_true: ndarray, y_pred: ndarray) -> dict:
    return {
        "rmse": round(float(np.sqrt(mean_squared_error(y_true, y_pred))), 2),
        "mae":  round(float(mean_absolute_error(y_true, y_pred)), 2),
        "r2":   round(float(r2_score(y_true, y_pred)), 4),
    }


def train_and_log(
    X_train: ndarray, X_test: ndarray,
    y_train: ndarray, y_test: ndarray,
    feature_cols: list,
    args: argparse.Namespace
) -> str:
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT_NAME)
    logger.info(f"MLflow Tracking URI : {MLFLOW_TRACKING_URI} | Expérience : {EXPERIMENT_NAME}")

    with mlflow.start_run(run_name=args.run_name) as run:
        run_id = run.info.run_id
        logger.info(f"Début du Run MLflow — run_id={run_id}")

        params = {
            "n_estimators": args.n_estimators,
            "max_depth":    args.max_depth,
            "lags":         args.lags,
            "num_features": len(feature_cols),
            "random_state": RANDOM_STATE,
        }
        mlflow.log_params(params)

        logger.info("Entraînement du modèle RandomForestRegressor multi-varié...")
        model = RandomForestRegressor(
            n_estimators=args.n_estimators,
            max_depth=args.max_depth,
            random_state=RANDOM_STATE,
            n_jobs=-1
        )
        model.fit(X_train, y_train)
        logger.info("Modèle entraîné avec succès.")

        predictions = model.predict(X_test)
        metrics = compute_metrics(y_test, predictions)
        logger.info(f"Métriques Évaluation : {metrics}")
        mlflow.log_metrics(metrics)

        mlflow.set_tags({
            "model_type":  "RandomForestRegressor_Multivariate",
            "dataset":     "ITGate_Revenue_Multivariate",
            "environment": "development",
        })

        signature = mlflow.models.signature.infer_signature(X_train, predictions)
        mlflow.sklearn.log_model(
            sk_model=model,
            artifact_path="random_forest_ts_model",
            signature=signature,
            input_example=X_train[:5],
        )
        logger.info(f"Modèle multi-varié enregistré dans MLflow. run_id={run_id}")

    return run_id


def main() -> None:
    args = parse_arguments()
    X_train, X_test, y_train, y_test, feature_cols, _ = prepare_data(args.lags)
    run_id = train_and_log(X_train, X_test, y_train, y_test, feature_cols, args)
    logger.info(f"Pipeline terminé avec succès. run_id={run_id}")


if __name__ == "__main__":
    main()
