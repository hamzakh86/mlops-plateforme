"""
tests/test_train.py
────────────────────
Tests unitaires pour le pipeline d'entraînement ML (train.py).
"""

import subprocess
import sys
import os
import pytest
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.train import prepare_data


class TestTrainPipeline:
    """Tests pour les fonctions du pipeline d'entraînement ITGate Revenue Forecast."""

    def test_revenue_dataset_loads_correctly(self):
        """Vérifie que le dataset ITGate Revenue multi-varié se charge avec les bonnes dimensions."""
        X_train, X_test, y_train, y_test, feature_cols, df = prepare_data(lags=3)
        assert len(feature_cols) == 6, "Le dataset doit comporter 6 features (3 métier + 3 lags)"
        assert len(X_train) > 0, "Les données d'entraînement ne doivent pas être vides"
        assert len(X_test) == 12, "Le jeu de test doit contenir 12 mois"

    def test_model_trains_and_predicts(self):
        """Vérifie qu'un RandomForestRegressor s'entraîne et produit des prédictions financières valides."""
        X_train, X_test, y_train, y_test, feature_cols, df = prepare_data(lags=3)
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        model.fit(X_train, y_train)
        predictions = model.predict(X_test[:5])
        assert len(predictions) == 5
        assert all(p > 0 for p in predictions)

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
