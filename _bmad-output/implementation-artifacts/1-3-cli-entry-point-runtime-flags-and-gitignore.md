# Story 1.3: CLI Entry Point, Runtime Flags & .gitignore

Status: review

## Story

As a PM,
I want to run `jira-report` with zero arguments or optional flags, and see clear help documentation,
so that I can control the tool at runtime without editing `config.yaml`.

## Acceptance Criteria

1. Given the Typer app is wired in `cli.py`, When I run `jira-report --help`, Then all four flags are listed with descriptions: `--week`, `--project`, `--output`, `--dry-run` (FR23).
2. Given no flags are provided, When `jira-report` is invoked, Then all values default to `config.yaml` settings: `output_dir`, `project_key`, auto-calculated week range (FR22).
3. Given `--week 2026-04-21` is provided, When `jira-report` is invoked, Then that date is used as week start override instead of the auto-calculated range (FR6).
4. Given `--project ALPHA` or `--output ./reports/` are provided, When `jira-report` is invoked, Then each flag overrides the corresponding `config.yaml` value for that run (FR7, FR19, FR24).
5. Given `jira-report` runs in a directory with a `.git/` ancestor, When `_ensure_gitignore()` executes, Then `config.yaml` is appended to `.gitignore` if not already present (NFR6), And if `.gitignore` does not exist, it is created with the `config.yaml` entry.
6. Given a `JiraReportError` is raised anywhere in the pipeline, When it reaches `cli.py`, Then the error is printed to stderr via `typer.echo(err=True)` (FR21), And the process exits with code 1, And no credential values appear in the output (NFR4).

## Tasks / Subtasks

- [x] Task 1: Add importable stub signatures to pipeline modules (AC: 1, 6)
  - [x] Add `fetch_jira_data(config, week_override=None)` stub to `jira_client.py` (raises `NotImplementedError`)
  - [x] Add `generate_report(config, jira_data)` stub to `ai_engine.py` (raises `NotImplementedError`)
  - [x] Add `render_and_write(config, sections, dry_run=False)` stub to `renderer.py` (raises `NotImplementedError`)
  - [x] Verify imports succeed: `uv run python -c "from jira_report.jira_client import fetch_jira_data; print('OK')"`

- [x] Task 2: Implement `_ensure_gitignore()` in `cli.py` (AC: 5)
  - [x] Walk up from `Path.cwd()` looking for a `.git/` directory
  - [x] If no `.git/` found, return silently (not in a git repo — no action)
  - [x] If `.gitignore` exists: read lines, append `config.yaml` only if not already present
  - [x] If `.gitignore` does not exist: create it with `config.yaml\n`
  - [x] Function name must start with `_` (private)

- [x] Task 3: Implement `main()` Typer command with all 4 flags (AC: 1, 2, 3, 4)
  - [x] Replace existing stub `main()` with full implementation
  - [x] Add `--week` flag: `Optional[str]`, default `None`, help text includes `(YYYY-MM-DD)`
  - [x] Add `--project` flag: `Optional[str]`, default `None`, help text mentions override
  - [x] Add `--output` flag: `Optional[str]`, default `None`, help text mentions override
  - [x] Add `--dry-run` flag: `bool`, default `False`, help text mentions no file saved
  - [x] Call `_ensure_gitignore()` first on every run
  - [x] Load config via `load_config(_CONFIG_PATH)` where `_CONFIG_PATH = Path("config.yaml")`
  - [x] Apply `--project` override: `config.model_copy(update={"project_key": project})`
  - [x] Apply `--output` override: `config.model_copy(update={"output_dir": output})`

- [x] Task 4: Wire up pipeline calls, status messages, and error handling (AC: 2, 3, 6)
  - [x] Echo status messages in exact order before each pipeline call (see Dev Notes)
  - [x] Call `fetch_jira_data(config, week_override=week)`
  - [x] Call `generate_report(config, jira_data)`
  - [x] Call `render_and_write(config, sections, dry_run=dry_run)`
  - [x] On `dry_run=True`: echo `"Dry run — no file written"` (no file path)
  - [x] On success: echo `f"Done. Report saved: {result_path}"`
  - [x] Wrap entire `main()` body in `try/except JiraReportError` → `typer.echo(str(e), err=True)` + `raise typer.Exit(code=1)`

- [x] Task 5: Implement `tests/test_cli.py` (AC: 1–6)
  - [x] `test_help_lists_all_flags` — CliRunner invokes `--help`, asserts all 4 flag names in output
  - [x] `test_ensure_gitignore_creates_file` — no .gitignore → creates it with `config.yaml`
  - [x] `test_ensure_gitignore_appends_entry` — existing .gitignore without entry → appends
  - [x] `test_ensure_gitignore_idempotent` — entry already present → no duplicate
  - [x] `test_ensure_gitignore_no_git_repo` — no .git ancestor → does nothing
  - [x] `test_jira_report_error_to_stderr_exit_1` — mocked ConfigError → exit 1, message on stderr
  - [x] `test_project_flag_overrides_config` — `--project ALPHA` passed through to fetch call
  - [x] `test_dry_run_flag` — `--dry-run` calls render_and_write with `dry_run=True`
  - [x] Run `uv run pytest tests/test_cli.py` — all tests pass

## Dev Notes

### Why Task 1 is Required

`cli.py` imports `fetch_jira_data`, `generate_report`, `render_and_write` at module level. Without importable symbols in those modules, `from jira_report.jira_client import fetch_jira_data` raises `ImportError` — breaking `--help`. The stubs added in Task 1 are MINIMAL (raise `NotImplementedError`) so Stories 2, 3, and 4 can overwrite them completely.

**DO NOT** add data model definitions (JiraTicket, JiraData, ReportSections) to these stubs — those belong in Story 2 scope.

### Stub Signatures for Pipeline Modules

**`src/jira_report/jira_client.py`:**
```python
from __future__ import annotations
from typing import Optional

def fetch_jira_data(config, week_override: Optional[str] = None):
    raise NotImplementedError
```

**`src/jira_report/ai_engine.py`:**
```python
from __future__ import annotations

def generate_report(config, jira_data):
    raise NotImplementedError
```

**`src/jira_report/renderer.py`:**
```python
from __future__ import annotations
from pathlib import Path
from typing import Optional

def render_and_write(config, sections, dry_run: bool = False) -> Optional[Path]:
    raise NotImplementedError
```

Note: `week_override` on `fetch_jira_data` is a deliberate extension to the architecture's base interface. Story 2.1 must accept this optional parameter when implementing the full function. [Source: architecture.md#API & Communication Patterns, FR6]

### `cli.py` — Complete Implementation Pattern

```python
from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from jira_report.config import JiraReportError, load_config
from jira_report.jira_client import fetch_jira_data
from jira_report.ai_engine import generate_report
from jira_report.renderer import render_and_write

app = typer.Typer()

_CONFIG_PATH = Path("config.yaml")


@app.command()
def main(
    week: Optional[str] = typer.Option(None, "--week", help="Override week start date (YYYY-MM-DD)"),
    project: Optional[str] = typer.Option(None, "--project", help="Override Jira project key from config"),
    output: Optional[str] = typer.Option(None, "--output", help="Override output directory from config"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview report without saving to file"),
) -> None:
    try:
        _ensure_gitignore()
        config = load_config(_CONFIG_PATH)

        if project:
            config = config.model_copy(update={"project_key": project})
        if output:
            config = config.model_copy(update={"output_dir": output})

        typer.echo("Authenticating...")
        typer.echo("Fetching Jira data...")
        jira_data = fetch_jira_data(config, week_override=week)

        typer.echo("Generating report...")
        sections = generate_report(config, jira_data)

        typer.echo("Writing output...")
        result_path = render_and_write(config, sections, dry_run=dry_run)

        if dry_run:
            typer.echo("Dry run — no file written")
        else:
            typer.echo(f"Done. Report saved: {result_path}")

    except JiraReportError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(code=1)


def _ensure_gitignore() -> None:
    current = Path.cwd()
    git_root: Optional[Path] = None
    for parent in [current, *current.parents]:
        if (parent / ".git").exists():
            git_root = parent
            break
    if git_root is None:
        return

    gitignore = git_root / ".gitignore"
    entry = "config.yaml"

    if gitignore.exists():
        lines = [line.strip() for line in gitignore.read_text(encoding="utf-8").splitlines()]
        if entry not in lines:
            with gitignore.open("a", encoding="utf-8") as f:
                f.write(f"{entry}\n")
    else:
        gitignore.write_text(f"{entry}\n", encoding="utf-8")
```

**Key design decisions:**
- `_CONFIG_PATH = Path("config.yaml")` — relative to CWD; `monkeypatch.chdir(tmp_path)` in tests controls this
- `config.model_copy(update={...})` — Pydantic v2 way to create a modified copy of an immutable model; never mutate Config in-place
- Status messages printed BEFORE each pipeline call, not after (NFR3 progressive feedback)
- `"Authenticating..."` comes first — the actual auth happens silently inside `fetch_jira_data()` (Story 1.4)
- Low-ticket-count warning check is NOT in this story — deferred to Story 2.3

### `_ensure_gitignore()` Algorithm Detail

1. Start at `Path.cwd()`, iterate `[current, current.parent, current.parent.parent, ...]`
2. First directory with a `.git/` subdirectory is the git root
3. If no git root found (e.g. running from `/tmp/` with no git ancestor): return immediately — no error, no file
4. Check `git_root/.gitignore`: if exists, read all lines (strip whitespace), check if `"config.yaml"` is a line
5. If present → do nothing (idempotent)
6. If absent → append `"config.yaml\n"` using `open("a")` (safe for concurrent writes)
7. If file doesn't exist → write `"config.yaml\n"` as entire content

### `tests/test_cli.py` — Test Patterns

```python
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner

from jira_report.cli import app, _ensure_gitignore
from jira_report.config import ConfigError

runner = CliRunner()


# ── AC 1: --help lists all flags ────────────────────────────────────────────

def test_help_lists_all_flags():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "--week" in result.output
    assert "--project" in result.output
    assert "--output" in result.output
    assert "--dry-run" in result.output


# ── AC 5: _ensure_gitignore() ───────────────────────────────────────────────

def test_ensure_gitignore_creates_file(tmp_path, monkeypatch):
    (tmp_path / ".git").mkdir()
    monkeypatch.chdir(tmp_path)
    _ensure_gitignore()
    assert (tmp_path / ".gitignore").read_text(encoding="utf-8") == "config.yaml\n"


def test_ensure_gitignore_appends_entry(tmp_path, monkeypatch):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".gitignore").write_text("*.pyc\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    _ensure_gitignore()
    content = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert "config.yaml" in content
    assert "*.pyc" in content


def test_ensure_gitignore_idempotent(tmp_path, monkeypatch):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".gitignore").write_text("config.yaml\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    _ensure_gitignore()
    lines = (tmp_path / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert lines.count("config.yaml") == 1


def test_ensure_gitignore_no_git_repo(tmp_path, monkeypatch):
    # tmp_path has no .git ancestor (it's under /tmp/)
    monkeypatch.chdir(tmp_path)
    _ensure_gitignore()  # must not raise and must not create any files
    assert not (tmp_path / ".gitignore").exists()


# ── AC 6: JiraReportError → stderr + exit 1 ─────────────────────────────────

def test_jira_report_error_to_stderr_exit_1(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with patch("jira_report.cli._ensure_gitignore"), \
         patch("jira_report.cli.load_config", side_effect=ConfigError("missing api_token")):
        result = runner.invoke(app, [], catch_exceptions=False)
    assert result.exit_code == 1
    assert "missing api_token" in result.output  # CliRunner mixes stderr by default


# ── AC 3 & 4: flag overrides passed through ─────────────────────────────────

def test_project_flag_overrides_config(tmp_path, monkeypatch, sample_config):
    monkeypatch.chdir(tmp_path)
    captured = {}

    def fake_fetch(config, week_override=None):
        captured["project_key"] = config.project_key
        raise ConfigError("stop pipeline")  # stop after fetch

    with patch("jira_report.cli._ensure_gitignore"), \
         patch("jira_report.cli.load_config", return_value=sample_config), \
         patch("jira_report.cli.fetch_jira_data", side_effect=fake_fetch):
        runner.invoke(app, ["--project", "ALPHA"])

    assert captured.get("project_key") == "ALPHA"


def test_dry_run_flag(tmp_path, monkeypatch, sample_config):
    monkeypatch.chdir(tmp_path)
    captured = {}

    def fake_render(config, sections, dry_run=False):
        captured["dry_run"] = dry_run
        return None

    with patch("jira_report.cli._ensure_gitignore"), \
         patch("jira_report.cli.load_config", return_value=sample_config), \
         patch("jira_report.cli.fetch_jira_data", return_value=MagicMock()), \
         patch("jira_report.cli.generate_report", return_value=MagicMock()), \
         patch("jira_report.cli.render_and_write", side_effect=fake_render):
        result = runner.invoke(app, ["--dry-run"])

    assert captured.get("dry_run") is True
    assert "Dry run" in result.output
```

**Critical test note:** `typer.testing.CliRunner` captures stdout and stderr together by default (`mix_stderr=True`). This is fine for these tests — checking `result.output` catches both. Do NOT pass `mix_stderr=False` unless you have a specific reason.

**Why patch `jira_report.cli.fetch_jira_data` (not `jira_report.jira_client.fetch_jira_data`):** `cli.py` imports `fetch_jira_data` at module level (`from jira_report.jira_client import fetch_jira_data`). Python's `unittest.mock.patch` replaces the name in the namespace where it's used — which is `jira_report.cli`, not the origin module. [Standard Python mocking pattern]

### Architecture Compliance

- **Module interface:** `main` is the only `@app.command()`. `_ensure_gitignore` is private (underscore prefix). `_CONFIG_PATH` is a private module-level constant. [Source: architecture.md#Module Interface Pattern]
- **Terminal output:** ALL output via `typer.echo()` — never `print()`. Errors via `typer.echo(str(e), err=True)`. [Source: architecture.md#Terminal Output Pattern]
- **Error propagation:** `cli.py` is the ONLY place that catches `JiraReportError`. Pipeline modules raise; `cli.py` catches. [Source: architecture.md#Error Propagation Pattern]
- **Credential safety:** `str(e)` is safe because modules use safe error messages (Story 1.2 credential safety rule). `cli.py` never formats config fields into strings directly. [Source: architecture.md#Credential Safety Rule]
- **NFR2 startup:** `load_config()` is called first before any API client imports (lazy would be inside function). Since imports are at module top, `--help` works without network, satisfying NFR2 in spirit. The pipeline functions are not called until after config is loaded. [Source: architecture.md#NFR2]
- **Status message order:** `"Authenticating..."` → `"Fetching Jira data..."` → `"Generating report..."` → `"Writing output..."` → `"Done. Report saved: {path}"` — exact strings, exact order. [Source: architecture.md#Terminal Output Pattern]

### Scope Boundaries

**This story implements:**
- `cli.py`: Typer app, 4 flags, `_ensure_gitignore()`, pipeline call structure, error handling
- Minimal stub signatures in `jira_client.py`, `ai_engine.py`, `renderer.py`
- `tests/test_cli.py`

**DO NOT implement in this story:**
- Any data model definitions (JiraTicket, JiraData, ReportSections) — Story 2 scope
- Actual auth logic in `jira_client.py` — Story 1.4 scope
- Low-ticket-count warning — Story 2.3 scope
- Dry-run terminal summary logic — Story 4.3 scope

### Previous Story Learnings (from Stories 1.1 and 1.2)

- **uv PATH on WSL2:** If `uv` not found: `export PATH="$HOME/.local/bin:$PATH"`
- **After code changes:** `uv tool upgrade jira-report` (NOT reinstall)
- **Import verification:** `uv run python -c "from jira_report.cli import app; print('OK')"`
- **Pydantic v2 copy:** Use `config.model_copy(update={...})` — NOT `config.copy()` (v1 API)

### References

- Terminal output pattern: [Source: architecture.md#Terminal Output Pattern]
- Error propagation: [Source: architecture.md#Error Propagation Pattern]
- Credential safety: [Source: architecture.md#Credential Safety Rule]
- Module interface: [Source: architecture.md#Module Interface Pattern]
- `.gitignore` requirement: [Source: architecture.md#Authentication & Security, NFR6]
- CLI flags and FR coverage: [Source: architecture.md#Requirements to Structure Mapping]
- Story acceptance criteria: [Source: epics.md#Story 1.3]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- No issues encountered during implementation

### Completion Notes List

- Added importable stub functions (`fetch_jira_data`, `generate_report`, `render_and_write`) to pipeline modules — stubs raise `NotImplementedError`; Stories 2–4 will overwrite
- Implemented `cli.py`: full Typer app with 4 flags (`--week`, `--project`, `--output`, `--dry-run`), `_ensure_gitignore()`, pipeline call sequence with status messages, `JiraReportError` → stderr + exit 1
- `_ensure_gitignore()` walks parent dirs for `.git/`, creates or appends to `.gitignore` idempotently
- `config.model_copy(update={...})` used for flag overrides (Pydantic v2 immutable copy pattern)
- `uv tool upgrade jira-report` confirmed: `jira-report --help` shows all 4 flags in WSL terminal
- 11 new CLI tests + 9 existing config tests = 20 passed, 0 regressions

### File List

- `src/jira_report/cli.py`
- `src/jira_report/jira_client.py`
- `src/jira_report/ai_engine.py`
- `src/jira_report/renderer.py`
- `tests/test_cli.py`
