"""Tests for the email generation API, core logic, and edge cases."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.prompts import build_advanced_prompt, build_baseline_prompt, build_critic_prompt
from app.main import app

client = TestClient(app)


# ── API Tests ────────────────────────────────────────────────────────────

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "provider" in data
    assert "has_valid_key" in data


def test_generate_endpoint_validation_empty_body():
    response = client.post("/generate", json={})
    assert response.status_code == 422


def test_generate_endpoint_validation_missing_intent():
    response = client.post("/generate", json={
        "key_facts": ["fact one"],
        "tone": "formal",
    })
    assert response.status_code == 422


def test_generate_endpoint_validation_empty_key_facts():
    response = client.post("/generate", json={
        "intent": "Test intent",
        "key_facts": [],
        "tone": "formal",
    })
    assert response.status_code == 422


def test_generate_endpoint_validation_short_intent():
    response = client.post("/generate", json={
        "intent": "Hi",
        "key_facts": ["fact one"],
        "tone": "formal",
    })
    assert response.status_code == 422


def test_generate_endpoint_invalid_strategy():
    response = client.post("/generate", json={
        "intent": "Test intent for validation",
        "key_facts": ["fact one"],
        "tone": "formal",
        "strategy": "nonexistent",
    })
    assert response.status_code == 400
    assert "Unknown strategy" in response.json()["detail"]


# ── Prompt Template Tests ────────────────────────────────────────────────

def test_advanced_prompt_template_builds():
    prompt = build_advanced_prompt()
    assert prompt is not None
    formatted = prompt.format_messages(
        intent="test", key_facts="- fact1", tone="formal"
    )
    assert len(formatted) == 2
    assert "B2B sales communications specialist" in formatted[0].content


def test_baseline_prompt_template_builds():
    prompt = build_baseline_prompt()
    assert prompt is not None
    formatted = prompt.format_messages(
        intent="test", key_facts="- fact1", tone="formal"
    )
    assert len(formatted) == 2
    assert "professional emails" in formatted[0].content.lower()


def test_critic_prompt_template_builds():
    prompt = build_critic_prompt()
    formatted = prompt.format_messages(
        intent="test",
        key_facts="- fact1",
        tone="formal",
        draft_email="Subject: Test\n\nHello,\n\nTest body.\n\nBest regards,",
    )
    assert len(formatted) == 2
    assert "APPROVED" in formatted[1].content


def test_advanced_prompt_contains_few_shot_examples():
    prompt = build_advanced_prompt()
    formatted = prompt.format_messages(
        intent="test", key_facts="- fact1", tone="formal"
    )
    human_msg = formatted[1].content
    assert "EXAMPLE 1" in human_msg
    assert "EXAMPLE 2" in human_msg
    assert "EXAMPLE 3" in human_msg


def test_advanced_prompt_has_cot_instructions():
    prompt = build_advanced_prompt()
    formatted = prompt.format_messages(
        intent="test", key_facts="- fact1", tone="formal"
    )
    human_msg = formatted[1].content
    assert "silently plan" in human_msg.lower()


# ── Scenario Data Tests ──────────────────────────────────────────────────

def test_scenarios_file_loads():
    path = Path(__file__).resolve().parent.parent / "data" / "scenarios.json"
    with open(path) as f:
        scenarios = json.load(f)

    assert len(scenarios) == 10
    for s in scenarios:
        assert "id" in s
        assert "intent" in s
        assert "key_facts" in s
        assert "tone" in s
        assert "reference_email" in s
        assert len(s["key_facts"]) >= 3
        assert len(s["intent"]) > 5
        assert len(s["reference_email"]) > 50


def test_scenarios_have_unique_ids():
    path = Path(__file__).resolve().parent.parent / "data" / "scenarios.json"
    with open(path) as f:
        scenarios = json.load(f)
    ids = [s["id"] for s in scenarios]
    assert len(ids) == len(set(ids))


def test_scenarios_cover_diverse_tones():
    path = Path(__file__).resolve().parent.parent / "data" / "scenarios.json"
    with open(path) as f:
        scenarios = json.load(f)
    tones = set(s["tone"] for s in scenarios)
    assert len(tones) >= 5


# ── Structure Metric Tests ───────────────────────────────────────────────

def test_structure_checker_good_email():
    from app.evaluation.metrics.professional_quality import _compute_structure_score

    good_email = (
        "Subject: Test Email\n\n"
        "Dear Team,\n\n"
        "This is the first paragraph of the body.\n\n"
        "This is the second paragraph with more details.\n\n"
        "Best regards,"
    )
    score, detail = _compute_structure_score(good_email)
    assert score >= 20.0
    assert "checks passed" in detail


def test_structure_checker_missing_parts():
    from app.evaluation.metrics.professional_quality import _compute_structure_score

    bad_email = "hey just wanted to say hi"
    score, _ = _compute_structure_score(bad_email)
    assert score < 15.0


def test_structure_checker_empty_email():
    from app.evaluation.metrics.professional_quality import _compute_structure_score

    score, detail = _compute_structure_score("")
    assert score == 0.0
    assert "empty" in detail.lower()


def test_structure_checker_none_like():
    from app.evaluation.metrics.professional_quality import _compute_structure_score

    score, detail = _compute_structure_score("   ")
    assert score == 0.0


# ── Readability Metric Tests ─────────────────────────────────────────────

def test_readability_short_email():
    from app.evaluation.metrics.professional_quality import _compute_readability_score

    score, detail = _compute_readability_score("Short text.")
    assert score == 10.0
    assert "too short" in detail.lower()


def test_readability_normal_email():
    from app.evaluation.metrics.professional_quality import _compute_readability_score

    email = (
        "Dear Team, I wanted to follow up on our meeting last week regarding the new "
        "project timeline. The team has reviewed the proposal and we believe the "
        "milestones are achievable within the specified timeframe. Please let me know "
        "if you have any questions about the deliverables or resource allocation."
    )
    score, detail = _compute_readability_score(email)
    assert 5.0 <= score <= 25.0
    assert "FRE=" in detail


# ── Conciseness Metric Tests ─────────────────────────────────────────────

def test_conciseness_no_reference():
    from app.evaluation.metrics.professional_quality import _compute_conciseness_score

    score, detail = _compute_conciseness_score("Some email text here.", "")
    assert score == 15.0
    assert "no reference" in detail.lower()


def test_conciseness_matching_length():
    from app.evaluation.metrics.professional_quality import _compute_conciseness_score

    text = "word " * 50
    score, _ = _compute_conciseness_score(text, text)
    assert score == 25.0


# ── Fact Recall Edge Cases (no LLM calls) ────────────────────────────────

@pytest.mark.asyncio
async def test_fact_recall_empty_facts():
    from app.evaluation.metrics.fact_recall import compute_fact_recall

    result = await compute_fact_recall([], "Some email text")
    assert result["score"] == 0.0
    assert "No facts" in result["details"]


@pytest.mark.asyncio
async def test_fact_recall_empty_email():
    from app.evaluation.metrics.fact_recall import compute_fact_recall

    result = await compute_fact_recall(["fact one", "fact two"], "")
    assert result["score"] == 0.0
    assert "empty email" in result["details"].lower()


# ── Tone Alignment Edge Cases (no LLM calls) ─────────────────────────────

@pytest.mark.asyncio
async def test_tone_alignment_empty_email():
    from app.evaluation.metrics.tone_alignment import compute_tone_alignment

    result = await compute_tone_alignment("formal", "")
    assert result["score"] == 0.0
    assert "empty" in result["details"].lower()


@pytest.mark.asyncio
async def test_tone_alignment_empty_tone():
    from app.evaluation.metrics.tone_alignment import compute_tone_alignment

    result = await compute_tone_alignment("", "Hello, this is a test email.")
    assert result["score"] == 50.0


# ── Professional Quality Edge Cases (no LLM calls) ──────────────────────

@pytest.mark.asyncio
async def test_professional_quality_empty_email():
    from app.evaluation.metrics.professional_quality import compute_professional_quality

    result = await compute_professional_quality("", "Reference text")
    assert result["score"] == 0.0
    assert "empty" in result["details"].lower()


# ── Chains Edge Cases (mocked LLM) ──────────────────────────────────────

@pytest.mark.asyncio
async def test_advanced_chain_rejects_empty_intent():
    from app.core.chains import generate_advanced
    with pytest.raises(ValueError, match="Intent must not be empty"):
        await generate_advanced("", ["fact"], "formal")


@pytest.mark.asyncio
async def test_advanced_chain_rejects_empty_facts():
    from app.core.chains import generate_advanced
    with pytest.raises(ValueError, match="non-empty key fact"):
        await generate_advanced("Follow up", [], "formal")


@pytest.mark.asyncio
async def test_baseline_chain_rejects_empty_intent():
    from app.core.chains import generate_baseline
    with pytest.raises(ValueError, match="Intent must not be empty"):
        await generate_baseline("", ["fact"], "formal")


@pytest.mark.asyncio
async def test_critic_handles_empty_response():
    from app.core.chains import _run_critic

    mock_model = AsyncMock()
    with patch("app.core.chains.invoke_with_retry", new_callable=AsyncMock, return_value=""):
        email, revised = await _run_critic(mock_model, "test", ["fact"], "formal", "original draft")
    assert email == "original draft"
    assert revised is False


@pytest.mark.asyncio
async def test_critic_handles_approved():
    from app.core.chains import _run_critic

    mock_model = AsyncMock()
    with patch("app.core.chains.invoke_with_retry", new_callable=AsyncMock, return_value="APPROVED"):
        email, revised = await _run_critic(mock_model, "test", ["fact"], "formal", "original draft")
    assert email == "original draft"
    assert revised is False


@pytest.mark.asyncio
async def test_critic_handles_revision():
    from app.core.chains import _run_critic

    revised_email = "Subject: Revised\n\nDear Team,\n\nRevised body.\n\nBest regards,"
    mock_model = AsyncMock()
    with patch("app.core.chains.invoke_with_retry", new_callable=AsyncMock, return_value=f"REVISION NEEDED\n{revised_email}"):
        email, revised = await _run_critic(mock_model, "test", ["fact"], "formal", "original draft")
    assert "Revised" in email
    assert revised is True


@pytest.mark.asyncio
async def test_critic_handles_garbage_response():
    from app.core.chains import _run_critic

    mock_model = AsyncMock()
    with patch("app.core.chains.invoke_with_retry", new_callable=AsyncMock, return_value="I don't know what to do"):
        email, revised = await _run_critic(mock_model, "test", ["fact"], "formal", "original draft")
    assert email == "original draft"
    assert revised is False


@pytest.mark.asyncio
async def test_critic_handles_exception():
    from app.core.chains import _run_critic

    mock_model = AsyncMock()
    with patch("app.core.chains.invoke_with_retry", new_callable=AsyncMock, side_effect=RuntimeError("API down")):
        email, revised = await _run_critic(mock_model, "test", ["fact"], "formal", "original draft")
    assert email == "original draft"
    assert revised is False


# ── Runner Validation Tests ──────────────────────────────────────────────

def test_runner_validates_scenarios():
    from app.evaluation.runner import ScenarioValidationError, _validate_scenario

    with pytest.raises(ScenarioValidationError, match="missing required keys"):
        _validate_scenario({"id": 1}, 0)

    with pytest.raises(ScenarioValidationError, match="non-empty list"):
        _validate_scenario({"id": 1, "intent": "test", "key_facts": [], "tone": "formal"}, 0)

    with pytest.raises(ScenarioValidationError, match="intent must not be empty"):
        _validate_scenario({"id": 1, "intent": "  ", "key_facts": ["f"], "tone": "formal"}, 0)

    _validate_scenario({"id": 1, "intent": "test", "key_facts": ["f"], "tone": "formal"}, 0)


def test_compute_summary_empty_results():
    from app.evaluation.runner import _compute_summary

    assert _compute_summary([]) == {}


# ── Config Tests ─────────────────────────────────────────────────────────

def test_settings_has_valid_key_detects_dummy():
    from app.config import Settings

    s = Settings(openai_api_key="sk-test-dummy-key")
    assert s.has_valid_key is False


def test_settings_auto_detect_openai():
    from app.config import Settings

    s = Settings(openai_api_key="sk-real-key-here-1234567890")
    assert s.resolved_provider == "openai"


def test_settings_get_model_name_defaults():
    from app.config import Settings

    s = Settings(openai_api_key="sk-real-key")
    assert s.get_model_name("primary") == "gpt-4o-mini"
    assert s.get_model_name("baseline") == "gpt-3.5-turbo"
    assert s.get_model_name("judge") == "gpt-4o"


def test_settings_get_model_name_explicit():
    from app.config import Settings

    s = Settings(openai_api_key="sk-real-key", primary_model="gpt-3.5-turbo")
    assert s.get_model_name("primary") == "gpt-3.5-turbo"
