# Story 4.2: Atomic File Write, Filename Generation & Dry-Run

Status: review

## Story

As a PM,
I want the report saved with an auto-generated date-stamped filename using a safe write process, with a dry-run option to preview without saving,
so that existing reports are never corrupted and I can preview before committing to disk.

## Acceptance Criteria

1. Given a successful render and `week_end` date, When `_generate_filename(week_end)` runs, Then the output filename is `report-YYYY-MM-DD.html` using the week end date (FR18).
2. Given the output file is being written, When `render_and_write()` executes the write, Then content is first written to a temp file in the output directory, And `shutil.move()` renames the temp file to the final path only after the write succeeds (NFR10), And if the write fails mid-way, the previously existing report file at that path is not corrupted.
3. Given `--output ./reports/` is provided, When `render_and_write()` determines the output path, Then the report is saved in `./reports/` instead of `config.output_dir` (FR19).
4. Given `--dry-run` is set, When `render_and_write(config, sections, week_end, dry_run=True)` is called, Then the rendered HTML is printed to stdout, And no file is written to disk under any circumstances (FR16, NFR11), And `render_and_write()` returns `None`.
5. Given `--dry-run` is set and the output directory does not exist, When `render_and_write()` runs, Then no error is raised — dry-run completes successfully regardless of output path validity (NFR11).

## Tasks / Subtasks

- [x] Task 1: Update `render_and_write` signature to accept `week_end: date` (AC: 1, breaking change)
  - [x] Architecture-doc signature is `render_and_write(config, sections, dry_run) -> Path | None`
  - [x] AC#1 explicitly requires `week_end` for filename generation; the canonical data path is `jira_data.week_end` from `jira_client.py`
  - [x] Add `week_end: date` as the third positional parameter (between `sections` and `dry_run`): `render_and_write(config: Config, sections: ReportSections, week_end: date, dry_run: bool = False) -> Optional[Path]`
  - [x] Add `from datetime import date` to renderer.py imports
  - [x] Document this signature evolution in Dev Notes — it fills a planning gap (analogous to the `Config.api_key` field added in Story 3.2)

- [x] Task 2: Implement `_generate_filename(week_end)` (AC: 1)
  - [x] Signature: `_generate_filename(week_end: date) -> str`
  - [x] Return `f"report-{week_end.isoformat()}.html"`
  - [x] No directory prefix — caller (`render_and_write`) joins with `output_dir`

- [x] Task 3: Implement atomic write via `_atomic_write` helper (AC: 2)
  - [x] Signature: `_atomic_write(final_path: Path, content: str) -> None`
  - [x] `tempfile.mkstemp(dir=str(final_path.parent), prefix=f".{final_path.name}.", suffix=".tmp")` — temp file in **same directory** as final path (cross-device renames may fail otherwise)
  - [x] Open the file descriptor with `os.fdopen(fd, "w", encoding="utf-8")` or `open(fd, ...)`; write content; close
  - [x] `shutil.move(str(tmp_path), str(final_path))` — atomic on same filesystem
  - [x] On any exception during write or move, attempt `tmp_path.unlink()` cleanup (best-effort); re-raise the original exception

- [x] Task 4: Implement `render_and_write` body (AC: 1–5)
  - [x] Replace the `NotImplementedError` body
  - [x] Step 1: `html = _render_html(config, sections)` (already implemented in Story 4.1)
  - [x] Step 2 (dry-run path): if `dry_run is True`, write `html` to `sys.stdout` via `sys.stdout.write(html)`, then return `None`. **No directory operations, no file writes — even if `config.output_dir` is invalid (NFR11)**
  - [x] Step 3 (write path): `output_dir = Path(config.output_dir)`
  - [x] Wrap `output_dir.mkdir(parents=True, exist_ok=True)` in `try/except OSError as e` → `raise OutputError(f"Cannot create output directory: {e}")`
  - [x] Compute `final_path = output_dir / _generate_filename(week_end)`
  - [x] Wrap `_atomic_write(final_path, html)` in `try/except OSError as e` → `raise OutputError(f"Failed to write report: {e}")`
  - [x] Return `final_path`

- [x] Task 5: Update `cli.py` to thread `jira_data.week_end` (AC: 1)
  - [x] Line 43 (Story 1.3 wiring): change `result_path = render_and_write(config, sections, dry_run=dry_run)` to `result_path = render_and_write(config, sections, jira_data.week_end, dry_run=dry_run)`
  - [x] No other cli.py changes — `JiraReportError` catch (line 50) already covers `OutputError` (subclass)

- [x] Task 6: Update `test_dry_run_flag` in `tests/test_cli.py` (AC: regression safety)
  - [x] Update `fake_render` signature: `def fake_render(config, sections, week_end, dry_run=False):`
  - [x] No other CLI test changes — all other tests use `return_value=Path(...)` which works for any signature

- [x] Task 7: Delete `test_render_and_write_still_raises_not_implemented` from `tests/test_renderer.py` (AC: regression cleanup)
  - [x] Story 4.1 added this guard test; Story 4.2 implements `render_and_write`, so the test is superseded by `test_render_and_write_writes_file_and_returns_path` (Task 8)

- [x] Task 8: Add tests in `tests/test_renderer.py` (AC: 1–5)
  - [x] Add imports: `from datetime import date`, `from unittest.mock import patch`, `from jira_report.config import OutputError`
  - [x] `test_generate_filename` — `_generate_filename(date(2026, 4, 27)) == "report-2026-04-27.html"`
  - [x] `test_render_and_write_writes_file_and_returns_path(tmp_path, sample_config, sample_sections)` — set `config.output_dir = str(tmp_path / "reports")`, call `render_and_write(...)` non-dry-run, assert returned `Path` exists, content contains `"Done body."` and DOCTYPE
  - [x] `test_render_and_write_filename_uses_week_end(tmp_path, sample_config, sample_sections)` — verify returned path's name is `report-2026-04-27.html` for `week_end=date(2026, 4, 27)`
  - [x] `test_render_and_write_creates_output_dir_if_missing(tmp_path, sample_config, sample_sections)` — `output_dir = tmp_path / "newdir"` doesn't exist; non-dry-run; assert `(tmp_path / "newdir").is_dir()` after call
  - [x] `test_render_and_write_uses_output_dir_from_config(tmp_path, sample_config, sample_sections)` — set custom `output_dir`; assert returned path is inside it
  - [x] `test_render_and_write_dry_run_returns_none(tmp_path, sample_config, sample_sections, capsys)` — `dry_run=True` → returns `None`
  - [x] `test_render_and_write_dry_run_writes_no_file(tmp_path, sample_config, sample_sections, capsys)` — `dry_run=True`, `output_dir = tmp_path`; assert no `*.html` files in `tmp_path` after call
  - [x] `test_render_and_write_dry_run_prints_html_to_stdout(tmp_path, sample_config, sample_sections, capsys)` — `dry_run=True`; `captured = capsys.readouterr()`; assert `"Done body."` in `captured.out` and `"<!DOCTYPE" in captured.out`
  - [x] `test_render_and_write_dry_run_with_nonexistent_output_dir(sample_config, sample_sections, capsys)` — `config.output_dir = "/path/that/definitely/does/not/exist"`; `dry_run=True`; no exception raised, returns `None` (NFR11)
  - [x] `test_atomic_write_uses_tempfile_then_move(tmp_path, sample_config, sample_sections)` — patch `jira_report.renderer.shutil.move` and `jira_report.renderer.tempfile.mkstemp`; call `render_and_write` non-dry-run; assert `mkstemp` called with `dir=str(output_dir)`, then `shutil.move(tmp_path_str, str(final_path))` called once, in that order
  - [x] `test_atomic_write_preserves_existing_file_on_failure(tmp_path, sample_config, sample_sections)` — pre-write a file at the final path with content `"OLD"`; patch `jira_report.renderer.shutil.move` to raise `OSError`; call `render_and_write` (expect `OutputError`); assert the original `"OLD"` content is still on disk at the final path
  - [x] `test_render_and_write_raises_output_error_on_mkdir_failure(tmp_path, sample_config, sample_sections)` — patch `jira_report.renderer.Path.mkdir` to raise `PermissionError("denied")`; assert `OutputError` raised; original SDK exception name (`PermissionError`) appears in message
  - [x] `test_render_and_write_raises_output_error_on_write_failure(tmp_path, sample_config, sample_sections)` — set valid `output_dir`; patch `jira_report.renderer._atomic_write` to raise `OSError("disk full")`; assert `OutputError` raised
  - [x] Run `uv run pytest` — all 99 pre-existing tests pass + new tests green (one deleted from test_renderer.py)

## Dev Notes

### Signature Change: `render_and_write` Adds `week_end`

The architecture document specifies:

```python
# renderer.py
def render_and_write(config: Config, sections: ReportSections, dry_run: bool) -> Path | None: ...
```

But Story 4.2's AC#1 explicitly requires `_generate_filename(week_end)` — and `week_end` is not derivable from `config` or `sections`. The canonical source of `week_end` is `jira_data.week_end` (from `jira_client.py`), which is available in `cli.py` at the time `render_and_write` is called.

**Three options were considered:**
- (a) Add `week_end` to `ReportSections` — pollutes the canonical data model with a non-AI-text field
- (b) Have `render_and_write` accept `jira_data` instead of `sections` — couples the renderer to Jira's data model
- (c) Add `week_end` as a positional parameter to `render_and_write`

**(c) is chosen.** It is the smallest, most explicit change. This is analogous to the `Config.api_key` field added in Story 3.2 — both fill planning gaps surfaced during implementation.

### `renderer.py` — Final State for Story 4.2

```python
from __future__ import annotations

import shutil
import sys
import tempfile
from datetime import date
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader

from jira_report.config import Config, OutputError
from jira_report.jira_client import ReportSections


_TEMPLATES_DIR = Path(__file__).parent / "templates"
_jinja_env = Environment(
    loader=FileSystemLoader(_TEMPLATES_DIR),
    autoescape=True,
    keep_trailing_newline=True,
)


def render_and_write(
    config: Config,
    sections: ReportSections,
    week_end: date,
    dry_run: bool = False,
) -> Optional[Path]:
    html = _render_html(config, sections)

    if dry_run:
        sys.stdout.write(html)
        return None

    output_dir = Path(config.output_dir)
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise OutputError(f"Cannot create output directory: {e}")

    final_path = output_dir / _generate_filename(week_end)
    try:
        _atomic_write(final_path, html)
    except OSError as e:
        raise OutputError(f"Failed to write report: {e}")
    return final_path


def _generate_filename(week_end: date) -> str:
    return f"report-{week_end.isoformat()}.html"


def _atomic_write(final_path: Path, content: str) -> None:
    fd, tmp_path_str = tempfile.mkstemp(
        dir=str(final_path.parent),
        prefix=f".{final_path.name}.",
        suffix=".tmp",
    )
    tmp_path = Path(tmp_path_str)
    try:
        with open(fd, "w", encoding="utf-8") as f:
            f.write(content)
        shutil.move(str(tmp_path), str(final_path))
    except Exception:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        raise


def _render_html(config: Config, sections: ReportSections) -> str:
    # Unchanged from Story 4.1
    template = _jinja_env.get_template("report.html.j2")
    return template.render(
        project_name=config.project_name,
        done_text=sections.done_text,
        in_progress_text=sections.in_progress_text,
        next_plan_text=sections.next_plan_text,
        executive_summary=sections.executive_summary,
    )
```

### Why `tempfile` Lives in the Output Directory

`tempfile.mkstemp(dir=str(final_path.parent), ...)` puts the temp file in the **same directory** as the final file. This matters because `shutil.move` is atomic only when source and destination are on the same filesystem. If the temp file lived in `/tmp` and the report in `~/reports/`, a cross-device write could leave a partial copy. Same-directory keeps the atomicity guarantee.

The `prefix=f".{final_path.name}."` puts the temp name with a leading `.` (typically hidden in `ls`) and embeds the final filename for grep-ability if a temp file leaks.

### Why `sys.stdout.write` (Not `typer.echo` or `print`) for Dry-Run

The architecture rules state:
- "All terminal output via `typer.echo()` only — never `print()`" — for status messages and warnings
- Module boundaries: `typer` is owned by `cli.py` (no other module imports it for status output)

The dry-run HTML payload is **report content**, not a status message. Three options:

- `print(html)` — violates the "never `print()`" rule literally
- `typer.echo(html)` — would force `renderer.py` to import `typer` solely for one call, weakening the cli.py-as-typer-owner convention
- `sys.stdout.write(html)` — explicit, no extra import, no rule violation

**`sys.stdout.write` is chosen.** It clearly signals "this is a payload write, not a styled status message." The existing typer.echo'd lines around the call ("Writing output...", "Dry run — no file written") still go through the cli.py status channel.

### Atomic Write Failure Modes

The atomic-write pattern protects against three failure modes:

1. **Mid-write crash** — content is partially written to the **temp file**, never to the final path. The original file at `final_path` (if any) is untouched.
2. **`shutil.move` failure** — temp file remains; final path is untouched. Cleanup attempts to `unlink` the temp.
3. **mkdir failure** — caught upstream; no temp file is created.

The `test_atomic_write_preserves_existing_file_on_failure` test enforces invariant #1+#2 by:
- Pre-writing `"OLD"` content to the final path
- Patching `shutil.move` to raise
- Asserting the file at `final_path` still contains `"OLD"` after the failed call

### `cli.py` Update — One-Line Change

Before (current):
```python
result_path = render_and_write(config, sections, dry_run=dry_run)
```

After:
```python
result_path = render_and_write(config, sections, jira_data.week_end, dry_run=dry_run)
```

`jira_data` is in scope at the call site (Story 2.3 introduced `_warn_low_ticket_counts(jira_data)` two lines above). No other changes to `cli.py`.

### Test File Changes

**`tests/test_cli.py`** — only one breaking change:

```python
# test_dry_run_flag — fake_render needs to accept week_end now
def fake_render(config, sections, week_end, dry_run=False):  # ← was (config, sections, dry_run=False)
    captured["dry_run"] = dry_run
    return None
```

All other CLI tests use `patch("jira_report.cli.render_and_write", return_value=Path(...))` which doesn't care about signature. They continue to work.

**`tests/test_renderer.py`** — delete `test_render_and_write_still_raises_not_implemented` (added in Story 4.1 as a placeholder guard); replaced by the suite of write/dry-run tests added in this story.

### Project Structure Notes

Files to modify:
- `src/jira_report/renderer.py` — add `_generate_filename`, `_atomic_write`; implement `render_and_write` body; add imports (`shutil`, `sys`, `tempfile`, `date`, `OutputError`)
- `src/jira_report/cli.py` — pass `jira_data.week_end` to `render_and_write` (one-line change)
- `tests/test_cli.py` — update `test_dry_run_flag` `fake_render` signature
- `tests/test_renderer.py` — delete one test, add ~13 new tests

No new files. No template, config, or jira_client changes.

### Architecture Compliance

- `render_and_write` remains the only public function; `_generate_filename`, `_atomic_write`, `_render_html` are private. [Source: architecture.md#Module Interface Pattern]
- `OutputError` raised on file-write failures; cli.py catches `JiraReportError` (base class). [Source: architecture.md#Error Propagation Pattern, architecture.md#Authentication & Security]
- Atomic temp-file-then-rename pattern. [Source: architecture.md#Atomic File Write Pattern]
- `--dry-run` short-circuits before any file touch (NFR11). [Source: architecture.md#Cross-Cutting Concerns NFR11]
- `--output` flag override propagated via `config.output_dir` mutation in cli.py (already implemented in Story 1.3). [Source: architecture.md#Requirements to Structure Mapping FR19]
- No `typer` import in renderer.py — payload write uses `sys.stdout.write` directly. [Source: architecture.md#Terminal Output Pattern, architecture.md#Module Boundaries]

### Scope Boundaries

**This story implements:**
- `_generate_filename(week_end) -> str`
- `_atomic_write(final_path, content) -> None`
- `render_and_write(config, sections, week_end, dry_run=False) -> Optional[Path]` — full body
- `cli.py` one-line update to pass `jira_data.week_end`
- `test_dry_run_flag` `fake_render` signature update
- `test_render_and_write_still_raises_not_implemented` deletion
- ~13 new tests in `test_renderer.py` covering filename generation, write happy path, output-dir creation, dry-run behavior, atomic write call order, write-failure file preservation, OutputError mapping

**DO NOT implement:**
- Terminal run summary with ticket counts — Story 4.3 scope
- Filename collision handling (overwriting existing report file is acceptable per AC: write succeeds → atomic move overwrites)
- File permissions / chmod — out of V1 scope
- Backup of existing report before overwrite — atomic move handles the "never corrupt on failure" requirement; preserving prior file is a nice-to-have for a later story
- Multi-format output (PDF, etc.) — out of V1 scope

### Previous Story Learnings (from Stories 1.1–4.1)

- **uv PATH on WSL2:** `export PATH="$HOME/.local/bin:$PATH"` if needed
- **CWD:** `uv run pytest` must run from `jira-report/` (the Python project root); some sessions drift to that dir after a `cd`. Always check `pwd` before staging git commits — root commits must run from `/mnt/c/Users/Public/nardi`.
- **Mock namespace rule:** patch `jira_report.renderer.<symbol>` (e.g., `jira_report.renderer.shutil.move`) — NOT `shutil.move` directly. Patches must target where the name is used.
- **`sample_sections` fixture (Story 4.1):** in `tests/conftest.py`. Reuse for all renderer tests.
- **`sample_config` fixture (Story 1.2 + Story 3.2 update):** has `api_key` and `output_dir="./reports"`. For renderer tests, override `output_dir` via `sample_config.model_copy(update={"output_dir": str(tmp_path)})` to scope writes to pytest's temp dir.
- **`tmp_path` is a pytest builtin** — provides a unique `Path` for each test. Use it as the file system sandbox.
- **`capsys` for stdout/stderr capture** — `capsys.readouterr()` returns `.out` (stdout) and `.err` (stderr).
- **Pydantic `Config.model_copy(update={...})`** — used in Stories 1.3 and 3.1; the same pattern works for `output_dir` overrides.
- **Empty placeholder gotcha:** `test_renderer.py` was a `# placeholder` until Story 4.1 filled it. Story 4.2 deletes one test and adds ~13 — straightforward Edit operations.
- **MagicMock `__len__()` returns 0:** not relevant for renderer tests (no MagicMock substitution for `Config`/`ReportSections`).
- **Architecture's signature evolution:** `render_and_write`'s `week_end` parameter is the second deviation from the architecture doc's specified signatures (the first was `Config.api_key`). Both are documented as planning gaps with explicit rationale.

### Latest Tech Information

- **`tempfile.mkstemp(dir=...)`** returns `(fd, path)` — caller owns the fd. Use `os.fdopen(fd, ...)` or `open(fd, ...)` to get a file object; closing it closes the fd. Do NOT also close the underlying fd separately.
- **`shutil.move(src, dst)`** — atomic on the same filesystem (uses `os.rename`); falls back to copy+delete cross-device. Requires str paths in older Python; Python 3.12 accepts Path-like.
- **`Path.mkdir(parents=True, exist_ok=True)`** — idempotent directory creation; raises `OSError` only on permission/IO failures, not on existing directory.
- **`sys.stdout.write` vs `print`** — `print` adds a trailing newline; `write` doesn't. Our template ends with a newline (`keep_trailing_newline=True` from Story 4.1), so `sys.stdout.write(html)` produces the same on-screen result as `print(html)` minus a redundant blank line.

### Git Intelligence Summary

- (current uncommitted) Story 4.1 just landed locally — `_render_html`, `report.html.j2`, `sample_sections` fixture. Story 4.2 builds directly on those.
- `b5ed1cd Add Story 3.2: Claude API call and ReportSections assembly` — established the "fill a planning gap with a documented signature deviation" precedent (`Config.api_key`). Story 4.2 follows the same precedent for `render_and_write`'s `week_end` parameter.
- `f5c42d1 Implement Story 2.3: low-ticket-count data quality warning` — established the cli.py pattern of receiving `jira_data` and calling helpers with parts of it (`_warn_low_ticket_counts(jira_data)`). Story 4.2 extends with `jira_data.week_end`.

### References

- FR16 (--dry-run preview): [Source: epics.md#Story 4.2, architecture.md#Requirements to Structure Mapping FR16]
- FR18 (auto-generated filename): [Source: epics.md#Story 4.2, architecture.md#Requirements to Structure Mapping FR18]
- FR19 (--output flag): [Source: epics.md#Story 4.2, architecture.md#Requirements to Structure Mapping FR19]
- NFR10 (atomic write, never corrupt previous file): [Source: architecture.md#Atomic File Write Pattern, architecture.md#Cross-Cutting Concerns NFR10]
- NFR11 (--dry-run no files): [Source: architecture.md#Cross-Cutting Concerns NFR11]
- `OutputError` exception: [Source: architecture.md#Error Propagation Pattern]
- Module interface (single public function): [Source: architecture.md#Module Interface Pattern]

## Dev Agent Record

### Agent Model Used

claude-opus-4-7 (1M context)

### Debug Log References

- Initial pytest run: 110 passed, 1 failed — `test_atomic_write_uses_tempfile_then_move` hit `RecursionError` because the test's `tracking_move(src, dst)` did `import shutil as real_shutil; real_shutil.move(src, dst)` which re-resolves to the patched `shutil.move` (the patch is on `jira_report.renderer.shutil.move`, but `shutil` is shared module state). Fix: replaced the inner call with `os.rename(src, dst)` which is filesystem-atomic and bypasses the patched `shutil` entirely. After the fix: 111 passed.

### Completion Notes List

- Implemented `_generate_filename(week_end) -> str` returning `f"report-{week_end.isoformat()}.html"`.
- Implemented `_atomic_write(final_path, content) -> None`: `tempfile.mkstemp` in the same directory as the final path (so `shutil.move` stays atomic), write content via `open(fd, "w", encoding="utf-8")`, `shutil.move` to final path. On any exception, best-effort `tmp_path.unlink()` cleanup before re-raising.
- Implemented `render_and_write(config, sections, week_end, dry_run=False) -> Optional[Path]`: dry-run path writes HTML via `sys.stdout.write` and returns `None` (no directory operations); write path creates the output dir (idempotent `mkdir(parents=True, exist_ok=True)`), wraps mkdir and `_atomic_write` failures into `OutputError` with descriptive messages, returns the final `Path`.
- Updated `cli.py` line 43 to thread `jira_data.week_end`: `render_and_write(config, sections, jira_data.week_end, dry_run=dry_run)`. No other cli.py changes — `JiraReportError` catch already covers `OutputError` (subclass).
- Updated `test_dry_run_flag` `fake_render` signature in `tests/test_cli.py` from `(config, sections, dry_run=False)` to `(config, sections, week_end, dry_run=False)`. All other CLI tests use `return_value=Path(...)` and didn't need updating.
- Deleted `test_render_and_write_still_raises_not_implemented` (Story 4.1's placeholder guard) — superseded by the new write-path tests.
- Added 13 new tests in `tests/test_renderer.py` covering: filename format, write happy path with file existence + content check, filename matches `week_end`, output dir auto-creation, output_dir override flow, dry-run returns `None`, dry-run writes no file, dry-run prints HTML to stdout via `capsys`, dry-run with non-existent output_dir doesn't raise (NFR11), atomic write call order (`mkstemp` → `move`) with `dir=str(output_dir)` argument verified, existing file preserved when `shutil.move` fails (`OutputError` raised, original `"OLD"` content intact), `OutputError` raised on `mkdir` `PermissionError`, `OutputError` raised on `_atomic_write` `OSError`.
- Test recursion gotcha (filed as a "previous story learning" for future work): patches like `patch("jira_report.renderer.shutil.move", side_effect=...)` make `shutil.move` recursive if the side_effect calls back into `shutil`. Use `os.rename` directly inside test side_effects to bypass the patch.
- Final result: **111 tests pass** (was 99; +12 net new; 0 regressions). All ACs satisfied.

### File List

- `jira-report/src/jira_report/renderer.py` (modified) — added `shutil`/`sys`/`tempfile`/`date` imports, `OutputError` import; implemented `render_and_write`, `_generate_filename`, `_atomic_write`
- `jira-report/src/jira_report/cli.py` (modified) — one-line update to pass `jira_data.week_end` to `render_and_write`
- `jira-report/tests/test_renderer.py` (modified) — deleted `test_render_and_write_still_raises_not_implemented`; added imports + 13 new tests covering filename, write/dry-run paths, atomic write, error mapping
- `jira-report/tests/test_cli.py` (modified) — added `week_end` parameter to `fake_render` in `test_dry_run_flag`

## Change Log

| Date       | Description                                                                                                                                                                                              |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-05-06 | Implemented Story 4.2: filename generation, atomic file write, dry-run path. Added `week_end: date` parameter to `render_and_write` (planning-gap fill, second after `Config.api_key`). Status: ready-for-dev → review. |
