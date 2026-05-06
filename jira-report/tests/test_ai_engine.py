import pytest
from datetime import date
from unittest.mock import MagicMock, patch

import anthropic

from jira_report.ai_engine import (
    _resolve_model,
    _build_system_prompt,
    _build_user_message,
    _format_tickets,
    _parse_response,
    _create_anthropic_client,
    generate_report,
)
from jira_report.config import AIGenerationError, DEFAULT_MODEL
from jira_report.jira_client import JiraData, JiraTicket, ReportSections


def _make_anthropic_response(text: str) -> MagicMock:
    response = MagicMock()
    response.content = [MagicMock(text=text)]
    return response


_GOOD_RESPONSE = (
    "## Done\nDone body paragraph.\n\n"
    "## In Progress\nIP body paragraph.\n\n"
    "## Next Plan\nNP body paragraph.\n\n"
    "## Executive Summary\nES body paragraph."
)


# ── _resolve_model ─────────────────────────────────────────────────────────────

def test_resolve_model_returns_configured_model(sample_config):
    cfg = sample_config.model_copy(update={"ai_model": "claude-opus-4-7"})
    assert _resolve_model(cfg) == "claude-opus-4-7"


def test_resolve_model_falls_back_to_default_when_empty(sample_config):
    cfg = sample_config.model_copy(update={"ai_model": ""})
    assert _resolve_model(cfg) == DEFAULT_MODEL


def test_resolve_model_default_from_pydantic(sample_config):
    # sample_config sets ai_model to "claude-sonnet-4-6" — same as DEFAULT_MODEL
    assert _resolve_model(sample_config) == DEFAULT_MODEL


# ── _build_system_prompt ───────────────────────────────────────────────────────

def test_system_prompt_includes_project_name(sample_config):
    prompt = _build_system_prompt(sample_config)
    assert sample_config.project_name in prompt


def test_system_prompt_includes_report_tone(sample_config):
    prompt = _build_system_prompt(sample_config)
    assert sample_config.report_tone in prompt


def test_system_prompt_includes_four_section_directive(sample_config):
    prompt = _build_system_prompt(sample_config)
    for section in ("Done", "In Progress", "Next Plan", "Executive Summary"):
        assert section in prompt


def test_system_prompt_requires_executive_language(sample_config):
    prompt = _build_system_prompt(sample_config).lower()
    assert "executive" in prompt


# ── _format_tickets ────────────────────────────────────────────────────────────

def test_format_tickets_empty_returns_none_marker():
    assert _format_tickets([]) == "(none)"


def test_format_tickets_includes_all_four_fields():
    ticket = JiraTicket(key="ABC-7", summary="Fix login", assignee="Bob", status="Done")
    out = _format_tickets([ticket])
    assert "ABC-7" in out
    assert "Fix login" in out
    assert "Bob" in out
    assert "Done" in out


# ── _build_user_message ────────────────────────────────────────────────────────

def test_user_message_includes_all_done_tickets(sample_config, sample_jira_data):
    msg = _build_user_message(sample_jira_data)
    # sample_jira_data uses TEST-1 three times in each section
    assert "TEST-1" in msg


def test_user_message_includes_all_three_sections(sample_jira_data):
    msg = _build_user_message(sample_jira_data)
    assert "Done" in msg
    assert "In Progress" in msg
    assert "Planned" in msg


def test_user_message_includes_reporting_period(sample_jira_data):
    msg = _build_user_message(sample_jira_data)
    assert "2026-04-21" in msg
    assert "2026-04-27" in msg


def test_user_message_no_summarization():
    """Every ticket summary appears verbatim — no rewriting or filtering."""
    tickets = [
        JiraTicket(key="A-1", summary="Distinctive summary one", assignee="Alice", status="Done"),
        JiraTicket(key="A-2", summary="Distinctive summary two", assignee="Bob", status="In Progress"),
        JiraTicket(key="A-3", summary="Distinctive summary three", assignee="Carol", status="To Do"),
    ]
    data = JiraData(
        done=[tickets[0]],
        in_progress=[tickets[1]],
        planned=[tickets[2]],
        week_start=date(2026, 4, 21),
        week_end=date(2026, 4, 27),
    )
    msg = _build_user_message(data)
    for t in tickets:
        assert t.summary in msg
        assert t.key in msg
        assert t.assignee in msg


# ── _parse_response ────────────────────────────────────────────────────────────

def test_parse_response_returns_report_sections():
    sections = _parse_response(_GOOD_RESPONSE)
    assert isinstance(sections, ReportSections)
    assert sections.done_text == "Done body paragraph."
    assert sections.in_progress_text == "IP body paragraph."
    assert sections.next_plan_text == "NP body paragraph."
    assert sections.executive_summary == "ES body paragraph."


def test_parse_response_strips_whitespace():
    text = (
        "## Done\n  body  \n\n"
        "## In Progress\nip\n\n"
        "## Next Plan\nnp\n\n"
        "## Executive Summary\nes"
    )
    sections = _parse_response(text)
    assert sections.done_text == "body"


def test_parse_response_raises_on_missing_section():
    text = "## Done\nbody only"
    with pytest.raises(AIGenerationError, match="4 sections"):
        _parse_response(text)


# ── _create_anthropic_client ───────────────────────────────────────────────────

def test_create_anthropic_client_uses_api_key(sample_config):
    with patch("jira_report.ai_engine.Anthropic") as mock_anthropic_cls:
        _create_anthropic_client(sample_config)
        mock_anthropic_cls.assert_called_once_with(api_key=sample_config.api_key)


# ── generate_report — happy path ───────────────────────────────────────────────

def test_generate_report_returns_report_sections(sample_config, sample_jira_data):
    with patch("jira_report.ai_engine.Anthropic") as mock_anthropic_cls:
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = _make_anthropic_response(_GOOD_RESPONSE)

        sections = generate_report(sample_config, sample_jira_data)

    assert isinstance(sections, ReportSections)
    assert sections.done_text == "Done body paragraph."
    assert sections.in_progress_text == "IP body paragraph."
    assert sections.next_plan_text == "NP body paragraph."
    assert sections.executive_summary == "ES body paragraph."


def test_generate_report_uses_resolved_model(sample_config, sample_jira_data):
    cfg = sample_config.model_copy(update={"ai_model": "custom-x"})
    with patch("jira_report.ai_engine.Anthropic") as mock_anthropic_cls:
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = _make_anthropic_response(_GOOD_RESPONSE)

        generate_report(cfg, sample_jira_data)

    kwargs = mock_client.messages.create.call_args.kwargs
    assert kwargs["model"] == "custom-x"


def test_generate_report_uses_default_model_when_empty(sample_config, sample_jira_data):
    cfg = sample_config.model_copy(update={"ai_model": ""})
    with patch("jira_report.ai_engine.Anthropic") as mock_anthropic_cls:
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = _make_anthropic_response(_GOOD_RESPONSE)

        generate_report(cfg, sample_jira_data)

    kwargs = mock_client.messages.create.call_args.kwargs
    assert kwargs["model"] == DEFAULT_MODEL


def test_generate_report_passes_system_and_user_message(sample_config, sample_jira_data):
    with patch("jira_report.ai_engine.Anthropic") as mock_anthropic_cls:
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = _make_anthropic_response(_GOOD_RESPONSE)

        generate_report(sample_config, sample_jira_data)

    kwargs = mock_client.messages.create.call_args.kwargs
    assert isinstance(kwargs["system"], str) and kwargs["system"]
    assert kwargs["messages"][0]["role"] == "user"
    assert kwargs["messages"][0]["content"]


# ── generate_report — empty / malformed responses ─────────────────────────────

def test_generate_report_raises_on_empty_response_content(sample_config, sample_jira_data):
    with patch("jira_report.ai_engine.Anthropic") as mock_anthropic_cls:
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        empty_response = MagicMock()
        empty_response.content = []
        mock_client.messages.create.return_value = empty_response

        with pytest.raises(AIGenerationError, match="empty"):
            generate_report(sample_config, sample_jira_data)


def test_generate_report_raises_on_whitespace_only_response(sample_config, sample_jira_data):
    with patch("jira_report.ai_engine.Anthropic") as mock_anthropic_cls:
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = _make_anthropic_response("   \n  \n")

        with pytest.raises(AIGenerationError, match="empty"):
            generate_report(sample_config, sample_jira_data)


def test_generate_report_raises_on_missing_sections(sample_config, sample_jira_data):
    with patch("jira_report.ai_engine.Anthropic") as mock_anthropic_cls:
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = _make_anthropic_response("## Done\nbody")

        with pytest.raises(AIGenerationError, match="section"):
            generate_report(sample_config, sample_jira_data)


def test_generate_report_raises_on_empty_section_body(sample_config, sample_jira_data):
    text = (
        "## Done\nDone body.\n\n"
        "## In Progress\nIP body.\n\n"
        "## Next Plan\n\n"  # ← empty body
        "## Executive Summary\nES body."
    )
    with patch("jira_report.ai_engine.Anthropic") as mock_anthropic_cls:
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = _make_anthropic_response(text)

        with pytest.raises(AIGenerationError, match="next_plan_text"):
            generate_report(sample_config, sample_jira_data)


# ── generate_report — SDK exception wrapping ──────────────────────────────────

def test_generate_report_wraps_api_error(sample_config, sample_jira_data):
    with patch("jira_report.ai_engine.Anthropic") as mock_anthropic_cls:
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.side_effect = anthropic.APIError(
            message="boom", request=MagicMock(), body=None
        )

        with pytest.raises(AIGenerationError, match="Claude API call failed"):
            generate_report(sample_config, sample_jira_data)


def test_generate_report_wraps_unexpected_exception(sample_config, sample_jira_data):
    with patch("jira_report.ai_engine.Anthropic") as mock_anthropic_cls:
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.side_effect = RuntimeError("boom")

        with pytest.raises(AIGenerationError, match="RuntimeError"):
            generate_report(sample_config, sample_jira_data)


def test_api_key_never_in_error_messages(sample_config, sample_jira_data):
    """NFR4: AIGenerationError messages must never leak the api_key."""
    secret = sample_config.api_key
    with patch("jira_report.ai_engine.Anthropic") as mock_anthropic_cls:
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.side_effect = RuntimeError(f"auth failed for key {secret}")

        with pytest.raises(AIGenerationError) as exc_info:
            generate_report(sample_config, sample_jira_data)
        assert secret not in str(exc_info.value)
