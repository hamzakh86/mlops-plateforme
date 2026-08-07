"""
tests/test_train.py
────────────────────
Tests unitaires pour le pipeline d'entraînement ML (train.py).
"""

import subprocess
import sys
import pytest
import mlflow
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import load_iris


class TestTrainPipeline:
    """Tests pour les fonctions du pipeline d'entraînement."""

    def test_iris_dataset_loads_correctly(self):
        """Vérifie que le dataset Iris se charge avec les bonnes dimensions."""
        iris = load_iris()
        X, y = iris.data, iris.target
        assert X.shape == (150, 4), "Le dataset Iris doit avoir 150 lignes et 4 features"
        assert len(np.unique(y)) == 3, "Il doit y avoir 3 classes"
        assert y.min() == 0 and y.max() == 2

    def test_model_trains_and_predicts(self):
        """Vérifie qu'un RandomForest s'entraîne et produit des prédictions valides."""
        iris = load_iris()
        X, y = iris.data, iris.target
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X, y)
        predictions = model.predict(X[:5])
        assert len(predictions) == 5
        assert all(p in [0, 1, 2] for p in predictions)

    def test_model_accuracy_above_threshold(self):
        """Vérifie que le modèle atteint un minimum d'accuracy sur Iris."""
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score
        iris = load_iris()
        X, y = iris.data, iris.target
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        acc = accuracy_score(y_test, model.predict(X_test))
        assert acc >= 0.85, f"Accuracy trop faible : {acc:.2f} (minimum requis: 0.85)"

    def test_train_script_runs_successfully(self):
        """Vérifie que le script train.py s'exécute sans erreur."""
        result = subprocess.run(
            [sys.executable, "src/train.py", "--run_name", "pytest_run"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, f"train.py a échoué :\n{result.stderr}"
        assert "Pipeline termin" in result.stderr
