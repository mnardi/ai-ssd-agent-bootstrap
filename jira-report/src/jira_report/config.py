from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ValidationError

DEFAULT_MODEL = "claude-sonnet-4-6"


class JiraReportError(Exception): ...


class ConfigError(JiraReportError): ...


class JiraFetchError(JiraReportError): ...


class AIGenerationError(JiraReportError): ...


class OutputError(JiraReportError): ...


class Config(BaseModel):
    jira_url: str
    api_token: str  # CREDENTIAL — never log or format into strings
    project_key: str
    output_dir: str  # stored as str; renderer.py converts to Path
    ai_provider: str
    ai_model: str = DEFAULT_MODEL
    report_tone: str
    project_name: str


def load_config(path: Path) -> Config:
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        raise ConfigError(f"Invalid YAML in config file: {path}")
    if not isinstance(raw, dict):
        raise ConfigError(f"Config file must be a YAML mapping: {path}")
    try:
        return Config(**raw)
    except ValidationError as exc:
        first = exc.errors()[0]
        field = str(first.get("loc", ("unknown",))[0])
        error_type = first.get("type", "")
        if "missing" in error_type:
            raise ConfigError(f"Missing required field: {field}")
        raise ConfigError(f"Invalid value for field: {field}")
