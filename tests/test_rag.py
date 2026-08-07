"""
tests/test_rag.py
──────────────────
Tests unitaires pour le moteur RAG (rag_engine.py).
"""

import pytest
from unittest.mock import MagicMock, patch


class TestRAGEngine:
    """Tests pour la classe RAGEngine."""

    def test_rag_engine_initial_state(self):
        """Le moteur RAG doit être non-chargé à l'initialisation."""
        from src.rag_engine import RAGEngine
        engine = RAGEngine()
        assert engine.is_loaded is False
        assert engine.run_info == {}

    def test_rag_engine_ask_raises_when_not_loaded(self):
        """Poser une question avant chargement doit lever une RuntimeError."""
        from src.rag_engine import RAGEngine
        engine = RAGEngine()
        with pytest.raises(RuntimeError, match="n'est pas encore chargé"):
            engine.ask("Quels sont les horaires de travail ?")

    @patch("src.rag_engine.mlflow")
    @patch("src.rag_engine.FAISS")
    @patch("src.rag_engine.HuggingFaceEmbeddings")
    @patch("src.rag_engine.ChatOllama")
    def test_rag_ask_returns_correct_structure(
        self, mock_ollama, mock_embeddings, mock_faiss, mock_mlflow
    ):
        """La méthode ask() doit retourner un dict avec 'answer' et 'sources'."""
        from src.rag_engine import RAGEngine

        # Configurer les mocks
        mock_retriever = MagicMock()
        mock_retriever.invoke.return_value = [
            MagicMock(metadata={"source": "data/raw/itgate_company_document.txt"})
        ]
        
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = "Les employés travaillent 40 heures par semaine."

        engine = RAGEngine()
        engine._chain = mock_chain  # Injection directe pour le test
        engine._retriever = mock_retriever

        result = engine.ask("Quels sont les horaires de travail ?")

        assert "answer" in result
        assert "sources" in result
        assert isinstance(result["answer"], str)
        assert isinstance(result["sources"], list)
        assert len(result["answer"]) > 0
        assert "data/raw/itgate_company_document.txt" in result["sources"]
