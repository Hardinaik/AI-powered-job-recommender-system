class LLMError(Exception):
    """Raised when Groq API call fails for any reason."""
    def __init__(self, message: str, status_code: int = 503):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class EmbeddingError(Exception):
    """Raised when SentenceTransformer encoding fails."""
    pass


class PDFExtractionError(Exception):
    """Raised when PDF text extraction fails."""
    pass