"""Professional Quality metric (0-100).

Four equally-weighted sub-scores (each 0-25):
  Readability  – Flesch Reading Ease, sweet spot 50-70 for business email.
  Conciseness  – word count vs. reference; big deviations get penalised.
  Structure    – presence of subject line, greeting, paragraphs, sign-off.
  Grammar      – LLM judge rates fluency on a 1-10 rubric.
"""

import logging
import re

from langchain_core.prompts import ChatPromptTemplate

from app.core.models import get_judge_model, invoke_with_retry

logger = logging.getLogger(__name__)

GRAMMAR_JUDGE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "You are a professional editor. Rate the grammar, fluency, and "
        "overall writing quality of an email on a scale of 1-10.\n\n"
        "Rubric:\n"
        "1-3: Multiple grammar errors, awkward phrasing, hard to read.\n"
        "4-5: Some errors or awkward sections, but generally understandable.\n"
        "6-7: Good writing with minor issues.\n"
        "8-9: Excellent writing, professional and polished.\n"
        "10: Flawless — publication-ready quality."
    )),
    ("human", (
        "Email:\n{email}\n\n"
        "Rate the grammar and fluency (1-10). "
        "Respond with ONLY a single integer number."
    )),
])

MIN_WORDS_FOR_READABILITY = 20


def _compute_readability_score(email: str) -> tuple[float, str]:
    """Flesch Reading Ease mapped to 0-25; sweet spot is FRE 50-70."""
    import textstat

    word_count = len(email.split())
    if word_count < MIN_WORDS_FOR_READABILITY:
        return 10.0, f"FRE=N/A (too short: {word_count} words) -> 10/25"

    try:
        fre = textstat.flesch_reading_ease(email)
    except Exception as e:
        logger.warning("textstat.flesch_reading_ease failed: %s", e)
        return 10.0, "FRE=error -> 10/25"

    if 50 <= fre <= 70:
        score = 25.0
    elif 40 <= fre < 50 or 70 < fre <= 80:
        score = 20.0
    elif 30 <= fre < 40 or 80 < fre <= 90:
        score = 15.0
    elif 20 <= fre < 30 or 90 < fre <= 100:
        score = 10.0
    else:
        score = 5.0

    return score, f"FRE={fre:.1f} -> {score}/25"


def _compute_conciseness_score(email: str, reference_email: str) -> tuple[float, str]:
    """Word-count ratio vs reference email; big deviations lose points."""
    gen_words = len(email.split())

    if not reference_email or not reference_email.strip():
        return 15.0, f"Words: {gen_words} (no reference available) -> 15/25"

    ref_words = len(reference_email.split())
    if ref_words == 0:
        return 15.0, f"Words: {gen_words} (empty reference) -> 15/25"

    ratio = gen_words / ref_words

    if 0.7 <= ratio <= 1.3:
        score = 25.0
    elif 0.5 <= ratio < 0.7 or 1.3 < ratio <= 1.6:
        score = 20.0
    elif 0.3 <= ratio < 0.5 or 1.6 < ratio <= 2.0:
        score = 15.0
    elif ratio < 0.3:
        score = 5.0
    else:
        score = 10.0

    return score, f"Words: {gen_words} vs ref {ref_words} (ratio={ratio:.2f}) -> {score}/25"


def _compute_structure_score(email: str) -> tuple[float, str]:
    """Checks for subject, greeting, paragraphs, sign-off, no placeholders."""
    if not email or not email.strip():
        return 0.0, "0/5 checks passed (empty email)"

    checks = {
        "subject_line": bool(re.search(r"(?i)^subject:", email, re.MULTILINE)),
        "greeting": bool(re.search(
            r"(?i)^(dear|hi|hello|hey|good morning|good afternoon|team)",
            email, re.MULTILINE,
        )),
        "body_paragraphs": len(re.findall(r"\n\n", email)) >= 2,
        "sign_off": bool(re.search(
            r"(?i)(best regards|sincerely|thanks|thank you|cheers|warm regards|regards)",
            email,
        )),
        "no_placeholders": not bool(re.search(r"\[.*?\]", email)),
    }

    passed = sum(checks.values())
    score = (passed / len(checks)) * 25

    missing = [k for k, v in checks.items() if not v]
    detail = f"{passed}/{len(checks)} checks passed"
    if missing:
        detail += f" (missing: {', '.join(missing)})"

    return round(score, 1), detail


async def _compute_grammar_score(email: str) -> tuple[float, str]:
    """LLM rates grammar/fluency 1-10, scaled to 0-25."""
    try:
        model = get_judge_model()
        chain = GRAMMAR_JUDGE_PROMPT | model
        text = await invoke_with_retry(chain, {"email": email})

        digits = "".join(c for c in text if c.isdigit())
        if not digits:
            logger.warning("No digits in grammar judge response: %s", text[:80])
            rating = 5
        else:
            rating = int(digits[:2])
            rating = max(1, min(10, rating))
    except Exception as e:
        logger.warning("Grammar judge failed: %s", e)
        rating = 5

    score = (rating / 10) * 25
    return round(score, 1), f"Grammar rating: {rating}/10 -> {score}/25"


async def compute_professional_quality(
    generated_email: str,
    reference_email: str,
) -> dict:
    if not generated_email or not generated_email.strip():
        return {
            "score": 0.0,
            "details": "Empty email — all sub-scores zero",
            "sub_scores": {"readability": 0, "conciseness": 0, "structure": 0, "grammar": 0},
        }

    readability, read_detail = _compute_readability_score(generated_email)
    conciseness, conc_detail = _compute_conciseness_score(generated_email, reference_email)
    structure, struct_detail = _compute_structure_score(generated_email)
    grammar, gram_detail = await _compute_grammar_score(generated_email)

    total = readability + conciseness + structure + grammar
    total = max(0.0, min(100.0, round(total, 1)))

    details = (
        f"Readability: {read_detail} | Conciseness: {conc_detail} | "
        f"Structure: {struct_detail} | Grammar: {gram_detail}"
    )

    return {
        "score": total,
        "details": details,
        "sub_scores": {
            "readability": readability,
            "conciseness": conciseness,
            "structure": structure,
            "grammar": grammar,
        },
    }
