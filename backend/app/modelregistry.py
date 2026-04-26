from app.config import settings
from app.exceptions import LLMError, EmbeddingError
from langchain_groq import ChatGroq
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.api_core.exceptions as google_exceptions

_embedding_model: GoogleGenerativeAIEmbeddings | None = None
_llm: ChatGroq | None = None

GEMINI_EMBEDDING_MODEL = "models/gemini-embedding-001"
EMBEDDING_DIMENSIONS   = 768  # suits LLM-generated summaries (3–6 sentences)


def get_llm() -> ChatGroq:
    global _llm
    if _llm is None:
        api_key = settings.GROQ_API_KEY
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


def get_embedding_model() -> GoogleGenerativeAIEmbeddings:
    global _embedding_model
    if _embedding_model is None:
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise EmbeddingError("GEMINI_API_KEY is not set.")
        try:
            _embedding_model = GoogleGenerativeAIEmbeddings(
                model=GEMINI_EMBEDDING_MODEL,
                google_api_key=api_key,
                task_type="retrieval_document",
            )
        except Exception as e:
            raise EmbeddingError(f"Failed to initialize Gemini embedding model: {str(e)}")
    return _embedding_model


def safe_encode(
    text: str,
    task_type: str = "retrieval_document",
) -> list[float]:
    """
    Encode a single text using gemini-embedding-001 via LangChain.

    task_type for job recommender:
      - "retrieval_document" → job skills, job summary, resume skills,
                               work summary, project summary (indexing side)
      - "retrieval_query"    → only if doing a one-shot live query embedding

    Output: 768-dimensional float vector (MRL truncated from 3072).
    Token limit: ~2048 tokens. Raises EmbeddingError if API fails.
    """
    if not text or not text.strip():
        raise EmbeddingError("Cannot encode empty text — embedding would be meaningless.")

    word_count = len(text.split())
    if word_count > 1200:
        print(f"[WARNING] Text has {word_count} words — may exceed Gemini's 2048 token limit.")

    try:
        if task_type != "retrieval_document":
            model = GoogleGenerativeAIEmbeddings(
                model=GEMINI_EMBEDDING_MODEL,
                google_api_key=settings.GEMINI_API_KEY,
                task_type=task_type,
            )
        else:
            model = get_embedding_model()

        return model.embed_query(
            text,
            output_dimensionality=EMBEDDING_DIMENSIONS,
        )

    except EmbeddingError:
        raise

    # ── Gemini / Google API errors ──────────────────────────────────────────
    except google_exceptions.ResourceExhausted:
        raise EmbeddingError(
            "Gemini embedding service is rate limited. Please try again in a moment."
        )
    except google_exceptions.ServiceUnavailable:
        raise EmbeddingError(
            "Gemini embedding service is temporarily unavailable. Please try again."
        )
    except google_exceptions.DeadlineExceeded:
        raise EmbeddingError(
            "Gemini embedding request timed out. Please try again."
        )
    except google_exceptions.Unauthenticated:
        raise EmbeddingError(
            "Gemini API key is invalid or expired.", 
        )
    except google_exceptions.PermissionDenied:
        raise EmbeddingError(
            "Gemini API key does not have permission to use this model."
        )
    except google_exceptions.InvalidArgument as e:
        raise EmbeddingError(f"Invalid input sent to Gemini: {str(e)}")

    except Exception as e:
        raise EmbeddingError(f"Gemini embedding failed: {str(e)}")


def safe_encode_batch(
    texts: list[str],
    task_type: str = "retrieval_document",
) -> list[list[float]]:
    """
    Batch encode multiple texts.
    Google caps batch size at 100 strings — LangChain handles this internally.

    Use for:
      - Bulk indexing job descriptions
      - Bulk re-embedding resumes
    """
    if not texts:
        raise EmbeddingError("Cannot encode empty list of texts.")

    cleaned = [t for t in texts if t and t.strip()]
    if not cleaned:
        raise EmbeddingError("All provided texts are empty.")

    try:
        if task_type != "retrieval_document":
            model = GoogleGenerativeAIEmbeddings(
                model=GEMINI_EMBEDDING_MODEL,
                google_api_key=settings.GEMINI_API_KEY,
                task_type=task_type,
            )
        else:
            model = get_embedding_model()

        return model.embed_documents(
            cleaned,
            output_dimensionality=EMBEDDING_DIMENSIONS,
        )

    except EmbeddingError:
        raise

    except google_exceptions.ResourceExhausted:
        raise EmbeddingError(
            "Gemini embedding service is rate limited. Please try again in a moment."
        )
    except google_exceptions.ServiceUnavailable:
        raise EmbeddingError(
            "Gemini embedding service is temporarily unavailable. Please try again."
        )
    except google_exceptions.DeadlineExceeded:
        raise EmbeddingError(
            "Gemini embedding request timed out. Please try again."
        )
    except google_exceptions.Unauthenticated:
        raise EmbeddingError(
            "Gemini API key is invalid or expired."
        )
    except google_exceptions.PermissionDenied:
        raise EmbeddingError(
            "Gemini API key does not have permission to use this model."
        )
    except google_exceptions.InvalidArgument as e:
        raise EmbeddingError(f"Invalid input sent to Gemini: {str(e)}")

    except Exception as e:
        raise EmbeddingError(f"Gemini batch embedding failed: {str(e)}")


def preload_models() -> None:
    get_embedding_model()
    get_llm()
    print("Models loaded: gemini-embedding-001 (768-dim, LangChain) + Groq Llama")


def cleanup_models() -> None:
    global _llm, _embedding_model
    _llm = None
    _embedding_model = None
    print("Models unloaded")