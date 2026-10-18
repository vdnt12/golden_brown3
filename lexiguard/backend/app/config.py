
"""Runtime configuration (single source of truth for hard limits).

Every cap here is a hard limit from the Guide. Changing a default requires an
ADR; changing one at runtime requires an environment variable and must be
recorded in the run ledger / reports.
"""
from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LEXIGUARD_", extra="forbid")

    # --- network surface (loopback only) ---
    host: str = "127.0.0.1"
    port: int = Field(default=8765, ge=1024, le=65535)
    ollama_url: str = "http://127.0.0.1:11434"

    # --- model contract (Guide 3.1, 3.2) ---
    model_tag: str = "gemma4:e4b-it-q4_K_M"
    model_alt_tag: str = "gemma4:e2b-it-q4_K_M"
    # Hermes-family tag served through the same Ollama endpoint. This is a model,
    # not the Hermes Agent framework (ADR-0011).
    hermes_model_tag: str = "hermes3:8b"
    model_digest: str | None = None  # recorded from /api/tags at setup time
    num_ctx: int = 8192
    seed: int = 42
    temperature: float = 0.0
    model_timeout_s: float = 120.0

    # --- ingestion caps (Guide 6) ---
    data_dir: Path = Path("data")
    max_upload_bytes: int = 20 * 1024 * 1024
    max_pages: int = 300
    max_text_chars: int = 2_000_000
    parser_timeout_s: float = 30.0
    parser_output_cap_bytes: int = 20 * 1024 * 1024

    # --- question / runtime caps (Guide 2.3, 8.3) ---
    max_question_chars: int = 500
    max_tool_calls: int = 8
    max_model_calls: int = 4
    max_retrieval_loops: int = 2
    max_chunks_per_call: int = 12
    max_packet_tokens: int = 2500
    max_points: int = 12
    max_sids_per_point: int = 6

    # --- session bootstrap (Guide 11.3) ---
    launch_code_ttl_s: int = 60
    session_ttl_s: int = 8 * 60 * 60

    # --- privacy posture ---
    history_enabled: bool = False  # answer history OFF by default

    @property
    def origin_https(self) -> bool:  # local app is http on loopback only
        return False

    def allowed_hosts(self) -> set[str]:
        return {f"127.0.0.1:{self.port}", f"localhost:{self.port}"}

    def allowed_origins(self) -> set[str]:
        return {f"http://127.0.0.1:{self.port}", f"http://localhost:{self.port}"}


def get_settings() -> Settings:
    """Settings factory. Tests construct Settings(...) directly."""
    return Settings()
