from __future__ import annotations

import re
from dataclasses import dataclass

import tiktoken
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.llm.embeddings import embed_texts
from app.models.kb import KbChunk, KbDocument

_settings = get_settings()
_enc = tiktoken.get_encoding("cl100k_base")


@dataclass
class ChunkSpec:
    index: int
    content: str
    token_count: int


def _split_text_to_chunks(
    text: str, max_tokens: int = 500, overlap_tokens: int = 50
) -> list[ChunkSpec]:
    text = text.strip()
    if not text:
        return []

    # Split first by paragraph, fall back to sentence, then to token windows.
    paragraphs = re.split(r"\n\s*\n", text)
    pieces: list[str] = []
    for para in paragraphs:
        p = para.strip()
        if not p:
            continue
        if len(_enc.encode(p)) <= max_tokens:
            pieces.append(p)
        else:
            sentences = re.split(r"(?<=[\.\!\?])\s+", p)
            buf: list[str] = []
            buf_tokens = 0
            for s in sentences:
                stoks = len(_enc.encode(s))
                if buf and buf_tokens + stoks > max_tokens:
                    pieces.append(" ".join(buf))
                    buf = [s]
                    buf_tokens = stoks
                else:
                    buf.append(s)
                    buf_tokens += stoks
            if buf:
                pieces.append(" ".join(buf))

    # Now combine adjacent pieces with overlap until each chunk is near max_tokens.
    chunks: list[ChunkSpec] = []
    current: list[str] = []
    current_tokens = 0
    for p in pieces:
        ptoks = len(_enc.encode(p))
        if current and current_tokens + ptoks > max_tokens:
            content = "\n\n".join(current).strip()
            chunks.append(ChunkSpec(index=len(chunks), content=content, token_count=current_tokens))
            # carry overlap (last sentence-ish)
            overlap_text = content[-overlap_tokens * 4 :]  # ~4 chars/token rough
            current = [overlap_text, p]
            current_tokens = len(_enc.encode("\n\n".join(current)))
        else:
            current.append(p)
            current_tokens += ptoks
    if current:
        content = "\n\n".join(current).strip()
        chunks.append(ChunkSpec(index=len(chunks), content=content, token_count=current_tokens))
    return chunks


async def reembed_document(session: AsyncSession, doc: KbDocument) -> KbDocument:
    """Drop existing chunks for a document and re-chunk + re-embed from current body_raw."""
    # Delete old chunks. SQLAlchemy delete via collection load + remove keeps cascade behaviour.
    from sqlalchemy import delete as sqla_delete

    await session.execute(sqla_delete(KbChunk).where(KbChunk.document_id == doc.id))
    await session.flush()

    chunks = _split_text_to_chunks(
        doc.body_raw,
        max_tokens=_settings.chunk_size_tokens,
        overlap_tokens=_settings.chunk_overlap_tokens,
    )
    if not chunks:
        return doc

    embeddings = await embed_texts([c.content for c in chunks])
    for spec, emb in zip(chunks, embeddings, strict=True):
        ch = KbChunk(
            tenant_id=doc.tenant_id,
            document_id=doc.id,
            chunk_index=spec.index,
            content=spec.content,
            token_count=spec.token_count,
            embedding=emb,
            category_tags=doc.category_tags,
        )
        session.add(ch)
    await session.flush()
    return doc


async def ingest_document(
    session: AsyncSession,
    *,
    title: str,
    body: str,
    source_type: str = "md",
    source_url: str | None = None,
    category_tags: list[str] | None = None,
    metadata: dict | None = None,
) -> KbDocument:
    doc = KbDocument(
        tenant_id=_settings.tenant_id,
        title=title,
        source_type=source_type,
        source_url=source_url,
        category_tags=category_tags,
        body_raw=body,
        char_count=len(body),
        extra_metadata=metadata,
    )
    session.add(doc)
    await session.flush()

    chunks = _split_text_to_chunks(
        body,
        max_tokens=_settings.chunk_size_tokens,
        overlap_tokens=_settings.chunk_overlap_tokens,
    )
    if not chunks:
        return doc

    embeddings = await embed_texts([c.content for c in chunks])
    for spec, emb in zip(chunks, embeddings, strict=True):
        ch = KbChunk(
            tenant_id=_settings.tenant_id,
            document_id=doc.id,
            chunk_index=spec.index,
            content=spec.content,
            token_count=spec.token_count,
            embedding=emb,
            category_tags=category_tags,
        )
        session.add(ch)

    await session.flush()
    return doc
