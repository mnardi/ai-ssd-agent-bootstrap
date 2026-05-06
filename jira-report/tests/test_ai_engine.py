import pytest
from datetime import date

from jira_report.ai_engine import (
    _resolve_model,
    _build_system_prompt,
    _build_user_message,
    _format_tickets,
    generate_report,
)
from jira_report.config import DEFAULT_MODEL
from jira_report.jira_client import JiraData, JiraTicket


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


# ── generate_report (still a stub at end of Story 3.1) ────────────────────────

def test_generate_report_still_raises_not_implemented(sample_config, sample_jira_data):
    with pytest.raises(NotImplementedError):
        generate_report(sample_config, sample_jira_data)
