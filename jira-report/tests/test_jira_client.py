import pytest
import requests
from datetime import date
from unittest.mock import MagicMock, patch
from jira import JIRAError

from jira_report.config import JiraFetchError
from jira_report.jira_client import (
    fetch_jira_data,
    DEFAULT_TIMEOUT_SECONDS,
    _calculate_week_range,
    _build_jql_done,
    _build_jql_in_progress,
    _build_jql_planned,
)


# ── Constant ──────────────────────────────────────────────────────────────────

def test_default_timeout_constant():
    assert DEFAULT_TIMEOUT_SECONDS == 10


# ── Auth failure ──────────────────────────────────────────────────────────────

def test_auth_failure_raises_jira_fetch_error(sample_config):
    with patch("jira_report.jira_client.JIRA") as mock_jira:
        mock_jira.side_effect = JIRAError(text="Unauthorized", status_code=401)
        with pytest.raises(JiraFetchError, match="authentication failed"):
            fetch_jira_data(sample_config)


def test_auth_forbidden_raises_jira_fetch_error(sample_config):
    with patch("jira_report.jira_client.JIRA") as mock_jira:
        mock_jira.side_effect = JIRAError(text="Forbidden", status_code=403)
        with pytest.raises(JiraFetchError, match="authentication failed"):
            fetch_jira_data(sample_config)


# ── Network errors ─────────────────────────────────────────────────────────────

def test_network_unreachable(sample_config):
    with patch("jira_report.jira_client.JIRA") as mock_jira:
        mock_jira.side_effect = requests.exceptions.ConnectionError("connection refused")
        with pytest.raises(JiraFetchError, match="Network unreachable"):
            fetch_jira_data(sample_config)


def test_timeout_raises_jira_fetch_error(sample_config):
    with patch("jira_report.jira_client.JIRA") as mock_jira:
        mock_jira.side_effect = requests.exceptions.Timeout("timed out")
        with pytest.raises(JiraFetchError, match="Network unreachable"):
            fetch_jira_data(sample_config)


# ── Project validation ─────────────────────────────────────────────────────────

def test_invalid_project_key(sample_config):
    with patch("jira_report.jira_client.JIRA") as mock_jira:
        mock_instance = MagicMock()
        mock_jira.return_value = mock_instance
        mock_instance.project.side_effect = JIRAError(text="Not Found", status_code=404)
        with pytest.raises(JiraFetchError, match=sample_config.project_key):
            fetch_jira_data(sample_config)


# ── Credential safety ──────────────────────────────────────────────────────────

def test_auth_token_not_in_error_message(sample_config):
    with patch("jira_report.jira_client.JIRA") as mock_jira:
        mock_jira.side_effect = JIRAError(text="Unauthorized", status_code=401)
        with pytest.raises(JiraFetchError) as exc_info:
            fetch_jira_data(sample_config)
        assert sample_config.api_token not in str(exc_info.value)


# ── Success path (auth + project valid; data retrieval is Story 2) ─────────────

def test_jira_initialized_with_correct_url(sample_config):
    with patch("jira_report.jira_client.JIRA") as mock_jira:
        mock_instance = MagicMock()
        mock_jira.return_value = mock_instance
        with pytest.raises(NotImplementedError):
            fetch_jira_data(sample_config)
        mock_jira.assert_called_once()
        assert mock_jira.call_args.kwargs.get("server") == sample_config.jira_url


def test_auth_succeeds_no_token_in_output(sample_config, capsys):
    with patch("jira_report.jira_client.JIRA") as mock_jira:
        mock_instance = MagicMock()
        mock_jira.return_value = mock_instance
        with pytest.raises(NotImplementedError):
            fetch_jira_data(sample_config)
        captured = capsys.readouterr()
        assert sample_config.api_token not in captured.out
        assert sample_config.api_token not in captured.err


# ── Date range calculation ─────────────────────────────────────────────────────

def test_auto_week_range_wednesday():
    # Apr 29 = Wed; most recent Sunday = Apr 26; week Mon Apr 20 – Sun Apr 26
    week_start, week_end = _calculate_week_range(_today=date(2026, 4, 29))
    assert week_start == date(2026, 4, 20)
    assert week_end == date(2026, 4, 26)


def test_auto_week_range_monday():
    # Apr 27 = Mon; most recent Sunday = Apr 26; week Mon Apr 20 – Sun Apr 26
    week_start, week_end = _calculate_week_range(_today=date(2026, 4, 27))
    assert week_start == date(2026, 4, 20)
    assert week_end == date(2026, 4, 26)


def test_auto_week_range_sunday():
    # Apr 26 = Sun (today IS the most recent Sunday); week Mon Apr 20 – Sun Apr 26
    week_start, week_end = _calculate_week_range(_today=date(2026, 4, 26))
    assert week_start == date(2026, 4, 20)
    assert week_end == date(2026, 4, 26)


def test_auto_week_range_saturday():
    # Apr 25 = Sat; most recent Sunday = Apr 19; week Mon Apr 13 – Sun Apr 19
    week_start, week_end = _calculate_week_range(_today=date(2026, 4, 25))
    assert week_start == date(2026, 4, 13)
    assert week_end == date(2026, 4, 19)


def test_week_override_returns_7day_window():
    week_start, week_end = _calculate_week_range(week_override="2026-04-21")
    assert week_start == date(2026, 4, 21)
    assert week_end == date(2026, 4, 27)


def test_week_override_week_end_is_start_plus_6():
    week_start, week_end = _calculate_week_range(week_override="2026-01-05")
    assert (week_end - week_start).days == 6


# ── JQL builder functions ──────────────────────────────────────────────────────

def test_jql_done_contains_required_parts():
    jql = _build_jql_done("TEST", date(2026, 4, 21), date(2026, 4, 27))
    assert "TEST" in jql
    assert "status = Done" in jql
    assert "2026-04-21" in jql
    assert "2026-04-27" in jql
    assert "updated >=" in jql
    assert "updated <=" in jql


def test_jql_done_no_extra_date_parts():
    jql = _build_jql_done("TEST", date(2026, 4, 21), date(2026, 4, 27))
    # Both dates must appear exactly
    assert jql.count("2026-04-21") == 1
    assert jql.count("2026-04-27") == 1


def test_jql_in_progress_structure():
    jql = _build_jql_in_progress("TEST")
    assert "TEST" in jql
    assert "In Progress" in jql
    assert "updated" not in jql


def test_jql_planned_structure():
    jql = _build_jql_planned("TEST")
    assert "TEST" in jql
    assert "To Do" in jql
    assert "Backlog" in jql
    assert "Next" in jql
    assert "updated" not in jql


def test_project_key_override_in_all_jql():
    week_start, week_end = date(2026, 4, 21), date(2026, 4, 27)
    assert "ALPHA" in _build_jql_done("ALPHA", week_start, week_end)
    assert "ALPHA" in _build_jql_in_progress("ALPHA")
    assert "ALPHA" in _build_jql_planned("ALPHA")


def test_default_project_key_not_in_override_jql():
    week_start, week_end = date(2026, 4, 21), date(2026, 4, 27)
    assert "TEST" not in _build_jql_done("ALPHA", week_start, week_end)
    assert "TEST" not in _build_jql_in_progress("ALPHA")
    assert "TEST" not in _build_jql_planned("ALPHA")
