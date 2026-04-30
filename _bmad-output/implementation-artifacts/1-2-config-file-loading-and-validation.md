# Story 1.2: Config File Loading & Validation

Status: review

## Story

As a PM setting up the tool,
I want the tool to read my `config.yaml` and give me specific, actionable error messages when something is wrong,
so that I can fix configuration problems quickly without guessing.

## Acceptance Criteria

1. Given a valid `config.yaml` with all required fields, When `load_config(path)` is called, Then a `Config` object is returned with all fields populated, And the call completes in under 2 seconds (NFR2).
2. Given a `config.yaml` with a missing required field (e.g., `api_token` absent), When `load_config(path)` is called, Then a `ConfigError` is raised naming the specific missing field (e.g., `"Missing required field: api_token"`), And the error message contains no credential values (NFR4).
3. Given `config.yaml` does not exist at the expected path, When `load_config(path)` is called, Then a `ConfigError` is raised indicating the file was not found and showing the path checked.
4. Given the exception hierarchy is defined in `config.py`, When I inspect the module, Then `JiraReportError`, `ConfigError`, `JiraFetchError`, `AIGenerationError`, and `OutputError` are all defined with correct inheritance from `JiraReportError`.
5. Given `config.yaml.example` exists at project root, When I inspect it, Then it contains all 8 Config fields: `jira_url`, `api_token`, `project_key`, `output_dir`, `ai_provider`, `ai_model`, `report_tone`, `project_name`.

## Tasks / Subtasks

- [x] Task 1: Define exception hierarchy in `config.py` (AC: 4)
  - [x] Define `JiraReportError(Exception)` as base
  - [x] Define `ConfigError(JiraReportError)`
  - [x] Define `JiraFetchError(JiraReportError)`
  - [x] Define `AIGenerationError(JiraReportError)`
  - [x] Define `OutputError(JiraReportError)`

- [x] Task 2: Implement `Config` Pydantic v2 model in `config.py` (AC: 1, 2, 5)
  - [x] Define `DEFAULT_MODEL = "claude-sonnet-4-6"` constant at module top
  - [x] Create `Config(BaseModel)` with all 8 fields (see Dev Notes for types)
  - [x] Set `ai_model` as optional with `default=DEFAULT_MODEL`
  - [x] All other 7 fields are required (no defaults)

- [x] Task 3: Implement `load_config(path: Path) -> Config` (AC: 1, 2, 3)
  - [x] Raise `ConfigError` if `path` does not exist (include path in message)
  - [x] Parse YAML with `yaml.safe_load` — raise `ConfigError` on invalid YAML
  - [x] Validate parsed dict with `Config(**raw)` — catch `ValidationError`
  - [x] On `ValidationError`: extract first error's field name (from `loc[0]`), raise `ConfigError(f"Missing required field: {field}")` for missing fields
  - [x] NEVER include field values (especially `api_token`) in any error message
  - [x] This is the ONLY public function — all helpers prefixed `_`

- [x] Task 4: Verify `config.yaml.example` at project root (AC: 5)
  - [x] Confirm it contains all 8 required fields (was created as placeholder in Story 1.1)
  - [x] If placeholder content is incomplete, update with canonical values from Dev Notes

- [x] Task 5: Update `tests/conftest.py` with `sample_config` fixture
  - [x] Import `Config` from `jira_report.config`
  - [x] Define `sample_config()` fixture returning a valid `Config` instance
  - [x] This fixture is used by ALL future test files — define it now, here

- [x] Task 6: Implement `tests/test_config.py` (AC: 1–4)
  - [x] `test_load_config_valid` — happy path returns Config object
  - [x] `test_load_config_missing_field` — ConfigError message names the field
  - [x] `test_load_config_file_not_found` — ConfigError includes path
  - [x] `test_exception_hierarchy` — assert inheritance chain
  - [x] `test_no_credentials_in_error` — api_token value absent from all error messages
  - [x] Run `uv run pytest tests/test_config.py` — all tests must pass

## Dev Notes

### `config.py` — Complete Implementation Contract

**Imports required:**
```python
from __future__ import annotations
from pathlib import Path
import yaml
from pydantic import BaseModel, ValidationError
```

**Constants (module top-level — never inline):**
```python
DEFAULT_MODEL = "claude-sonnet-4-6"  # fallback when ai_model absent from config.yaml
```

**Exception hierarchy (all 5 classes in config.py — future modules import from here):**
```python
class JiraReportError(Exception): ...
class ConfigError(JiraReportError): ...
class JiraFetchError(JiraReportError): ...
class AIGenerationError(JiraReportError): ...
class OutputError(JiraReportError): ...
```

Why all exceptions in `config.py`: Every module imports exceptions from `config.py`. This single source prevents duplicate definitions across modules. [Source: architecture.md#Error Handling]

**Config Pydantic v2 model — exact field types:**
```python
class Config(BaseModel):
    jira_url: str
    api_token: str        # CREDENTIAL — never log or format into strings
    project_key: str
    output_dir: str       # stored as str; renderer.py converts to Path
    ai_provider: str
    ai_model: str = DEFAULT_MODEL   # optional — fallback is DEFAULT_MODEL
    report_tone: str
    project_name: str
```

**`load_config` — full implementation pattern:**
```python
def load_config(path: Path) -> Config:
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        raise ConfigError(f"Invalid YAML in config file: {path}")
    if not isinstance(raw, dict):
        raise ConfigError(f"Config file must be a YAML mapping: {path}")
    try:
        return Config(**raw)
    except ValidationError as exc:
        first = exc.errors()[0]
        field = str(first.get("loc", ("unknown",))[0])
        error_type = first.get("type", "")
        if "missing" in error_type:
            raise ConfigError(f"Missing required field: {field}")
        raise ConfigError(f"Invalid value for field: {field}")
```

**Credential safety — CRITICAL (NFR4):**
- `api_token` and `api_key` values must NEVER appear in exception messages or log strings
- The pattern above extracts only the field NAME from `ValidationError`, never the input value
- Never do `raise ConfigError(f"... {config.api_token}")` or `str(exc)` for ValidationError (Pydantic v2 includes input values in its string output)
- Never `repr()` or `str()` a `Config` instance in error messages

**What NOT to do:**
```python
# FORBIDDEN — exposes token
raise ConfigError(f"Auth failed: {config.api_token}")

# FORBIDDEN — Pydantic v2 str(exc) may include input values
raise ConfigError(str(exc))

# CORRECT — field name only, no values
raise ConfigError(f"Missing required field: {field}")
```

### `config.yaml.example` — Canonical Content

Must exist at project root with these exact 8 fields (Story 1.1 created a placeholder — verify/update):
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

### `tests/conftest.py` — Shared Fixture (Add Now)

This fixture is the single source of a valid `Config` for ALL test files in this project. Define it in this story, not later:
```python
import pytest
from jira_report.config import Config

@pytest.fixture
def sample_config():
    return Config(
        jira_url="https://example.atlassian.net",
        api_token="test-token-not-real",
        project_key="TEST",
        output_dir="./reports",
        ai_provider="anthropic",
        ai_model="claude-sonnet-4-6",
        report_tone="professional",
        project_name="Test Project",
    )
```

Do NOT redefine `Config` or create a different fixture in individual test files — import from `conftest.py` via pytest's fixture injection.

### `tests/test_config.py` — Test Patterns

Use `tmp_path` (pytest built-in) to write temporary YAML files:
```python
import pytest
from pathlib import Path
from jira_report.config import (
    load_config, Config,
    JiraReportError, ConfigError, JiraFetchError, AIGenerationError, OutputError,
)

VALID_CONFIG = {
    "jira_url": "https://example.atlassian.net",
    "api_token": "test-token",
    "project_key": "TEST",
    "output_dir": "./reports",
    "ai_provider": "anthropic",
    "ai_model": "claude-sonnet-4-6",
    "report_tone": "professional",
    "project_name": "Test Project",
}

def _write_config(tmp_path: Path, data: dict) -> Path:
    import yaml
    p = tmp_path / "config.yaml"
    p.write_text(yaml.dump(data), encoding="utf-8")
    return p

def test_load_config_valid(tmp_path):
    p = _write_config(tmp_path, VALID_CONFIG)
    config = load_config(p)
    assert isinstance(config, Config)
    assert config.jira_url == "https://example.atlassian.net"

def test_load_config_missing_field(tmp_path):
    data = {k: v for k, v in VALID_CONFIG.items() if k != "api_token"}
    p = _write_config(tmp_path, data)
    with pytest.raises(ConfigError, match="api_token"):
        load_config(p)

def test_load_config_file_not_found(tmp_path):
    with pytest.raises(ConfigError, match=str(tmp_path / "missing.yaml")):
        load_config(tmp_path / "missing.yaml")

def test_exception_hierarchy():
    assert issubclass(ConfigError, JiraReportError)
    assert issubclass(JiraFetchError, JiraReportError)
    assert issubclass(AIGenerationError, JiraReportError)
    assert issubclass(OutputError, JiraReportError)

def test_no_credentials_in_error(tmp_path):
    data = {k: v for k, v in VALID_CONFIG.items() if k != "project_key"}
    p = _write_config(tmp_path, data)
    with pytest.raises(ConfigError) as exc_info:
        load_config(p)
    # Ensure the actual api_token value never leaks into error messages
    assert VALID_CONFIG["api_token"] not in str(exc_info.value)
```

### Architecture Compliance

- **Module interface:** `load_config` is the ONLY public function in `config.py`. All helpers use `_` prefix. [Source: architecture.md#Module Interface Pattern]
- **Exception hierarchy:** All 5 exception classes defined here. Every other module imports from `jira_report.config` — never redefines. [Source: architecture.md#Error Handling]
- **Naming:** `snake_case` functions/variables, `PascalCase` classes, `UPPER_SNAKE_CASE` constants. [Source: architecture.md#Naming Patterns]
- **No terminal output in modules:** `config.py` raises exceptions; `cli.py` catches and prints via `typer.echo(err=True)`. [Source: architecture.md#Terminal Output Pattern]
- **Constants:** `DEFAULT_MODEL` defined at top of `config.py`. `LOW_TICKET_WARNING_THRESHOLD` and `DEFAULT_TIMEOUT_SECONDS` belong in `jira_client.py` (Story 2 scope). [Source: architecture.md#Constants]
- **Pydantic v2 confirmed:** `pydantic>=2.0` is in `pyproject.toml` dependencies. [Source: story 1-1, architecture.md]

### Previous Story Learnings (from Story 1.1)

- **uv PATH on WSL2:** If `uv` is not found, run `export PATH="$HOME/.local/bin:$PATH"` before uv commands
- **hatchling is NOT a project dep:** It belongs only in `[build-system].requires` — never `uv add hatchling`
- **After code changes:** Run `uv tool upgrade jira-report` to update the global binary (not reinstall)
- **Import verification command:** `uv run python -c "from jira_report.config import load_config, Config; print('OK')"`

### Scope Boundaries

This story implements `config.py` and its tests only. Do NOT implement:
- Any content in `cli.py`, `jira_client.py`, `ai_engine.py`, or `renderer.py` — leave as stubs
- `_ensure_gitignore()` — that is Story 1.3 scope
- Any Jira authentication logic — that is Story 1.4 scope

### References

- Exception hierarchy and credential safety: [Source: architecture.md#Error Handling]
- Config model and load_config interface: [Source: architecture.md#Data Architecture]
- Module interface pattern: [Source: architecture.md#Module Interface Pattern]
- Naming conventions: [Source: architecture.md#Naming Patterns]
- Credential safety rule with anti-pattern examples: [Source: architecture.md#Credential Safety Rule]
- Constants definition: [Source: architecture.md#Constants]
- Story acceptance criteria: [Source: epics.md#Story 1.2]
- Config fields (8 required): [Source: epics.md#Additional Requirements]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- config.yaml.example was already complete from Story 1.1 — no update needed

### Completion Notes List

- Implemented full exception hierarchy (5 classes) and `Config` Pydantic v2 model with 8 fields in `config.py`
- `load_config()` handles: file-not-found, invalid YAML, non-mapping YAML, missing fields, invalid fields — all with safe, credential-free error messages
- `api_token` value never leaks into exception messages (field name only extracted from ValidationError)
- `ai_model` defaults to `DEFAULT_MODEL = "claude-sonnet-4-6"` — other 7 fields required
- `conftest.py` `sample_config` fixture defined for use by all future test files
- 9 tests pass: valid config, default ai_model, 2× missing field, file-not-found, invalid YAML, non-mapping, exception hierarchy, no-credential-leak
- Full regression suite: 9 passed, 0 failed

### File List

- `src/jira_report/config.py`
- `tests/conftest.py`
- `tests/test_config.py`
