"""
Single source of truth for all heavy model singletons.
Loaded ONCE at FastAPI startup. Import get_llm() / get_embedding_model()
from here instead of re-declaring them in each module.
"""
from app.config import settings
from langchain_groq import ChatGroq
from sentence_transformers import SentenceTransformer

_embedding_model: SentenceTransformer | None = None
_llm: ChatGroq | None = None

def get_llm() -> ChatGroq:
    global _llm
    if _llm is None:
        api_key = settings.API_KEY
        if not api_key:
            raise RuntimeError("GROQ_API_KEY environment variable is not set.")
        _llm = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0,
            groq_api_key=api_key,
        )
    return _llm

def get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedding_model


def preload_models() -> None:
    """
    Call this once at app startup. Forces both models into memory
    so the first real request never pays the cold-start cost.
    """
    get_embedding_model()
    get_llm()
    print(" Models loaded: SentenceTransformer + Groq Lamma")


def cleanup_models() -> None:
    global _llm, _embedding_model
    _llm = None
    _embedding_model = None
    print(" Models unloaded")