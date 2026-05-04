"""Seed KB from D:/Python/emoti_test/code/kb_seed/ (mounted as /app/kb_seed in Docker).

Each markdown file may have YAML frontmatter (---...---) with fields:
- doc_id, title, category, applies_to (list), language, version, ai_draft_allowed, sensitivity.

`applies_to` is used as category_tags for the chunks (drives the retriever's category boost).
"""
from __future__ import annotations

import asyncio
import re
from pathlib import Path

import yaml

from app.db import session_scope
from app.services.kb_ingest import ingest_document

KB_DIR = Path("/app/kb_seed")
if not KB_DIR.exists():
    KB_DIR = Path(__file__).resolve().parents[3] / "kb_seed"


_FRONTMATTER_RE = re.compile(r"^---\n(.+?)\n---\n", re.DOTALL)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        meta = {}
    body = text[m.end() :]
    return meta, body


async def main() -> None:
    print(f"[seed_kb] reading from {KB_DIR}")
    files = sorted(p for p in KB_DIR.glob("*.md") if p.name != "README.md")
    if not files:
        print("[seed_kb] no markdown files found")
        return
    async with session_scope() as session:
        for f in files:
            raw = f.read_text(encoding="utf-8")
            meta, body = parse_frontmatter(raw)
            title = meta.get("title") or f.stem.replace("_", " ").title()
            tags = meta.get("applies_to") or []
            if isinstance(tags, str):
                tags = [tags]
            doc = await ingest_document(
                session,
                title=str(title),
                body=body if body.strip() else raw,
                source_type="md",
                source_url=f"file://{f.name}",
                category_tags=[str(t) for t in tags],
                metadata={
                    "doc_id": meta.get("doc_id"),
                    "category": meta.get("category"),
                    "version": meta.get("version"),
                    "ai_draft_allowed": meta.get("ai_draft_allowed"),
                    "sensitivity": meta.get("sensitivity"),
                    "language": meta.get("language", "pl"),
                },
            )
            print(f"[seed_kb] ingested {f.name} -> {doc.id} (tags={tags})")
    print("[seed_kb] done")


if __name__ == "__main__":
    asyncio.run(main())
