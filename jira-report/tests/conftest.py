import pytest
from jira_report.config import Config


@pytest.fixture
def sample_config():
    return Config(
        jira_url="https://example.atlassian.net",
        api_token="test-token-not-real",
        project_key="TEST",
        output_dir="./reports",
        ai_provider="anthropic",
        ai_model="claude-sonnet-4-6",
        report_tone="professional",
        project_name="Test Project",
    )
