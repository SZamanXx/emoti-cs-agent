from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.llm.embeddings import embed_query

_settings = get_settings()


@dataclass
class RetrievedChunk:
    chunk_id: str
    document_id: str
    document_title: str
    content: str
    relevance: float
    category_tags: list[str] | None


async def retrieve(
    session: AsyncSession,
    *,
    query: str,
    category: str | None = None,
    top_k: int | None = None,
) -> list[RetrievedChunk]:
    if not query.strip():
        return []
    top_k = top_k or _settings.retriever_top_k

    embedding_vec = await embed_query(query)
    embedding_literal = "[" + ",".join(f"{x:.7f}" for x in embedding_vec) + "]"

    sql = text(
        """
        WITH cosine AS (
            SELECT
                c.id AS chunk_id,
                c.document_id,
                c.content,
                c.category_tags,
                d.title AS document_title,
                1 - (c.embedding <=> CAST(:emb AS vector)) AS score,
                'cosine' AS source
            FROM kb_chunks c
            JOIN kb_documents d ON d.id = c.document_id
            WHERE c.tenant_id = :tenant
            ORDER BY c.embedding <=> CAST(:emb AS vector)
            LIMIT :k
        ),
        fts AS (
            SELECT
                c.id AS chunk_id,
                c.document_id,
                c.content,
                c.category_tags,
                d.title AS document_title,
                ts_rank(to_tsvector('simple', c.content), plainto_tsquery('simple', :q)) AS score,
                'fts' AS source
            FROM kb_chunks c
            JOIN kb_documents d ON d.id = c.document_id
            WHERE c.tenant_id = :tenant
              AND to_tsvector('simple', c.content) @@ plainto_tsquery('simple', :q)
            ORDER BY score DESC
            LIMIT :k
        )
        SELECT * FROM cosine
        UNION ALL
        SELECT * FROM fts
        """
    ).bindparams(
        bindparam("emb", value=embedding_literal),
        bindparam("q", value=query),
        bindparam("tenant", value=_settings.tenant_id),
        bindparam("k", value=top_k),
    )

    rows = (await session.execute(sql)).mappings().all()

    by_chunk: dict[str, dict] = {}
    for r in rows:
        cid = r["chunk_id"]
        if cid not in by_chunk or r["score"] > by_chunk[cid]["score"]:
            by_chunk[cid] = dict(r)

    if category:
        # Lift chunks tagged for this category
        for r in by_chunk.values():
            tags = r.get("category_tags") or []
            if isinstance(tags, list) and category in tags:
                r["score"] = float(r["score"]) + 0.1

    sorted_chunks = sorted(by_chunk.values(), key=lambda r: float(r["score"]), reverse=True)[:top_k]

    return [
        RetrievedChunk(
            chunk_id=r["chunk_id"],
            document_id=r["document_id"],
            document_title=r["document_title"],
            content=r["content"],
            relevance=float(r["score"]),
            category_tags=r.get("category_tags"),
        )
        for r in sorted_chunks
    ]


def format_kb_context(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return ""
    parts: list[str] = []
    for ch in chunks:
        parts.append(
            f'<chunk id="{ch.chunk_id}" doc="{ch.document_title}" relevance="{ch.relevance:.3f}">\n'
            f"{ch.content.strip()}\n"
            f"</chunk>"
        )
    return "\n\n".join(parts)
