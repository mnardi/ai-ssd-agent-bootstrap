# Story 4.1: HTML Report Template & Jinja2 Rendering

Status: review

## Story

As a PM,
I want the generated report rendered as a clean, email-safe HTML file I can paste directly into my email client,
so that the report is ready to send without any formatting work on my part.

## Acceptance Criteria

1. Given a `ReportSections` object, When the rendering helper runs `report.html.j2` via Jinja2, Then the output is a complete HTML document with inline CSS — no external stylesheets, no JavaScript (FR17).
2. Given `report.html.j2` is inspected, When I review the template structure, Then it contains fixed section headings: Done, In Progress, Next Plan, Executive Summary, And each section has a `{{ }}` slot where the corresponding `ReportSections` field is injected (NFR12).
3. Given the same `ReportSections` input is rendered twice, When the HTML output of both renders is compared, Then the structure — headings, layout, CSS — is identical; only the AI-generated text content varies (NFR12).
4. Given AI-generated section text contains HTML-unsafe characters (`<`, `>`, `&`, quotes), When the template renders, Then those characters are HTML-escaped — the rendered HTML cannot inject markup or scripts from the section text.
5. Given the HTML is opened in an email client, When the content is reviewed, Then formatting renders correctly without broken styles from external dependencies.

## Tasks / Subtasks

- [x] Task 1: Add `sample_sections` fixture to `tests/conftest.py` (AC: 2, 3, 4)
  - [x] Add import `from jira_report.jira_client import ReportSections` (already imported via `JiraData, JiraTicket` — extend the existing import)
  - [x] Add `sample_sections` fixture returning `ReportSections(done_text="Done body.", in_progress_text="IP body.", next_plan_text="NP body.", executive_summary="ES body.")`
  - [x] Place after `sample_jira_data` fixture
  - [x] Distinct, recognizable strings make assertions in renderer tests trivial

- [x] Task 2: Replace empty `src/jira_report/templates/report.html.j2` with the email-safe template (AC: 1, 2, 5)
  - [x] Use the exact template content shown in Dev Notes
  - [x] Inline `style=""` on every styled element — no `<style>` block, no `<link rel="stylesheet">`, no `<script>`
  - [x] Four fixed `<h2>` headings: `Done`, `In Progress`, `Next Plan`, `Executive Summary`
  - [x] Four `<p>` slots with `{{ done_text }}`, `{{ in_progress_text }}`, `{{ next_plan_text }}`, `{{ executive_summary }}`
  - [x] Title and `<h1>` use `{{ project_name }}`

- [x] Task 3: Implement Jinja2 environment and `_render_html` in `renderer.py` (AC: 1, 2, 3, 4)
  - [x] Replace existing 8-line stub completely
  - [x] Add imports: `from jinja2 import Environment, FileSystemLoader`, `from jira_report.config import Config`, `from jira_report.jira_client import ReportSections`
  - [x] Define `_TEMPLATES_DIR = Path(__file__).parent / "templates"` (module level)
  - [x] Define `_jinja_env = Environment(loader=FileSystemLoader(_TEMPLATES_DIR), autoescape=True, keep_trailing_newline=True)` (module level)
  - [x] Implement `_render_html(config: Config, sections: ReportSections) -> str`:
    - Load `report.html.j2` via `_jinja_env.get_template(...)`
    - Render with kwargs: `project_name`, `done_text`, `in_progress_text`, `next_plan_text`, `executive_summary`
    - Return the rendered string
  - [x] Keep `render_and_write(config, sections, dry_run: bool = False) -> Optional[Path]` raising `NotImplementedError` — Story 4.2 wires file output

- [x] Task 4: Add tests in `tests/test_renderer.py` (AC: 1, 2, 3, 4)
  - [x] Replace `# placeholder` line completely
  - [x] Add imports: `pytest`, `re`, `from jira_report.renderer import _render_html, render_and_write`, `from jira_report.jira_client import ReportSections`
  - [x] `test_render_html_returns_string` — call `_render_html(sample_config, sample_sections)` → `isinstance(result, str)` and length > 0
  - [x] `test_render_html_includes_all_four_section_headers` — output contains `Done`, `In Progress`, `Next Plan`, `Executive Summary`
  - [x] `test_render_html_includes_all_four_section_texts` — output contains `"Done body."`, `"IP body."`, `"NP body."`, `"ES body."`
  - [x] `test_render_html_includes_project_name` — output contains `sample_config.project_name` (`"Test Project"`)
  - [x] `test_render_html_no_external_stylesheets` — `'<link rel="stylesheet"' not in output` and `"<style>" not in output` (case-insensitive)
  - [x] `test_render_html_no_javascript` — `"<script" not in output.lower()`; also assert no `onclick=`, `onload=`, `onerror=`, `javascript:` substrings
  - [x] `test_render_html_has_doctype_and_html_root` — output starts with `<!DOCTYPE html>` (case-insensitive) and contains `<html` and `</html>`
  - [x] `test_render_html_has_charset_meta` — output contains `<meta charset="utf-8">` (case-insensitive)
  - [x] `test_render_html_uses_inline_styles` — at least 3 `style="` occurrences in output (inline CSS confirmation)
  - [x] `test_render_html_escapes_html_in_section_text` — pass `ReportSections(done_text="<script>alert(1)</script>", ...)` with sample_config → assert `"<script>alert(1)</script>"` NOT in output, and `"&lt;script&gt;"` IS in output
  - [x] `test_render_html_escapes_ampersand` — pass `ReportSections(done_text="A & B", ...)` → output contains `"A &amp; B"` and not raw `"A & B"`
  - [x] `test_render_html_deterministic_for_same_input` — call `_render_html` twice with same config + sections → both outputs identical (NFR12)
  - [x] `test_render_html_section_order_matches_template` — Done appears before In Progress, which appears before Next Plan, which appears before Executive Summary (output ordering check using `output.index()`)
  - [x] `test_render_and_write_still_raises_not_implemented` — `render_and_write(sample_config, sample_sections)` raises `NotImplementedError` (Story 4.2 will wire this)
  - [x] Run `uv run pytest` — all 85 pre-existing tests pass + new tests green

## Dev Notes

### `templates/report.html.j2` — Final Content

Inline-styled, email-client-safe. No `<style>` block, no external stylesheets, no JavaScript.

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{{ project_name }} — Weekly Status Report</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; max-width: 720px; margin: 0 auto; padding: 24px; color: #1f2328; background: #ffffff;">

<h1 style="font-size: 24px; margin: 0 0 24px 0; color: #1f2328;">{{ project_name }} — Weekly Status Report</h1>

<h2 style="font-size: 18px; margin: 32px 0 8px 0; color: #1f2328; border-bottom: 1px solid #d1d5da; padding-bottom: 6px;">Done</h2>
<p style="margin: 0 0 16px 0; line-height: 1.6;">{{ done_text }}</p>

<h2 style="font-size: 18px; margin: 32px 0 8px 0; color: #1f2328; border-bottom: 1px solid #d1d5da; padding-bottom: 6px;">In Progress</h2>
<p style="margin: 0 0 16px 0; line-height: 1.6;">{{ in_progress_text }}</p>

<h2 style="font-size: 18px; margin: 32px 0 8px 0; color: #1f2328; border-bottom: 1px solid #d1d5da; padding-bottom: 6px;">Next Plan</h2>
<p style="margin: 0 0 16px 0; line-height: 1.6;">{{ next_plan_text }}</p>

<h2 style="font-size: 18px; margin: 32px 0 8px 0; color: #1f2328; border-bottom: 1px solid #d1d5da; padding-bottom: 6px;">Executive Summary</h2>
<p style="margin: 0 0 16px 0; line-height: 1.6;">{{ executive_summary }}</p>

</body>
</html>
```

**Why inline styles only:** every major email client (Gmail, Outlook, Apple Mail, Outlook Web) strips or ignores `<style>` blocks and external stylesheets. Inline `style=""` is the only universally supported styling channel.

**Font stack:** system fonts only — no web font fetches. Fast render, no broken-font fallbacks in offline / restricted email clients.

**Colors:** GitHub-ish neutral palette (`#1f2328` text, `#d1d5da` borders) — readable, professional, not vendor-specific.

**Layout:** `max-width: 720px` keeps line length readable in wide email panes; `margin: 0 auto` centers the content.

### `renderer.py` — Final State for Story 4.1

```python
from __future__ import annotations

from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader

from jira_report.config import Config
from jira_report.jira_client import ReportSections


_TEMPLATES_DIR = Path(__file__).parent / "templates"
_jinja_env = Environment(
    loader=FileSystemLoader(_TEMPLATES_DIR),
    autoescape=True,
    keep_trailing_newline=True,
)


def render_and_write(config: Config, sections: ReportSections, dry_run: bool = False) -> Optional[Path]:
    """Render the report and write it to disk (or skip on dry_run).

    Story 4.1 implements the rendering portion via `_render_html`; Story 4.2
    wires filename generation, atomic file write, and the dry-run path.
    """
    raise NotImplementedError  # Story 4.2: filename generation + atomic write + dry-run handling


def _render_html(config: Config, sections: ReportSections) -> str:
    template = _jinja_env.get_template("report.html.j2")
    return template.render(
        project_name=config.project_name,
        done_text=sections.done_text,
        in_progress_text=sections.in_progress_text,
        next_plan_text=sections.next_plan_text,
        executive_summary=sections.executive_summary,
    )
```

### Why `autoescape=True` (Always)

`select_autoescape(["html", "j2"])` is the Jinja2 idiom but matches by extension: `.html.j2` extension is technically `.j2`, which would match. To eliminate any chance of a security gap from filename-extension matching surprises, we set `autoescape=True` unconditionally — every render escapes HTML-unsafe characters.

**This matters because** AI-generated section text is **untrusted** in the security sense: a prompt-injection attack or quirky model output could include `<script>` or `<iframe>` tags. Autoescape guarantees those become `&lt;script&gt;` / `&lt;iframe&gt;` in the output and never execute when the HTML is opened.

The `test_render_html_escapes_html_in_section_text` test enforces this.

### `_render_html` Signature Decision

Two viable signatures:

- **(a)** `_render_html(sections: ReportSections) -> str` — minimal, no config dependency
- **(b)** `_render_html(config: Config, sections: ReportSections) -> str` — passes `project_name` for the title

**(b) is chosen** because the `<h1>` and `<title>` use `project_name`. AC#5 asks for "formatting renders correctly" — a generic title degrades the email's contextual value. Passing `config` matches the other `*_engine` modules' "config first" parameter convention.

### `tests/conftest.py` Update — Add `sample_sections` Fixture

```python
@pytest.fixture
def sample_sections():
    return ReportSections(
        done_text="Done body.",
        in_progress_text="IP body.",
        next_plan_text="NP body.",
        executive_summary="ES body.",
    )
```

Distinct, recognizable strings (`"Done body."` vs `"IP body."` etc.) make every renderer test assertion grep-friendly: `assert "Done body." in result` immediately localizes which slot rendered which content.

Add `ReportSections` to the existing `from jira_report.jira_client import JiraData, JiraTicket` line.

### Render Determinism (NFR12)

Jinja2 renders are pure functions of (template, render kwargs). With autoescape on (deterministic escape rules) and no `now()` / random calls in the template, repeated `template.render(**kwargs)` calls produce byte-identical output. The `test_render_html_deterministic_for_same_input` test verifies this directly.

If a future change introduces dynamic content (e.g., a render timestamp), it must be an **input** (passed in by `render_and_write`), not a template-side `{{ now() }}`. This keeps the template deterministic and unit-testable.

### `cli.py` — No Changes Required

`cli.py` already echoes `"Writing output..."` before calling `render_and_write` (Story 1.3). It still calls a stub-form `render_and_write` that raises `NotImplementedError` until Story 4.2 — but no end-to-end runs occur in tests (all CLI tests patch `render_and_write`). No `cli.py` changes in Story 4.1.

### Project Structure Notes

Files to modify / create:
- `src/jira_report/templates/report.html.j2` — currently empty (0 bytes); replace with the full template
- `src/jira_report/renderer.py` — replace the 8-line stub with imports, env setup, `_render_html`, stub `render_and_write`
- `tests/conftest.py` — add `ReportSections` import and `sample_sections` fixture
- `tests/test_renderer.py` — replace `# placeholder` with full test suite (~14 tests)

No new files. No `cli.py`, `ai_engine.py`, `jira_client.py`, or `config.py` changes.

### Architecture Compliance

- `render_and_write` is the only public function; `_render_html` is private. [Source: architecture.md#Module Interface Pattern]
- `ReportSections` imported from `jira_client.py` — never redefined. [Source: architecture.md#Canonical Data Models]
- `Config` imported from `config.py`. [Source: architecture.md#Module Interface Pattern]
- Jinja2 used (per architecture); no other templating library. [Source: architecture.md#Selected Starter, architecture.md#HTML Templating]
- Autoescape ON: required for safe rendering of AI-generated text. [Source: architecture.md#NFR12 Deterministic + general security best practice]
- No `print()` calls or terminal output here. [Source: architecture.md#Terminal Output Pattern]
- Inline CSS only — `<style>` and external stylesheets forbidden per FR17. [Source: epics.md#Story 4.1]

### Scope Boundaries

**This story implements:**
- Email-safe HTML template with 4 fixed sections + inline CSS
- Jinja2 `Environment` + `FileSystemLoader` setup with `autoescape=True`
- `_render_html(config, sections) -> str` private helper
- `sample_sections` fixture for `tests/conftest.py`
- ~14 tests covering rendering, escaping, structure, and determinism

**DO NOT implement:**
- `render_and_write` body — Story 4.2 wires file output
- `_generate_filename()` — Story 4.2 scope
- Atomic temp-file write via `shutil.move` — Story 4.2 scope
- `--dry-run` handling — Story 4.2 scope
- `--output` flag override (already in `cli.py` as flag; payload propagation is Story 4.2)
- Any `cli.py` changes
- Email-client compatibility testing across Outlook/Gmail/Apple Mail (manual user verification post-implementation)

### Previous Story Learnings (from Stories 1.1–3.2)

- **uv PATH on WSL2:** `export PATH="$HOME/.local/bin:$PATH"` if needed
- **CWD drift in this repo:** the project root is `/mnt/c/Users/Public/nardi/`; the Python project is at `jira-report/`. `uv run pytest` must run from inside `jira-report/`. Tests reference `_bmad-output/...` only via story files, never in-test code.
- **Mock namespace rule:** patch `jira_report.renderer.<symbol>` when needed — NOT `jinja2.<symbol>`. Story 4.1 likely doesn't need mocking (Jinja2 is fast, deterministic, and template I/O is tiny).
- **Empty placeholder gotcha:** `tests/test_renderer.py` is `# placeholder`; `report.html.j2` is 0 bytes. Both must be fully replaced — `Read` tool will warn on empty/short files. Use `Write` for replacement.
- **`MagicMock().__len__()` returns 0:** not relevant here (no MagicMock substitution for `ReportSections`), but if a future test uses one, the same trap from Story 2.3 applies.
- **Pydantic `Config`** has `api_key` since Story 3.2 — `sample_config` already includes it. Renderer doesn't need `api_key`, but if a renderer test instantiates `Config` directly (vs using fixture), include `api_key`.
- **`ReportSections`** lives in `jira_report.jira_client` per architecture (canonical location). Already imported there since Story 2.2.

### Latest Tech Information

- **Jinja2** `>=3.1.6` (per `pyproject.toml`); installed: `3.1.6`
- **`FileSystemLoader`** is the safe choice over `PackageLoader` for editable installs and dev workflow — `Path(__file__).parent / "templates"` resolves correctly under both `uv run` and `uv tool install`.
- **`autoescape=True`** is more conservative than `select_autoescape([...])` — both are correct here; we choose unconditional for security clarity.
- **`keep_trailing_newline=True`** preserves the trailing newline at the end of the template — produces cleaner-on-disk HTML files (POSIX-style).
- **Email-client CSS support reference:** Litmus / Email on Acid have published CSS-support tables; the inline subset used here (color, font-family, font-size, margin, padding, line-height, border, max-width, background) is universally supported. No CSS Grid, no flexbox, no `position: fixed`, no `@media` queries — none of these are reliable in email.

### Git Intelligence Summary

Recent commits (most recent first):
- `b5ed1cd Add Story 3.2: Claude API call and ReportSections assembly` — `ReportSections` is now actively populated by `generate_report`. Story 4.1 consumes it. Story 3.2 also added the `api_key` field to `Config` and the `sample_config` fixture.
- `7dad096 Add Story 3.1: AI prompt construction` — `sample_jira_data` fixture pattern in `conftest.py` is the model to follow for `sample_sections`.
- `f5c42d1 Implement Story 2.3: low-ticket-count data quality warning` — established the "fixture per data class" convention in `tests/conftest.py`.
- `a4c5081 Add Story 2.2: parallel ticket retrieval and JiraData assembly` — defined `ReportSections(done_text, in_progress_text, next_plan_text, executive_summary)` (the canonical dataclass Story 4.1 imports).

### References

- FR17 (HTML email-safe output): [Source: epics.md#Story 4.1, architecture.md#Requirements to Structure Mapping FR17]
- NFR12 (deterministic structure): [Source: epics.md#Story 4.1, architecture.md#Cross-Cutting Concerns NFR12]
- Jinja2 + `templates/report.html.j2` location: [Source: architecture.md#Project Structure & Boundaries]
- Module interface (single public function `render_and_write`): [Source: architecture.md#Module Interface Pattern]
- `ReportSections` dataclass fields: [Source: architecture.md#Canonical Data Models]
- Inline-CSS requirement: [Source: epics.md#Story 4.1 AC #1, architecture.md#Technical Constraints & Dependencies]

## Dev Agent Record

### Agent Model Used

claude-opus-4-7 (1M context)

### Debug Log References

- `uv run pytest` — 99 passed (was 85 before this story; +14 new renderer tests).
- No debugging required. All 14 tests passed on first run.

### Completion Notes List

- Added `sample_sections` fixture to `tests/conftest.py` with grep-friendly distinct strings (`"Done body."`, `"IP body."`, `"NP body."`, `"ES body."`). Extended the existing `from jira_report.jira_client import JiraData, JiraTicket` line to also import `ReportSections`.
- Replaced the empty `src/jira_report/templates/report.html.j2` (0 bytes) with the full email-safe template: DOCTYPE, charset meta, inline-styled `<h1>` (project name title), four `<h2>` section headings (`Done`, `In Progress`, `Next Plan`, `Executive Summary`), four `{{ }}` slots for `ReportSections` fields. No `<style>` block, no external stylesheets, no JavaScript.
- Replaced the 8-line `renderer.py` stub with module-level Jinja2 environment (`FileSystemLoader` pointing at `src/jira_report/templates/`, `autoescape=True`, `keep_trailing_newline=True`), and implemented `_render_html(config, sections) -> str`. `render_and_write` remains `NotImplementedError` — Story 4.2 will wire filename generation, atomic write, and dry-run.
- Replaced the `# placeholder` `tests/test_renderer.py` with a 14-test suite covering: returns string; all 4 headers present; all 4 section texts present; project_name in output; no external stylesheets / `<style>` blocks; no JavaScript / inline event handlers / `javascript:` URIs; DOCTYPE + `<html>` root; charset meta; ≥3 inline `style="..."` occurrences; HTML escapes `<script>` to `&lt;script&gt;`; ampersand escapes to `&amp;`; deterministic output for same input (NFR12); section order Done → In Progress → Next Plan → Executive Summary; `render_and_write` still raises `NotImplementedError`.
- `cli.py` unchanged — `"Writing output..."` echo and `JiraReportError` catch were already in place from Story 1.3, and existing CLI tests patch `render_and_write` so they continue to pass against the still-stubbed function.
- Final result: 99 tests pass, zero regressions.

### File List

- `jira-report/src/jira_report/templates/report.html.j2` (modified) — replaced empty placeholder with email-safe inline-styled HTML template
- `jira-report/src/jira_report/renderer.py` (modified) — replaced 8-line stub with Jinja2 env + `_render_html`; `render_and_write` remains `NotImplementedError`
- `jira-report/tests/conftest.py` (modified) — extended `ReportSections` import; added `sample_sections` fixture
- `jira-report/tests/test_renderer.py` (modified) — replaced `# placeholder` with 14-test suite

## Change Log

| Date       | Description                                                                                                |
| ---------- | ---------------------------------------------------------------------------------------------------------- |
| 2026-05-06 | Implemented Story 4.1: HTML report template + Jinja2 rendering (FR17, NFR12). Status: ready-for-dev → review. |
