import os
import argparse
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevance
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings

from src.rag_engine import RAGEngine
from dotenv import load_dotenv

load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="Evaluer la qualite du moteur RAG avec Ragas")
    parser.add_argument("--run-name", type=str, default="RAG_Document_QA", help="Nom du run MLflow du RAG")
    args = parser.parse_args()
    
    print("Initialisation du RAG Engine...")
    rag = RAGEngine()
    try:
        rag.load_from_mlflow(os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db"), args.run_name)
    except Exception as e:
        print(f"Erreur lors du chargement du RAG: {e}")
        return
        
    if not rag.is_loaded:
        print("Moteur RAG non charge. Assurez-vous d'avoir lance train_rag.py")
        return

    # Dataset d'evaluation simple pour la CI (eviter le RateLimit Groq)
    eval_questions = [
        "Quelle est l'architecture globale de la plateforme ?",
        "Comment les indisponibilites de l'API Groq sont-elles gerees ?",
    ]
    
    # Ground truth manuel (optionnel pour certaines metriques, mais requis pour d'autres)
    eval_ground_truths = [
        "L'architecture de la plateforme comprend 5 couches : Machine Learning, Backend, Frontend, Orchestration (Kubernetes) et CI/CD.",
        "Les indisponibilites sont gerees par une logique de fallback. La recherche locale continue et renvoie les sources avec un marqueur fallback.",
    ]
    
    print("Generation des reponses via le RAG...")
    answers = []
    contexts = []
    
    for q in eval_questions:
        res = rag.ask(q)
        answers.append(res["answer"])
        # Le retriever FAISS renvoie les documents, on recupere le texte des chunks
        docs = rag.retriever.get_relevant_documents(q)
        contexts.append([doc.page_content for doc in docs])
        
    data = {
        "question": eval_questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": eval_ground_truths,
    }
    
    dataset = Dataset.from_dict(data)
    
    print("Evaluation avec Ragas...")
    # Ragas utilise un LLM et un modele d'embeddings pour evaluer
    eval_llm = ChatGroq(model="llama3-8b-8192")
    eval_embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    result = evaluate(
        dataset = dataset,
        metrics=[
            faithfulness,
            answer_relevance,
        ],
        llm=eval_llm,
        embeddings=eval_embeddings
    )
    
    print("\n--- Resultats de l'evaluation RAG ---")
    print(result)
    print("-------------------------------------")

if __name__ == "__main__":
    main()
