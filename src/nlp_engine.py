import logging
import os
import json
from typing import List, Dict, Any

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DocumentClassifier:
    """
    Classifieur Zéro-Shot utilisant Ollama (phi3:mini).
    Permet de classifier un texte brut dans une catégorie prédéfinie.
    """

    def __init__(self):
        self._ollama_model = os.getenv("OLLAMA_MODEL", "phi3:mini")
        self._ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        self.llm = ChatOllama(
            model=self._ollama_model,
            base_url=self._ollama_base_url,
            temperature=0.0,  # Déterministe
            format="json",    # Force Ollama à répondre en JSON
        )

        self.prompt = PromptTemplate(
            template="""Tu es un expert en classification de documents.
Classe le document suivant dans EXACTEMENT UNE des catégories de cette liste : {categories}.

DOCUMENT:
{text}

Tu DOIS répondre UNIQUEMENT avec un objet JSON valide contenant une seule clé "categorie" avec la valeur choisie. 
Ne rajoute aucun autre texte.
Exemple: {{"categorie": "Facture"}}
""",
            input_variables=["text", "categories"]
        )

        self.chain = self.prompt | self.llm | JsonOutputParser()

    def classify(self, text: str, categories: List[str]) -> str:
        logger.info(f"Classification du document ({len(text)} caractères) parmi {categories}...")
        try:
            result = self.chain.invoke({
                "text": text,
                "categories": ", ".join(categories)
            })
            return result.get("categorie", "Inconnu")
        except Exception as e:
            logger.error(f"Erreur lors de la classification: {e}")
            return "Erreur_Classification"


class DocumentExtractor:
    """
    Extracteur Zéro-Shot utilisant Ollama (phi3:mini).
    Permet d'extraire des entités d'un document texte.
    """

    def __init__(self):
        self._ollama_model = os.getenv("OLLAMA_MODEL", "phi3:mini")
        self._ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        self.llm = ChatOllama(
            model=self._ollama_model,
            base_url=self._ollama_base_url,
            temperature=0.0,
            format="json", # Force la sortie JSON
        )

        self.prompt = PromptTemplate(
            template="""Tu es un assistant expert en extraction d'informations.
Extrais les données suivantes du document. 

SI UNE INFORMATION N'EST PAS PRÉSENTE, mets la valeur null.

DOCUMENT:
{text}

Tu DOIS répondre UNIQUEMENT avec un objet JSON valide selon ce format exact :
{{"montant_total": float ou null, "date": "YYYY-MM-DD" ou null, "fournisseur": "nom" ou null}}
Ne rajoute aucun autre texte.
""",
            input_variables=["text"]
        )

        self.chain = self.prompt | self.llm | JsonOutputParser()

    def extract(self, text: str) -> Dict[str, Any]:
        logger.info(f"Extraction des données du document ({len(text)} caractères)...")
        try:
            return self.chain.invoke({"text": text})
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction: {e}")
            return {"erreur": str(e)}
