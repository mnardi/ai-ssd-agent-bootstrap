from __future__ import annotations

from typing import Optional

import requests
from jira import JIRA, JIRAError

from jira_report.config import Config, JiraFetchError

DEFAULT_TIMEOUT_SECONDS = 10


def fetch_jira_data(config: Config, week_override: Optional[str] = None):
    jira = _create_jira_client(config)
    _validate_project(jira, config)
    raise NotImplementedError  # Story 2 implements data retrieval and return type


def _create_jira_client(config: Config) -> JIRA:
    try:
        return JIRA(
            server=config.jira_url,
            token_auth=config.api_token,
            timeout=DEFAULT_TIMEOUT_SECONDS,
            validate=True,
        )
    except JIRAError as e:
        if e.status_code in (401, 403):
            raise JiraFetchError("Jira authentication failed — check api_token in config.yaml")
        raise JiraFetchError(
            f"Jira connection failed (status {e.status_code}) — check jira_url in config.yaml"
        )
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, OSError):
        raise JiraFetchError("Network unreachable — check jira_url in config.yaml")


def _validate_project(jira: JIRA, config: Config) -> None:
    try:
        jira.project(config.project_key)
    except JIRAError as e:
        if e.status_code == 404:
            raise JiraFetchError(
                f"Project {config.project_key} not found — check project_key in config.yaml"
            )
        raise JiraFetchError(f"Jira error verifying project (status {e.status_code})")
