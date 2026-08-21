"""
tests/test_api.py
──────────────────
Tests d'intégration pour l'API FastAPI (serve.py).
"""

import pytest
from datetime import timedelta
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from src.models import User


# ── Helpers JWT ────────────────────────────────────────────────────────────────

def _make_token(username: str = "admin") -> str:
    """Génère un token JWT valide pour les tests (sans base de données)."""
    from src.auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
    return create_access_token(
        data={"sub": username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_model():
    """Modèle mocké pour les tests (pas besoin de MLflow en cours)."""
    model = MagicMock()
    model.predict.side_effect = lambda df: [75400.0] * len(df)
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
    
    serve_module._model = mock_model
    serve_module._model_info = {
        "run_id": "test-run-id-12345",
        "r2": 0.95,
        "experiment": "ITGate_Revenue_Forecast",
    }
    
    from fastapi.testclient import TestClient
    
    # Mock the auth dependencies at the serve module level
    with patch("src.serve._load_best_model"), \
         patch.object(serve_module._rag_engine, "load_from_mlflow",
                     return_value={"run_id": "test-rag-run", "num_chunks": 0}), \
         patch("src.serve.get_current_user", return_value=mock_user):
        serve_module._model = mock_model
        serve_module._model_info = {
            "run_id": "test-run-id-12345",
            "accuracy": 0.95,
            "experiment": "Iris_Classification",
        }
        with TestClient(serve_module.app, raise_server_exceptions=True) as client:
            yield client


@pytest.fixture
def auth_headers():
    """Headers d'authentification Bearer JWT pour les endpoints protégés."""
    token = _make_token()
    return {"Authorization": f"Bearer {token}"}


# ── Tests ──────────────────────────────────────────────────────────────────────

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
        assert any(title in response.text for title in ["Plateforme MLOps - ITGate", "Plateforme MLOps"])
        assert "/assets/" in response.text


class TestPredictEndpoint:
    """Tests pour l'endpoint POST /predict."""

    def test_predict_valid_input(self, client, auth_headers):
        """Une requête valide doit retourner les prédictions financières du chiffre d'affaires."""
        payload = {
            "data": [
                {
                    "num_engineers": 45,
                    "active_projects": 16,
                    "avg_contract_value": 4800.0,
                    "lag_1": 72500.0,
                    "lag_2": 68000.0,
                    "lag_3": 65400.0
                }
            ]
        }
        response = client.post("/predict", json=payload, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        assert "model_run_id" in data
        assert "duration_ms" in data
        assert len(data["predictions"]) == 1
        assert isinstance(data["predictions"][0], (int, float))

    def test_predict_invalid_input_missing_field(self, client, auth_headers):
        """Une requête avec un champ manquant doit retourner 422."""
        payload = {
            "data": [
                {"lag_1": 72500.0}  # champs manquants
            ]
        }
        response = client.post("/predict", json=payload, headers=auth_headers)
        assert response.status_code == 422

    def test_predict_empty_data_list(self, client, auth_headers):
        """Une liste vide de données doit retourner 422."""
        payload = {"data": []}
        response = client.post("/predict", json=payload, headers=auth_headers)
        assert response.status_code == 422


class TestExtractEndpoint:
    """Tests pour l'endpoint POST /extract."""

    def test_extract_endpoint(self, client, auth_headers):
        with patch("src.serve._extractor.extract") as mock_extract:
            mock_extract.return_value = {
                "montant_total": 1250.5,
                "date": "2026-08-10",
                "fournisseur": "ITGate Group",
            }
            response = client.post(
                "/extract",
                json={"text": "Facture ITGate Group du 10/08/2026. Montant: 1250.50 TND."},
                headers=auth_headers,
            )
            assert response.status_code == 200
            body = response.json()
            assert body["extracted_data"]["fournisseur"] == "ITGate Group"
            assert "duration_ms" in body

    def test_extract_validation_error_short_text(self, client, auth_headers):
        # min_length=10 sur ExtractRequest.text
        response = client.post("/extract", json={"text": "court"}, headers=auth_headers)
        assert response.status_code == 422


class TestClassifyEndpoint:
    """Tests pour l'endpoint POST /classify."""

    def test_classify_endpoint(self, client, auth_headers):
        with patch("src.serve._classifier.classify") as mock_classify:
            mock_classify.return_value = "Facture"
            response = client.post(
                "/classify",
                json={
                    "text": "Facture ITGate Group du 10/08/2026. Montant total: 1250.50 TND.",
                    "categories": ["Facture", "CV", "Contrat", "Rapport"],
                },
                headers=auth_headers,
            )
            assert response.status_code == 200
            body = response.json()
            assert body["category"] == "Facture"
            assert "duration_ms" in body

    def test_classify_validation_error_single_category(self, client, auth_headers):
        # min_length=2 sur ClassifyRequest.categories
        response = client.post(
            "/classify",
            json={"text": "texte suffisamment long pour passer", "categories": ["Facture"]},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_classify_validation_error_short_text(self, client, auth_headers):
        response = client.post(
            "/classify",
            json={"text": "court", "categories": ["Facture", "CV"]},
            headers=auth_headers,
        )
        assert response.status_code == 422
