import logging
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

OPENAI_MODELS = {"primary": "gpt-4o-mini", "baseline": "gpt-4o-mini", "judge": "gpt-4o-mini"}


class Settings(BaseSettings):
    openai_api_key: str = Field(default="", description="OpenAI API key")

    primary_model: str = ""
    baseline_model: str = ""
    judge_model: str = ""

    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def resolved_provider(self) -> str:
        return "openai"

    @property
    def has_valid_key(self) -> bool:
        """Check if the OpenAI API key is configured (non-empty, non-dummy)."""
        return bool(
            self.openai_api_key
            and self.openai_api_key.startswith("sk-")
            and "test" not in self.openai_api_key
        )

    def get_model_name(self, role: str) -> str:
        """Return the model name for a role (primary/baseline/judge).
        If explicitly set in .env, use that. Otherwise pick OpenAI defaults."""
        explicit = getattr(self, f"{role}_model", "")
        if explicit:
            return explicit
        return OPENAI_MODELS.get(role, OPENAI_MODELS["primary"])


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    logger.info("Provider auto-detected: %s", s.resolved_provider)
    return s


def reset_settings() -> Settings:
    """Clear cached settings and reload from .env. Useful for testing."""
    get_settings.cache_clear()
    return get_settings()
