"""
src/rag_engine.py
──────────────────
Moteur RAG (Retrieval-Augmented Generation).

Utilise :
  - sentence-transformers (all-MiniLM-L6-v2) pour les embeddings (local)
  - FAISS (chargé depuis MLflow) pour la recherche de contexte (local)
  - Groq (cloud) pour la génération de réponses

Nécessite une clé API Groq gratuite (voir .env.example).
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Optional

import mlflow
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_huggingface import HuggingFaceEmbeddings
from src.llm_provider import get_llm
from src.monitoring import LLM_FALLBACKS_TOTAL, RAG_RETRIEVED_DOCUMENTS

logger = logging.getLogger(__name__)

# ─── Template du Prompt ───────────────────────────────────────────────────────
RAG_PROMPT_TEMPLATE = """
Tu es un assistant IA expert qui répond aux questions en te basant UNIQUEMENT sur le contexte fourni ci-dessous.
Si la réponse ne se trouve pas dans le contexte, dis clairement : "Cette information ne se trouve pas dans les documents fournis."
Ne fabrique jamais de réponse. Sois précis, concis et professionnel.

CONTEXTE :
{context}

QUESTION : {question}

RÉPONSE :
"""

rag_prompt = PromptTemplate.from_template(RAG_PROMPT_TEMPLATE)


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


class RAGEngine:
    """
    Moteur RAG : charge l'index FAISS depuis MLflow,
    utilise Groq (cloud) pour la génération de réponses.
    """

    def __init__(self):
        self._chain = None
        self._retriever = None
        self._run_info: dict = {}
        self._embedding_model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    def load_from_mlflow(self, tracking_uri: str, experiment_name: str) -> dict:
        """
        Charge le dernier run RAG depuis MLflow et reconstruit la chaîne Q&A.
        """
        mlflow.set_tracking_uri(tracking_uri)
        client = mlflow.tracking.MlflowClient()

        experiment = client.get_experiment_by_name(experiment_name)
        if experiment is None:
            raise RuntimeError(
                f"Expérience MLflow '{experiment_name}' introuvable. "
                f"Lancez d'abord : python src/train_rag.py"
            )

        runs = client.search_runs(
            experiment_ids=[experiment.experiment_id],
            filter_string="status = 'FINISHED'",
            order_by=["start_time DESC"],
            max_results=1,
        )
        if not runs:
            raise RuntimeError(
                f"Aucun run terminé trouvé dans '{experiment_name}'. "
                f"Lancez d'abord : python src/train_rag.py"
            )

        run = runs[0]
        run_id = run.info.run_id
        logger.info(f"Chargement du Run RAG MLflow — run_id={run_id}")

        # Télécharger l'index FAISS depuis les artefacts MLflow
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_path = client.download_artifacts(run_id, "faiss_index", tmpdir)
            faiss_dir = Path(artifact_path)

            # Embeddings locaux
            logger.info(f"Chargement des embeddings locaux ({self._embedding_model})...")
            embeddings = HuggingFaceEmbeddings(
                model_name=self._embedding_model,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )

            vectorstore = FAISS.load_local(
                str(faiss_dir),
                embeddings,
                allow_dangerous_deserialization=True,
            )

        # Initialiser le LLM (Groq, cloud)
        llm = get_llm(temperature=0.2)

        self._retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

        # Construire la chaîne RAG moderne (LCEL)
        self._chain = (
            {"context": self._retriever | format_docs, "question": RunnablePassthrough()}
            | rag_prompt
            | llm
            | StrOutputParser()
        )

        llm_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

        self._run_info = {
            "run_id":            run_id,
            "num_documents":     int(run.data.metrics.get("num_documents", 0)),
            "num_chunks":        int(run.data.metrics.get("num_chunks", 0)),
            "embedding_model":   self._embedding_model,
            "llm_provider":      "groq",
            "llm_model":         llm_model,
        }
        logger.info(
            f"✅ Moteur RAG prêt. Provider=groq | LLM={llm_model} | "
            f"Embeddings={self._embedding_model} | Chunks={self._run_info['num_chunks']}"
        )
        return self._run_info

    def ask(self, question: str) -> dict:
        """Pose une question au moteur RAG et retourne la réponse + les sources."""
        if self._chain is None or self._retriever is None:
            raise RuntimeError("Le moteur RAG n'est pas encore chargé.")

        logger.info(f"❓ Question : {question[:80]}...")

        # 1. Retrieve the documents locally
        docs = self._retriever.invoke(question)
        RAG_RETRIEVED_DOCUMENTS.observe(len(docs))

        # 2. Generate the answer using Groq, with a degraded fallback if needed
        fallback = False
        try:
            answer = self._chain.invoke(question)
        except Exception as e:
            logger.error(f"Erreur LLM pendant la génération RAG: {e}")
            LLM_FALLBACKS_TOTAL.labels(endpoint="ask", reason=type(e).__name__).inc()
            fallback = True
            if docs:
                answer = (
                    "Le service LLM Groq est indisponible ou limité pour le moment. "
                    "Voici les sources locales les plus pertinentes retrouvées par FAISS ; "
                    "relancez la question lorsque le service sera disponible."
                )
            else:
                answer = (
                    "Le service LLM Groq est indisponible ou limité pour le moment, "
                    "et aucun document pertinent n'a été retrouvé localement."
                )

        # 3. Extract the sources
        sources = [doc.metadata.get("source", "Inconnu") for doc in docs]
        unique_sources = list(dict.fromkeys(sources))

        logger.info(f"✅ Réponse générée. Sources : {unique_sources}")
        return {"answer": answer, "sources": unique_sources, "fallback": fallback}

    @property
    def is_loaded(self) -> bool:
        return self._chain is not None

    @property
    def run_info(self) -> dict:
        return self._run_info
