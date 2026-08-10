"""
tests/test_nlp_engine.py
──────────────────────────
Tests unitaires pour DocumentClassifier et DocumentExtractor.
Le LLM est mocké — aucun appel réel à Ollama ou Groq n'est fait ici,
pour garder les tests rapides et compatibles CI/CD.
"""

import pytest
from unittest.mock import patch, MagicMock
from src.nlp_engine import DocumentClassifier, DocumentExtractor


class TestDocumentClassifier:

    @patch("src.nlp_engine.get_llm")
    def test_classify_returns_valid_category(self, mock_get_llm):
        classifier = DocumentClassifier()
        classifier.chain = MagicMock()
        classifier.chain.invoke.return_value = {"categorie": "Facture"}

        result = classifier.classify(
            "Facture n°123, total 500 TND",
            ["Facture", "CV", "Contrat"],
        )
        assert result == "Facture"

    @patch("src.nlp_engine.get_llm")
    def test_classify_rejects_hallucinated_category(self, mock_get_llm):
        classifier = DocumentClassifier()
        classifier.chain = MagicMock()
        classifier.chain.invoke.return_value = {"categorie": "Devis"}  # hors liste

        result = classifier.classify("texte", ["Facture", "CV", "Contrat"])
        assert result == "Inconnu"

    @patch("src.nlp_engine.get_llm")
    def test_classify_handles_llm_error(self, mock_get_llm):
        classifier = DocumentClassifier()
        classifier.chain = MagicMock()
        classifier.chain.invoke.side_effect = Exception("Ollama timeout")

        result = classifier.classify("texte", ["Facture", "CV"])
        assert result == "Erreur_Classification"

    @patch("src.nlp_engine.get_llm")
    def test_classify_handles_missing_key(self, mock_get_llm):
        classifier = DocumentClassifier()
        classifier.chain = MagicMock()
        classifier.chain.invoke.return_value = {}  # clé "categorie" absente

        result = classifier.classify("texte", ["Facture", "CV"])
        assert result == "Inconnu"


class TestDocumentExtractor:

    @patch("src.nlp_engine.get_llm")
    def test_extract_returns_expected_fields(self, mock_get_llm):
        extractor = DocumentExtractor()
        extractor.chain = MagicMock()
        extractor.chain.invoke.return_value = {
            "montant_total": 1250.5,
            "date": "2026-08-10",
            "fournisseur": "ITGate Group",
        }

        result = extractor.extract(
            "Facture ITGate Group du 10/08/2026. Montant: 1250.50 TND."
        )
        assert result["montant_total"] == 1250.5
        assert result["fournisseur"] == "ITGate Group"
        assert result["date"] == "2026-08-10"

    @patch("src.nlp_engine.get_llm")
    def test_extract_handles_missing_fields(self, mock_get_llm):
        extractor = DocumentExtractor()
        extractor.chain = MagicMock()
        extractor.chain.invoke.return_value = {
            "montant_total": None,
            "date": None,
            "fournisseur": None,
        }

        result = extractor.extract("texte sans info")
        assert result["montant_total"] is None
        assert result["date"] is None
        assert result["fournisseur"] is None

    @patch("src.nlp_engine.get_llm")
    def test_extract_handles_llm_error_gracefully(self, mock_get_llm):
        extractor = DocumentExtractor()
        extractor.chain = MagicMock()
        extractor.chain.invoke.side_effect = Exception("Erreur réseau")

        result = extractor.extract("texte quelconque ici")
        # Doit retourner une structure vide cohérente, pas planter
        assert result == {"montant_total": None, "date": None, "fournisseur": None}

    @patch("src.nlp_engine.get_llm")
    def test_extract_handles_invalid_json_shape(self, mock_get_llm):
        extractor = DocumentExtractor()
        extractor.chain = MagicMock()
        # Le LLM renvoie un champ du mauvais type (string au lieu de float)
        extractor.chain.invoke.return_value = {
            "montant_total": "pas un nombre",
            "date": "2026-08-10",
            "fournisseur": "ITGate Group",
        }

        result = extractor.extract("texte")
        # Pydantic doit rejeter et le except doit retourner la structure vide
        assert result == {"montant_total": None, "date": None, "fournisseur": None}