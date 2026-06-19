import logging
import os

from langchain_cerebras import ChatCerebras
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

logger = logging.getLogger("helix.llm")


def build_llm():
    """
    Construye cadena LLM con fallback triple:
    Groq (llama-3.3-70b) → Cerebras (gpt-oss-120b) → Gemini 2.5 Flash
    Cada provider tiene retry=2 antes de pasar al siguiente.
    """
    _assert_keys()

    primary = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=os.environ["GROQ_API_KEY"],
    ).with_retry(stop_after_attempt=2)

    secondary = ChatCerebras(
        model="llama-3.3-70b",
        api_key=os.environ["CEREBRAS_API_KEY"],
    ).with_retry(stop_after_attempt=2)

    tertiary = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.environ["GOOGLE_API_KEY"],
    ).with_retry(stop_after_attempt=2)

    llm = primary.with_fallbacks([secondary, tertiary])
    logger.info("LLM inicializado: Groq → Cerebras → Gemini 2.5 Flash")
    return llm


def _assert_keys() -> None:
    required = ["GROQ_API_KEY", "CEREBRAS_API_KEY", "GOOGLE_API_KEY"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise EnvironmentError(
            f"API keys faltantes: {', '.join(missing)}. "
            "Copiá .env.example → .env y completá los valores."
        )
