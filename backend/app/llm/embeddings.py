"""Embedding backend abstraction.

Two backends:
  - 'local'   : sentence-transformers multilingual-e5-small  (384 dim, ~120 MB, no API key, free)
  - 'openai'  : OpenAI text-embedding-3-small                (1536 dim, $0.02 / 1M tokens)

The default for the demo is `local` — no API key required. To swap to OpenAI you must:
  1. set EMBEDDING_BACKEND=openai
  2. set OPENAI_API_KEY
  3. change embedding_dim in config.py to 1536
  4. migrate the kb_chunks.embedding column to vector(1536) and re-embed.
"""
from __future__ import annotations

import asyncio
from functools import lru_cache

from app.config import get_settings


@lru_cache(maxsize=1)
def _local_model():
    # Lazy import — sentence-transformers + torch are heavy and we don't want to pay the
    # import cost on `EMBEDDING_BACKEND=openai` setups.
    from sentence_transformers import SentenceTransformer

    s = get_settings()
    return SentenceTransformer(s.local_embedding_model)


def _e5_input(texts: list[str]) -> list[str]:
    """multilingual-e5 expects a 'passage: ' prefix for documents (we treat all our chunks
    as passages; queries get 'query: ' in the retriever)."""
    return [f"passage: {t}" for t in texts]


def _embed_local_sync(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    model = _local_model()
    settings = get_settings()
    inputs = _e5_input(texts) if "e5" in settings.local_embedding_model.lower() else texts
    arr = model.encode(inputs, normalize_embeddings=True, show_progress_bar=False)
    return [v.tolist() for v in arr]


async def embed_texts(texts: list[str], model: str | None = None) -> list[list[float]]:
    if not texts:
        return []
    settings = get_settings()
    backend = (settings.embedding_backend or "local").lower()

    if backend == "openai":
        from app.llm.openai_client import embed_texts as _openai_embed
        return await _openai_embed(texts, model=model or settings.openai_embedding_model)

    # 'local' — sentence-transformers in a thread to avoid blocking the event loop.
    return await asyncio.to_thread(_embed_local_sync, texts)


async def embed_query(query: str) -> list[float]:
    """Same backend as embed_texts but with the multilingual-e5 'query: ' prefix when local."""
    settings = get_settings()
    if settings.embedding_backend == "openai":
        return (await embed_texts([query]))[0]

    def _go() -> list[float]:
        model = _local_model()
        text = f"query: {query}" if "e5" in settings.local_embedding_model.lower() else query
        arr = model.encode([text], normalize_embeddings=True, show_progress_bar=False)
        return arr[0].tolist()

    return await asyncio.to_thread(_go)
