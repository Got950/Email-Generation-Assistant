"""
LangChain chains for email generation.

Two strategies:
  - AdvancedEmailChain: CoT + Few-Shot + Role-Play with self-reflection critic loop
  - BaselineEmailChain: Zero-shot simple prompt
"""

import logging
import re
from dataclasses import dataclass

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

from app.config import get_settings
from app.core.models import _build_model, get_baseline_model, get_primary_model, invoke_with_retry
from app.core.prompts import (
    build_advanced_prompt,
    build_baseline_prompt,
    build_critic_prompt,
)

logger = logging.getLogger(__name__)

_SUBJECT_RE = re.compile(r"(?i)^subject\s*:", re.MULTILINE)


@dataclass
class GenerationResult:
    email: str
    model_name: str
    strategy: str
    was_revised: bool = False


def _format_key_facts(facts: list[str]) -> str:
    return "\n".join(f"- {fact}" for fact in facts)


def _looks_like_email(text: str) -> bool:
    """Quick heuristic: does the text resemble an actual email?"""
    if not text or len(text.strip()) < 30:
        return False
    return bool(_SUBJECT_RE.search(text)) or "regards" in text.lower()


async def _invoke_chain(
    prompt: ChatPromptTemplate,
    model: BaseChatModel,
    intent: str,
    key_facts: list[str],
    tone: str,
) -> str:
    chain = prompt | model
    result = await invoke_with_retry(chain, {
        "intent": intent,
        "key_facts": _format_key_facts(key_facts),
        "tone": tone,
    })
    if not result or not result.strip():
        raise ValueError("LLM returned an empty response")
    return result


async def _run_critic(
    critic_model: BaseChatModel,
    intent: str,
    key_facts: list[str],
    tone: str,
    draft_email: str,
) -> tuple[str, bool]:
    """Run a single critic pass. Returns (final_email, was_revised)."""
    try:
        prompt = build_critic_prompt()
        chain = prompt | critic_model
        critic_output = await invoke_with_retry(chain, {
            "intent": intent,
            "key_facts": _format_key_facts(key_facts),
            "tone": tone,
            "draft_email": draft_email,
        })

        if not critic_output or not critic_output.strip():
            logger.warning("Critic returned empty response, keeping draft")
            return draft_email, False

        stripped = critic_output.strip()

        if stripped.upper().startswith("APPROVED"):
            return draft_email, False

        revised = re.sub(
            r"(?i)^revision\s+needed\s*:?\s*\n*", "", stripped, count=1
        ).strip()

        if revised and _looks_like_email(revised):
            logger.info("Critic revised the email draft")
            return revised, True

        if _looks_like_email(stripped):
            logger.info("Critic returned a revised email (no header)")
            return stripped, True

        logger.warning("Critic output was not a valid email, keeping draft")
        return draft_email, False
    except Exception as e:
        logger.warning("Critic pass failed (%s), keeping draft", e)
        return draft_email, False


async def generate_advanced(
    intent: str,
    key_facts: list[str],
    tone: str,
    with_reflection: bool = True,
) -> GenerationResult:
    if not intent or not intent.strip():
        raise ValueError("Intent must not be empty")
    if not key_facts or not any(f.strip() for f in key_facts):
        raise ValueError("At least one non-empty key fact is required")
    if not tone or not tone.strip():
        tone = "professional"

    model = get_primary_model()
    prompt = build_advanced_prompt()

    draft = await _invoke_chain(prompt, model, intent, key_facts, tone)

    was_revised = False
    final_email = draft
    if with_reflection:
        critic_model = _build_model("gpt-4o-mini", temperature=0.0)
        final_email, was_revised = await _run_critic(
            critic_model, intent, key_facts, tone, draft
        )

    return GenerationResult(
        email=final_email,
        model_name=get_settings().get_model_name("primary"),
        strategy="advanced",
        was_revised=was_revised,
    )


async def generate_baseline(
    intent: str,
    key_facts: list[str],
    tone: str,
) -> GenerationResult:
    if not intent or not intent.strip():
        raise ValueError("Intent must not be empty")
    if not key_facts or not any(f.strip() for f in key_facts):
        raise ValueError("At least one non-empty key fact is required")
    if not tone or not tone.strip():
        tone = "professional"

    model = get_baseline_model()
    prompt = build_baseline_prompt()

    email = await _invoke_chain(prompt, model, intent, key_facts, tone)

    return GenerationResult(
        email=email,
        model_name=get_settings().get_model_name("baseline"),
        strategy="baseline",
        was_revised=False,
    )


STRATEGY_MAP = {
    "advanced": generate_advanced,
    "baseline": generate_baseline,
}
