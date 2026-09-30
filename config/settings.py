"""
config/settings.py
Central configuration loaded from .env
"""
import os
from dotenv import load_dotenv
from dataclasses import dataclass, field

load_dotenv()


@dataclass
class Settings:
    # ── API Keys ──────────────────────────────────────────────────────
    anthropic_api_key: str = field(
        default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", "")
    )
    tavily_api_key: str = field(
        default_factory=lambda: os.getenv("TAVILY_API_KEY", "")
    )

    # ── Model ─────────────────────────────────────────────────────────
    model: str = field(
        default_factory=lambda: os.getenv("AGENT_MODEL", "claude-haiku-4-5-20251001")
    )
    max_tokens: int = 4096

    # ── Agent behaviour ───────────────────────────────────────────────
    max_iterations: int = field(
        default_factory=lambda: int(os.getenv("AGENT_MAX_ITERATIONS", "15"))
    )
    log_level: str = field(
        default_factory=lambda: os.getenv("AGENT_LOG_LEVEL", "INFO")
    )

    # ── Paths ─────────────────────────────────────────────────────────
    memory_dir: str = "./memory/store"
    logs_dir: str = "./logs"
    workspace_dir: str = "./workspace"

    def validate(self) -> None:
        if not self.anthropic_api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is not set.\n"
                "Copy .env.example → .env and add your key."
            )


settings = Settings()
