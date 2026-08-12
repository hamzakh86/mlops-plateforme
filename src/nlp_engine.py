"""
src/nlp_engine.py
──────────────────
Moteurs NLP pour la classification et l'extraction de documents.
Utilise Groq comme LLM cloud, avec fallback applicatif en cas d'indisponibilité.
"""

import logging
from typing import List, Dict, Any

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel

from src.llm_provider import get_llm
from src.monitoring import LLM_FALLBACKS_TOTAL

logger = logging.getLogger(__name__)


class ExtractionSchema(BaseModel):
    montant_total: float | None = None
    date: str | None = None
    fournisseur: str | None = None


class DocumentClassifier:
    """
    Classifieur Zéro-Shot. Permet de classifier un texte brut
    dans une catégorie prédéfinie, sans entraînement préalable.
    """

    def __init__(self):
        self.prompt = PromptTemplate(
            template="""Tu es un expert en classification de documents.
Classe le document suivant dans EXACTEMENT UNE des catégories de cette liste : {categories}.

DOCUMENT:
{text}

Tu DOIS répondre UNIQUEMENT avec un objet JSON valide contenant une seule clé "categorie" avec la valeur choisie.
Ne rajoute aucun autre texte.
Exemple: {{"categorie": "Facture"}}
""",
            input_variables=["text", "categories"],
        )
        self.llm = None
        self.chain = None
        self.last_error: str | None = None

    def _ensure_chain(self) -> None:
        if self.chain is None:
            self.llm = get_llm(temperature=0.0, json_mode=True)
            self.chain = self.prompt | self.llm | JsonOutputParser()

    def classify(self, text: str, categories: List[str]) -> str:
        logger.info(f"Classification du document ({len(text)} caractères) parmi {categories}...")
        self.last_error = None
        try:
            self._ensure_chain()
            result = self.chain.invoke({
                "text": text,
                "categories": ", ".join(categories),
            })
            category = result.get("categorie", "Inconnu")
            # Garde-fou : rejette toute catégorie hallucinée hors de la liste fournie
            if category not in categories:
                logger.warning(f"Catégorie hors liste renvoyée par le LLM : '{category}'")
                return "Inconnu"
            return category
        except Exception as e:
            logger.error(f"Erreur lors de la classification: {e}")
            self.last_error = type(e).__name__
            LLM_FALLBACKS_TOTAL.labels(endpoint="classify", reason=type(e).__name__).inc()
            return "Erreur_Classification"


class DocumentExtractor:
    """
    Extracteur Zéro-Shot. Permet d'extraire des entités structurées
    d'un document texte, sans entraînement préalable.
    """

    def __init__(self):
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
            input_variables=["text"],
        )
        self.llm = None
        self.chain = None
        self.last_error: str | None = None

    def _ensure_chain(self) -> None:
        if self.chain is None:
            self.llm = get_llm(temperature=0.0, json_mode=True)
            self.chain = self.prompt | self.llm | JsonOutputParser()

    def extract(self, text: str) -> Dict[str, Any]:
        logger.info(f"Extraction des données du document ({len(text)} caractères)...")
        self.last_error = None
        try:
            self._ensure_chain()
            raw = self.chain.invoke({"text": text})
            validated = ExtractionSchema(**raw)
            return validated.model_dump()
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction: {e}")
            self.last_error = type(e).__name__
            LLM_FALLBACKS_TOTAL.labels(endpoint="extract", reason=type(e).__name__).inc()
            # Retourne une structure vide mais cohérente plutôt qu'un dict "erreur"
            # qui casserait la forme attendue par les consommateurs de l'API
            return ExtractionSchema().model_dump()
