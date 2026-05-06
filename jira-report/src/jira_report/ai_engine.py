from __future__ import annotations

from jira_report.config import Config, DEFAULT_MODEL
from jira_report.jira_client import JiraData, JiraTicket


def generate_report(config: Config, jira_data: JiraData):
    """Public entry point for AI report generation.

    Story 3.1 builds the prompt artifacts; Story 3.2 wires the Anthropic API call
    and returns a `ReportSections` instance.
    """
    raise NotImplementedError  # Story 3.2: Claude API call + ReportSections assembly


def _resolve_model(config: Config) -> str:
    return config.ai_model if config.ai_model else DEFAULT_MODEL


def _build_system_prompt(config: Config) -> str:
    return (
        f"You are a senior product manager writing the weekly executive status update "
        f"for the project '{config.project_name}'. "
        f"Write in a {config.report_tone} tone. "
        f"Translate Jira operational language into executive communication language: "
        f"focus on outcomes, business value, and forward-looking commitments — "
        f"not ticket statuses, sprint mechanics, or implementation details."
        f"\n\n"
        f"Produce exactly four sections in this order: "
        f"Done, In Progress, Next Plan, Executive Summary. "
        f"Each section is a paragraph (not a bullet list). "
        f"The Executive Summary synthesizes the week's narrative for a leadership audience."
    )


def _format_tickets(tickets: list[JiraTicket]) -> str:
    if not tickets:
        return "(none)"
    return "\n".join(
        f"- [{t.key}] {t.summary} — assignee: {t.assignee} — status: {t.status}"
        for t in tickets
    )


def _build_user_message(jira_data: JiraData) -> str:
    return (
        f"Reporting period: {jira_data.week_start.isoformat()} to "
        f"{jira_data.week_end.isoformat()}\n\n"
        f"## Done\n{_format_tickets(jira_data.done)}\n\n"
        f"## In Progress\n{_format_tickets(jira_data.in_progress)}\n\n"
        f"## Planned\n{_format_tickets(jira_data.planned)}\n\n"
        f"Generate the weekly status report. Produce exactly four sections "
        f"(Done, In Progress, Next Plan, Executive Summary) in executive "
        f"communication language."
    )
