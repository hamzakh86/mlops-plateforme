"""
src/llm_provider.py
────────────────────
Fabrique centralisée pour le LLM utilisé par la plateforme (Groq, cloud).

Choix architectural : Ollama en local a été abandonné en raison de la
latence trop élevée sur un CPU sans GPU dédié (Intel UHD Graphics intégré).
Groq offre une inférence rapide et gratuite (tier gratuit) via une API
compatible OpenAI, hébergeant des modèles open-source (Llama 3.x).
"""

import logging
import os

logger = logging.getLogger(__name__)


def get_llm(temperature: float = 0.0, json_mode: bool = False):
    """
    Retourne une instance de LLM LangChain connectée à l'API Groq.

    Args:
        temperature: contrôle l'aléatoire de la génération (0.0 = déterministe)
        json_mode: si True, force le LLM à répondre en JSON valide
    """
    from langchain_groq import ChatGroq

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY n'est pas défini dans .env. "
            "Récupérez une clé gratuite sur https://console.groq.com"
        )
    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    logger.info(f"LLM Provider : Groq (cloud) | model={model}")

    kwargs = {"model": model, "api_key": api_key, "temperature": temperature}
    if json_mode:
        kwargs["model_kwargs"] = {"response_format": {"type": "json_object"}}
    return ChatGroq(**kwargs)


def get_current_model_name() -> str:
    """Retourne le nom du modèle actuellement configuré (pour /health, logs, etc.)."""
    return os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")