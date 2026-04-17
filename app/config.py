import logging
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

OPENAI_MODELS = {"primary": "gpt-4o-mini", "baseline": "gpt-3.5-turbo", "judge": "gpt-4o"}


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
        """True when the key looks real (starts with sk-, isn't a test stub)."""
        return bool(
            self.openai_api_key
            and self.openai_api_key.startswith("sk-")
            and "test" not in self.openai_api_key
        )

    def get_model_name(self, role: str) -> str:
        """Look up model for a given role; falls back to OPENAI_MODELS defaults."""
        explicit = getattr(self, f"{role}_model", "")
        if explicit:
            return explicit
        return OPENAI_MODELS.get(role, OPENAI_MODELS["primary"])


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    logger.info("Provider auto-detected: %s", s.resolved_provider)
    return s


