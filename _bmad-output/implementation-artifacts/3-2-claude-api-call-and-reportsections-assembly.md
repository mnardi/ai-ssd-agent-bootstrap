# Story 3.2: Claude API Call & ReportSections Assembly

Status: review

## Story

As a PM,
I want the tool to call Claude with my prompt and return a complete, validated report — or fail loudly if anything goes wrong,
so that I always get a usable draft or a clear error, never silent empty output.

## Acceptance Criteria

1. Given a fully assembled prompt and `JiraData`, When `generate_report(config, jira_data)` is called, Then a single synchronous call is made to the Anthropic API using the `anthropic` SDK, And `cli.py` prints `"Generating report..."` to stdout before the call begins (NFR3).
2. Given the API call returns a response, When the response is parsed, Then it is mapped into `ReportSections(done_text, in_progress_text, next_plan_text, executive_summary)` (FR12).
3. Given the parsed response has any empty field, When validation runs before returning, Then an `AIGenerationError` is raised identifying which field is empty, And no `ReportSections` object is returned (NFR8).
4. Given the API call fails (connection error, auth failure, rate limit), When the exception is caught, Then an `AIGenerationError` is raised with a specific message describing the failure, And no partial output is returned — the pipeline exits cleanly (NFR8).
5. Given a successful `generate_report()` call, When the returned `ReportSections` text is reviewed, Then each section reads in executive communication language — not raw ticket summaries (FR14).

## Tasks / Subtasks

- [x] Task 1: Add `api_key` field to Config and surface it in the example (AC: 1, 4)
  - [x] Add `api_key: str` to `Config` (required, no default — required because runs without a key cannot succeed)
  - [x] Place it immediately after `api_token` in the model definition (groups credentials)
  - [x] Update `config.yaml.example`: add line `api_key: your-anthropic-api-key-here` after `api_token`
  - [x] No `Config` field reordering beyond inserting `api_key` after `api_token`

- [x] Task 2: Update `sample_config` fixture in `tests/conftest.py` (AC: 1, regression safety)
  - [x] Add `api_key="test-anthropic-key-not-real"` to the `Config(...)` call
  - [x] Place after `api_token=...` to mirror the model order

- [x] Task 3: Update `VALID_CONFIG` in `tests/test_config.py` and add an `api_key` field test (AC: 1, regression safety)
  - [x] Add `"api_key": "test-anthropic-key"` to `VALID_CONFIG`
  - [x] Update `test_load_config_valid`: assert `config.api_key == "test-anthropic-key"`
  - [x] Add `test_load_config_missing_api_key` mirroring `test_load_config_missing_field`: drop `api_key`, expect `ConfigError` matching `"api_key"`
  - [x] Update `test_no_credentials_in_error`: also assert `VALID_CONFIG["api_key"]` not in error string

- [x] Task 4: Tighten `_build_system_prompt` to specify exact section headers (AC: 2)
  - [x] Replace the closing block in `_build_system_prompt` (the part starting with `"Produce exactly four sections in this order:"`) with the precise instructions shown in Dev Notes
  - [x] Existing Story 3.1 tests still pass (they assert substring presence — adding text doesn't break them)
  - [x] No other changes to `_resolve_model`, `_format_tickets`, `_build_user_message`

- [x] Task 5: Implement `_create_anthropic_client(config)` (AC: 1, 4)
  - [x] Signature: `_create_anthropic_client(config: Config) -> Anthropic`
  - [x] Add module-level import `from anthropic import Anthropic, APIError`
  - [x] Return `Anthropic(api_key=config.api_key)` — never reference `config.api_key` outside this function
  - [x] No try/except here — let `Anthropic.__init__` errors propagate (caller wraps)

- [x] Task 6: Implement `_parse_response(text)` (AC: 2, 3)
  - [x] Signature: `_parse_response(text: str) -> ReportSections`
  - [x] Use a single multiline regex to find all four `## Done` / `## In Progress` / `## Next Plan` / `## Executive Summary` headers
  - [x] Section body = text from end-of-header to start-of-next-header (or EOF for last); `.strip()` each body
  - [x] If fewer than 4 headers matched → `raise AIGenerationError(f"Expected 4 sections, found {n}")`
  - [x] Return `ReportSections(done_text=..., in_progress_text=..., next_plan_text=..., executive_summary=...)` — imported from `jira_client.py`

- [x] Task 7: Implement `generate_report(config, jira_data) -> ReportSections` (AC: 1–5)
  - [x] Replace the `NotImplementedError` body
  - [x] Build system prompt + user message via existing helpers
  - [x] Wrap the SDK call in `try/except APIError` → `raise AIGenerationError(f"Claude API call failed: {e.__class__.__name__}: {str(e)}")`
  - [x] Also wrap in `try/except Exception` for non-APIError SDK paths (e.g., `APIConnectionError` may not be a subclass of `APIError` in all versions) — catch `Exception` last and re-raise as `AIGenerationError(f"Claude SDK error: {e.__class__.__name__}")`. Never let a raw SDK exception escape.
  - [x] Use `max_tokens=4096`
  - [x] Extract response text: `text = message.content[0].text` (with empty-content guard — see next subtask)
  - [x] If `not message.content` or content text is empty/whitespace → `raise AIGenerationError("Claude API returned empty response")`
  - [x] Call `_parse_response(text)` to get a `ReportSections`
  - [x] Validate every field non-empty: iterate over `[("done_text", s.done_text), ...]`; first empty field → `raise AIGenerationError(f"Empty section in AI response: {field_name}")`
  - [x] Return the validated `ReportSections`

- [x] Task 8: Update existing CLI tests that may break with `generate_report` no longer a stub (AC: regression safety)
  - [x] `test_dry_run_flag`, `test_success_prints_saved_path`, all 6 low-ticket-warning tests — all already patch `jira_report.cli.generate_report`, so they should keep working unchanged
  - [x] Run `uv run pytest` to confirm no regressions in the cli/jira_client/config test suites

- [x] Task 9: Update Story 3.1's `generate_report` `NotImplementedError` test (AC: regression cleanup)
  - [x] Delete `test_generate_report_still_raises_not_implemented` from `tests/test_ai_engine.py` — `generate_report` is now implemented
  - [x] No replacement test needed at this exact name; `test_generate_report_returns_report_sections` (Task 10) supersedes it

- [x] Task 10: Add tests in `tests/test_ai_engine.py` (AC: 1–4)
  - [x] Add imports: `from unittest.mock import MagicMock, patch`, `from jira_report.config import AIGenerationError`, `from jira_report.jira_client import ReportSections`
  - [x] Helper `_make_anthropic_response(text)` — returns a `MagicMock` with `.content[0].text = text`
  - [x] `test_generate_report_returns_report_sections` — patch `jira_report.ai_engine.Anthropic`, return `_make_anthropic_response("## Done\nDone body\n\n## In Progress\nIP body\n\n## Next Plan\nNP body\n\n## Executive Summary\nES body")` → assert returned `ReportSections` has exact field values
  - [x] `test_generate_report_uses_resolved_model` — patch SDK, override `config.ai_model = "custom-x"`, capture `messages.create` kwargs, assert `model == "custom-x"`
  - [x] `test_generate_report_uses_default_model_when_empty` — `config.ai_model = ""` → assert `model == DEFAULT_MODEL`
  - [x] `test_generate_report_passes_system_and_user_message` — capture `messages.create` kwargs, assert `system` is a non-empty string and `messages[0]["role"] == "user"` with non-empty content
  - [x] `test_generate_report_raises_on_empty_response_content` — return `MagicMock(content=[])` → `AIGenerationError` with `"empty"` in message
  - [x] `test_generate_report_raises_on_whitespace_only_response` — return response with text `"   \n  \n"` → `AIGenerationError`
  - [x] `test_generate_report_raises_on_missing_sections` — return response with only `"## Done\nbody"` → `AIGenerationError` with `"4 sections"` or `"section"` in message
  - [x] `test_generate_report_raises_on_empty_section_body` — return response with all 4 headers but `## Next Plan` body blank → `AIGenerationError` with `"next_plan_text"` in message
  - [x] `test_generate_report_wraps_api_error` — make `messages.create` raise `anthropic.APIError(...)` → `AIGenerationError` with `"APIError"` substring or `"Claude API call failed"`. Use `pytest.raises(AIGenerationError)` and inspect message
  - [x] `test_generate_report_wraps_unexpected_exception` — `messages.create` raises `RuntimeError("boom")` → `AIGenerationError` (not `RuntimeError`)
  - [x] `test_parse_response_strips_whitespace` — `_parse_response("## Done\n  body  \n\n## In Progress\nip\n\n## Next Plan\nnp\n\n## Executive Summary\nes")` → `done_text == "body"` (trimmed)
  - [x] `test_create_anthropic_client_uses_api_key` — patch `Anthropic` class, call `_create_anthropic_client(config)`, assert `Anthropic.__init__` called with `api_key=config.api_key`
  - [x] `test_api_key_never_in_error_messages` — make `messages.create` raise an exception whose message contains the api_key value; assert resulting `AIGenerationError` message does NOT contain the api_key (credential safety: NFR4)
  - [x] Run `uv run pytest` — all 70 pre-existing tests pass + new tests green

## Dev Notes

### `Config` Schema Change — `api_key` Field

The architecture document explicitly states:

> Claude: API key sourced from `config.yaml` field `api_key` — never logged, never printed to terminal

But the field is missing from both `src/jira_report/config.py` and `config.yaml.example`. This is a **planning gap** — Story 3.2 fills it. The field is **required** (no default): a missing API key cannot be silently defaulted to a working value.

```python
# config.py — final state of Config
class Config(BaseModel):
    jira_url: str
    api_token: str  # CREDENTIAL — Jira; never log or format into strings
    api_key: str    # CREDENTIAL — Anthropic; never log or format into strings  ← NEW
    project_key: str
    output_dir: str
    ai_provider: str
    ai_model: str = DEFAULT_MODEL
    report_tone: str
    project_name: str
```

```yaml
# config.yaml.example — final state
jira_url: https://yourcompany.atlassian.net
api_token: your-jira-api-token-here
api_key: your-anthropic-api-key-here   # ← NEW
project_key: PROJ
output_dir: ./reports
ai_provider: anthropic
ai_model: claude-sonnet-4-6
report_tone: professional
project_name: Project Alpha
```

### `_build_system_prompt` Update — Exact Section Markers

Story 3.1 left the structural directive at "Produce exactly four sections in this order: Done, In Progress, Next Plan, Executive Summary. Each section is a paragraph". For deterministic parsing, Story 3.2 tightens this. Replace the closing block in `_build_system_prompt`:

```python
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
```

**Why pinning the marker format matters:** the `_parse_response` helper in this story uses a regex anchored to `^##\s+<name>\s*$` (multiline). Any deviation — different header level, omitted/added words, code-fence wrapping — breaks parsing. The instruction "do not include text before/after" prevents Claude from prefacing the report with a "Here is your weekly report:" line that would land in `done_text` if not anchored.

**Story 3.1 test impact:** the existing tests assert *substring presence* (`"Done" in prompt`, `"executive" in prompt.lower()`) — adding more text doesn't break them. No Story 3.1 test changes needed.

### `ai_engine.py` — Final State (Story 3.2 scope)

```python
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


def generate_report(config: Config, jira_data: JiraData) -> ReportSections:
    client = _create_anthropic_client(config)
    system_prompt = _build_system_prompt(config)
    user_message = _build_user_message(jira_data)

    try:
        response = client.messages.create(
            model=_resolve_model(config),
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
    except APIError as e:
        raise AIGenerationError(f"Claude API call failed: {e.__class__.__name__}")
    except Exception as e:
        # Defensive: SDK may raise types outside APIError (e.g., APIConnectionError
        # in some versions, transport errors). Never let a raw SDK exception escape.
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
        raise AIGenerationError(
            f"Expected 4 sections, found {len(matches)}"
        )

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


# ── Story 3.1 helpers (unchanged except _build_system_prompt update — see Task 4) ──

def _resolve_model(config: Config) -> str:
    return config.ai_model if config.ai_model else DEFAULT_MODEL


def _build_system_prompt(config: Config) -> str:
    # See "_build_system_prompt Update" above — replace closing block with exact markers
    ...


def _format_tickets(tickets: list[JiraTicket]) -> str:
    # Unchanged from Story 3.1
    ...


def _build_user_message(jira_data: JiraData) -> str:
    # Unchanged from Story 3.1
    ...
```

### Why Catch Both `APIError` and `Exception`

The `anthropic` SDK 0.97 surface includes:
- `anthropic.APIError` — base for all server-side errors (4xx/5xx)
- `anthropic.APIConnectionError` — transport-level failures
- `anthropic.APITimeoutError` — request timeouts
- `anthropic.AuthenticationError` — 401/403 (subclass of `APIError`)
- `anthropic.RateLimitError` — 429 (subclass of `APIError`)
- `anthropic.BadRequestError` — 400 (subclass of `APIError`)

In SDK 0.97, all of these are subclasses of `anthropic.APIError`. **However**, the ordering of `except APIError` then `except Exception` is the credential-safe defense-in-depth pattern: any error raised before the API call (e.g., `Anthropic.__init__` raising `httpx`-level errors during client construction in some versions, or our own `_create_anthropic_client` failures) will still be wrapped. The `Exception` catch must come **second** (Python's `except` ordering) so `APIError` matches first when applicable.

**Critical: `AIGenerationError` messages must NEVER contain `config.api_key`.** Use `e.__class__.__name__` only — do not include `str(e)` if there's any chance the SDK exception message contains the key. Production SDK exceptions have been observed to include the key in some auth-failure paths. The `test_api_key_never_in_error_messages` test enforces this.

### `_parse_response` — Regex Detail

```python
re.compile(
    r"^##\s+(Done|In\ Progress|Next\ Plan|Executive\ Summary)\s*$",
    re.MULTILINE,
)
```

- `^` and `$` are line anchors with `re.MULTILINE`
- `##\s+` requires "## " then any whitespace
- The header alternatives are `re.escape`'d to handle the spaces correctly
- `\s*$` allows trailing whitespace on the header line

The four section bodies are extracted by slicing between consecutive header matches. `body.strip()` handles surrounding blank lines.

If Claude **shuffles** section order (e.g., emits `## Executive Summary` first), `_parse_response` still finds them — they map by name to the correct `ReportSections` field. The parser does NOT enforce order; the system prompt does (and dev review of report content will catch deviations).

### Mocking `Anthropic` in Tests

```python
@patch("jira_report.ai_engine.Anthropic")
def test_generate_report_returns_report_sections(mock_anthropic_cls, sample_config, sample_jira_data):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=(
        "## Done\nDone body paragraph.\n\n"
        "## In Progress\nIP body paragraph.\n\n"
        "## Next Plan\nNP body paragraph.\n\n"
        "## Executive Summary\nES body paragraph."
    ))]
    mock_client.messages.create.return_value = mock_response

    sections = generate_report(sample_config, sample_jira_data)

    assert sections.done_text == "Done body paragraph."
    assert sections.in_progress_text == "IP body paragraph."
    assert sections.next_plan_text == "NP body paragraph."
    assert sections.executive_summary == "ES body paragraph."
```

**Patch namespace rule (continued from prior stories):** patch `jira_report.ai_engine.Anthropic`, NOT `anthropic.Anthropic`. The `Anthropic` symbol is imported into `ai_engine`'s namespace at module load — patches must target where the name is **used**, not where it is **defined**.

### Helper `_make_anthropic_response(text)`

```python
def _make_anthropic_response(text: str) -> MagicMock:
    response = MagicMock()
    response.content = [MagicMock(text=text)]
    return response
```

Reuse this across all SDK-mocking tests.

### `cli.py` — No Changes Required

`cli.py` already:
- Echoes `"Generating report..."` before calling `generate_report` (Story 1.3)
- Catches `JiraReportError` (the base class — `AIGenerationError` is a subclass, automatically caught)

Story 3.2 changes nothing in `cli.py`. The existing CLI tests that patch `jira_report.cli.generate_report` continue to work unchanged.

### Project Structure Notes

Files to modify:
- `src/jira_report/config.py` — add `api_key: str` to `Config`
- `config.yaml.example` — add `api_key` line
- `src/jira_report/ai_engine.py` — refine `_build_system_prompt`; add imports + `_create_anthropic_client`, `_parse_response`, `_SECTION_HEADERS`, `_SECTION_REGEX`; implement `generate_report`
- `tests/conftest.py` — add `api_key` to `sample_config` fixture
- `tests/test_config.py` — add `api_key` to `VALID_CONFIG`; update assertions; add `test_load_config_missing_api_key`
- `tests/test_ai_engine.py` — delete `test_generate_report_still_raises_not_implemented`; add ~13 new tests + helper

No new files. No `cli.py` changes.

### Architecture Compliance

- `generate_report` is the only public function; all helpers prefixed `_`. [Source: architecture.md#Module Interface Pattern]
- `JiraData`, `JiraTicket`, `ReportSections` imported from `jira_client.py`. [Source: architecture.md#Canonical Data Models]
- `Config`, `DEFAULT_MODEL`, `AIGenerationError` imported from `config.py`. [Source: architecture.md#Constants, architecture.md#Error Propagation Pattern]
- API isolation: only `ai_engine.py` imports `anthropic`; no other module touches the SDK. [Source: architecture.md#External API Boundaries]
- No terminal output in this module — `cli.py` echoes status messages. [Source: architecture.md#Terminal Output Pattern]
- Exception handling: SDK errors wrapped as `AIGenerationError`; never raw SDK exceptions escape. [Source: architecture.md#Error Propagation Pattern]
- Credential safety: `config.api_key` referenced ONLY in `_create_anthropic_client`; error messages use `e.__class__.__name__`, never `str(e)` when key could leak. [Source: architecture.md#Credential Safety Rule]
- No streaming, no tool use — single sync call per architecture decision. [Source: architecture.md#API & Communication Patterns]

### Scope Boundaries

**This story implements:**
- `api_key` field on `Config` + example file + fixtures
- `_build_system_prompt` tightened with exact `##` header instructions (Story 3.1 substring tests still pass)
- `_create_anthropic_client(config)`, `_parse_response(text)`, regex/constants
- `generate_report(config, jira_data) -> ReportSections` — full SDK call + parse + validate + error wrapping
- ~13 new tests in `test_ai_engine.py` + 1 deletion + small `test_config.py` updates

**DO NOT implement:**
- Streaming responses — out of V1 scope
- Tool use / structured output — markdown header parsing is the agreed approach
- Prompt caching (`cache_control`) — performance optimization, deferred to a later improvement story if needed
- Retry logic — single attempt per architecture; failures surface immediately
- Any changes to `renderer.py`, `cli.py`, `jira_client.py` — out of scope
- Any changes to the existing `_resolve_model`, `_format_tickets`, `_build_user_message` helpers — only `_build_system_prompt` is touched

### Previous Story Learnings (from Stories 1.1–3.1)

- **uv PATH on WSL2:** `export PATH="$HOME/.local/bin:$PATH"` if needed
- **After code changes:** `uv tool upgrade jira-report` (only when CLI behavior changes — not for ai_engine alone)
- **Mock namespace rule (critical):** patch `jira_report.ai_engine.Anthropic` — NOT `anthropic.Anthropic`. The cli.py mocks for `fetch_jira_data` and `generate_report` already follow this convention; carry it forward.
- **Click 8.3 `mix_stderr` removed:** not relevant here (no CLI changes), but noted for ongoing reference. Story 2.3's stderr test uses `result.stderr` / `result.stdout` directly.
- **MagicMock `.__len__()` returns 0:** caused spurious low-ticket warnings in Story 2.3 — same gotcha applies if any test substitutes `MagicMock()` for a `JiraData` or `ReportSections`. Use the `sample_*` fixtures.
- **Pydantic field defaults:** `ai_model: str = DEFAULT_MODEL` already provides a default; `_resolve_model` adds a defensive empty-string guard. `api_key` does NOT get a default — missing key must fail loudly at config load.
- **Fixture reuse:** `sample_config` (Story 1.2, updated by 3.2 with `api_key`) and `sample_jira_data` (Story 2.3) live in `tests/conftest.py`. `_make_jira_data` helper (Story 2.3) lives inside `test_cli.py` — duplicate the inline approach in `test_ai_engine.py` for `_make_anthropic_response`.
- **API token never in errors:** Story 1.4 established the rule. Story 3.2 extends to `api_key`. The `test_api_key_never_in_error_messages` test enforces it.
- **Calendar verification:** not relevant in this story.

### Latest Tech Information

- **anthropic SDK** `>=0.97.0` (per `pyproject.toml`); installed: `0.97.0`
- **Default model:** `claude-sonnet-4-6` (per `config.py:DEFAULT_MODEL`, `architecture.md#Decision Priority Analysis`)
- **`messages.create` signature** (sync API, SDK 0.97):
  ```python
  client.messages.create(
      model: str,
      max_tokens: int,
      system: str | list[TextBlock],   # str is fine for V1
      messages: list[MessageParam],    # [{"role": "user", "content": "..."}]
  ) -> Message  # .content is list[ContentBlock]; for text-only, .content[0].text is the body
  ```
- **`max_tokens=4096`** is sufficient for a 4-paragraph executive report (~2-3K output tokens worst case). If reports get longer, raise this in a follow-up story.
- **Exception types (SDK 0.97):** `anthropic.APIError` is the base class; `APIConnectionError`, `APITimeoutError`, `AuthenticationError`, `RateLimitError`, `BadRequestError` are all subclasses. Catching `APIError` covers the SDK-defined error tree; catching `Exception` afterwards is defense-in-depth for transport-level errors that may bypass `APIError` in some versions.
- **No async needed for V1:** single synchronous call. `anthropic.AsyncAnthropic` exists but is out of scope.

### Git Intelligence Summary (Recent Commits)

- `7dad096 Add Story 3.1: AI prompt construction` — established `_build_system_prompt`, `_build_user_message`, `_format_tickets`, `_resolve_model`. Story 3.2 extends but does not regress this work.
- `f5c42d1 Implement Story 2.3: low-ticket-count data quality warning` — established the `sample_jira_data` fixture in `tests/conftest.py`. Story 3.2 reuses it.
- `79e99b0 Add Story 2.3: low-ticket-count data quality warning` — original story spec.
- `a4c5081 Add Story 2.2: parallel ticket retrieval and JiraData assembly` — established `JiraTicket`, `JiraData`, `ReportSections` dataclasses. Story 3.2 imports `ReportSections` for the first time.

### References

- FR12 (4-section response): [Source: epics.md#Story 3.2, architecture.md#Requirements to Structure Mapping FR12]
- FR14 (executive language — covered by Story 3.1's prompt): [Source: epics.md#Story 3.2, architecture.md#Requirements to Structure Mapping FR14]
- NFR8 (no silent AI failure): [Source: architecture.md#Requirements Overview, architecture.md#Cross-Cutting Concerns NFR8]
- NFR3 (progressive feedback): [Source: architecture.md#Requirements Overview NFR3] — already satisfied by `cli.py` echoing `"Generating report..."`
- NFR4 (credential safety): [Source: architecture.md#Credential Safety Rule]
- `Config.api_key` field per architecture: [Source: architecture.md#Authentication & Security]
- Single sync call (no streaming): [Source: architecture.md#API & Communication Patterns]
- Module interface (single public function): [Source: architecture.md#Module Interface Pattern]
- API isolation rule (only ai_engine.py imports anthropic): [Source: architecture.md#External API Boundaries]

## Dev Agent Record

### Agent Model Used

claude-opus-4-7 (1M context)

### Debug Log References

- `uv run pytest` — 85 passed (was 70 before this story; +15 net new tests: 16 added, 1 deleted).
- No debugging required. Implementation matched the spec exactly; all tests passed on first run.

### Completion Notes List

- Filled the planning gap: added `api_key: str` field (required, no default) to `Config`, immediately after `api_token`, with a comment marking it as a credential. Updated `config.yaml.example` with a placeholder.
- Updated `sample_config` fixture in `tests/conftest.py` to include `api_key="test-anthropic-key-not-real"`.
- Updated `tests/test_config.py`: added `api_key` to `VALID_CONFIG`, asserted it on the happy path, added `test_load_config_missing_api_key` mirroring the existing missing-field pattern, and extended `test_no_credentials_in_error` to also assert the `api_key` is not leaked.
- Tightened `_build_system_prompt` with exact section-header instructions (`## Done`, `## In Progress`, `## Next Plan`, `## Executive Summary`) plus a "no preamble or trailing text" directive — Story 3.1's substring tests still pass since the change only adds text.
- Added module-level constants `_SECTION_HEADERS`, `_SECTION_REGEX`, and `_MAX_TOKENS = 4096`.
- Implemented `_create_anthropic_client(config) -> Anthropic` — only reference site for `config.api_key`.
- Implemented `_parse_response(text) -> ReportSections` — single multiline regex, slice-between-matches body extraction, `.strip()` per body. Raises `AIGenerationError("Expected 4 sections, found N")` on header-count mismatch.
- Implemented `generate_report(config, jira_data) -> ReportSections` — defense-in-depth: `except APIError` first, then `except Exception` second. Both wrap as `AIGenerationError` using `e.__class__.__name__` only (never `str(e)`) to keep the API key out of error output. Empty/whitespace response → `AIGenerationError("Claude API returned empty response")`. Per-field empty-section validation post-parse.
- Deleted `test_generate_report_still_raises_not_implemented` (the helper was implemented in this story; the test is superseded by `test_generate_report_returns_report_sections`).
- Added 16 new tests in `tests/test_ai_engine.py` covering: parser happy-path + whitespace + missing-section, client constructor api_key wiring, generate_report happy path, model resolution flow-through (configured + default), system/user message wiring, empty content, whitespace-only response, missing sections, empty section body, `APIError` wrapping, generic exception wrapping, and `api_key` never appearing in error messages (NFR4).
- `cli.py` unchanged — `"Generating report..."` echo and `JiraReportError` catch were already in place from Story 1.3.
- Final result: 85 tests pass, zero regressions.

### File List

- `jira-report/src/jira_report/config.py` (modified) — added `api_key: str` field to `Config`
- `jira-report/config.yaml.example` (modified) — added `api_key` line; clarified `api_token` to `your-jira-api-token-here`
- `jira-report/src/jira_report/ai_engine.py` (modified) — tightened `_build_system_prompt`; added `re` import, `Anthropic`/`APIError` imports, `ReportSections` import, `AIGenerationError` import; added `_SECTION_HEADERS`, `_SECTION_REGEX`, `_MAX_TOKENS` constants; added `_create_anthropic_client`, `_parse_response`; implemented `generate_report`
- `jira-report/tests/conftest.py` (modified) — added `api_key="test-anthropic-key-not-real"` to `sample_config`
- `jira-report/tests/test_config.py` (modified) — added `api_key` to `VALID_CONFIG`; added `test_load_config_missing_api_key`; extended `test_no_credentials_in_error`; updated `test_load_config_valid` assertions
- `jira-report/tests/test_ai_engine.py` (modified) — replaced `NotImplementedError` test with 16 new tests + `_make_anthropic_response` helper + `_GOOD_RESPONSE` constant

## Change Log

| Date       | Description                                                                                                                                |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| 2026-05-06 | Implemented Story 3.2: Claude API call + ReportSections assembly. Added `Config.api_key` to fill planning gap. Status: ready-for-dev → review. |
