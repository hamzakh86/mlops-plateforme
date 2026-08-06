import argparse
import logging
import mlflow
import mlflow.sklearn
from typing import Tuple
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from numpy import ndarray

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def parse_arguments() -> argparse.Namespace:
    """Analyse les arguments passés en ligne de commande."""
    parser = argparse.ArgumentParser(description="Script d'entraînement MLOps avec MLflow.")
    parser.add_argument("--n_estimators", type=int, default=100, help="Nombre d'arbres dans la forêt.")
    parser.add_argument("--max_depth", type=int, default=None, help="Profondeur maximale de l'arbre.")
    return parser.parse_args()

def prepare_data() -> Tuple[ndarray, ndarray, ndarray, ndarray]:
    """Charge et sépare le dataset Iris en ensembles d'entraînement et de test."""
    logger.info("Chargement du dataset Iris...")
    data = load_iris()
    X, y = data.data, data.target
    
    logger.info("Séparation des données en Train/Test (80/20)...")
    return train_test_split(X, y, test_size=0.2, random_state=42)

def train_and_evaluate(X_train: ndarray, X_test: ndarray, y_train: ndarray, y_test: ndarray, args: argparse.Namespace) -> None:
    """Entraîne le modèle RandomForest et évalue ses performances avec MLflow Tracking."""
    
    # Configuration explicite de la base de données locale pour éviter les problèmes de chemin sous Windows
    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("Iris_Classification")

    with mlflow.start_run():
        logger.info(f"Début de l'entraînement avec n_estimators={args.n_estimators}, max_depth={args.max_depth}")
        
        # 1. Enregistrement des Hyperparamètres
        mlflow.log_params({
            "n_estimators": args.n_estimators,
            "max_depth": args.max_depth,
            "random_state": 42
        })

        # 2. Entraînement du Modèle
        model = RandomForestClassifier(
            n_estimators=args.n_estimators,
            max_depth=args.max_depth,
            random_state=42
        )
        model.fit(X_train, y_train)
        logger.info("Modèle entraîné avec succès.")

        # 3. Prédictions et Évaluation
        predictions = model.predict(X_test)
        metrics = {
            "accuracy": accuracy_score(y_test, predictions),
            "precision": precision_score(y_test, predictions, average='macro'),
            "recall": recall_score(y_test, predictions, average='macro'),
            "f1_score": f1_score(y_test, predictions, average='macro')
        }
        
        logger.info(f"Résultats de l'évaluation : {metrics}")

        # 4. Enregistrement des Métriques
        mlflow.log_metrics(metrics)

        # 5. Enregistrement du Modèle avec sa Signature
        signature = mlflow.models.signature.infer_signature(X_train, predictions)
        mlflow.sklearn.log_model(
            sk_model=model,
            artifact_path="random_forest_model",
            signature=signature,
            input_example=X_train[:5]
        )
        logger.info("Modèle et métriques enregistrés dans MLflow Tracking.")

def main():
    """Point d'entrée principal du script."""
    args = parse_arguments()
    X_train, X_test, y_train, y_test = prepare_data()
    train_and_evaluate(X_train, X_test, y_train, y_test, args)

if __name__ == "__main__":
    main()
