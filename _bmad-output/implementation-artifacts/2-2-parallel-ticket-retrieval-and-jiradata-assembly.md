# Story 2.2: Parallel Ticket Retrieval & JiraData Assembly

Status: review

## Story

As a PM,
I want the tool to fetch Done, In Progress, and Planned tickets simultaneously,
so that the full data retrieval completes well within 60 seconds.

## Acceptance Criteria

1. Given three JQL queries are ready, When `fetch_jira_data()` executes, Then all three queries run concurrently via `concurrent.futures.ThreadPoolExecutor` — not sequentially (NFR1).
2. Given a query returns tickets from Jira, When results are assembled, Then each ticket is represented as `JiraTicket(key, summary, assignee, status)` with no other fields, And the full result is `JiraData(done=[...], in_progress=[...], planned=[...], week_start=..., week_end=...)`.
3. Given all three queries complete successfully, When the fetch returns, Then total elapsed time is under 60 seconds on a standard internet connection (NFR1), And the `jira` library communicates with Jira Cloud REST API v3 (NFR9).
4. Given a query raises a `JIRAError` or network error, When the exception propagates, Then a `JiraFetchError` is raised naming the failing query (Done / In Progress / Planned).

## Tasks / Subtasks

- [x] Task 1: Define dataclasses in `jira_client.py` (AC: 2)
  - [x] Add `from dataclasses import dataclass` import at module top
  - [x] Define `@dataclass class JiraTicket` with fields: `key: str`, `summary: str`, `assignee: str`, `status: str`
  - [x] Define `@dataclass class JiraData` with fields: `done: list[JiraTicket]`, `in_progress: list[JiraTicket]`, `planned: list[JiraTicket]`, `week_start: date`, `week_end: date`
  - [x] Define `@dataclass class ReportSections` with fields: `done_text: str`, `in_progress_text: str`, `next_plan_text: str`, `executive_summary: str`
  - [x] Place all three after imports, before `DEFAULT_TIMEOUT_SECONDS` — canonical location per architecture

- [x] Task 2: Implement `_fetch_tickets()` in `jira_client.py` (AC: 2, 4)
  - [x] Signature: `_fetch_tickets(jira: JIRA, jql: str, label: str) -> list[JiraTicket]`
  - [x] Call `jira.search_issues(jql, maxResults=False, fields=["summary", "assignee", "status"])`
  - [x] Map each issue: `key=issue.key`, `summary=issue.fields.summary`, `assignee=issue.fields.assignee.displayName if issue.fields.assignee else "Unassigned"`, `status=issue.fields.status.name`
  - [x] Catch `JIRAError` → raise `JiraFetchError(f"Jira {label} query failed (status {e.status_code})")`
  - [x] Catch `(requests.exceptions.Timeout, requests.exceptions.ConnectionError, OSError)` → raise `JiraFetchError(f"Jira {label} query timed out — check jira_url in config.yaml")`

- [x] Task 3: Update `fetch_jira_data()` for parallel execution (AC: 1, 2, 3)
  - [x] Add `from concurrent.futures import ThreadPoolExecutor` import
  - [x] Update return type annotation: `def fetch_jira_data(config: Config, week_override: Optional[str] = None) -> JiraData:`
  - [x] Replace `raise NotImplementedError` with `ThreadPoolExecutor(max_workers=3)` block
  - [x] Submit all 3 futures BEFORE calling `.result()` on any — guarantees parallel execution
  - [x] Return `JiraData(done=..., in_progress=..., planned=..., week_start=week_start, week_end=week_end)`

- [x] Task 4: Update two existing success-path tests in `tests/test_jira_client.py` (AC: 1)
  - [x] `test_jira_initialized_with_correct_url`: add `mock_instance.search_issues.return_value = []`, remove `with pytest.raises(NotImplementedError):` wrapper
  - [x] `test_auth_succeeds_no_token_in_output`: add `mock_instance.search_issues.return_value = []`, remove `with pytest.raises(NotImplementedError):` wrapper

- [x] Task 5: Add new tests in `tests/test_jira_client.py` (AC: 1–4)
  - [x] Update import block: add `JiraTicket`, `JiraData` to imports from `jira_report.jira_client`
  - [x] `test_fetch_returns_jira_data` — search returns `[]`; assert result is `JiraData` with empty lists
  - [x] `test_jira_ticket_fields_populated_correctly` — mock issue with all fields; assert `JiraTicket` matches
  - [x] `test_assignee_none_becomes_unassigned` — mock issue with `assignee=None`; assert `"Unassigned"`
  - [x] `test_all_three_queries_called` — verify `search_issues.call_count == 3`
  - [x] `test_search_jira_error_raises_jira_fetch_error` — `search_issues` raises `JIRAError` → `JiraFetchError`
  - [x] `test_search_timeout_raises_jira_fetch_error` — `search_issues` raises `Timeout` → `JiraFetchError`
  - [x] `test_jira_data_dates_match_week_range` — `week_override="2026-04-21"` → verify `result.week_start == date(2026, 4, 21)` and `result.week_end == date(2026, 4, 27)`
  - [x] Run `uv run pytest tests/test_jira_client.py` — all tests pass (41 pre-existing + new)

## Dev Notes

### Dataclass Definitions — Exact Code

Place immediately after imports in `jira_client.py`, before `DEFAULT_TIMEOUT_SECONDS`:

```python
from dataclasses import dataclass


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
```

**`ReportSections` scope note:** Not used in this story. Define it here now so `ai_engine.py` (Story 3) can `from jira_report.jira_client import ReportSections`. Never redefine it.

### `_fetch_tickets()` — Exact Implementation

```python
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
```

**Critical details:**
- `maxResults=False` — jira library fetches ALL results via internal pagination (not just the default 50)
- `fields=["summary", "assignee", "status"]` — requests only needed fields; reduces response payload
- `assignee` is `None` on unassigned Jira tickets — the conditional guard is mandatory
- `label` (e.g., `"Done"`, `"In Progress"`, `"Planned"`) names the failing query in error messages

### `fetch_jira_data()` — Full Updated Implementation

```python
from concurrent.futures import ThreadPoolExecutor

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
```

**Why `submit()` not `map()`:** All three futures are submitted before any `.result()` is called — guaranteeing all three queries start in parallel. `executor.map()` is lazy and does not make this guarantee.

**Exception propagation:** `future.result()` re-raises whatever exception was thrown in the thread. If `future_done.result()` raises `JiraFetchError`, the `with` block exits and the remaining futures are abandoned. This is correct fail-fast behavior.

**Project key override:** The `--project` CLI flag is handled in `cli.py` via `config.model_copy(update={"project_key": project})` before calling `fetch_jira_data`. By the time `fetch_jira_data` runs, `config.project_key` already reflects the override — no changes needed here.

### Updated Existing Tests — Exact Code

These two tests currently use `pytest.raises(NotImplementedError)` — that must be removed:

```python
def test_jira_initialized_with_correct_url(sample_config):
    with patch("jira_report.jira_client.JIRA") as mock_jira:
        mock_instance = MagicMock()
        mock_jira.return_value = mock_instance
        mock_instance.search_issues.return_value = []  # Story 2.2: returns JiraData now
        result = fetch_jira_data(sample_config)
        mock_jira.assert_called_once()
        assert mock_jira.call_args.kwargs.get("server") == sample_config.jira_url


def test_auth_succeeds_no_token_in_output(sample_config, capsys):
    with patch("jira_report.jira_client.JIRA") as mock_jira:
        mock_instance = MagicMock()
        mock_jira.return_value = mock_instance
        mock_instance.search_issues.return_value = []  # Story 2.2: returns JiraData now
        fetch_jira_data(sample_config)
        captured = capsys.readouterr()
        assert sample_config.api_token not in captured.out
        assert sample_config.api_token not in captured.err
```

### New Tests — Exact Code

Update the import block at the top of `tests/test_jira_client.py`:

```python
from jira_report.jira_client import (
    fetch_jira_data,
    DEFAULT_TIMEOUT_SECONDS,
    _calculate_week_range,
    _build_jql_done,
    _build_jql_in_progress,
    _build_jql_planned,
    JiraTicket,
    JiraData,
)
```

Add these tests after the existing JQL builder tests:

```python
# ── Ticket retrieval & JiraData assembly ───────────────────────────────────────

def test_fetch_returns_jira_data(sample_config):
    with patch("jira_report.jira_client.JIRA") as mock_jira_cls:
        mock_jira = MagicMock()
        mock_jira_cls.return_value = mock_jira
        mock_jira.search_issues.return_value = []
        result = fetch_jira_data(sample_config)
        assert isinstance(result, JiraData)
        assert result.done == []
        assert result.in_progress == []
        assert result.planned == []


def test_jira_ticket_fields_populated_correctly(sample_config):
    with patch("jira_report.jira_client.JIRA") as mock_jira_cls:
        mock_jira = MagicMock()
        mock_jira_cls.return_value = mock_jira
        mock_issue = MagicMock()
        mock_issue.key = "TEST-42"
        mock_issue.fields.summary = "Fix login timeout"
        mock_issue.fields.assignee.displayName = "Alice"
        mock_issue.fields.status.name = "Done"
        mock_jira.search_issues.return_value = [mock_issue]
        result = fetch_jira_data(sample_config)
        ticket = result.done[0]
        assert ticket.key == "TEST-42"
        assert ticket.summary == "Fix login timeout"
        assert ticket.assignee == "Alice"
        assert ticket.status == "Done"


def test_assignee_none_becomes_unassigned(sample_config):
    with patch("jira_report.jira_client.JIRA") as mock_jira_cls:
        mock_jira = MagicMock()
        mock_jira_cls.return_value = mock_jira
        mock_issue = MagicMock()
        mock_issue.key = "TEST-1"
        mock_issue.fields.summary = "Unassigned task"
        mock_issue.fields.assignee = None
        mock_issue.fields.status.name = "To Do"
        mock_jira.search_issues.return_value = [mock_issue]
        result = fetch_jira_data(sample_config)
        assert result.done[0].assignee == "Unassigned"


def test_all_three_queries_called(sample_config):
    with patch("jira_report.jira_client.JIRA") as mock_jira_cls:
        mock_jira = MagicMock()
        mock_jira_cls.return_value = mock_jira
        mock_jira.search_issues.return_value = []
        fetch_jira_data(sample_config)
        assert mock_jira.search_issues.call_count == 3


def test_search_jira_error_raises_jira_fetch_error(sample_config):
    with patch("jira_report.jira_client.JIRA") as mock_jira_cls:
        mock_jira = MagicMock()
        mock_jira_cls.return_value = mock_jira
        mock_jira.search_issues.side_effect = JIRAError(text="Server Error", status_code=500)
        with pytest.raises(JiraFetchError):
            fetch_jira_data(sample_config)


def test_search_timeout_raises_jira_fetch_error(sample_config):
    with patch("jira_report.jira_client.JIRA") as mock_jira_cls:
        mock_jira = MagicMock()
        mock_jira_cls.return_value = mock_jira
        mock_jira.search_issues.side_effect = requests.exceptions.Timeout("timed out")
        with pytest.raises(JiraFetchError, match="timed out"):
            fetch_jira_data(sample_config)


def test_jira_data_dates_match_week_range(sample_config):
    with patch("jira_report.jira_client.JIRA") as mock_jira_cls:
        mock_jira = MagicMock()
        mock_jira_cls.return_value = mock_jira
        mock_jira.search_issues.return_value = []
        result = fetch_jira_data(sample_config, week_override="2026-04-21")
        assert result.week_start == date(2026, 4, 21)
        assert result.week_end == date(2026, 4, 27)
```

### Concurrency & Test Thread Safety

`ThreadPoolExecutor` in production does not affect test reliability. CPython's GIL makes `MagicMock` thread-safe for reads. All three threads call `search_issues` concurrently and return the same mock value — correct for unit testing.

In `test_jira_ticket_fields_populated_correctly`: all three queries return `[mock_issue]`, so `result.done`, `result.in_progress`, and `result.planned` all contain the same ticket. The test only checks `result.done[0]` — the duplicate data is acceptable for a unit test verifying field extraction logic.

### Project Structure Notes

Files to modify:
- `src/jira_report/jira_client.py` — add dataclasses, `_fetch_tickets`, update `fetch_jira_data`
- `tests/test_jira_client.py` — update 2 existing tests, add 7+ new tests

No new files created. No other modules touched.

### Architecture Compliance

- **Canonical data models:** `JiraTicket`, `JiraData`, `ReportSections` defined ONLY in `jira_client.py`. [Source: architecture.md#Canonical Data Models]
- **Module interface:** `fetch_jira_data` remains the ONLY public function; `_fetch_tickets` is private. [Source: architecture.md#Module Interface Pattern]
- **ThreadPoolExecutor:** correct choice — jira library is sync-only; asyncio adds complexity with no benefit. [Source: architecture.md#API & Communication Patterns]
- **No terminal output:** `jira_client.py` raises; `cli.py` echoes status messages. [Source: architecture.md#Terminal Output Pattern]
- **Credential safety:** `label` in error messages never contains JQL or config values. [Source: architecture.md#Credential Safety Rule]
- **Return type:** `fetch_jira_data() -> JiraData` per module interface contract. [Source: architecture.md#Module Boundaries]

### Scope Boundaries

**This story implements:**
- `JiraTicket`, `JiraData`, `ReportSections` dataclasses
- `_fetch_tickets(jira, jql, label) -> list[JiraTicket]` with error handling
- Parallel execution in `fetch_jira_data()` via `ThreadPoolExecutor`
- Updated existing success-path tests + new retrieval tests

**DO NOT implement:**
- `LOW_TICKET_WARNING_THRESHOLD` check or any low-count warnings — Story 2.3 scope
- Any changes to `ai_engine.py` or `renderer.py` — Stories 3–4 scope

### Previous Story Learnings (from Stories 1.1–2.1)

- **uv PATH on WSL2:** `export PATH="$HOME/.local/bin:$PATH"` if needed
- **After code changes:** `uv tool upgrade jira-report`
- **Mock namespace:** always patch `jira_report.jira_client.JIRA`, never `jira.JIRA`
- **Exceptions from config.py:** `JiraFetchError` lives in `jira_report.config` — import from there
- **Test date seam:** `_calculate_week_range(_today=date(...))` avoids real clock dependency
- **Calendar verification:** always verify test expected dates against a real calendar (April 27, 2026 is Monday — verify before writing assertions)

### References

- FR8–FR10 (parallel retrieval, JiraData): [Source: epics.md#Story 2.2]
- NFR1 (< 60s end-to-end), NFR9 (Jira Cloud v3): [Source: epics.md#Story 2.2, architecture.md#Requirements Overview]
- ThreadPoolExecutor pattern: [Source: architecture.md#API & Communication Patterns]
- Canonical data models: [Source: architecture.md#Canonical Data Models]
- Module interface (single public function, `-> JiraData` return): [Source: architecture.md#Module Interface Pattern]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None — implementation matched spec exactly; no debugging required.

### Completion Notes List

- All 5 tasks implemented per spec; 48 tests pass (20 pre-existing + 7 new retrieval tests) — zero regressions
- `JiraTicket`, `JiraData`, `ReportSections` dataclasses defined in `jira_client.py` as canonical location
- `_fetch_tickets(jira, jql, label)` with full error handling: `JIRAError` → `JiraFetchError`, network errors → `JiraFetchError` with label naming the failing query
- `ThreadPoolExecutor(max_workers=3)` with all 3 `submit()` calls before any `result()` call — guarantees parallel start
- Existing success-path tests updated: removed `NotImplementedError` expectation, added `search_issues.return_value = []`
- `fields=["summary", "assignee", "status"]` on `search_issues` reduces Jira API response payload
- Assignee None guard verified by dedicated test

### File List

- `src/jira_report/jira_client.py` — added `JiraTicket`, `JiraData`, `ReportSections` dataclasses; added `_fetch_tickets`; updated `fetch_jira_data` with `ThreadPoolExecutor` parallel execution and `-> JiraData` return type
- `tests/test_jira_client.py` — updated 2 existing success-path tests; added 7 new retrieval/assembly tests; updated import block
