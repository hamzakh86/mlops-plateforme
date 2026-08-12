"""
src/train_rag.py
────────────────
Pipeline d'ingestion de documents pour le système RAG.

Utilise :
  - sentence-transformers (all-MiniLM-L6-v2) pour les embeddings locaux
  - FAISS pour le stockage vectoriel
  - MLflow pour le tracking du pipeline

Cette étape d'ingestion fonctionne hors ligne. La génération de réponses
est ensuite réalisée par Groq au moment de l'inférence.

Usage:
    python src/train_rag.py
    python src/train_rag.py --data-dir data/raw --run-name "RAG_v1"
"""

import argparse
import logging
import os
import sys
from pathlib import Path

import mlflow
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# ─── Charger les variables d'environnement ────────────────────────────────────
load_dotenv()

# ─── Logger ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ─── Configuration ────────────────────────────────────────────────────────────
MLFLOW_TRACKING_URI  = os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")
RAG_EXPERIMENT_NAME  = os.getenv("RAG_EXPERIMENT_NAME", "RAG_Document_QA")
EMBEDDING_MODEL      = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
FAISS_INDEX_PATH     = "data/processed/faiss_index"
CHUNK_SIZE           = 500
CHUNK_OVERLAP        = 50


def load_documents(data_dir: str) -> list:
    """Charge tous les fichiers .txt depuis le dossier de données."""
    logger.info(f"📂 Chargement des documents depuis : {data_dir}")
    loader = DirectoryLoader(
        data_dir,
        glob="**/*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
        show_progress=True,
    )
    docs = loader.load()
    logger.info(f"✅ {len(docs)} document(s) chargé(s).")
    if not docs:
        logger.error(f"❌ Aucun fichier .txt trouvé dans '{data_dir}'.")
        sys.exit(1)
    return docs


def split_documents(docs: list, chunk_size: int, chunk_overlap: int) -> list:
    """Découpe les documents en petits morceaux (chunks) pour la recherche."""
    logger.info(f"✂️  Découpage (chunk_size={chunk_size}, overlap={chunk_overlap})...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunks = splitter.split_documents(docs)
    logger.info(f"✅ {len(chunks)} chunks créés depuis {len(docs)} document(s).")
    return chunks


def build_vectorstore(chunks: list) -> FAISS:
    """Calcule les embeddings locaux (sentence-transformers) et construit l'index FAISS."""
    logger.info(f"🧠 Calcul des embeddings locaux avec '{EMBEDDING_MODEL}' (HuggingFace)...")
    logger.info("   (Premier téléchargement ~90MB — patience...)")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    vectorstore = FAISS.from_documents(chunks, embeddings)
    logger.info("✅ Index vectoriel FAISS construit avec succès.")
    return vectorstore


def save_vectorstore(vectorstore: FAISS, path: str) -> None:
    """Sauvegarde l'index FAISS localement."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(path)
    logger.info(f"💾 Index FAISS sauvegardé dans : {path}")


def main(data_dir: str, run_name: str) -> None:
    """Orchestration complète du pipeline RAG."""

    # ─── Chargement et préparation des documents ──────────────────────────────
    docs   = load_documents(data_dir)
    chunks = split_documents(docs, CHUNK_SIZE, CHUNK_OVERLAP)

    # ─── Construction du vectorstore ──────────────────────────────────────────
    vectorstore = build_vectorstore(chunks)
    save_vectorstore(vectorstore, FAISS_INDEX_PATH)

    # ─── MLflow Tracking ──────────────────────────────────────────────────────
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(RAG_EXPERIMENT_NAME)

    with mlflow.start_run(run_name=run_name) as run:
        mlflow.log_params({
            "data_dir":        data_dir,
            "chunk_size":      CHUNK_SIZE,
            "chunk_overlap":   CHUNK_OVERLAP,
            "embedding_model": EMBEDDING_MODEL,
            "llm_backend":     "Groq (cloud, inference)",
            "num_documents":   len(docs),
            "num_chunks":      len(chunks),
        })
        mlflow.set_tags({
            "pipeline_type": "RAG",
            "vectorstore":   "FAISS",
            "llm_provider":  "Groq (cloud)",
            "embedding_provider": "sentence-transformers (local)",
        })
        mlflow.log_metric("num_documents", len(docs))
        mlflow.log_metric("num_chunks",    len(chunks))
        mlflow.log_metric("avg_chunk_size",
            sum(len(c.page_content) for c in chunks) / len(chunks))

        # Sauvegarder l'index FAISS comme artefact dans MLflow
        mlflow.log_artifacts(FAISS_INDEX_PATH, artifact_path="faiss_index")

        run_id = run.info.run_id
        logger.info(f"✅ Run MLflow créé — run_id={run_id}")
        logger.info(f"📊 MLflow UI : mlflow ui --backend-store-uri {MLFLOW_TRACKING_URI}")
        logger.info("🚀 Index RAG prêt ! Lancez l'API pour poser des questions.")

    return run_id


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Pipeline d'ingestion RAG (sentence-transformers + FAISS locaux)"
    )
    parser.add_argument("--data-dir", type=str, default="data/raw",
                        help="Dossier contenant les documents .txt à ingérer.")
    parser.add_argument("--run-name", type=str, default="RAG_Local_Ingestion",
                        help="Nom du Run MLflow.")
    args = parser.parse_args()
    main(data_dir=args.data_dir, run_name=args.run_name)
