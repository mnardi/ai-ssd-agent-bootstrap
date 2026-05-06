from __future__ import annotations

import re

from anthropic import Anthropic, APIError

from jira_report.config import AIGenerationError, Config, DEFAULT_MODEL
from jira_report.jira_client import JiraData, JiraTicket, ReportSections


_SECTION_HEADERS = ("Done", "In Progress", "Next Plan", "Executive Summary")
_SECTION_REGEX = re.compile(
    r"^##\s+(" + "|".join(re.escape(h) for h in _SECTION_HEADERS) + r")\s*$",
    re.MULTILINE,
)
_MAX_TOKENS = 4096


def generate_report(config: Config, jira_data: JiraData) -> ReportSections:
    client = _create_anthropic_client(config)
    system_prompt = _build_system_prompt(config)
    user_message = _build_user_message(jira_data)

    try:
        response = client.messages.create(
            model=_resolve_model(config),
            max_tokens=_MAX_TOKENS,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
    except APIError as e:
        raise AIGenerationError(f"Claude API call failed: {e.__class__.__name__}")
    except Exception as e:
        raise AIGenerationError(f"Claude SDK error: {e.__class__.__name__}")

    if not response.content:
        raise AIGenerationError("Claude API returned empty response")
    text = response.content[0].text
    if not text or not text.strip():
        raise AIGenerationError("Claude API returned empty response")

    sections = _parse_response(text)

    for field_name, value in (
        ("done_text", sections.done_text),
        ("in_progress_text", sections.in_progress_text),
        ("next_plan_text", sections.next_plan_text),
        ("executive_summary", sections.executive_summary),
    ):
        if not value:
            raise AIGenerationError(f"Empty section in AI response: {field_name}")

    return sections


def _create_anthropic_client(config: Config) -> Anthropic:
    return Anthropic(api_key=config.api_key)


def _parse_response(text: str) -> ReportSections:
    matches = list(_SECTION_REGEX.finditer(text))
    if len(matches) != len(_SECTION_HEADERS):
        raise AIGenerationError(f"Expected 4 sections, found {len(matches)}")

    bodies: dict[str, str] = {}
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        bodies[m.group(1)] = text[start:end].strip()

    return ReportSections(
        done_text=bodies["Done"],
        in_progress_text=bodies["In Progress"],
        next_plan_text=bodies["Next Plan"],
        executive_summary=bodies["Executive Summary"],
    )


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
        f"Produce exactly four sections in this order, each preceded by a Markdown "
        f"level-2 header on its own line, using these exact strings: "
        f"'## Done', '## In Progress', '## Next Plan', '## Executive Summary'. "
        f"Each section body is a paragraph (not a bullet list). "
        f"Do not include any text before the first header or after the last section's body. "
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
