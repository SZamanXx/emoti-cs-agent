"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-04

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")

    op.create_table(
        "tickets",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("channel_thread_id", sa.String(), nullable=True),
        sa.Column("from_email", sa.String(), nullable=True),
        sa.Column("from_phone", sa.String(), nullable=True),
        sa.Column("from_name", sa.String(), nullable=True),
        sa.Column("subject", sa.String(), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("language_hint", sa.String(), nullable=False, server_default="pl"),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("classifier_confidence", sa.Float(), nullable=True),
        sa.Column("classifier_reasoning", sa.Text(), nullable=True),
        sa.Column("suspected_injection", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("injection_signals", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="received"),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_tickets_tenant_id", "tickets", ["tenant_id"])
    op.create_index("ix_tickets_status", "tickets", ["status"])
    op.create_index("ix_tickets_category", "tickets", ["category"])
    op.create_index("ix_tickets_channel_thread_id", "tickets", ["channel_thread_id"])
    op.create_index("ix_tickets_tenant_status", "tickets", ["tenant_id", "status"])
    op.create_index("ix_tickets_tenant_category", "tickets", ["tenant_id", "category"])

    op.create_table(
        "drafts",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("ticket_id", sa.String(), sa.ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("subject", sa.String(), nullable=True),
        sa.Column("body_text", sa.Text(), nullable=False),
        sa.Column("body_html", sa.Text(), nullable=True),
        sa.Column("recipient", sa.String(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("requires_action", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("action_type", sa.String(), nullable=True),
        sa.Column("action_params", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("citations", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("warnings", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("prompt_version", sa.String(), nullable=False),
        sa.Column("model_name", sa.String(), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cached_input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Float(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("edited_body", sa.Text(), nullable=True),
        sa.Column("reviewed_by", sa.String(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_drafts_ticket_id", "drafts", ["ticket_id"])

    op.create_table(
        "ticket_events",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("ticket_id", sa.String(), sa.ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("actor", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ticket_events_ticket_id", "ticket_events", ["ticket_id"])
    op.create_index("ix_ticket_events_event_type", "ticket_events", ["event_type"])

    op.create_table(
        "kb_documents",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("source_url", sa.String(), nullable=True),
        sa.Column("category_tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("body_raw", sa.Text(), nullable=False),
        sa.Column("char_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_kb_documents_tenant_id", "kb_documents", ["tenant_id"])

    op.create_table(
        "kb_chunks",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column(
            "document_id", sa.String(), sa.ForeignKey("kb_documents.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("embedding", Vector(384), nullable=True),
        sa.Column("category_tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_kb_chunks_tenant", "kb_chunks", ["tenant_id"])
    op.create_index("ix_kb_chunks_document_id", "kb_chunks", ["document_id"])
    op.execute(
        "CREATE INDEX ix_kb_chunks_embedding ON kb_chunks USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)"
    )
    op.execute(
        "CREATE INDEX ix_kb_chunks_content_fts ON kb_chunks USING gin (to_tsvector('simple', content))"
    )

    op.create_table(
        "audit_log",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("ticket_id", sa.String(), nullable=True),
        sa.Column("draft_id", sa.String(), nullable=True),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("actor", sa.String(), nullable=True),
        sa.Column("prompt_version", sa.String(), nullable=True),
        sa.Column("model_name", sa.String(), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cached_input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cache_creation_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_audit_tenant_id", "audit_log", ["tenant_id"])
    op.create_index("ix_audit_ticket_id", "audit_log", ["ticket_id"])
    op.create_index("ix_audit_action", "audit_log", ["action"])
    op.create_index("ix_audit_created_at", "audit_log", ["created_at"])
    op.create_index("ix_audit_tenant_created", "audit_log", ["tenant_id", "created_at"])

    op.create_table(
        "killswitches",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("scope", sa.String(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("auto_disabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("last_changed_by", sa.String(), nullable=True),
        sa.Column(
            "last_changed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "scope", name="uq_killswitch_tenant_scope"),
    )
    op.create_index("ix_killswitches_tenant_id", "killswitches", ["tenant_id"])


def downgrade() -> None:
    op.drop_table("killswitches")
    op.drop_table("audit_log")
    op.drop_table("kb_chunks")
    op.drop_table("kb_documents")
    op.drop_table("ticket_events")
    op.drop_table("drafts")
    op.drop_table("tickets")
