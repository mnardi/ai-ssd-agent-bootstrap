# Story 2.3: Low-Ticket-Count Data Quality Warning

Status: ready-for-dev

## Story

As a PM,
I want the tool to warn me when any ticket section returns suspiciously few results before generating the report,
so that I can confirm data accuracy before a thin report gets sent.

## Acceptance Criteria

1. Given any section (done, in_progress, or planned) has fewer than `LOW_TICKET_WARNING_THRESHOLD` (3) tickets, When `fetch_jira_data()` returns, Then `cli.py` emits a warning to stderr naming the section and actual count (FR11), And the warning reads e.g.: `"Warning: Only 2 ticket(s) found for Done — verify data accuracy before proceeding"`.
2. Given a warning is emitted, When execution continues, Then report generation proceeds normally — the warning does not stop the pipeline.
3. Given all three sections have 3 or more tickets, When `fetch_jira_data()` returns, Then no warning is emitted.

## Tasks / Subtasks

- [ ] Task 1: Add `LOW_TICKET_WARNING_THRESHOLD = 3` constant to `jira_client.py` (AC: 1, 3)
  - [ ] Add immediately after `DEFAULT_TIMEOUT_SECONDS = 10` — same constants block
  - [ ] No other changes to `jira_client.py`

- [ ] Task 2: Add warning helper and import to `cli.py` (AC: 1, 2, 3)
  - [ ] Update `jira_client` import line: add `JiraData` and `LOW_TICKET_WARNING_THRESHOLD`
  - [ ] Add `_warn_low_ticket_counts(jira_data: JiraData) -> None` private function
  - [ ] Iterate `[("Done", jira_data.done), ("In Progress", jira_data.in_progress), ("Planned", jira_data.planned)]`
  - [ ] For each section where `len(tickets) < LOW_TICKET_WARNING_THRESHOLD`, call `typer.echo(f"Warning: Only {len(tickets)} ticket(s) found for {label} — verify data accuracy before proceeding", err=True)`
  - [ ] Call `_warn_low_ticket_counts(jira_data)` in `main()` immediately after `jira_data = fetch_jira_data(...)`

- [ ] Task 3: Add `sample_jira_data` fixture to `tests/conftest.py` (AC: 1–3)
  - [ ] Import `JiraData`, `JiraTicket` from `jira_report.jira_client`; import `date` from `datetime`
  - [ ] Create `sample_jira_data` fixture returning `JiraData` with 3 tickets per section (meets threshold — no warning)
  - [ ] Use a single reusable `JiraTicket(key="TEST-1", summary="Sample ticket", assignee="Alice", status="Done")`

- [ ] Task 4: Update two existing CLI tests to use `sample_jira_data` (AC: regression safety)
  - [ ] `test_dry_run_flag`: replace `return_value=MagicMock()` for `fetch_jira_data` with `return_value=sample_jira_data`; add `sample_jira_data` fixture parameter
  - [ ] `test_success_prints_saved_path`: same replacement; add `sample_jira_data` fixture parameter
  - [ ] Reason: `MagicMock().__len__()` returns 0, which would trigger spurious warnings in those tests

- [ ] Task 5: Add new tests in `tests/test_cli.py` (AC: 1–3)
  - [ ] Add imports: `from datetime import date`, `from jira_report.jira_client import JiraData, JiraTicket, LOW_TICKET_WARNING_THRESHOLD`
  - [ ] `test_low_ticket_threshold_constant` — `LOW_TICKET_WARNING_THRESHOLD == 3`
  - [ ] `test_warning_emitted_for_low_done_count` — 2 Done tickets → "Warning" + "Done" in output
  - [ ] `test_warning_emitted_for_low_in_progress_count` — 1 In Progress ticket → "Warning" + "In Progress" in output
  - [ ] `test_warning_emitted_for_low_planned_count` — 0 Planned tickets → "Warning" + "Planned" in output
  - [ ] `test_no_warning_when_all_sections_meet_threshold` — 3 each → "Warning" NOT in output
  - [ ] `test_multiple_sections_can_warn` — 2 Done + 1 In Progress + 5 Planned → both "Done" and "In Progress" warnings
  - [ ] `test_warning_goes_to_stderr_not_stdout` — use `CliRunner(mix_stderr=False)`; assert "Warning" in `result.stderr` and "Warning" not in `result.output`
  - [ ] `test_pipeline_continues_after_warning` — warning emitted but `generate_report` still called (pipeline not stopped)
  - [ ] Run `uv run pytest` — all 48 existing tests still pass + new tests green

## Dev Notes

### `jira_client.py` — Constant Addition

Add `LOW_TICKET_WARNING_THRESHOLD` immediately after `DEFAULT_TIMEOUT_SECONDS`:

```python
DEFAULT_TIMEOUT_SECONDS = 10
LOW_TICKET_WARNING_THRESHOLD = 3
```

That's the only change to `jira_client.py`. The constant lives here per the architecture constants spec.

### `cli.py` — Updated Import and New Code

Update the jira_client import line:

```python
from jira_report.jira_client import fetch_jira_data, JiraData, LOW_TICKET_WARNING_THRESHOLD
```

Add the private helper (place after `_ensure_gitignore`, before end of file):

```python
def _warn_low_ticket_counts(jira_data: JiraData) -> None:
    for label, tickets in [
        ("Done", jira_data.done),
        ("In Progress", jira_data.in_progress),
        ("Planned", jira_data.planned),
    ]:
        if len(tickets) < LOW_TICKET_WARNING_THRESHOLD:
            typer.echo(
                f"Warning: Only {len(tickets)} ticket(s) found for {label}"
                " — verify data accuracy before proceeding",
                err=True,
            )
```

In `main()`, call it immediately after `fetch_jira_data()` returns:

```python
typer.echo("Fetching Jira data...")
jira_data = fetch_jira_data(config, week_override=week)
_warn_low_ticket_counts(jira_data)

typer.echo("Generating report...")
```

**Architecture compliance:**
- Warning emitted via `typer.echo(..., err=True)` — stderr only, never stdout [Source: architecture.md#Terminal Output Pattern]
- `_warn_low_ticket_counts` is private (`_` prefix) — not part of module's public interface [Source: architecture.md#Module Interface Pattern]
- `LOW_TICKET_WARNING_THRESHOLD` imported from canonical source — never redefined [Source: architecture.md#Constants]
- Pipeline continues after warning — no exception raised [Source: epics.md AC 2]

### `tests/conftest.py` — New Fixture

```python
from datetime import date
from jira_report.jira_client import JiraData, JiraTicket

@pytest.fixture
def sample_jira_data():
    ticket = JiraTicket(key="TEST-1", summary="Sample ticket", assignee="Alice", status="Done")
    return JiraData(
        done=[ticket, ticket, ticket],
        in_progress=[ticket, ticket, ticket],
        planned=[ticket, ticket, ticket],
        week_start=date(2026, 4, 21),
        week_end=date(2026, 4, 27),
    )
```

3 tickets per section = at or above `LOW_TICKET_WARNING_THRESHOLD` — no spurious warnings in tests that use this fixture.

### Updated Existing CLI Tests (Task 4)

**Why:** `MagicMock().__len__()` returns 0 by default. With the new warning logic, a `MagicMock` jira_data causes all 3 sections to warn spuriously. The existing tests still pass (they don't assert "Warning" absent from output), but the output is noisy and misleading.

```python
def test_dry_run_flag(tmp_path, monkeypatch, sample_config, sample_jira_data):
    ...
    with patch("jira_report.cli.fetch_jira_data", return_value=sample_jira_data), \  # ← was MagicMock()
    ...

def test_success_prints_saved_path(tmp_path, monkeypatch, sample_config, sample_jira_data):
    ...
    with patch("jira_report.cli.fetch_jira_data", return_value=sample_jira_data), \  # ← was MagicMock()
    ...
```

### New Tests — Exact Code

Imports to add at top of `tests/test_cli.py`:

```python
from datetime import date
from jira_report.jira_client import JiraData, JiraTicket, LOW_TICKET_WARNING_THRESHOLD
```

Helper for building low-count JiraData inline (use in tests below):

```python
def _make_jira_data(done_count=3, in_progress_count=3, planned_count=3):
    ticket = JiraTicket(key="T-1", summary="s", assignee="a", status="s")
    return JiraData(
        done=[ticket] * done_count,
        in_progress=[ticket] * in_progress_count,
        planned=[ticket] * planned_count,
        week_start=date(2026, 4, 21),
        week_end=date(2026, 4, 27),
    )
```

Tests:

```python
# ── Low-ticket-count warnings ──────────────────────────────────────────────────

def test_low_ticket_threshold_constant():
    assert LOW_TICKET_WARNING_THRESHOLD == 3


def test_warning_emitted_for_low_done_count(tmp_path, monkeypatch, sample_config):
    monkeypatch.chdir(tmp_path)
    with patch("jira_report.cli._ensure_gitignore"), \
         patch("jira_report.cli.load_config", return_value=sample_config), \
         patch("jira_report.cli.fetch_jira_data", return_value=_make_jira_data(done_count=2)), \
         patch("jira_report.cli.generate_report", return_value=MagicMock()), \
         patch("jira_report.cli.render_and_write", return_value=Path("./r.html")):
        result = runner.invoke(app, [])
    assert "Warning" in result.output
    assert "Done" in result.output


def test_warning_emitted_for_low_in_progress_count(tmp_path, monkeypatch, sample_config):
    monkeypatch.chdir(tmp_path)
    with patch("jira_report.cli._ensure_gitignore"), \
         patch("jira_report.cli.load_config", return_value=sample_config), \
         patch("jira_report.cli.fetch_jira_data", return_value=_make_jira_data(in_progress_count=1)), \
         patch("jira_report.cli.generate_report", return_value=MagicMock()), \
         patch("jira_report.cli.render_and_write", return_value=Path("./r.html")):
        result = runner.invoke(app, [])
    assert "Warning" in result.output
    assert "In Progress" in result.output


def test_warning_emitted_for_low_planned_count(tmp_path, monkeypatch, sample_config):
    monkeypatch.chdir(tmp_path)
    with patch("jira_report.cli._ensure_gitignore"), \
         patch("jira_report.cli.load_config", return_value=sample_config), \
         patch("jira_report.cli.fetch_jira_data", return_value=_make_jira_data(planned_count=0)), \
         patch("jira_report.cli.generate_report", return_value=MagicMock()), \
         patch("jira_report.cli.render_and_write", return_value=Path("./r.html")):
        result = runner.invoke(app, [])
    assert "Warning" in result.output
    assert "Planned" in result.output


def test_no_warning_when_all_sections_meet_threshold(tmp_path, monkeypatch, sample_config):
    monkeypatch.chdir(tmp_path)
    with patch("jira_report.cli._ensure_gitignore"), \
         patch("jira_report.cli.load_config", return_value=sample_config), \
         patch("jira_report.cli.fetch_jira_data", return_value=_make_jira_data()), \
         patch("jira_report.cli.generate_report", return_value=MagicMock()), \
         patch("jira_report.cli.render_and_write", return_value=Path("./r.html")):
        result = runner.invoke(app, [])
    assert "Warning" not in result.output


def test_multiple_sections_can_warn(tmp_path, monkeypatch, sample_config):
    monkeypatch.chdir(tmp_path)
    with patch("jira_report.cli._ensure_gitignore"), \
         patch("jira_report.cli.load_config", return_value=sample_config), \
         patch("jira_report.cli.fetch_jira_data", return_value=_make_jira_data(done_count=2, in_progress_count=1)), \
         patch("jira_report.cli.generate_report", return_value=MagicMock()), \
         patch("jira_report.cli.render_and_write", return_value=Path("./r.html")):
        result = runner.invoke(app, [])
    assert "Done" in result.output
    assert "In Progress" in result.output


def test_warning_goes_to_stderr_not_stdout(tmp_path, monkeypatch, sample_config):
    monkeypatch.chdir(tmp_path)
    split_runner = CliRunner(mix_stderr=False)
    with patch("jira_report.cli._ensure_gitignore"), \
         patch("jira_report.cli.load_config", return_value=sample_config), \
         patch("jira_report.cli.fetch_jira_data", return_value=_make_jira_data(done_count=1)), \
         patch("jira_report.cli.generate_report", return_value=MagicMock()), \
         patch("jira_report.cli.render_and_write", return_value=Path("./r.html")):
        result = split_runner.invoke(app, [])
    assert "Warning" in result.stderr
    assert "Warning" not in result.output


def test_pipeline_continues_after_warning(tmp_path, monkeypatch, sample_config):
    monkeypatch.chdir(tmp_path)
    generate_called = {}

    def fake_generate(config, jira_data):
        generate_called["called"] = True
        return MagicMock()

    with patch("jira_report.cli._ensure_gitignore"), \
         patch("jira_report.cli.load_config", return_value=sample_config), \
         patch("jira_report.cli.fetch_jira_data", return_value=_make_jira_data(done_count=0)), \
         patch("jira_report.cli.generate_report", side_effect=fake_generate), \
         patch("jira_report.cli.render_and_write", return_value=Path("./r.html")):
        result = runner.invoke(app, [])

    assert generate_called.get("called") is True
    assert result.exit_code == 0
```

### Scope Boundaries

**This story implements:**
- `LOW_TICKET_WARNING_THRESHOLD = 3` constant in `jira_client.py`
- `_warn_low_ticket_counts(jira_data)` in `cli.py`
- `sample_jira_data` fixture in `conftest.py`
- Updated existing CLI tests + new warning tests

**DO NOT implement:**
- Any changes to `jira_client.py` beyond adding the constant
- Any changes to `ai_engine.py`, `renderer.py` — Stories 3–4 scope

### Project Structure Notes

Files to modify:
- `src/jira_report/jira_client.py` — add `LOW_TICKET_WARNING_THRESHOLD = 3` (one line)
- `src/jira_report/cli.py` — update import, add `_warn_low_ticket_counts`, call it in `main()`
- `tests/conftest.py` — add `sample_jira_data` fixture (new imports + new fixture)
- `tests/test_cli.py` — update 2 existing tests, add new imports + helper + 8 new tests

### Architecture Compliance

- `LOW_TICKET_WARNING_THRESHOLD` defined at `jira_client.py` module top (constants block). [Source: architecture.md#Constants]
- `typer.echo(..., err=True)` — warning to stderr, never `print()`. [Source: architecture.md#Terminal Output Pattern]
- `_warn_low_ticket_counts` is private (no external callers). [Source: architecture.md#Module Interface Pattern]
- Modules raise, `cli.py` catches/warns — no warning logic inside `jira_client.py`. [Source: architecture.md#Error Propagation Pattern]

### Previous Story Learnings (from Stories 1.1–2.2)

- **uv PATH on WSL2:** `export PATH="$HOME/.local/bin:$PATH"` if needed
- **After code changes:** `uv tool upgrade jira-report`
- **Mock namespace:** patch `jira_report.cli.fetch_jira_data` (not `jira_report.jira_client.fetch_jira_data`) — mock the name in the namespace where it was imported
- **CliRunner default:** `mix_stderr=True` merges stderr into `result.output`; use `CliRunner(mix_stderr=False)` + `result.stderr` to test stderr specifically
- **MagicMock `__len__` returns 0:** important gotcha — any test passing `MagicMock()` as `jira_data` will trigger warnings for all 3 sections

### References

- FR11 (low ticket warning): [Source: epics.md#Story 2.3]
- `LOW_TICKET_WARNING_THRESHOLD = 3`: [Source: architecture.md#Constants]
- Warning routing to stderr: [Source: architecture.md#Terminal Output Pattern]
- FR11 implementation location: [Source: architecture.md#Requirements to Structure Mapping FR11]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
