"""
Model factory: creates LangChain ChatOpenAI instances for primary, baseline, and judge roles.
Includes automatic retry with backoff for rate-limited APIs.
"""

import asyncio
import logging
from functools import lru_cache

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI

from app.config import get_settings

logger = logging.getLogger(__name__)

MAX_RETRIES = 2
BASE_DELAY = 1.0


@lru_cache(maxsize=8)
def _build_model(model_name: str, temperature: float = 0.7) -> ChatOpenAI:
    s = get_settings()
    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        api_key=s.openai_api_key,
        request_timeout=30,
        max_retries=MAX_RETRIES,
    )


def get_primary_model(temperature: float = 0.7) -> BaseChatModel:
    s = get_settings()
    return _build_model(s.get_model_name("primary"), temperature)


def get_baseline_model(temperature: float = 0.7) -> BaseChatModel:
    s = get_settings()
    return _build_model(s.get_model_name("baseline"), temperature)


def get_judge_model() -> BaseChatModel:
    """Judge uses temperature=0 for deterministic evaluation."""
    s = get_settings()
    return _build_model(s.get_model_name("judge"), temperature=0.0)


async def invoke_with_retry(chain, inputs: dict, max_retries: int = MAX_RETRIES) -> str:
    """Invoke a chain with exponential backoff retry for rate limits."""
    for attempt in range(max_retries + 1):
        try:
            response = await chain.ainvoke(inputs)
            return response.content.strip()
        except Exception as e:
            error_str = str(e).lower()
            if "rate_limit" in error_str or "429" in error_str:
                if attempt < max_retries:
                    delay = BASE_DELAY * (2 ** attempt)
                    logger.warning(
                        "Rate limited (attempt %d/%d), retrying in %.1fs",
                        attempt + 1, max_retries, delay,
                    )
                    await asyncio.sleep(delay)
                    continue
            raise
    raise RuntimeError("Max retries exceeded")
