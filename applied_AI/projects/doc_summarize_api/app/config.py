"""
app/config.py
Application-wide settings loaded from environment variables / .env file.
Never import raw os.environ anywhere else — always go through this module.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── OpenRouter / LLM ─────────────────────────────────────────────────────
    openrouter_api_key: str = Field(
        ...,
        description="Bearer token for OpenRouter (required)",
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenAI-compatible base URL for OpenRouter",
    )
    model_slug: str = Field(
        default="meta-llama/llama-3.3-70b-instruct:free",
        description="OpenRouter model identifier",
    )

    # Optional OpenRouter attribution headers
    http_referer: str = Field(default="", description="HTTP-Referer header sent to OpenRouter")
    x_openrouter_title: str = Field(default="", description="X-OpenRouter-Title header")

    # ── LLM request parameters ────────────────────────────────────────────────
    llm_timeout_seconds: int = Field(default=45, description="httpx timeout per LLM call (seconds)")
    llm_max_output_tokens: int = Field(default=1024, description="Max tokens in LLM response")
    llm_temperature: float = Field(default=0.3, description="Sampling temperature (low = deterministic)")

    # ── File upload ───────────────────────────────────────────────────────────
    max_file_size_mb: int = Field(default=2, description="Maximum accepted upload size in MB")

    # ── Chunking ──────────────────────────────────────────────────────────────
    # 131K context window; reserve headroom for prompt template + output tokens.
    # Threshold is set conservatively at ~100K tokens.
    chunk_token_threshold: int = Field(
        default=100_000,
        description="Token count above which text is split into chunks",
    )

    # ── PII ───────────────────────────────────────────────────────────────────
    enable_pii_redaction: bool = Field(
        default=True,
        description="Toggle PII redaction pass before sending text to OpenRouter",
    )

    # ── Rate limiting (our own /summarize endpoint) ───────────────────────────
    rate_limit_per_minute: int = Field(
        default=10,
        description="Max requests per client IP per minute on /summarize",
    )


# Module-level singleton — import and use `settings` everywhere.
settings = Settings()
