from openai import OpenAI

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class OpenAIClient:
    def __init__(self) -> None:
        self._client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    @property
    def enabled(self) -> bool:
        return self._client is not None

    def embed(self, text: str) -> list[float]:
        if not self._client:
            return [0.0] * 1536
        response = self._client.embeddings.create(
            model="text-embedding-3-small",
            input=text[:8000],
        )
        return response.data[0].embedding

    def chat(self, system: str, user: str) -> str:
        if not self._client:
            logger.info("openai_stub", user_preview=user[:120])
            return (
                "Stub AI response (set OPENAI_API_KEY). "
                "Review recent deploys, check error rates, and follow matched runbooks."
            )
        response = self._client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content or ""


openai_client = OpenAIClient()
