from google import genai

from app.core.config import settings


class EmbeddingsClient:
    """Thin wrapper over Gemini text embeddings for Tier-2 similarity.

    Exposes a batch call so a single turn can embed many projects (plus the
    query) in as few round-trips as possible. The underlying genai client is
    created lazily on first use, so merely constructing this (e.g. via FastAPI
    dependency wiring) never reaches the network.
    """

    def __init__(self) -> None:
        self._client: genai.Client | None = None

    @property
    def client(self) -> genai.Client:
        if self._client is None:
            self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return self._client

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed each text, preserving order. Empty input -> empty output."""

        if not texts:
            return []

        response = self.client.models.embed_content(
            model=settings.EMBEDDING_MODEL,
            contents=texts,
        )

        return [list(embedding.values) for embedding in response.embeddings]

    def embed(self, text: str) -> list[float]:
        """Embed a single text."""

        return self.embed_batch([text])[0]
