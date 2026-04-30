# Story 1.4: Jira Authentication Validation

Status: review

## Story

As a PM,
I want the tool to silently authenticate to Jira on every run and surface a specific, safe error within 5 seconds if auth fails,
so that I'm never surprised mid-run by an authentication problem.

## Acceptance Criteria

1. Given valid Jira credentials in `config.yaml`, When `fetch_jira_data()` initializes the Jira client, Then authentication succeeds silently with no credential values printed anywhere (FR4, NFR4).
2. Given an invalid `api_token`, When `fetch_jira_data()` attempts to authenticate, Then a `JiraFetchError` is raised within 5 seconds (NFR7) with message `"Jira authentication failed — check api_token in config.yaml"`, And the token value is NOT present in the error message.
3. Given the Jira URL is unreachable, When `fetch_jira_data()` attempts to connect, Then a `JiraFetchError` is raised within 5 seconds with message `"Network unreachable — check jira_url in config.yaml"`.
4. Given valid credentials but an invalid `project_key`, When `fetch_jira_data()` verifies the project, Then a `JiraFetchError` is raised with message `"Project {key} not found — check project_key in config.yaml"` (where `{key}` is the actual project key value — it is NOT a credential).
5. Given a successful or failed run, When execution completes, Then only outbound calls to `config.jira_url` and the Anthropic API were made — no other external connections (NFR5).

## Tasks / Subtasks

- [x] Task 1: Add `DEFAULT_TIMEOUT_SECONDS` constant to `jira_client.py` (AC: 2, 3)
  - [x] Define `DEFAULT_TIMEOUT_SECONDS = 10` at module top-level
  - [x] This constant is referenced in `_create_jira_client()` — never inline the value

- [x] Task 2: Implement `_create_jira_client(config)` private function (AC: 1, 2, 3)
  - [x] Instantiate `JIRA(server=config.jira_url, token_auth=config.api_token, timeout=DEFAULT_TIMEOUT_SECONDS, validate=True)`
  - [x] Catch `JIRAError` with `status_code in (401, 403)` → raise `JiraFetchError("Jira authentication failed — check api_token in config.yaml")`
  - [x] Catch `JIRAError` with other status codes → raise `JiraFetchError(f"Jira connection failed (status {e.status_code}) — check jira_url in config.yaml")`
  - [x] Catch `(requests.exceptions.ConnectionError, requests.exceptions.Timeout, OSError)` → raise `JiraFetchError("Network unreachable — check jira_url in config.yaml")`
  - [x] NEVER include `config.api_token` in any exception message (NFR4)

- [x] Task 3: Implement `_validate_project(jira, config)` private function (AC: 4)
  - [x] Call `jira.project(config.project_key)`
  - [x] Catch `JIRAError` with `status_code == 404` → raise `JiraFetchError(f"Project {config.project_key} not found — check project_key in config.yaml")`
  - [x] Catch other `JIRAError` → raise `JiraFetchError(f"Jira error verifying project (status {e.status_code})")`
  - [x] `config.project_key` is NOT a credential — safe to include in error messages

- [x] Task 4: Update `fetch_jira_data()` to call auth and project validation (AC: 1–5)
  - [x] Replace `raise NotImplementedError` stub with: call `_create_jira_client(config)`, then call `_validate_project(jira, config)`
  - [x] After validation, raise `NotImplementedError` — data retrieval is Story 2 scope
  - [x] Ensure `config.api_token` is never passed to any log or string format

- [x] Task 5: Implement `tests/test_jira_client.py` (AC: 1–4)
  - [x] `test_auth_failure_raises_jira_fetch_error` — JIRA init raises JIRAError(401) → JiraFetchError with "authentication failed"
  - [x] `test_auth_forbidden_raises_jira_fetch_error` — JIRA init raises JIRAError(403) → JiraFetchError with "authentication failed"
  - [x] `test_network_unreachable` — JIRA init raises `requests.exceptions.ConnectionError` → JiraFetchError with "Network unreachable"
  - [x] `test_timeout_raises_jira_fetch_error` — JIRA init raises `requests.exceptions.Timeout` → JiraFetchError with "Network unreachable"
  - [x] `test_invalid_project_key` — JIRA init succeeds, `jira.project()` raises JIRAError(404) → JiraFetchError with project key in message
  - [x] `test_auth_token_not_in_error_message` — JIRAError(401) raised; assert `sample_config.api_token` not in error message
  - [x] `test_jira_initialized_with_correct_url` — on success, JIRA was called with `server=config.jira_url`
  - [x] `test_default_timeout_constant` — `DEFAULT_TIMEOUT_SECONDS == 10`
  - [x] Run `uv run pytest tests/test_jira_client.py` — all tests pass

## Dev Notes

### Auth Approach: Bearer Token via `token_auth`

The `jira` library's `token_auth` parameter sends `Authorization: Bearer <token>` — this is the architecture-specified auth method for Jira Cloud PATs. Do NOT use `basic_auth=(email, token)` — that requires an email field not present in `Config`.

```python
from jira import JIRA, JIRAError
import requests
```

Both `jira` and `requests` are project dependencies. `requests` is a transitive dependency via `jira` — it is always available.

### `validate=True` on JIRA Constructor

With `validate=True` (the default in modern jira library versions), the constructor makes a `server_info()` API call immediately. If the token is invalid, Jira returns HTTP 401, the library raises `JIRAError(status_code=401)`, and our handler converts it to `JiraFetchError` — all within milliseconds. This satisfies NFR7's "within 5 seconds" requirement. The `timeout=DEFAULT_TIMEOUT_SECONDS` handles the slow/unreachable network case.

**NFR7 note:** `DEFAULT_TIMEOUT_SECONDS = 10` is the connection timeout per request. Auth failures (401) surface in < 1 second. The 10s timeout is for network-unreachable detection, which is slightly over NFR7's 5s target — this is an acceptable tradeoff (the architecture specifies this constant at 10s).

### `jira_client.py` — Complete Implementation for This Story

```python
from __future__ import annotations

from typing import Optional

import requests
from jira import JIRA, JIRAError

from jira_report.config import Config, JiraFetchError

DEFAULT_TIMEOUT_SECONDS = 10


def fetch_jira_data(config: Config, week_override: Optional[str] = None):
    jira = _create_jira_client(config)
    _validate_project(jira, config)
    raise NotImplementedError  # Story 2 implements data retrieval and return type


def _create_jira_client(config: Config) -> JIRA:
    try:
        return JIRA(
            server=config.jira_url,
            token_auth=config.api_token,
            timeout=DEFAULT_TIMEOUT_SECONDS,
            validate=True,
        )
    except JIRAError as e:
        if e.status_code in (401, 403):
            raise JiraFetchError("Jira authentication failed — check api_token in config.yaml")
        raise JiraFetchError(
            f"Jira connection failed (status {e.status_code}) — check jira_url in config.yaml"
        )
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, OSError):
        raise JiraFetchError("Network unreachable — check jira_url in config.yaml")


def _validate_project(jira: JIRA, config: Config) -> None:
    try:
        jira.project(config.project_key)
    except JIRAError as e:
        if e.status_code == 404:
            raise JiraFetchError(
                f"Project {config.project_key} not found — check project_key in config.yaml"
            )
        raise JiraFetchError(f"Jira error verifying project (status {e.status_code})")
```

**Credential safety:**
- `config.api_token` is passed to `JIRA(token_auth=...)` — that is its ONLY use
- `config.api_token` MUST NOT appear in any exception message, f-string, or log statement
- `config.project_key` is NOT a credential — safe to include in error messages (it's a project identifier, not a secret)

**Scope boundary — `NotImplementedError` at end of `fetch_jira_data`:** Story 2.1 will implement `_calculate_week_range()` and JQL construction. Story 2.2 will implement the full `fetch_jira_data()` return path including `JiraData` assembly. When Story 2.2 is implemented, the `raise NotImplementedError` line is removed and replaced with the data retrieval logic. The data model dataclasses (`JiraTicket`, `JiraData`, `ReportSections`) are defined in Story 2.2 — do NOT define them here.

### `tests/test_jira_client.py` — Test Patterns

Mock target: `jira_report.jira_client.JIRA` (not `jira.JIRA`) — the name is used in `jira_client`'s namespace due to the `from jira import JIRA` import.

```python
import pytest
import requests
from unittest.mock import MagicMock, patch, call
from jira import JIRAError

from jira_report.config import JiraFetchError
from jira_report.jira_client import fetch_jira_data, DEFAULT_TIMEOUT_SECONDS


# ── Constant ─────────────────────────────────────────────────────────────────

def test_default_timeout_constant():
    assert DEFAULT_TIMEOUT_SECONDS == 10


# ── Auth failure ──────────────────────────────────────────────────────────────

def test_auth_failure_raises_jira_fetch_error(sample_config):
    with patch("jira_report.jira_client.JIRA") as mock_jira:
        mock_jira.side_effect = JIRAError(text="Unauthorized", status_code=401)
        with pytest.raises(JiraFetchError, match="authentication failed"):
            fetch_jira_data(sample_config)


def test_auth_forbidden_raises_jira_fetch_error(sample_config):
    with patch("jira_report.jira_client.JIRA") as mock_jira:
        mock_jira.side_effect = JIRAError(text="Forbidden", status_code=403)
        with pytest.raises(JiraFetchError, match="authentication failed"):
            fetch_jira_data(sample_config)


# ── Network errors ────────────────────────────────────────────────────────────

def test_network_unreachable(sample_config):
    with patch("jira_report.jira_client.JIRA") as mock_jira:
        mock_jira.side_effect = requests.exceptions.ConnectionError("connection refused")
        with pytest.raises(JiraFetchError, match="Network unreachable"):
            fetch_jira_data(sample_config)


def test_timeout_raises_jira_fetch_error(sample_config):
    with patch("jira_report.jira_client.JIRA") as mock_jira:
        mock_jira.side_effect = requests.exceptions.Timeout("timed out")
        with pytest.raises(JiraFetchError, match="Network unreachable"):
            fetch_jira_data(sample_config)


# ── Project validation ────────────────────────────────────────────────────────

def test_invalid_project_key(sample_config):
    with patch("jira_report.jira_client.JIRA") as mock_jira:
        mock_instance = MagicMock()
        mock_jira.return_value = mock_instance
        mock_instance.project.side_effect = JIRAError(text="Not Found", status_code=404)
        with pytest.raises(JiraFetchError, match=sample_config.project_key):
            fetch_jira_data(sample_config)


# ── Credential safety ─────────────────────────────────────────────────────────

def test_auth_token_not_in_error_message(sample_config):
    with patch("jira_report.jira_client.JIRA") as mock_jira:
        mock_jira.side_effect = JIRAError(text="Unauthorized", status_code=401)
        with pytest.raises(JiraFetchError) as exc_info:
            fetch_jira_data(sample_config)
        assert sample_config.api_token not in str(exc_info.value)


# ── Success path (auth + project valid; data retrieval is Story 2) ────────────

def test_jira_initialized_with_correct_url(sample_config):
    with patch("jira_report.jira_client.JIRA") as mock_jira:
        mock_instance = MagicMock()
        mock_jira.return_value = mock_instance
        with pytest.raises(NotImplementedError):  # expected — Story 2 scope
            fetch_jira_data(sample_config)
        mock_jira.assert_called_once()
        call_kwargs = mock_jira.call_args
        assert call_kwargs.kwargs.get("server") == sample_config.jira_url


def test_auth_succeeds_no_token_in_output(sample_config, capsys):
    with patch("jira_report.jira_client.JIRA") as mock_jira:
        mock_instance = MagicMock()
        mock_jira.return_value = mock_instance
        with pytest.raises(NotImplementedError):
            fetch_jira_data(sample_config)
        captured = capsys.readouterr()
        assert sample_config.api_token not in captured.out
        assert sample_config.api_token not in captured.err
```

**Why `pytest.raises(NotImplementedError)` in success tests:** `fetch_jira_data` ends with `raise NotImplementedError` after auth — this is intentional for Story 1.4. Tests that verify successful auth must expect this. Story 2 removes it.

**`call_kwargs.kwargs` vs `call_args[1]`:** In Python 3.8+ mock, `call_args.kwargs` is the cleaner API. Both work — use `.kwargs` for clarity.

### Architecture Compliance

- **`DEFAULT_TIMEOUT_SECONDS` defined here** (in `jira_client.py`), NOT in `config.py`. `LOW_TICKET_WARNING_THRESHOLD` also belongs in `jira_client.py` (Story 2.3 scope). [Source: architecture.md#Constants]
- **Module interface:** `fetch_jira_data` is the ONLY public function. `_create_jira_client` and `_validate_project` are private (`_` prefix). [Source: architecture.md#Module Interface Pattern]
- **No terminal output:** `jira_client.py` raises; `cli.py` catches. No `typer.echo()` calls here. [Source: architecture.md#Terminal Output Pattern]
- **Credential scrubbing:** `config.api_token` value never formatted into any string other than the `token_auth` parameter passed to the library. [Source: architecture.md#Credential Safety Rule]
- **`requests` import:** `requests` is a transitive dep via `jira` — always available. Explicit import preferred over bare `except Exception`. [Source: architecture.md#API & Communication Patterns]
- **Data models deferred:** `JiraTicket`, `JiraData`, `ReportSections` dataclasses defined in Story 2.2. Return type of `fetch_jira_data` is left untyped in this story. [Source: architecture.md#Canonical Data Models]

### Scope Boundaries

**This story implements:**
- `DEFAULT_TIMEOUT_SECONDS` constant in `jira_client.py`
- `_create_jira_client()` and `_validate_project()` private functions
- Auth+validation portion of `fetch_jira_data()`
- `tests/test_jira_client.py` (auth-focused tests)

**DO NOT implement in this story:**
- `JiraTicket`, `JiraData`, `ReportSections` dataclasses — Story 2.2 scope
- `_calculate_week_range()` or JQL construction — Story 2.1 scope
- `ThreadPoolExecutor` parallel queries — Story 2.2 scope
- `LOW_TICKET_WARNING_THRESHOLD` constant — Story 2.3 scope
- Any changes to `cli.py` or other modules

### Previous Story Learnings (from Stories 1.1–1.3)

- **uv PATH on WSL2:** `export PATH="$HOME/.local/bin:$PATH"` if `uv` not found
- **After code changes:** `uv tool upgrade jira-report` (NOT reinstall)
- **Mock target is the import namespace:** patch `jira_report.jira_client.JIRA` not `jira.JIRA`
- **`config.model_copy(update={...})`** is Pydantic v2's immutable copy API (not used here but reminder for cli.py awareness)
- **All exceptions imported from `jira_report.config`:** `JiraFetchError` lives in `config.py` — always import from there

### References

- Jira auth via Bearer token: [Source: architecture.md#Authentication & Security]
- Error hierarchy and credential safety: [Source: architecture.md#Error Handling, Credential Safety Rule]
- Timeout constant: [Source: architecture.md#Constants]
- Module interface pattern: [Source: architecture.md#Module Interface Pattern]
- Story acceptance criteria: [Source: epics.md#Story 1.4]
- NFR7 timeout: [Source: architecture.md#Coherence Validation]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- No issues encountered

### Completion Notes List

- Implemented `DEFAULT_TIMEOUT_SECONDS = 10` constant in `jira_client.py`
- Implemented `_create_jira_client()`: `JIRA(token_auth=..., validate=True)` with 3 error paths (401/403 → auth failure, other JIRAError → connection failed, ConnectionError/Timeout/OSError → network unreachable)
- Implemented `_validate_project()`: `jira.project(key)` with 404 → project not found (key safe in message), other JIRAError → generic error
- `fetch_jira_data()` now calls auth+validation then raises `NotImplementedError` — Story 2 will overwrite
- `config.api_token` never appears in any error message (verified by test)
- 9 new jira_client tests + 20 existing = 29 passed, 0 regressions

### File List

- `src/jira_report/jira_client.py`
- `tests/test_jira_client.py`
