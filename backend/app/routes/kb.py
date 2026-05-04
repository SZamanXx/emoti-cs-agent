from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_session
from app.models.kb import KbChunk, KbDocument
from app.schemas.kb import KbDocumentFull, KbDocumentOut, KbSearchHit, KbUpdateIn, KbUploadIn
from app.security.api_key import require_api_key
from app.services import retriever as retriever_service
from app.services.kb_ingest import ingest_document, reembed_document

router = APIRouter(prefix="/api/v1/kb", tags=["kb"])
_settings = get_settings()


async def _get_doc_or_404(session: AsyncSession, document_id: str) -> KbDocument:
    stmt = select(KbDocument).where(
        KbDocument.id == document_id, KbDocument.tenant_id == _settings.tenant_id
    )
    res = await session.execute(stmt)
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="document not found")
    return doc


async def _doc_full(session: AsyncSession, doc: KbDocument) -> KbDocumentFull:
    count = (
        await session.execute(
            select(func.count(KbChunk.id)).where(KbChunk.document_id == doc.id)
        )
    ).scalar_one()
    return KbDocumentFull(
        id=doc.id,
        title=doc.title,
        source_type=doc.source_type,
        source_url=doc.source_url,
        category_tags=doc.category_tags,
        summary=doc.summary,
        char_count=doc.char_count,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        body_raw=doc.body_raw,
        chunk_count=int(count or 0),
    )


@router.post("/documents", response_model=KbDocumentOut)
async def upload_document(
    payload: KbUploadIn,
    api_key: str = Depends(require_api_key),
    session: AsyncSession = Depends(get_session),
):
    doc = await ingest_document(
        session,
        title=payload.title,
        body=payload.body,
        source_type=payload.source_type,
        source_url=payload.source_url,
        category_tags=payload.category_tags,
        metadata=payload.metadata,
    )
    await session.commit()
    return doc


@router.get("/documents", response_model=list[KbDocumentOut])
async def list_documents(
    api_key: str = Depends(require_api_key),
    session: AsyncSession = Depends(get_session),
):
    stmt = (
        select(KbDocument)
        .where(KbDocument.tenant_id == _settings.tenant_id)
        .order_by(KbDocument.created_at.desc())
    )
    res = await session.execute(stmt)
    return list(res.scalars().all())


@router.get("/documents/{document_id}", response_model=KbDocumentFull)
async def get_document(
    document_id: str,
    api_key: str = Depends(require_api_key),
    session: AsyncSession = Depends(get_session),
):
    doc = await _get_doc_or_404(session, document_id)
    return await _doc_full(session, doc)


@router.put("/documents/{document_id}", response_model=KbDocumentFull)
async def update_document(
    document_id: str,
    payload: KbUpdateIn,
    api_key: str = Depends(require_api_key),
    session: AsyncSession = Depends(get_session),
):
    doc = await _get_doc_or_404(session, document_id)

    body_changed = payload.body is not None and payload.body != doc.body_raw

    if payload.title is not None:
        doc.title = payload.title
    if payload.body is not None:
        doc.body_raw = payload.body
        doc.char_count = len(payload.body)
    if payload.category_tags is not None:
        doc.category_tags = payload.category_tags
    if payload.source_url is not None:
        doc.source_url = payload.source_url

    if body_changed:
        await reembed_document(session, doc)
    elif payload.category_tags is not None:
        from sqlalchemy import update as sqla_update

        await session.execute(
            sqla_update(KbChunk)
            .where(KbChunk.document_id == doc.id)
            .values(category_tags=payload.category_tags)
        )

    await session.commit()
    return await _doc_full(session, doc)


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    api_key: str = Depends(require_api_key),
    session: AsyncSession = Depends(get_session),
):
    doc = await _get_doc_or_404(session, document_id)
    await session.delete(doc)
    await session.commit()
    return {"ok": True}


@router.get("/search", response_model=list[KbSearchHit])
async def search_kb(
    q: str,
    category: str | None = None,
    top_k: int = 5,
    api_key: str = Depends(require_api_key),
    session: AsyncSession = Depends(get_session),
):
    chunks = await retriever_service.retrieve(session, query=q, category=category, top_k=top_k)
    return [
        KbSearchHit(
            chunk_id=c.chunk_id,
            document_id=c.document_id,
            document_title=c.document_title,
            content=c.content,
            relevance=c.relevance,
            category_tags=c.category_tags,
        )
        for c in chunks
    ]
