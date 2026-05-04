"""Seed tickets from D:/Python/emoti_test/code/sample_data/tickets.jsonl.

Each line is a JSON object with:
- id, channel, from, subject, body
- expected_category, expected_action  (used by eval harness)
- notes  (free-form rationale)

We persist `expected_*` in ticket.extra_metadata so the eval script can compute accuracy.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from app.config import get_settings
from app.db import SessionLocal
from app.models.ticket import Ticket
from app.services.audit import write_audit
from app.services.pipeline import run_pipeline

DATA_DIR = Path("/app/sample_data")
if not DATA_DIR.exists():
    DATA_DIR = Path(__file__).resolve().parents[3] / "sample_data"

_settings = get_settings()


async def main(only_ingest: bool = False) -> None:
    path = DATA_DIR / "tickets.jsonl"
    if not path.exists():
        path = DATA_DIR / "tickets.json"  # fallback if user uses single-array form
    print(f"[seed_tickets] reading {path}")

    items: list[dict] = []
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".jsonl":
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    else:
        items = json.loads(text)

    async with SessionLocal() as session:
        for item in items:
            channel = item.get("channel") or item.get("source") or "form"
            sender_email = item.get("from")
            sender_name = item.get("from_name")

            t = Ticket(
                tenant_id=_settings.tenant_id,
                source=channel,
                channel_thread_id=item.get("channel_thread_id"),
                from_email=sender_email if sender_email and "@" in sender_email else None,
                from_phone=item.get("from_phone"),
                from_name=sender_name,
                subject=item.get("subject"),
                body=item["body"],
                language_hint=item.get("language_hint", "pl"),
                received_at=datetime.now(timezone.utc),
                extra_metadata={
                    "external_id": item.get("id"),
                    "expected_category": item.get("expected_category"),
                    "expected_action": item.get("expected_action"),
                    "notes": item.get("notes"),
                },
                status="received",
            )
            session.add(t)
            await session.flush()
            await write_audit(session, action="ticket_received", ticket_id=t.id, actor="seed")
            label = item.get("id") or t.id
            print(f"[seed_tickets] ingested {label} -> {t.id}")
            if not only_ingest:
                try:
                    outcome = await run_pipeline(session, t)
                    print(f"  -> pipeline: {outcome.status} (esc={outcome.escalation_reason})")
                except Exception as exc:  # noqa: BLE001
                    print(f"  -> pipeline FAILED: {exc!r}")
            await session.commit()


if __name__ == "__main__":
    import sys
    only_ingest = "--only-ingest" in sys.argv
    asyncio.run(main(only_ingest=only_ingest))
