import pytest
import yaml
from pathlib import Path
from jira_report.config import (
    load_config,
    Config,
    JiraReportError,
    ConfigError,
    JiraFetchError,
    AIGenerationError,
    OutputError,
)

VALID_CONFIG = {
    "jira_url": "https://example.atlassian.net",
    "api_token": "test-token",
    "project_key": "TEST",
    "output_dir": "./reports",
    "ai_provider": "anthropic",
    "ai_model": "claude-sonnet-4-6",
    "report_tone": "professional",
    "project_name": "Test Project",
}


def _write_config(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / "config.yaml"
    p.write_text(yaml.dump(data), encoding="utf-8")
    return p


def test_load_config_valid(tmp_path):
    p = _write_config(tmp_path, VALID_CONFIG)
    config = load_config(p)
    assert isinstance(config, Config)
    assert config.jira_url == "https://example.atlassian.net"
    assert config.api_token == "test-token"
    assert config.project_key == "TEST"
    assert config.output_dir == "./reports"
    assert config.ai_provider == "anthropic"
    assert config.ai_model == "claude-sonnet-4-6"
    assert config.report_tone == "professional"
    assert config.project_name == "Test Project"


def test_load_config_default_ai_model(tmp_path):
    data = {k: v for k, v in VALID_CONFIG.items() if k != "ai_model"}
    p = _write_config(tmp_path, data)
    config = load_config(p)
    assert config.ai_model == "claude-sonnet-4-6"


def test_load_config_missing_field(tmp_path):
    data = {k: v for k, v in VALID_CONFIG.items() if k != "api_token"}
    p = _write_config(tmp_path, data)
    with pytest.raises(ConfigError, match="api_token"):
        load_config(p)


def test_load_config_missing_jira_url(tmp_path):
    data = {k: v for k, v in VALID_CONFIG.items() if k != "jira_url"}
    p = _write_config(tmp_path, data)
    with pytest.raises(ConfigError, match="jira_url"):
        load_config(p)


def test_load_config_file_not_found(tmp_path):
    missing = tmp_path / "missing.yaml"
    with pytest.raises(ConfigError, match=str(missing)):
        load_config(missing)


def test_load_config_invalid_yaml(tmp_path):
    p = tmp_path / "config.yaml"
    p.write_text("key: [unclosed", encoding="utf-8")
    with pytest.raises(ConfigError, match="Invalid YAML"):
        load_config(p)


def test_load_config_not_a_mapping(tmp_path):
    p = tmp_path / "config.yaml"
    p.write_text("- item1\n- item2\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="YAML mapping"):
        load_config(p)


def test_exception_hierarchy():
    assert issubclass(ConfigError, JiraReportError)
    assert issubclass(JiraFetchError, JiraReportError)
    assert issubclass(AIGenerationError, JiraReportError)
    assert issubclass(OutputError, JiraReportError)
    assert issubclass(JiraReportError, Exception)


def test_no_credentials_in_error(tmp_path):
    data = {k: v for k, v in VALID_CONFIG.items() if k != "project_key"}
    p = _write_config(tmp_path, data)
    with pytest.raises(ConfigError) as exc_info:
        load_config(p)
    assert VALID_CONFIG["api_token"] not in str(exc_info.value)
