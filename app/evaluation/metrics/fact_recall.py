"""Fact Recall metric (0-100).

For each key fact we ask the judge LLM "is this present in the email?".
If the LLM call fails or says NO, we fall back to cosine similarity via
sentence-transformers (threshold 0.75).  Score = confirmed / total * 100.
"""

import logging
import re

from langchain_core.prompts import ChatPromptTemplate

from app.core.models import get_judge_model, invoke_with_retry

logger = logging.getLogger(__name__)

FACT_CHECK_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "You are a precise fact-checking assistant. Your job is to determine "
        "whether a specific fact is present in an email. The fact may be paraphrased "
        "or expressed differently, but the core information must be there."
    )),
    ("human", (
        "Fact to check: \"{fact}\"\n\n"
        "Email:\n{email}\n\n"
        "Is this fact present in the email? Consider paraphrases and indirect references.\n"
        "Respond with ONLY 'YES' or 'NO'."
    )),
])


async def _check_single_fact_llm(fact: str, email: str) -> bool:
    try:
        model = get_judge_model()
        chain = FACT_CHECK_PROMPT | model
        answer = await invoke_with_retry(chain, {"fact": fact, "email": email})
        return answer.upper().startswith("YES")
    except Exception as e:
        logger.warning("LLM fact check failed for '%s': %s", fact[:40], e)
        return False


def _check_single_fact_semantic(fact: str, email_sentences: list[str], model) -> bool:
    """Cosine-sim fallback when the LLM judge is unavailable."""
    try:
        from sentence_transformers import util

        fact_embedding = model.encode(fact, convert_to_tensor=True)
        sentence_embeddings = model.encode(email_sentences, convert_to_tensor=True)

        similarities = util.cos_sim(fact_embedding, sentence_embeddings)
        max_sim = similarities.max().item()
        return max_sim >= 0.75
    except Exception as e:
        logger.warning("Semantic similarity check failed: %s", e)
        return False


def _split_email_sentences(email: str) -> list[str]:
    if not email or not email.strip():
        return []
    sentences = re.split(r'[.!?\n]+', email)
    return [s.strip() for s in sentences if len(s.strip()) > 10]


async def compute_fact_recall(
    key_facts: list[str],
    generated_email: str,
    use_semantic_fallback: bool = True,
) -> dict:
    if not key_facts:
        return {"score": 0.0, "details": "No facts provided", "per_fact": []}

    if not generated_email or not generated_email.strip():
        return {
            "score": 0.0,
            "details": f"0/{len(key_facts)} facts confirmed (empty email)",
            "per_fact": [{"fact": f, "present": False, "method": "empty_email"} for f in key_facts],
        }

    per_fact = []
    confirmed = 0

    sentences = _split_email_sentences(generated_email)
    semantic_model = None

    for fact in key_facts:
        if not fact or not fact.strip():
            per_fact.append({"fact": fact, "present": False, "method": "empty_fact"})
            continue

        llm_present = await _check_single_fact_llm(fact, generated_email)

        if llm_present:
            per_fact.append({"fact": fact, "present": True, "method": "llm_judge"})
            confirmed += 1
        elif use_semantic_fallback and sentences:
            if semantic_model is None:
                try:
                    from sentence_transformers import SentenceTransformer
                    semantic_model = SentenceTransformer("all-MiniLM-L6-v2")
                except Exception as e:
                    logger.warning("Could not load sentence-transformer: %s", e)
                    per_fact.append({"fact": fact, "present": False, "method": "llm_judge"})
                    continue
            present = _check_single_fact_semantic(fact, sentences, semantic_model)
            per_fact.append({"fact": fact, "present": present, "method": "semantic_similarity"})
            if present:
                confirmed += 1
        else:
            per_fact.append({"fact": fact, "present": False, "method": "llm_judge"})

    total = len(key_facts)
    score = (confirmed / total) * 100
    score = max(0.0, min(100.0, round(score, 1)))
    details = f"{confirmed}/{total} facts confirmed"

    return {"score": score, "details": details, "per_fact": per_fact}
