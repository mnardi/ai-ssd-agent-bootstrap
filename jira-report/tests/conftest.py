from datetime import date

import pytest
from jira_report.config import Config
from jira_report.jira_client import JiraData, JiraTicket


@pytest.fixture
def sample_config():
    return Config(
        jira_url="https://example.atlassian.net",
        api_token="test-token-not-real",
        api_key="test-anthropic-key-not-real",
        project_key="TEST",
        output_dir="./reports",
        ai_provider="anthropic",
        ai_model="claude-sonnet-4-6",
        report_tone="professional",
        project_name="Test Project",
    )


@pytest.fixture
def sample_jira_data():
    ticket = JiraTicket(key="TEST-1", summary="Sample ticket", assignee="Alice", status="Done")
    return JiraData(
        done=[ticket, ticket, ticket],
        in_progress=[ticket, ticket, ticket],
        planned=[ticket, ticket, ticket],
        week_start=date(2026, 4, 21),
        week_end=date(2026, 4, 27),
    )
