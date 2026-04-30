from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

import requests
from jira import JIRA, JIRAError

from jira_report.config import Config, JiraFetchError


@dataclass
class JiraTicket:
    key: str
    summary: str
    assignee: str
    status: str


@dataclass
class JiraData:
    done: list[JiraTicket]
    in_progress: list[JiraTicket]
    planned: list[JiraTicket]
    week_start: date
    week_end: date


@dataclass
class ReportSections:
    done_text: str
    in_progress_text: str
    next_plan_text: str
    executive_summary: str


DEFAULT_TIMEOUT_SECONDS = 10


def fetch_jira_data(config: Config, week_override: Optional[str] = None) -> JiraData:
    jira = _create_jira_client(config)
    _validate_project(jira, config)

    week_start, week_end = _calculate_week_range(week_override)
    jql_done = _build_jql_done(config.project_key, week_start, week_end)
    jql_in_progress = _build_jql_in_progress(config.project_key)
    jql_planned = _build_jql_planned(config.project_key)

    with ThreadPoolExecutor(max_workers=3) as executor:
        future_done = executor.submit(_fetch_tickets, jira, jql_done, "Done")
        future_in_progress = executor.submit(_fetch_tickets, jira, jql_in_progress, "In Progress")
        future_planned = executor.submit(_fetch_tickets, jira, jql_planned, "Planned")
        done_tickets = future_done.result()
        in_progress_tickets = future_in_progress.result()
        planned_tickets = future_planned.result()

    return JiraData(
        done=done_tickets,
        in_progress=in_progress_tickets,
        planned=planned_tickets,
        week_start=week_start,
        week_end=week_end,
    )


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


def _fetch_tickets(jira: JIRA, jql: str, label: str) -> list[JiraTicket]:
    try:
        issues = jira.search_issues(jql, maxResults=False, fields=["summary", "assignee", "status"])
    except JIRAError as e:
        raise JiraFetchError(f"Jira {label} query failed (status {e.status_code})")
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, OSError):
        raise JiraFetchError(f"Jira {label} query timed out — check jira_url in config.yaml")
    return [
        JiraTicket(
            key=issue.key,
            summary=issue.fields.summary,
            assignee=issue.fields.assignee.displayName if issue.fields.assignee else "Unassigned",
            status=issue.fields.status.name,
        )
        for issue in issues
    ]


def _calculate_week_range(
    week_override: Optional[str] = None,
    _today: Optional[date] = None,
) -> tuple[date, date]:
    if week_override:
        week_start = date.fromisoformat(week_override)
        return week_start, week_start + timedelta(days=6)

    today = _today or date.today()
    days_since_sunday = (today.weekday() + 1) % 7
    last_sunday = today - timedelta(days=days_since_sunday)
    week_start = last_sunday - timedelta(days=6)
    return week_start, last_sunday


def _build_jql_done(project_key: str, week_start: date, week_end: date) -> str:
    start_str = week_start.strftime("%Y-%m-%d")
    end_str = week_end.strftime("%Y-%m-%d")
    return (
        f'project = "{project_key}" AND status = Done '
        f'AND updated >= "{start_str}" AND updated <= "{end_str}"'
    )


def _build_jql_in_progress(project_key: str) -> str:
    return f'project = "{project_key}" AND status in ("In Progress")'


def _build_jql_planned(project_key: str) -> str:
    return f'project = "{project_key}" AND status in ("To Do", "Backlog", "Next")'
