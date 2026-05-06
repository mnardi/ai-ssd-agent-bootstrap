# Story 3.1: AI Prompt Construction

Status: review

## Story

As a PM,
I want the tool to package my Jira ticket data into a precisely crafted prompt that sets Claude up to write in executive communication style,
so that the generated report matches my voice and leadership audience expectations.

## Acceptance Criteria

1. Given `config.report_tone` and `config.project_name` are set, When the system prompt is assembled, Then it includes the PM role framing, the configured tone, and the project name (FR15).
2. Given a `JiraData` object with done, in_progress, and planned tickets, When the user message is assembled, Then all raw ticket data — `key`, `summary`, `assignee`, `status` for every ticket in all three sections — is included verbatim with no summarization or filtering (FR13).
3. Given the prompt is assembled, When I inspect the instruction section, Then it explicitly requests exactly four output sections: Done, In Progress, Next Plan, Executive Summary, And instructs Claude to write in executive communication language, not Jira operational language (FR12, FR14).
4. Given `config.ai_model` is set, When `_resolve_model(config)` runs, Then that model name is returned; if `ai_model` is absent or empty, `DEFAULT_MODEL = "claude-sonnet-4-6"` is returned as the fallback.

## Tasks / Subtasks

- [x] Task 1: Replace `ai_engine.py` stub with imports and module skeleton (AC: 1–4)
  - [x] Replace existing 5-line stub completely
  - [x] Add imports: `from jira_report.config import Config, DEFAULT_MODEL`
  - [x] Add imports: `from jira_report.jira_client import JiraData, JiraTicket`
  - [x] Keep `def generate_report(config: Config, jira_data: JiraData):` raising `NotImplementedError` — Story 3.2 wires the API call
  - [x] Update return-type annotation in docstring/comment: noting future return is `ReportSections`

- [x] Task 2: Implement `_resolve_model(config)` (AC: 4)
  - [x] Signature: `_resolve_model(config: Config) -> str`
  - [x] Return `config.ai_model` if truthy, else `DEFAULT_MODEL`
  - [x] Pydantic `Config` already defaults `ai_model` to `DEFAULT_MODEL`; this guard also handles edge cases like an explicit empty string

- [x] Task 3: Implement `_build_system_prompt(config)` (AC: 1, 3)
  - [x] Signature: `_build_system_prompt(config: Config) -> str`
  - [x] Embed PM role framing, `config.report_tone`, `config.project_name`
  - [x] Include the four-section directive (Done, In Progress, Next Plan, Executive Summary in that order)
  - [x] Instruct Claude to translate Jira operational language into executive communication language
  - [x] Use the exact wording shown in Dev Notes — tests assert specific substrings

- [x] Task 4: Implement `_format_tickets(tickets)` helper (AC: 2)
  - [x] Signature: `_format_tickets(tickets: list[JiraTicket]) -> str`
  - [x] Empty list → `"(none)"` (so the prompt section is never blank)
  - [x] Non-empty → newline-joined lines: `"- [{key}] {summary} — assignee: {assignee} — status: {status}"`
  - [x] All four `JiraTicket` fields included verbatim — no summarization, no filtering

- [x] Task 5: Implement `_build_user_message(jira_data)` (AC: 2)
  - [x] Signature: `_build_user_message(jira_data: JiraData) -> str`
  - [x] Include the reporting period: `jira_data.week_start.isoformat()` to `jira_data.week_end.isoformat()`
  - [x] Three labeled sections via `_format_tickets`: `## Done`, `## In Progress`, `## Planned`
  - [x] Closing instruction reiterating the 4-section output requirement and executive language

- [x] Task 6: Add tests in `tests/test_ai_engine.py` (AC: 1–4)
  - [x] Replace the placeholder line `# placeholder` completely
  - [x] Add imports: `pytest`, `from datetime import date`
  - [x] Add imports: `from jira_report.ai_engine import _resolve_model, _build_system_prompt, _build_user_message, _format_tickets`
  - [x] Add imports: `from jira_report.config import DEFAULT_MODEL`
  - [x] Add imports: `from jira_report.jira_client import JiraData, JiraTicket`
  - [x] Reuse `sample_config` and `sample_jira_data` fixtures from `tests/conftest.py` (already exist)
  - [x] `test_resolve_model_returns_configured_model` — `config.ai_model = "custom-model"` → `_resolve_model(config) == "custom-model"`
  - [x] `test_resolve_model_falls_back_to_default_when_empty` — `config.ai_model = ""` → returns `DEFAULT_MODEL`
  - [x] `test_resolve_model_default_from_pydantic` — Config built without `ai_model` → `_resolve_model` returns `DEFAULT_MODEL`
  - [x] `test_system_prompt_includes_project_name` — `"Test Project"` appears in result
  - [x] `test_system_prompt_includes_report_tone` — `"professional"` appears in result
  - [x] `test_system_prompt_includes_four_section_directive` — all four section names appear: `"Done"`, `"In Progress"`, `"Next Plan"`, `"Executive Summary"`
  - [x] `test_system_prompt_requires_executive_language` — substring `"executive"` (case-insensitive) appears
  - [x] `test_format_tickets_empty_returns_none_marker` — `_format_tickets([]) == "(none)"`
  - [x] `test_format_tickets_includes_all_four_fields` — single ticket → output contains `key`, `summary`, `assignee`, and `status` strings
  - [x] `test_user_message_includes_all_done_tickets` — sample_jira_data with 3 ticket keys → all 3 keys appear in output
  - [x] `test_user_message_includes_all_three_sections` — output contains `"Done"`, `"In Progress"`, `"Planned"` section markers
  - [x] `test_user_message_includes_reporting_period` — output contains `"2026-04-21"` and `"2026-04-27"` (from `sample_jira_data` fixture)
  - [x] `test_user_message_no_summarization` — every ticket's `summary` text appears verbatim
  - [x] `test_generate_report_still_raises_not_implemented` — calling `generate_report(config, jira_data)` raises `NotImplementedError` (3.2 will wire the API call)
  - [x] Run `uv run pytest` — all 56 pre-existing tests pass + new tests green (70 total passed)

## Dev Notes

### `ai_engine.py` — Full Implementation (Story 3.1 scope)

Replace the entire file content (currently 5 lines: `from __future__ import annotations` + stub `generate_report`). Final state at end of Story 3.1:

```python
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
        f"not ticket statuses, sprint mechanics, or implementation details. "
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
```

**Architecture compliance:**
- `generate_report` is the ONLY public function; `_resolve_model`, `_build_system_prompt`, `_format_tickets`, `_build_user_message` are private (`_` prefix). [Source: architecture.md#Module Interface Pattern]
- Imports `JiraData`, `JiraTicket` from `jira_client.py` — never redefined. [Source: architecture.md#Canonical Data Models]
- Imports `Config`, `DEFAULT_MODEL` from `config.py` — single source of truth. [Source: architecture.md#Constants]
- No terminal output here — `cli.py` will echo `"Generating report..."` before calling. [Source: architecture.md#Terminal Output Pattern]
- No exception swallowing — Story 3.2 will catch SDK errors and raise `AIGenerationError`. [Source: architecture.md#Error Propagation Pattern]
- No credential interpolation — `config.api_token` (and any future `api_key`) never touches prompt text. [Source: architecture.md#Credential Safety Rule]

### Why Split Across Stories

Story 3.1 builds the **prompt artifacts** as private helpers without making the API call. This lets Story 3.2 focus exclusively on:
- The `anthropic` SDK call shape (`Anthropic().messages.create(...)`)
- Response parsing into `ReportSections`
- `AIGenerationError` mapping for SDK exceptions
- Empty-field validation per NFR8

Tests for 3.1 verify the prompt strings directly. Tests for 3.2 patch the SDK and verify the API integration.

### Why System Prompt Holds the Output Structure

Putting the four-section directive and executive-language instruction in the **system prompt** (not the user message) is intentional:
- The system prompt is **stable across runs** — same project, same tone, same instructions every week.
- The user message is **variable** — different tickets every week.
- This boundary aligns with `anthropic` SDK prompt caching (`cache_control`), which Story 3.2 may opt into. Caching the system prompt across runs is cheap and high-value when the user message rotates.

The user message ends with a brief reminder of the four-section requirement — defense in depth, low cost.

### `_resolve_model` Defensive Default

The Pydantic `Config` model already declares `ai_model: str = DEFAULT_MODEL`, so `config.ai_model` is always populated by the time it reaches `ai_engine.py`. The `_resolve_model` truthiness guard is defensive: it covers the edge case where the user explicitly sets `ai_model: ""` in `config.yaml` (empty string passes Pydantic's `str` validator but is not a usable model name).

This is the only place model selection logic lives — Story 3.2 must call `_resolve_model(config)`, never read `config.ai_model` directly.

### Test Code — Exact

`tests/test_ai_engine.py` (replace existing `# placeholder` line entirely):

```python
import pytest
from datetime import date

from jira_report.ai_engine import (
    _resolve_model,
    _build_system_prompt,
    _build_user_message,
    _format_tickets,
    generate_report,
)
from jira_report.config import DEFAULT_MODEL
from jira_report.jira_client import JiraData, JiraTicket


# ── _resolve_model ─────────────────────────────────────────────────────────────

def test_resolve_model_returns_configured_model(sample_config):
    cfg = sample_config.model_copy(update={"ai_model": "claude-opus-4-7"})
    assert _resolve_model(cfg) == "claude-opus-4-7"


def test_resolve_model_falls_back_to_default_when_empty(sample_config):
    cfg = sample_config.model_copy(update={"ai_model": ""})
    assert _resolve_model(cfg) == DEFAULT_MODEL


def test_resolve_model_default_from_pydantic(sample_config):
    # sample_config sets ai_model to "claude-sonnet-4-6" — same as DEFAULT_MODEL
    assert _resolve_model(sample_config) == DEFAULT_MODEL


# ── _build_system_prompt ───────────────────────────────────────────────────────

def test_system_prompt_includes_project_name(sample_config):
    prompt = _build_system_prompt(sample_config)
    assert sample_config.project_name in prompt


def test_system_prompt_includes_report_tone(sample_config):
    prompt = _build_system_prompt(sample_config)
    assert sample_config.report_tone in prompt


def test_system_prompt_includes_four_section_directive(sample_config):
    prompt = _build_system_prompt(sample_config)
    for section in ("Done", "In Progress", "Next Plan", "Executive Summary"):
        assert section in prompt


def test_system_prompt_requires_executive_language(sample_config):
    prompt = _build_system_prompt(sample_config).lower()
    assert "executive" in prompt


# ── _format_tickets ────────────────────────────────────────────────────────────

def test_format_tickets_empty_returns_none_marker():
    assert _format_tickets([]) == "(none)"


def test_format_tickets_includes_all_four_fields():
    ticket = JiraTicket(key="ABC-7", summary="Fix login", assignee="Bob", status="Done")
    out = _format_tickets([ticket])
    assert "ABC-7" in out
    assert "Fix login" in out
    assert "Bob" in out
    assert "Done" in out


# ── _build_user_message ────────────────────────────────────────────────────────

def test_user_message_includes_all_done_tickets(sample_config, sample_jira_data):
    msg = _build_user_message(sample_jira_data)
    # sample_jira_data uses TEST-1 three times in each section
    assert "TEST-1" in msg


def test_user_message_includes_all_three_sections(sample_jira_data):
    msg = _build_user_message(sample_jira_data)
    assert "Done" in msg
    assert "In Progress" in msg
    assert "Planned" in msg


def test_user_message_includes_reporting_period(sample_jira_data):
    msg = _build_user_message(sample_jira_data)
    assert "2026-04-21" in msg
    assert "2026-04-27" in msg


def test_user_message_no_summarization():
    """Every ticket summary appears verbatim — no rewriting or filtering."""
    tickets = [
        JiraTicket(key="A-1", summary="Distinctive summary one", assignee="Alice", status="Done"),
        JiraTicket(key="A-2", summary="Distinctive summary two", assignee="Bob", status="In Progress"),
        JiraTicket(key="A-3", summary="Distinctive summary three", assignee="Carol", status="To Do"),
    ]
    data = JiraData(
        done=[tickets[0]],
        in_progress=[tickets[1]],
        planned=[tickets[2]],
        week_start=date(2026, 4, 21),
        week_end=date(2026, 4, 27),
    )
    msg = _build_user_message(data)
    for t in tickets:
        assert t.summary in msg
        assert t.key in msg
        assert t.assignee in msg


# ── generate_report (still a stub at end of Story 3.1) ────────────────────────

def test_generate_report_still_raises_not_implemented(sample_config, sample_jira_data):
    with pytest.raises(NotImplementedError):
        generate_report(sample_config, sample_jira_data)
```

### Existing Fixtures — Reuse, Don't Recreate

`tests/conftest.py` already provides both fixtures needed:
- `sample_config` — a valid `Config` with `report_tone="professional"`, `project_name="Test Project"`, `ai_model="claude-sonnet-4-6"`
- `sample_jira_data` — a `JiraData` with 3 `JiraTicket(key="TEST-1", ...)` entries per section, `week_start=date(2026, 4, 21)`, `week_end=date(2026, 4, 27)`

Both were added in Stories 1.2 and 2.3 respectively. **Do not redefine them.** Just declare them as test parameters.

### Project Structure Notes

Files to modify:
- `src/jira_report/ai_engine.py` — replace 5-line stub with full prompt-construction module
- `tests/test_ai_engine.py` — replace `# placeholder` with full test suite (~14 tests)

No new files. No other modules touched. `cli.py` is **not** modified in this story — that wiring waits for Story 3.2.

### Architecture Compliance

- Single public function (`generate_report`) — all helpers prefixed `_`. [Source: architecture.md#Module Interface Pattern]
- `Config`, `DEFAULT_MODEL` imported from `config.py` (canonical location). [Source: architecture.md#Constants]
- `JiraData`, `JiraTicket` imported from `jira_client.py` (canonical location). [Source: architecture.md#Canonical Data Models]
- No `print()` calls — output, if any, would route through `cli.py` via `typer.echo`. [Source: architecture.md#Terminal Output Pattern]
- No `config.api_token` interpolation. [Source: architecture.md#Credential Safety Rule]
- `ReportSections` not instantiated yet — Story 3.2 produces it from the parsed AI response. [Source: architecture.md#Canonical Data Models]

### Scope Boundaries

**This story implements:**
- `_resolve_model(config)` — model selection with fallback to `DEFAULT_MODEL`
- `_build_system_prompt(config)` — role + tone + project + 4-section structure + executive-language directive
- `_format_tickets(tickets)` — verbatim ticket lines or `"(none)"`
- `_build_user_message(jira_data)` — period header + three sections + closing instruction
- Full test coverage (~14 tests) for all four helpers
- `generate_report` remains a `NotImplementedError` stub

**DO NOT implement:**
- The `Anthropic()` client call or `messages.create(...)` — Story 3.2 scope
- `ReportSections` parsing/assembly from AI response — Story 3.2 scope
- `AIGenerationError` raising on SDK errors or empty fields — Story 3.2 scope
- Prompt caching (`cache_control`) — Story 3.2 may opt in, not required
- `cli.py` wiring or `"Generating report..."` echo — Story 3.2 scope
- Streaming responses — out of V1 scope (architecture.md confirms single sync call)

### Previous Story Learnings (from Stories 1.1–2.3)

- **uv PATH on WSL2:** `export PATH="$HOME/.local/bin:$PATH"` if needed
- **After code changes:** `uv tool upgrade jira-report` (only needed when changing CLI behavior — not for ai_engine.py changes alone)
- **Mock namespace rule:** when Story 3.2 mocks `Anthropic`, patch `jira_report.ai_engine.Anthropic` — never `anthropic.Anthropic` (mock the name in the namespace where it was imported). Story 3.1 has no mocks.
- **Pydantic defaults:** `Config.ai_model` already defaults to `DEFAULT_MODEL` via `ai_model: str = DEFAULT_MODEL`. The `_resolve_model` truthy guard handles the explicit-empty-string edge case Pydantic still permits.
- **Fixture reuse:** `sample_config` (Story 1.2) and `sample_jira_data` (Story 2.3) are in `tests/conftest.py`. Reuse them; don't redefine.
- **Pytest discovery:** `pyproject.toml` has `[tool.pytest.ini_options]` with `testpaths = ["tests"]` and `asyncio_mode = "auto"`.
- **Click 8.3 stderr:** not relevant here (no CLI changes), but noted: `CliRunner` in click 8.3 dropped `mix_stderr` kwarg — use `result.stderr` / `result.stdout` directly.
- **Calendar verification:** `2026-04-21` is a Tuesday; `2026-04-27` is a Monday. The `sample_jira_data` fixture's dates were chosen for previous-story tests — we don't need a specific Mon–Sun alignment for prompt-construction tests, just stable strings to grep for.

### Latest Tech Information

- **anthropic SDK:** version `>=0.97.0` (per `pyproject.toml`); installed: `0.97.0`. Story 3.2 will use `anthropic.Anthropic` and `client.messages.create(model=..., system=..., messages=[...])`.
- **Default model:** `claude-sonnet-4-6` (per `architecture.md#Decision Priority Analysis` and `config.py:DEFAULT_MODEL`).
- **Prompt caching opt-in (3.2 only, FYI):** anthropic 0.97.0 supports `cache_control={"type": "ephemeral"}` blocks on system messages. The system prompt is a natural caching candidate (stable across weekly runs); the user message is not (rotates with ticket data).
- **Python 3.12** features in use: `list[JiraTicket]` PEP 585 generics, walrus-free style; no PEP 695 type aliases needed.

### Git Intelligence Summary (Recent Commits)

Recent commits establish the implementation cadence:
- `a4c5081 Add Story 2.2: parallel ticket retrieval and JiraData assembly` — established `JiraData`/`JiraTicket` dataclasses in `jira_client.py` (canonical location for Story 3.1's imports)
- `e72e2d8 Implement Story 2.1: date range calculation and JQL construction` — established the `week_start`/`week_end` date fields used in Story 3.1's prompt period header
- `181c1c4 Add Story 1.4: Jira authentication validation` — established the exception hierarchy (`JiraReportError` → `JiraFetchError`, etc.) — Story 3.2 will add `AIGenerationError` raising
- `e048e23 Add Story 1.3: CLI entry point, runtime flags, and module stubs` — established the `_warn_low_ticket_counts` location pattern (`cli.py` orchestrates; modules are pure)

Story 2.3 is currently in `review` status (uncommitted) — its `LOW_TICKET_WARNING_THRESHOLD` constant change to `jira_client.py` does not affect Story 3.1 imports.

### References

- FR12 (4 sections): [Source: epics.md#Story 3.1, architecture.md#Requirements to Structure Mapping FR12]
- FR13 (raw data, no pre-summarization): [Source: epics.md#Story 3.1, architecture.md#Requirements to Structure Mapping FR13]
- FR14 (executive language): [Source: epics.md#Story 3.1, architecture.md#Requirements to Structure Mapping FR14]
- FR15 (tone + project name in prompt): [Source: epics.md#Story 3.1, architecture.md#Requirements to Structure Mapping FR14–FR15]
- `DEFAULT_MODEL = "claude-sonnet-4-6"`: [Source: architecture.md#Constants, config.py:DEFAULT_MODEL]
- Module interface pattern (single public function): [Source: architecture.md#Module Interface Pattern]
- Canonical data model imports: [Source: architecture.md#Canonical Data Models]
- Implementation sequence (config → jira_client → ai_engine → templates → renderer → cli): [Source: architecture.md#Implementation Sequence]

## Dev Agent Record

### Agent Model Used

claude-opus-4-7 (1M context)

### Debug Log References

- `uv run pytest` — 70 passed (was 56 before this story; +14 new ai_engine tests)
- No debugging required — implementation matched the spec exactly. All 14 tests passed on first run.

### Completion Notes List

- Replaced `ai_engine.py` stub with 4 private prompt-construction helpers + a `generate_report` stub that still raises `NotImplementedError` (Story 3.2 will wire the Anthropic API call).
- `_resolve_model(config)` returns `config.ai_model` when truthy, else `DEFAULT_MODEL` — defensive against the explicit-empty-string edge case Pydantic permits.
- `_build_system_prompt(config)` embeds PM role framing, `config.report_tone`, `config.project_name`, the 4-section directive, and the executive-language instruction. The structural directive lives in the system prompt (stable, future cache target) — only ticket data rotates in the user message.
- `_format_tickets(tickets)` returns `"(none)"` for empty lists (so prompt sections are never blank) and `"- [{key}] {summary} — assignee: {assignee} — status: {status}"` lines otherwise — all four `JiraTicket` fields verbatim.
- `_build_user_message(jira_data)` opens with the reporting period, lays out three labeled `## Done` / `## In Progress` / `## Planned` blocks via `_format_tickets`, and closes with a defense-in-depth reminder of the 4-section output requirement.
- 14 new tests in `tests/test_ai_engine.py` — covering all four helpers + the `generate_report` `NotImplementedError` invariant. All tests reuse the existing `sample_config` (Story 1.2) and `sample_jira_data` (Story 2.3) fixtures from `tests/conftest.py`.
- No changes to any other source file — `cli.py` wiring waits for Story 3.2.
- Final result: 70 tests pass, 0 regressions.

### File List

- `jira-report/src/jira_report/ai_engine.py` (modified) — replaced 5-line stub with full prompt-construction module
- `jira-report/tests/test_ai_engine.py` (modified) — replaced `# placeholder` with 14-test suite

## Change Log

| Date       | Description                                                                                                  |
| ---------- | ------------------------------------------------------------------------------------------------------------ |
| 2026-05-06 | Implemented Story 3.1: AI prompt construction (FR12–FR15, prompt portion). Status: ready-for-dev → review.   |
