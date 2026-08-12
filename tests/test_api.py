"""
tests/test_api.py
──────────────────
Tests d'intégration pour l'API FastAPI (serve.py).
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from src.models import User


@pytest.fixture
def mock_model():
    """Modèle mocké pour les tests (pas besoin de MLflow en cours)."""
    model = MagicMock()
    model.predict.return_value = [0, 2]  # setosa, virginica
    return model


@pytest.fixture
def mock_user():
    """Utilisateur mocké pour les tests."""
    user = MagicMock(spec=User)
    user.id = 1
    user.username = "testuser"
    return user


@pytest.fixture
def client(mock_model, mock_user):
    """Client de test FastAPI avec le modèle mocké."""
    import src.serve as serve_module
    import src.auth as auth_module
    
    serve_module._model = mock_model
    serve_module._model_info = {
        "run_id": "test-run-id-12345",
        "accuracy": 0.95,
        "experiment": "Iris_Classification",
    }
    from fastapi.testclient import TestClient
    
    # Le lifespan FastAPI est exécuté par TestClient : on neutralise les chargements externes.
    with patch("src.serve._load_best_model"), \
         patch.object(serve_module._rag_engine, "load_from_mlflow",
                     return_value={"run_id": "test-rag-run", "num_chunks": 0}), \
         patch.object(auth_module.oauth2_scheme, "__call__", return_value="fake-token"), \
         patch("src.auth.get_current_user", new_callable=AsyncMock, return_value=mock_user):
        serve_module._model = mock_model
        serve_module._model_info = {
            "run_id": "test-run-id-12345",
            "accuracy": 0.95,
            "experiment": "Iris_Classification",
        }
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


class TestFrontendEndpoint:
    """Tests pour l'interface web de pilotage."""

    def test_dashboard_returns_html(self, client):
        response = client.get("/")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Plateforme MLOps - ITGate" in response.text
        assert "/assets/" in response.text


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


class TestExtractEndpoint:
    """Tests pour l'endpoint POST /extract."""

    def test_extract_endpoint(self, client):
        with patch("src.serve._extractor.extract") as mock_extract:
            mock_extract.return_value = {
                "montant_total": 1250.5,
                "date": "2026-08-10",
                "fournisseur": "ITGate Group",
            }
            response = client.post(
                "/extract",
                json={"text": "Facture ITGate Group du 10/08/2026. Montant: 1250.50 TND."},
            )
            assert response.status_code == 200
            body = response.json()
            assert body["extracted_data"]["fournisseur"] == "ITGate Group"
            assert "duration_ms" in body

    def test_extract_validation_error_short_text(self, client):
        # min_length=10 sur ExtractRequest.text
        response = client.post("/extract", json={"text": "court"})
        assert response.status_code == 422


class TestClassifyEndpoint:
    """Tests pour l'endpoint POST /classify."""

    def test_classify_endpoint(self, client):
        with patch("src.serve._classifier.classify") as mock_classify:
            mock_classify.return_value = "Facture"
            response = client.post(
                "/classify",
                json={
                    "text": "Facture ITGate Group du 10/08/2026. Montant total: 1250.50 TND.",
                    "categories": ["Facture", "CV", "Contrat", "Rapport"],
                },
            )
            assert response.status_code == 200
            body = response.json()
            assert body["category"] == "Facture"
            assert "duration_ms" in body

    def test_classify_validation_error_single_category(self, client):
        # min_length=2 sur ClassifyRequest.categories
        response = client.post(
            "/classify",
            json={"text": "texte suffisamment long pour passer", "categories": ["Facture"]},
        )
        assert response.status_code == 422

    def test_classify_validation_error_short_text(self, client):
        response = client.post(
            "/classify",
            json={"text": "court", "categories": ["Facture", "CV"]},
        )
        assert response.status_code == 422
