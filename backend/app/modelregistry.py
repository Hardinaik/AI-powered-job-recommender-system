from app.config import settings
from app.exceptions import LLMError, EmbeddingError
from langchain_groq import ChatGroq
from sentence_transformers import SentenceTransformer

_embedding_model: SentenceTransformer | None = None
_llm: ChatGroq | None = None

MAX_TOKENS_SAFE = 4096  # llama-3.1-8b-instant context is 8192 — stay safe

def get_llm() -> ChatGroq:
    global _llm
    if _llm is None:
        api_key = settings.API_KEY
        if not api_key:
            raise LLMError("GROQ_API_KEY is not set.", status_code=500)
        _llm = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0,
            groq_api_key=api_key,
            request_timeout=30,     
            max_retries=2,          
        )
    return _llm


def get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        try:
            _embedding_model = SentenceTransformer("all-MiniLM-L6-v2",device="cpu")
        except Exception as e:
            raise EmbeddingError(f"Failed to load SentenceTransformer model: {str(e)}")
    return _embedding_model


def safe_encode(text: str) -> list[float]:
    """
    Encode text with SentenceTransformer safely.
    Handles: empty string, truncation warning, encoding errors.
    all-MiniLM-L6-v2 max token limit is 256 tokens — silently truncates beyond that.
    """
    if not text or not text.strip():
        raise EmbeddingError("Cannot encode empty text — embedding would be meaningless.")

    # Warn if text is very long (will be silently truncated at 256 tokens)
    word_count = len(text.split())
    if word_count > 200:
        print(f"[WARNING] Text has {word_count} words — may be truncated by model (256 token limit).")

    try:
        model = get_embedding_model()
        return model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).tolist()
    except EmbeddingError:
        raise
    except Exception as e:
        raise EmbeddingError(f"Encoding failed: {str(e)}")


def preload_models() -> None:
    get_embedding_model()
    get_llm()
    print("Models loaded: SentenceTransformer + Groq Llama")


def cleanup_models() -> None:
    global _llm, _embedding_model
    _llm = None
    _embedding_model = None
    print("Models unloaded")