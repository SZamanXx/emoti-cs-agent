from __future__ import annotations

from openai import AsyncOpenAI

from app.config import get_settings

_settings = get_settings()
_client: AsyncOpenAI | None = None


def get_openai() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=_settings.openai_api_key)
    return _client


async def embed_texts(texts: list[str], model: str | None = None) -> list[list[float]]:
    if not texts:
        return []
    client = get_openai()
    model_name = model or _settings.openai_embedding_model
    resp = await client.embeddings.create(model=model_name, input=texts)
    return [d.embedding for d in resp.data]
