# Story 1.1: Project Scaffold & Module Structure

Status: review

## Story

As a developer setting up the tool for the first time,
I want a properly scaffolded Python project with all dependencies installed and the correct module structure in place,
so that all subsequent stories can be implemented without environment or structure issues.

## Acceptance Criteria

1. Running the scaffold commands creates `pyproject.toml` with all required dependencies, `requires-python = ">=3.12"`, and generates `uv.lock`.
2. `src/jira_report/` contains exactly: `__init__.py`, `cli.py`, `config.py`, `jira_client.py`, `ai_engine.py`, `renderer.py`, and `templates/report.html.j2` (empty placeholder).
3. `pyproject.toml` contains `[project.scripts]` with `jira-report = "jira_report.cli:app"`, `[tool.hatch.build.targets.wheel]` with `packages = ["src/jira_report"]`, and `[tool.pytest.ini_options]` with `testpaths = ["tests"]` and `asyncio_mode = "auto"`.
4. `tests/` contains stub files: `conftest.py`, `test_config.py`, `test_jira_client.py`, `test_ai_engine.py`, `test_renderer.py`, `test_cli.py`.
5. Running `uv tool install .` makes the `jira-report` command available globally in the WSL terminal.

## Tasks / Subtasks

- [x] Task 1: Initialize uv project (AC: 1)
  - [x] Run `uv init jira-report --python 3.12` in the desired parent directory
  - [x] `cd jira-report`
  - [x] Run `uv add "typer>=0.14.0" "anthropic>=0.97.0" jira "pyyaml>=6.0.3" "jinja2>=3.1.6" "pydantic>=2.0"`
  - [x] Run `uv add --dev pytest pytest-asyncio`
  - [x] Verify `uv.lock` is generated

- [x] Task 2: Configure pyproject.toml (AC: 3)
  - [x] Add `[project.scripts]` section with `jira-report = "jira_report.cli:app"`
  - [x] Add `[build-system]` section with `requires = ["hatchling"]` and `build-backend = "hatchling.build"`
  - [x] Add `[tool.hatch.build.targets.wheel]` with `packages = ["src/jira_report"]`
  - [x] Add `[tool.pytest.ini_options]` with `testpaths = ["tests"]` and `asyncio_mode = "auto"`

- [x] Task 3: Create src/jira_report module structure (AC: 2)
  - [x] Create `src/jira_report/__init__.py` with `__version__ = "0.1.0"`
  - [x] Create `src/jira_report/cli.py` (stub — empty Typer app placeholder)
  - [x] Create `src/jira_report/config.py` (stub — empty placeholder)
  - [x] Create `src/jira_report/jira_client.py` (stub — empty placeholder)
  - [x] Create `src/jira_report/ai_engine.py` (stub — empty placeholder)
  - [x] Create `src/jira_report/renderer.py` (stub — empty placeholder)
  - [x] Create `src/jira_report/templates/` directory
  - [x] Create `src/jira_report/templates/report.html.j2` (empty placeholder file)

- [x] Task 4: Create tests/ structure (AC: 4)
  - [x] Create `tests/conftest.py` (empty stub)
  - [x] Create `tests/test_config.py` (empty stub)
  - [x] Create `tests/test_jira_client.py` (empty stub)
  - [x] Create `tests/test_ai_engine.py` (empty stub)
  - [x] Create `tests/test_renderer.py` (empty stub)
  - [x] Create `tests/test_cli.py` (empty stub)

- [x] Task 5: Create supporting files
  - [x] Create `config.yaml.example` at project root (placeholder with all 8 fields — content finalized in Story 1.2)
  - [x] Create `README.md` at project root with basic tool description

- [x] Task 6: Install globally and verify (AC: 5)
  - [x] Run `uv tool install .` from project root
  - [x] Verify `jira-report --help` runs without error in WSL terminal
  - [x] Run `uv run pytest` to verify test suite runs (0 tests collected is OK at this stage)

## Dev Notes

### Environment
- **Platform:** WSL2 (Windows Subsystem for Linux 2)
- **Python:** 3.12 (pinned via `uv init --python 3.12`)
- **Package manager:** uv 0.11.8 — do NOT use pip, poetry, or conda
- **Build backend:** hatchling (required for src/ layout discovery)

### Exact pyproject.toml Structure

The final `pyproject.toml` must contain these sections exactly:

```toml
[project]
name = "jira-report"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "typer>=0.14.0",
    "anthropic>=0.97.0",
    "jira",
    "pyyaml>=6.0.3",
    "jinja2>=3.1.6",
    "pydantic>=2.0",
]

[project.scripts]
jira-report = "jira_report.cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/jira_report"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

**Critical:** `[project.scripts]` maps `jira-report` to `jira_report.cli:app` — this means `cli.py` MUST expose a Typer app named `app` (even as a stub). Without this, `uv tool install .` will fail on lookup.

### Minimum Viable Stub Files

**`src/jira_report/cli.py`** — must have a real (importable) Typer app stub so the entry point resolves:
```python
import typer
app = typer.Typer()

@app.command()
def main() -> None:
    pass
```

**`src/jira_report/__init__.py`**:
```python
__version__ = "0.1.0"
```

All other `.py` files can be truly empty or contain a single `# placeholder` comment.

### config.yaml.example Content

Create at project root with all 8 required fields (Story 1.2 will implement the Pydantic model that validates these):
```yaml
jira_url: https://yourcompany.atlassian.net
api_token: your-api-token-here
project_key: PROJ
output_dir: ./reports
ai_provider: anthropic
ai_model: claude-sonnet-4-6
report_tone: professional
project_name: Project Alpha
```

### Project Structure Reference

Final layout this story must produce:
```
jira-report/
├── pyproject.toml
├── uv.lock
├── .gitignore              ← uv creates this; do not modify
├── config.yaml.example
├── README.md
├── src/
│   └── jira_report/
│       ├── __init__.py     ← __version__ = "0.1.0"
│       ├── cli.py          ← Typer app stub (app must be importable)
│       ├── config.py       ← empty stub
│       ├── jira_client.py  ← empty stub
│       ├── ai_engine.py    ← empty stub
│       ├── renderer.py     ← empty stub
│       └── templates/
│           └── report.html.j2  ← empty placeholder
└── tests/
    ├── conftest.py
    ├── test_config.py
    ├── test_jira_client.py
    ├── test_ai_engine.py
    ├── test_renderer.py
    └── test_cli.py
```

### Architecture Compliance

- **Module interface pattern (future stories):** Each module will expose exactly ONE public entry function. Do not add any public functions to stubs — leave them truly empty. Future stories own their module content.
- **Naming convention:** All module files use `snake_case`. No exceptions.
- **src/ layout:** All package code lives under `src/jira_report/`. Nothing at project root except config/tool files.
- **Do NOT create:** `setup.py`, `setup.cfg`, `requirements.txt`, or any non-uv dependency file.

### WSL-Specific Notes

- `uv tool install .` installs the `jira-report` binary into uv's tool environment, making it available as a global WSL command.
- After code changes in future stories, run `uv tool upgrade jira-report` (NOT reinstall) to update the global binary.
- If `jira-report` command is not found after install, run `source ~/.bashrc` or open a new terminal.

### Testing Verification

At the end of this story, these commands must all succeed without error:
```bash
uv run pytest          # → "no tests ran" is OK
jira-report --help     # → Typer help output (even empty)
uv run python -c "from jira_report.cli import app; print('OK')"
```

### Project Structure Notes

- This story establishes the ONLY correct file locations for all future stories
- `src/jira_report/templates/` is inside the package — Jinja2 will load templates via package-relative path in Story 4.1
- `tests/` is flat (no subdirectories) — all test files live at `tests/*.py`

### References

- Architecture: Starter Template Evaluation section — `uv init` + Typer selection rationale [Source: architecture.md#Starter Template Evaluation]
- Architecture: Project Structure diagram [Source: architecture.md#Project Structure & Boundaries]
- Architecture: pyproject.toml key configuration [Source: architecture.md#pyproject.toml — Key Configuration]
- Epics: Story 1.1 acceptance criteria [Source: epics.md#Story 1.1]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- hatchling was accidentally added to `[project.dependencies]` via `uv add hatchling`; removed with `uv remove hatchling` — hatchling belongs only in `[build-system].requires`
- uv not found in WSL2 PATH on first run; installed via `curl -LsSf https://astral.sh/uv/install.sh | sh`, then prefixed all commands with `export PATH="$HOME/.local/bin:$PATH"`

### Completion Notes List

- All 6 acceptance criteria verified
- `uv run pytest` → 0 tests collected (expected)
- `jira-report --help` → Typer help output confirmed
- `uv run python -c "from jira_report.cli import app; print('OK')"` → OK

### File List

- `pyproject.toml`
- `uv.lock`
- `config.yaml.example`
- `README.md`
- `src/jira_report/__init__.py`
- `src/jira_report/cli.py`
- `src/jira_report/config.py`
- `src/jira_report/jira_client.py`
- `src/jira_report/ai_engine.py`
- `src/jira_report/renderer.py`
- `src/jira_report/templates/report.html.j2`
- `tests/conftest.py`
- `tests/test_config.py`
- `tests/test_jira_client.py`
- `tests/test_ai_engine.py`
- `tests/test_renderer.py`
- `tests/test_cli.py`
