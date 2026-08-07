"""
tests/test_api.py
──────────────────
Tests d'intégration pour l'API FastAPI (serve.py).
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def mock_model():
    """Modèle mocké pour les tests (pas besoin de MLflow en cours)."""
    model = MagicMock()
    model.predict.return_value = [0, 2]  # setosa, virginica
    return model


@pytest.fixture
def client(mock_model):
    """Client de test FastAPI avec le modèle mocké."""
    import src.serve as serve_module
    serve_module._model = mock_model
    serve_module._model_info = {
        "run_id": "test-run-id-12345",
        "accuracy": 0.95,
        "experiment": "Iris_Classification",
    }
    from fastapi.testclient import TestClient
    # On utilise le client sans lifespan pour éviter de charger MLflow
    with TestClient(serve_module.app, raise_server_exceptions=True) as client:
        yield client


class TestHealthEndpoint:
    """Tests pour l'endpoint GET /health."""

    def test_health_returns_200(self, client):
        """L'endpoint /health doit retourner 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_structure(self, client):
        """La réponse de /health doit contenir les champs requis."""
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert "model_loaded" in data
        assert "model_info" in data


class TestPredictEndpoint:
    """Tests pour l'endpoint POST /predict."""

    def test_predict_valid_input(self, client):
        """Une requête valide doit retourner les prédictions correctes."""
        payload = {
            "data": [
                {"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2},
                {"sepal_length": 6.7, "sepal_width": 3.0, "petal_length": 5.2, "petal_width": 2.3},
            ]
        }
        response = client.post("/predict", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        assert "model_run_id" in data
        assert "duration_ms" in data
        assert len(data["predictions"]) == 2
        assert data["predictions"][0] == "setosa"
        assert data["predictions"][1] == "virginica"

    def test_predict_invalid_input_missing_field(self, client):
        """Une requête avec un champ manquant doit retourner 422."""
        payload = {
            "data": [
                {"sepal_length": 5.1, "sepal_width": 3.5}  # petal_length et petal_width manquants
            ]
        }
        response = client.post("/predict", json=payload)
        assert response.status_code == 422

    def test_predict_invalid_input_negative_values(self, client):
        """Des valeurs négatives (gt=0) doivent retourner 422."""
        payload = {
            "data": [
                {"sepal_length": -1.0, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}
            ]
        }
        response = client.post("/predict", json=payload)
        assert response.status_code == 422

    def test_predict_empty_data_list(self, client):
        """Une liste vide de données doit retourner 422."""
        payload = {"data": []}
        response = client.post("/predict", json=payload)
        assert response.status_code == 422
