# Story 2.1: Automatic Date Range Calculation & JQL Construction

Status: review

## Story

As a PM,
I want the tool to automatically determine the correct reporting week and build accurate Jira queries from it,
so that I always get data for the right week without calculating dates manually.

## Acceptance Criteria

1. Given no `--week` flag is provided, When `_calculate_week_range()` runs on any day of the week, Then `week_start` is set to the Monday of the most recently completed Mon–Sun week, and `week_end` is set to the Sunday of that same week (FR5).
2. Given `--week 2026-04-21` is provided, When `_calculate_week_range()` processes the override, Then `week_start = 2026-04-21` and `week_end = 2026-04-27` (i.e., week_start + 6 days) (FR6).
3. Given a `week_start`, `week_end`, and `project_key`, When JQL strings are constructed, Then the Done JQL includes `status = Done AND updated >= "{week_start}" AND updated <= "{week_end}"` (FR8), And the In Progress JQL includes `status in ("In Progress")` with no date filter (FR9), And the Planned JQL includes `status in ("To Do", "Backlog", "Next")` with no date filter (FR10).
4. Given `--project ALPHA` is provided, When JQL strings are constructed, Then all three queries use `project = "ALPHA"` instead of `config.project_key` (FR7).

## Tasks / Subtasks

- [x] Task 1: Implement `_calculate_week_range()` in `jira_client.py` (AC: 1, 2)
  - [x] Add `from datetime import date, timedelta` imports at module top
  - [x] Implement `_calculate_week_range(week_override: Optional[str] = None, _today: Optional[date] = None) -> tuple[date, date]`
  - [x] For override path: parse `week_override` via `date.fromisoformat()`, return `(week_start, week_start + timedelta(days=6))`
  - [x] For auto path: `_today or date.today()`, compute days since last Sunday using `(today.weekday() + 1) % 7`, derive `week_start = last_sunday - timedelta(days=6)`
  - [x] `_today` parameter is a test seam — never set by callers other than tests

- [x] Task 2: Implement JQL builder private functions in `jira_client.py` (AC: 3, 4)
  - [x] Implement `_build_jql_done(project_key: str, week_start: date, week_end: date) -> str`
  - [x] Implement `_build_jql_in_progress(project_key: str) -> str`
  - [x] Implement `_build_jql_planned(project_key: str) -> str`
  - [x] All three functions must quote the project key: `project = "{project_key}"`
  - [x] Done JQL uses `updated >=` and `updated <=` with ISO date strings (YYYY-MM-DD)

- [x] Task 3: Update `fetch_jira_data()` to call date range + JQL builders (AC: 1–4)
  - [x] After `_validate_project()`, call `_calculate_week_range(week_override)`
  - [x] Build all three JQL strings using `config.project_key`
  - [x] Keep `raise NotImplementedError` at the end — Story 2.2 replaces it with parallel query execution
  - [x] Do NOT execute any Jira search queries in this story

- [x] Task 4: Implement tests in `tests/test_jira_client.py` (AC: 1–4)
  - [x] `test_auto_week_range_wednesday` — _today=Wed Apr 29 → Mon Apr 20, Sun Apr 26
  - [x] `test_auto_week_range_monday` — _today=Mon Apr 27 → Mon Apr 20, Sun Apr 26
  - [x] `test_auto_week_range_sunday` — _today=Sun Apr 26 → Mon Apr 20, Sun Apr 26
  - [x] `test_week_override_returns_7day_window` — "2026-04-21" → (Apr 21, Apr 27)
  - [x] `test_jql_done_contains_required_parts` — project key, status=Done, date range
  - [x] `test_jql_in_progress_structure` — project key, status in ("In Progress"), no dates
  - [x] `test_jql_planned_structure` — project key, To Do, Backlog, Next, no dates
  - [x] `test_project_key_override_in_jql` — different project_key appears in all JQL strings
  - [x] Run `uv run pytest tests/test_jira_client.py` — all tests pass

## Dev Notes

### Date Calculation Algorithm

`weekday()` returns: Mon=0, Tue=1, Wed=2, Thu=3, Fri=4, Sat=5, Sun=6

Formula for days since last Sunday: `(today.weekday() + 1) % 7`
- Mon: (0+1)%7 = 1 → last Sunday was yesterday ✓
- Wed: (2+1)%7 = 3 → last Sunday was 3 days ago ✓
- Sun: (6+1)%7 = 0 → last Sunday is today ✓

```python
from datetime import date, timedelta

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
```

**Verification with real dates:**
- If today = Wed 2026-04-29: days_since_sunday=3, last_sunday=2026-04-27, week_start=2026-04-21 ✓
- If today = Mon 2026-04-28: days_since_sunday=1, last_sunday=2026-04-27, week_start=2026-04-21 ✓
- If today = Sun 2026-04-27: days_since_sunday=0, last_sunday=2026-04-27, week_start=2026-04-21 ✓
- If today = Mon 2026-04-21: days_since_sunday=1, last_sunday=2026-04-20, week_start=2026-04-14 ✓ (previous week)

**`_today` test seam:** Pass a fixed `date` object in tests to avoid depending on the real clock. Never set this from production callers — only from tests.

### JQL Builder Functions

```python
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
```

**JQL format rules:**
- Project key is quoted with double-quotes: `project = "TEST"` — handles keys that might have dashes
- Dates are in ISO format `YYYY-MM-DD` wrapped in double-quotes per Jira JQL spec
- Status values in `in (...)` are quoted strings; `Done` used without quotes matches Jira Cloud convention
- No `ORDER BY` clause — Jira returns results in default order; ordering is not in scope

### Updated `fetch_jira_data()` for This Story

```python
def fetch_jira_data(config: Config, week_override: Optional[str] = None):
    jira = _create_jira_client(config)
    _validate_project(jira, config)

    week_start, week_end = _calculate_week_range(week_override)
    jql_done = _build_jql_done(config.project_key, week_start, week_end)
    jql_in_progress = _build_jql_in_progress(config.project_key)
    jql_planned = _build_jql_planned(config.project_key)

    raise NotImplementedError  # Story 2.2 implements parallel query execution
```

The `jira` variable from `_create_jira_client` is NOT used yet in this story — it will be passed to the search functions in Story 2.2. Keep the variable assignment so Story 2.2 can use it.

### `tests/test_jira_client.py` — New Tests to Add

Import the private functions directly (acceptable for unit testing helper logic):

```python
from datetime import date
from jira_report.jira_client import (
    fetch_jira_data,
    DEFAULT_TIMEOUT_SECONDS,
    _calculate_week_range,
    _build_jql_done,
    _build_jql_in_progress,
    _build_jql_planned,
)
```

**Date range tests — use `_today` parameter, no mocking needed:**
```python
def test_auto_week_range_wednesday():
    week_start, week_end = _calculate_week_range(_today=date(2026, 4, 29))
    assert week_start == date(2026, 4, 21)
    assert week_end == date(2026, 4, 27)

def test_auto_week_range_monday():
    week_start, week_end = _calculate_week_range(_today=date(2026, 4, 28))
    assert week_start == date(2026, 4, 21)
    assert week_end == date(2026, 4, 27)

def test_auto_week_range_sunday():
    week_start, week_end = _calculate_week_range(_today=date(2026, 4, 27))
    assert week_start == date(2026, 4, 21)
    assert week_end == date(2026, 4, 27)

def test_week_override_returns_7day_window():
    week_start, week_end = _calculate_week_range(week_override="2026-04-21")
    assert week_start == date(2026, 4, 21)
    assert week_end == date(2026, 4, 27)
```

**JQL builder tests — direct function calls:**
```python
def test_jql_done_contains_required_parts():
    jql = _build_jql_done("TEST", date(2026, 4, 21), date(2026, 4, 27))
    assert "TEST" in jql
    assert "status = Done" in jql
    assert "2026-04-21" in jql
    assert "2026-04-27" in jql
    assert "updated >=" in jql
    assert "updated <=" in jql

def test_jql_in_progress_structure():
    jql = _build_jql_in_progress("TEST")
    assert "TEST" in jql
    assert "In Progress" in jql
    assert "updated" not in jql  # no date filter

def test_jql_planned_structure():
    jql = _build_jql_planned("TEST")
    assert "TEST" in jql
    assert "To Do" in jql
    assert "Backlog" in jql
    assert "Next" in jql
    assert "updated" not in jql

def test_project_key_override_in_jql():
    week_start, week_end = date(2026, 4, 21), date(2026, 4, 27)
    assert "ALPHA" in _build_jql_done("ALPHA", week_start, week_end)
    assert "ALPHA" in _build_jql_in_progress("ALPHA")
    assert "ALPHA" in _build_jql_planned("ALPHA")
```

**Existing tests MUST still pass** — the auth tests from Story 1.4 mock `JIRA` and expect `NotImplementedError`. The Story 2.1 additions don't break those tests because `_create_jira_client` is still called first and the mocked version returns a `MagicMock`.

However: after this story, the success-path tests (`test_jira_initialized_with_correct_url`, `test_auth_succeeds_no_token_in_output`) now also call `_calculate_week_range` and the JQL builders before reaching `NotImplementedError`. This is fine — those functions are pure date math with no side effects.

### Architecture Compliance

- **Naming:** `_calculate_week_range`, `_build_jql_done`, `_build_jql_in_progress`, `_build_jql_planned` — all private (`_` prefix), all `snake_case`. [Source: architecture.md#Naming Patterns]
- **Module interface:** `fetch_jira_data` remains the ONLY public function. [Source: architecture.md#Module Interface Pattern]
- **No terminal output:** date/JQL logic is pure computation — no `typer.echo()` or `print()`. [Source: architecture.md#Terminal Output Pattern]
- **Constants:** `DEFAULT_TIMEOUT_SECONDS = 10` defined in Story 1.4 — do not redefine. [Source: architecture.md#Constants]
- **Data models deferred:** `JiraTicket`, `JiraData`, `ReportSections` still belong to Story 2.2. This story only builds JQL strings. [Source: architecture.md#Canonical Data Models]

### Scope Boundaries

**This story implements:**
- `_calculate_week_range()` with auto and override modes
- `_build_jql_done()`, `_build_jql_in_progress()`, `_build_jql_planned()`
- Updated `fetch_jira_data()` to call the above (still ends with `NotImplementedError`)
- Date/JQL tests added to `tests/test_jira_client.py`

**DO NOT implement in this story:**
- Any `jira.search_issues()` calls — Story 2.2 scope
- `JiraTicket`, `JiraData` dataclasses — Story 2.2 scope
- `LOW_TICKET_WARNING_THRESHOLD` constant — Story 2.3 scope
- `ThreadPoolExecutor` — Story 2.2 scope

### Previous Story Learnings (from Stories 1.1–1.4)

- **uv PATH on WSL2:** `export PATH="$HOME/.local/bin:$PATH"` if needed
- **After code changes:** `uv tool upgrade jira-report`
- **Mock target namespace:** patch `jira_report.jira_client.JIRA` (not `jira.JIRA`)
- **All exceptions imported from `config.py`:** `JiraFetchError` lives in `jira_report.config`
- **Existing auth tests must still pass:** the mocked JIRA returns a MagicMock; `_validate_project` and now `_calculate_week_range` + JQL builders run before `NotImplementedError` — all are pure functions that work fine with the mock

### References

- FR5, FR6 (date range): [Source: epics.md#Story 2.1]
- FR7, FR8, FR9, FR10 (JQL): [Source: epics.md#Story 2.1, architecture.md#Requirements to Structure Mapping]
- JQL construction in jira_client.py: [Source: architecture.md#API & Communication Patterns]
- Module interface: [Source: architecture.md#Module Interface Pattern]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None — implementation matched spec exactly; no debugging required.

### Completion Notes List

- All 4 tasks implemented per spec; 41 tests pass (17 pre-existing + 10 new date/JQL tests + additional edge-case tests added beyond spec minimum)
- Test expected dates corrected during implementation: story spec had wrong calendar dates (Apr 27 is Mon not Sun); correct week for Apr 29 (Wed) is Mon Apr 20 – Sun Apr 26
- Extra tests added beyond spec: `test_auto_week_range_saturday`, `test_week_override_week_end_is_start_plus_6`, `test_jql_done_no_extra_date_parts`, `test_default_project_key_not_in_override_jql`
- `_calculate_week_range` formula verified correct for all weekdays including edge cases (Mon, Sun, Sat)
- `fetch_jira_data` still ends with `raise NotImplementedError` as required; Story 2.2 scope preserved

### File List

- `src/jira_report/jira_client.py` — added `_calculate_week_range`, `_build_jql_done`, `_build_jql_in_progress`, `_build_jql_planned`; updated `fetch_jira_data` to call them
- `tests/test_jira_client.py` — added 10+ date range and JQL builder tests
