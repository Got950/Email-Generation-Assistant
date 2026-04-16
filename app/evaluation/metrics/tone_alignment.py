"""Tone Alignment metric (0-100).

Blends an LLM rubric score (80 % weight) with a VADER/TextBlob sentiment
sanity-check (20 % weight).  The sentiment profiles in TONE_SENTIMENT_PROFILES
encode rough expected ranges so we can catch obvious mismatches even if the LLM
is generous.
"""

import logging

from langchain_core.prompts import ChatPromptTemplate

from app.core.models import get_judge_model, invoke_with_retry

logger = logging.getLogger(__name__)

TONE_JUDGE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "You are an expert in professional communication styles. "
        "Rate how well an email matches a requested tone on a scale of 1-10.\n\n"
        "Rubric:\n"
        "1-3: Tone is clearly wrong or contradictory to the request.\n"
        "4-5: Some elements match but overall tone feels off.\n"
        "6-7: Mostly matches with minor inconsistencies.\n"
        "8-9: Strong match with consistent tone throughout.\n"
        "10: Perfect tone match — every sentence reinforces the requested style."
    )),
    ("human", (
        "Requested tone: {tone}\n\n"
        "Email:\n{email}\n\n"
        "Rate the tone alignment (1-10). "
        "Respond with ONLY a single integer number."
    )),
])

TONE_SENTIMENT_PROFILES = {
    "formal": {"compound_min": -0.1, "compound_max": 0.5, "subjectivity_max": 0.4},
    "professional": {"compound_min": 0.0, "compound_max": 0.6, "subjectivity_max": 0.5},
    "friendly-casual": {"compound_min": 0.2, "compound_max": 1.0, "subjectivity_max": 0.8},
    "empathetic": {"compound_min": 0.1, "compound_max": 0.8, "subjectivity_max": 0.7},
    "excited": {"compound_min": 0.3, "compound_max": 1.0, "subjectivity_max": 0.9},
    "neutral": {"compound_min": -0.2, "compound_max": 0.4, "subjectivity_max": 0.5},
    "persuasive": {"compound_min": 0.1, "compound_max": 0.8, "subjectivity_max": 0.7},
    "warm-grateful": {"compound_min": 0.3, "compound_max": 1.0, "subjectivity_max": 0.8},
    "urgent": {"compound_min": -0.3, "compound_max": 0.5, "subjectivity_max": 0.7},
    "casual-compelling": {"compound_min": 0.1, "compound_max": 0.9, "subjectivity_max": 0.8},
}


async def _get_llm_tone_score(tone: str, email: str) -> int:
    try:
        model = get_judge_model()
        chain = TONE_JUDGE_PROMPT | model
        text = await invoke_with_retry(chain, {"tone": tone, "email": email})
        digits = "".join(c for c in text if c.isdigit())
        if not digits:
            logger.warning("No digits in tone judge response: %s", text[:80])
            return 5
        score = int(digits[:2])
        return max(1, min(10, score))
    except Exception as e:
        logger.warning("LLM tone scoring failed: %s", e)
        return 5


def _get_sentiment_signal(tone: str, email: str) -> float:
    """VADER + TextBlob sentiment check against expected tone profile (0-10)."""
    try:
        from textblob import TextBlob
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

        analyzer = SentimentIntensityAnalyzer()
        vader_scores = analyzer.polarity_scores(email)
        compound = vader_scores["compound"]

        blob = TextBlob(email)
        subjectivity = blob.sentiment.subjectivity
    except Exception as e:
        logger.warning("Sentiment analysis failed: %s", e)
        return 7.0

    profile = TONE_SENTIMENT_PROFILES.get(tone.lower())
    if not profile:
        return 7.0

    score = 10.0

    if compound < profile["compound_min"]:
        score -= 3.0
    elif compound > profile["compound_max"]:
        score -= 1.5

    if subjectivity > profile.get("subjectivity_max", 1.0):
        score -= 1.5

    return max(0.0, min(10.0, score))


async def compute_tone_alignment(tone: str, generated_email: str) -> dict:
    if not generated_email or not generated_email.strip():
        return {
            "score": 0.0,
            "details": "Empty email — cannot evaluate tone",
            "llm_score": 0,
            "sentiment_signal": 0.0,
        }

    if not tone or not tone.strip():
        return {
            "score": 50.0,
            "details": "No tone specified — defaulting to neutral midpoint",
            "llm_score": 5,
            "sentiment_signal": 5.0,
        }

    llm_score = await _get_llm_tone_score(tone, generated_email)
    sentiment_signal = _get_sentiment_signal(tone, generated_email)

    final_score = (llm_score * 0.8 + sentiment_signal * 0.2) * 10
    final_score = max(0.0, min(100.0, round(final_score, 1)))

    details = (
        f"LLM judge: {llm_score}/10, "
        f"Sentiment signal: {sentiment_signal:.1f}/10, "
        f"Weighted: {final_score}/100"
    )

    return {
        "score": final_score,
        "details": details,
        "llm_score": llm_score,
        "sentiment_signal": round(sentiment_signal, 1),
    }
