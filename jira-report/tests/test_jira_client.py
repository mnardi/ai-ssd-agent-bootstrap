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
