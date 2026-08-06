import argparse
import logging
import os
import mlflow
import mlflow.sklearn
from typing import Tuple
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
)
from numpy import ndarray

# ─── Logger ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ─── Configuration (lecture depuis variables d'environnement, avec valeurs par défaut) ──
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")
EXPERIMENT_NAME     = os.getenv("MLFLOW_EXPERIMENT_NAME", "Iris_Classification")
TEST_SIZE           = float(os.getenv("TEST_SIZE", "0.2"))
RANDOM_STATE        = int(os.getenv("RANDOM_STATE", "42"))


def parse_arguments() -> argparse.Namespace:
    """Analyse les arguments passés en ligne de commande.
    
    Returns:
        argparse.Namespace: Les arguments parsés.
    """
    parser = argparse.ArgumentParser(
        description="Script d'entraînement MLOps — Plateforme IA ITGate.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--n_estimators", type=int, default=100,
                        help="Nombre d'arbres dans la forêt aléatoire.")
    parser.add_argument("--max_depth", type=int, default=None,
                        help="Profondeur maximale de chaque arbre (None = illimitée).")
    parser.add_argument("--run_name", type=str, default="RandomForest_Iris",
                        help="Nom identifiable du Run dans l'interface MLflow.")
    return parser.parse_args()


def prepare_data() -> Tuple[ndarray, ndarray, ndarray, ndarray]:
    """Charge le dataset Iris et le sépare en ensembles d'entraînement et de test.
    
    Returns:
        Tuple contenant X_train, X_test, y_train, y_test.
    """
    logger.info("Chargement du dataset Iris (150 observations, 4 features, 3 classes)...")
    data = load_iris()
    X, y = data.data, data.target

    logger.info(f"Séparation Train/Test ({int((1-TEST_SIZE)*100)}/{int(TEST_SIZE*100)}) avec random_state={RANDOM_STATE}...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )
    logger.info(f"Données prêtes — Train: {X_train.shape[0]} | Test: {X_test.shape[0]} exemples")
    return X_train, X_test, y_train, y_test


def compute_metrics(y_true: ndarray, y_pred: ndarray) -> dict:
    """Calcule les métriques de classification.
    
    Args:
        y_true: Labels réels.
        y_pred: Labels prédits.
    
    Returns:
        dict: Dictionnaire des métriques calculées.
    """
    return {
        "accuracy":  round(accuracy_score(y_true, y_pred), 4),
        "precision": round(precision_score(y_true, y_pred, average="macro"), 4),
        "recall":    round(recall_score(y_true, y_pred, average="macro"), 4),
        "f1_score":  round(f1_score(y_true, y_pred, average="macro"), 4),
    }


def train_and_log(
    X_train: ndarray, X_test: ndarray,
    y_train: ndarray, y_test: ndarray,
    args: argparse.Namespace
) -> str:
    """Entraîne le modèle RandomForest et log toute l'expérience dans MLflow.
    
    Args:
        X_train, X_test, y_train, y_test: Données d'entraînement et de test.
        args: Hyperparamètres passés en ligne de commande.
    
    Returns:
        str: Le run_id MLflow de l'expérience.
    """
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT_NAME)
    logger.info(f"MLflow Tracking URI : {MLFLOW_TRACKING_URI} | Expérience : {EXPERIMENT_NAME}")

    with mlflow.start_run(run_name=args.run_name) as run:
        run_id = run.info.run_id
        logger.info(f"Début du Run MLflow — run_id={run_id}")

        # ── 1. Log des hyperparamètres ──────────────────────────────────────
        params = {
            "n_estimators": args.n_estimators,
            "max_depth":    args.max_depth,
            "random_state": RANDOM_STATE,
            "test_size":    TEST_SIZE,
        }
        mlflow.log_params(params)
        logger.info(f"Hyperparamètres enregistrés : {params}")

        # ── 2. Entraînement ─────────────────────────────────────────────────
        logger.info("Entraînement du modèle RandomForestClassifier...")
        model = RandomForestClassifier(
            n_estimators=args.n_estimators,
            max_depth=args.max_depth,
            random_state=RANDOM_STATE,
            n_jobs=-1  # Utilise tous les cœurs CPU disponibles
        )
        model.fit(X_train, y_train)
        logger.info("Modèle entraîné avec succès.")

        # ── 3. Évaluation ───────────────────────────────────────────────────
        predictions = model.predict(X_test)
        metrics = compute_metrics(y_test, predictions)
        logger.info(f"Métriques : {metrics}")
        mlflow.log_metrics(metrics)

        # ── 4. Tag descriptif pour retrouver facilement dans l'UI ──────────
        mlflow.set_tags({
            "model_type":  "RandomForestClassifier",
            "dataset":     "Iris",
            "environment": "development",
        })

        # ── 5. Enregistrement du modèle avec signature ──────────────────────
        signature = mlflow.models.signature.infer_signature(X_train, predictions)
        mlflow.sklearn.log_model(
            sk_model=model,
            artifact_path="random_forest_model",
            signature=signature,
            input_example=X_train[:5],
        )
        logger.info(f"Modèle enregistré dans MLflow. run_id={run_id}")

    return run_id


def main() -> None:
    """Point d'entrée principal du pipeline d'entraînement."""
    args   = parse_arguments()
    X_train, X_test, y_train, y_test = prepare_data()
    run_id = train_and_log(X_train, X_test, y_train, y_test, args)
    logger.info(f"Pipeline terminé avec succès. run_id={run_id}")
    logger.info(f"Consultez les résultats sur : mlflow ui --backend-store-uri {MLFLOW_TRACKING_URI}")


if __name__ == "__main__":
    main()
