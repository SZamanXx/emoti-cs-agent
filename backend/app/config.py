from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    anthropic_model_classifier: str = Field(default="claude-haiku-4-5-20251001", alias="ANTHROPIC_MODEL_CLASSIFIER")
    anthropic_model_drafter: str = Field(default="claude-sonnet-4-6", alias="ANTHROPIC_MODEL_DRAFTER")

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_embedding_model: str = Field(default="text-embedding-3-small", alias="OPENAI_EMBEDDING_MODEL")

    # Embedding backend — "local" (sentence-transformers, no API key) or "openai"
    # Local model is multilingual-e5-small: 384-dim, ~120MB, multilingual including Polish.
    embedding_backend: str = Field(default="local", alias="EMBEDDING_BACKEND")
    local_embedding_model: str = Field(default="intfloat/multilingual-e5-small", alias="LOCAL_EMBEDDING_MODEL")

    database_url: str = Field(
        default="postgresql+asyncpg://emoti:emoti_dev_pwd@localhost:5433/emoti",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6380/0", alias="REDIS_URL")

    api_key: str = Field(default="demo-emoti-key-change-me", alias="API_KEY")
    webhook_hmac_secret: str = Field(default="demo-hmac-secret-change-me", alias="WEBHOOK_HMAC_SECRET")

    tenant_id: str = Field(default="emoti", alias="TENANT_ID")

    ai_draft_enabled: bool = Field(default=True, alias="AI_DRAFT_ENABLED")
    ai_refund_escalation_only: bool = Field(default=True, alias="AI_REFUND_ESCALATION_ONLY")
    auto_reply_enabled: bool = Field(default=False, alias="AUTO_REPLY_ENABLED")

    daily_budget_usd: float = Field(default=5.00, alias="DAILY_BUDGET_USD")

    outbound_webhook_url: str = Field(default="", alias="OUTBOUND_WEBHOOK_URL")
    outbound_webhook_hmac_secret: str = Field(default="", alias="OUTBOUND_WEBHOOK_HMAC_SECRET")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    embedding_dim: int = 384  # multilingual-e5-small. If you swap to text-embedding-3-small, set 1536 + new migration.
    chunk_size_tokens: int = 500
    chunk_overlap_tokens: int = 50
    retriever_top_k: int = 5

    cache_ttl_seconds: int = 3600
    idempotency_ttl_seconds: int = 86400

    classifier_categories: tuple[str, ...] = (
        "voucher_redemption",
        "expired_complaint",
        "refund_request",
        "supplier_dispute",
        "gift_recipient_confusion",
        "other",
    )
    escalation_categories: tuple[str, ...] = ("refund_request", "supplier_dispute")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
