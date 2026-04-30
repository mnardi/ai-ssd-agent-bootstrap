---
stepsCompleted: ['step-01-validate-prerequisites', 'step-02-design-epics', 'step-03-create-stories', 'step-04-final-validation']
status: 'complete'
completedAt: '2026-04-29'
inputDocuments: ['_bmad-output/planning-artifacts/prd.md', '_bmad-output/planning-artifacts/architecture.md']
workflowType: 'epics-and-stories'
project_name: 'Jira Weekly Report CLI'
user_name: 'Nardi'
date: '2026-04-29'
---

# Jira Weekly Report CLI - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for the Jira Weekly Report CLI, decomposing the requirements from the PRD and Architecture into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1: PM configures the tool via `config.yaml` specifying Jira connection, AI provider, project name, and output preferences
FR2: PM validates configuration and Jira authentication via CLI before generating a report
FR3: The system reports specific, actionable errors when configuration is missing or invalid
FR4: The system authenticates to Jira silently on every run without prompting for credentials
FR5: The system calculates the report date range (last Monday–Sunday) automatically at runtime
FR6: PM overrides the report date range via `--week` flag
FR7: PM overrides the target Jira project via `--project` flag
FR8: The system retrieves completed tickets (Done) for the date range including ticket subject and assignee
FR9: The system retrieves in-progress tickets at time of run including ticket subject and assignee
FR10: The system retrieves planned tickets (Next/To Do) at time of run including ticket subject and assignee
FR11: The system warns when a data section returns unusually low ticket counts (< 3) before generating the report
FR12: The system generates a report with four sections: Done, In Progress, Next Plan, Executive Summary
FR13: The system passes raw Jira ticket data as full context to the AI with no pre-summarization
FR14: The system generates report text in executive communication language, not Jira operational language
FR15: The system uses configurable tone and project name to align AI output with PM's voice and context
FR16: PM previews report output without saving to file via `--dry-run` flag
FR17: The system saves the generated report as an HTML file formatted for copy-paste into an email client
FR18: The system auto-generates the output filename with a date stamp
FR19: PM overrides the output directory via `--output` flag
FR20: The system displays a terminal summary after each run: ticket counts per section + output file path
FR21: The system routes all errors and warnings to stderr, separate from report content
FR22: PM runs the tool with zero arguments using defaults from `config.yaml`
FR23: PM accesses usage instructions and flag descriptions via `--help`
FR24: PM overrides key parameters at runtime without editing `config.yaml`

### NonFunctional Requirements

NFR1: End-to-end execution (auth → data retrieval → AI generation → file output) completes in under 60 seconds on a standard internet connection
NFR2: CLI startup and config validation completes in under 2 seconds before any external API calls
NFR3: Terminal feedback is progressive — PM sees status updates during execution, not silence followed by output
NFR4: Jira API token is stored only in `config.yaml` on the local filesystem; never logged, printed to terminal, or included in output files
NFR5: The tool makes no outbound network calls except to the configured Jira instance and AI provider
NFR6: `config.yaml` is excluded from version control by default (`.gitignore` entry generated on first run)
NFR7: Jira API connection failures surface within 5 seconds with a specific error message (auth failure vs. network unreachable vs. project not found)
NFR8: AI provider API failures do not silently produce empty or partial output — the tool exits with a clear error and no file is written
NFR9: Compatible with Jira Cloud REST API v3 (Atlassian hosted instances)
NFR10: A failed run never overwrites or corrupts a previously generated report file
NFR11: `--dry-run` always exits without writing any files, regardless of execution outcome
NFR12: The tool produces identical output structure for the same input data (deterministic section headings, consistent HTML formatting)

### Additional Requirements

- **Project scaffold (Epic 1, Story 1):** `uv init jira-report --python 3.12` then install dependencies: `typer>=0.14.0`, `anthropic>=0.97.0`, `jira`, `pyyaml>=6.0.3`, `jinja2>=3.1.6`, `pydantic>=2.0`; dev deps: `pytest`, `pytest-asyncio`; `pyproject.toml` entry point: `jira-report = "jira_report.cli:app"`; global install: `uv tool install .`
- **Canonical data models:** `JiraTicket(key, summary, assignee, status)`, `JiraData(done, in_progress, planned, week_start, week_end)`, `ReportSections(done_text, in_progress_text, next_plan_text, executive_summary)` — defined as Python dataclasses; never redefined across modules
- **Config validation:** Pydantic v2 `Config` model — validates all `config.yaml` fields; missing fields produce `ConfigError` with specific field names
- **Exception hierarchy:** `JiraReportError` (base) → `ConfigError`, `JiraFetchError`, `AIGenerationError`, `OutputError` — modules raise; `cli.py` catches and prints to stderr
- **Concurrency:** `concurrent.futures.ThreadPoolExecutor` for 3 parallel JQL queries — not asyncio (jira library is sync-only)
- **Atomic file write:** All HTML output uses temp file → `shutil.move()` — never write directly to final path
- **Credential scrubbing:** API tokens must never be interpolated into exception messages or log strings
- **Module interface pattern:** Each module exposes exactly one public entry function (`load_config`, `fetch_jira_data`, `generate_report`, `render_and_write`); all other functions are private (prefixed `_`)
- **Named constants:** `LOW_TICKET_WARNING_THRESHOLD = 3`, `DEFAULT_TIMEOUT_SECONDS = 10`, `DEFAULT_MODEL = "claude-sonnet-4-6"`
- **Terminal output:** All output via `typer.echo()` only — never `print()`; ordered status messages: `"Authenticating..."` → `"Fetching Jira data..."` → `"Generating report..."` → `"Writing output..."` → `"Done. Report saved: {path}"`
- **Implementation sequence:** config.py → jira_client.py → ai_engine.py → templates/report.html.j2 → renderer.py → cli.py

### UX Design Requirements

Not applicable — V1 is a CLI tool with no visual interface. UX is fully expressed through command structure, flags, error messages, and terminal output (captured in FR22–FR24 and NFRs).

### FR Coverage Map

FR1: Epic 1 — config.yaml schema + Pydantic Config model
FR2: Epic 1 — Auth validation before report generation
FR3: Epic 1 — Actionable ConfigError messages with field names
FR4: Epic 1 — Silent Bearer token auth on every run
FR5: Epic 2 — Auto date range calculation (last Mon–Sun)
FR6: Epic 2 — `--week` flag override
FR7: Epic 2 — `--project` flag override
FR8: Epic 2 — Fetch Done tickets (date range)
FR9: Epic 2 — Fetch In Progress tickets
FR10: Epic 2 — Fetch Planned tickets
FR11: Epic 2 — Low ticket count warning (< 3)
FR12: Epic 3 — 4-section report structure
FR13: Epic 3 — Raw Jira data passed to AI unmodified
FR14: Epic 3 — Executive language generation
FR15: Epic 3 — Tone + project name in AI prompt
FR16: Epic 3 — `--dry-run` flag
FR17: Epic 4 — HTML file output (inline CSS, email-safe)
FR18: Epic 4 — Auto date-stamped filename
FR19: Epic 4 — `--output` flag override
FR20: Epic 4 — Terminal summary (counts + file path)
FR21: Epic 1 — stderr routing for all errors and warnings
FR22: Epic 1 — Zero-arg run from config.yaml defaults
FR23: Epic 1 — `--help` auto-generated
FR24: Epic 1 — Runtime flag overrides without editing config

## Epic List

### Epic 1: Tool Setup & Configuration
PM can install, configure, and validate the tool — ready to use on the first run, with clear errors on misconfiguration and credentials protected from the start.
**FRs covered:** FR1, FR2, FR3, FR4, FR21, FR22, FR23, FR24
**NFRs covered:** NFR2, NFR4, NFR5, NFR6
**Architecture:** Project scaffold (`uv init`), Pydantic Config model, exception hierarchy, module structure, `.gitignore` auto-generation

### Epic 2: Jira Data Retrieval
PM can fetch complete, accurate Jira ticket data for any week — Done, In Progress, and Planned — with warnings when data looks thin and full visibility into what was retrieved.
**FRs covered:** FR5, FR6, FR7, FR8, FR9, FR10, FR11
**NFRs covered:** NFR1, NFR7, NFR9
**Architecture:** ThreadPoolExecutor parallel JQL, JQL builder, `JiraTicket`/`JiraData` dataclasses

### Epic 3: AI Report Generation
PM can generate a polished, executive-ready report draft from Jira data in a single command — with the right tone, voice, and four structured sections.
**FRs covered:** FR12, FR13, FR14, FR15, FR16
**NFRs covered:** NFR3, NFR8
**Architecture:** `ai_engine.py`, `ReportSections` dataclass, system prompt engineering, Claude API call

### Epic 4: Report Output & Delivery
PM can save, review, and trust the final HTML report — auto-named, in the right directory, never corrupted, with a clear terminal summary after every run.
**FRs covered:** FR17, FR18, FR19, FR20
**NFRs covered:** NFR10, NFR11, NFR12
**Architecture:** `renderer.py`, `templates/report.html.j2`, atomic file write, Jinja2

---

## Epic 1: Tool Setup & Configuration

PM can install, configure, and validate the tool — ready to use on the first run, with clear errors on misconfiguration and credentials protected from the start.

### Story 1.1: Project Scaffold & Module Structure

As a developer setting up the tool for the first time,
I want a properly scaffolded Python project with all dependencies installed and the correct module structure in place,
So that all subsequent stories can be implemented without environment or structure issues.

**Acceptance Criteria:**

**Given** a WSL2 environment with uv installed,
**When** I run the scaffold commands (`uv init jira-report --python 3.12`, install all deps, `uv add --dev pytest pytest-asyncio`),
**Then** `pyproject.toml` is created with all dependencies and `requires-python = ">=3.12"`,
**And** `uv.lock` is generated.

**Given** the scaffold is created,
**When** I inspect `src/jira_report/`,
**Then** it contains: `__init__.py`, `cli.py`, `config.py`, `jira_client.py`, `ai_engine.py`, `renderer.py`, and `templates/report.html.j2` (empty placeholder).

**Given** the scaffold is created,
**When** I inspect `pyproject.toml`,
**Then** it contains `[project.scripts]` with `jira-report = "jira_report.cli:app"`,
**And** `[tool.hatch.build.targets.wheel]` with `packages = ["src/jira_report"]`,
**And** `[tool.pytest.ini_options]` with `testpaths = ["tests"]` and `asyncio_mode = "auto"`.

**Given** the scaffold is created,
**When** I inspect `tests/`,
**Then** it contains stub files: `conftest.py`, `test_config.py`, `test_jira_client.py`, `test_ai_engine.py`, `test_renderer.py`, `test_cli.py`.

**Given** the scaffold is created,
**When** I run `uv tool install .`,
**Then** the `jira-report` command is available globally in the WSL terminal.

---

### Story 1.2: Config File Loading & Validation

As a PM setting up the tool,
I want the tool to read my `config.yaml` and give me specific, actionable error messages when something is wrong,
So that I can fix configuration problems quickly without guessing.

**Acceptance Criteria:**

**Given** a valid `config.yaml` with all required fields,
**When** `load_config(path)` is called,
**Then** a `Config` object is returned with all fields populated,
**And** the call completes in under 2 seconds (NFR2).

**Given** a `config.yaml` with a missing required field (e.g., `api_token` absent),
**When** `load_config(path)` is called,
**Then** a `ConfigError` is raised naming the specific missing field (e.g., `"Missing required field: api_token"`),
**And** the error message contains no credential values (NFR4).

**Given** `config.yaml` does not exist at the expected path,
**When** `load_config(path)` is called,
**Then** a `ConfigError` is raised indicating the file was not found and showing the path checked.

**Given** the exception hierarchy is defined in `config.py`,
**When** I inspect the module,
**Then** `JiraReportError`, `ConfigError`, `JiraFetchError`, `AIGenerationError`, and `OutputError` are all defined with correct inheritance from `JiraReportError`.

**Given** `config.yaml.example` exists at project root,
**When** I inspect it,
**Then** it contains all 8 Config fields: `jira_url`, `api_token`, `project_key`, `output_dir`, `ai_provider`, `ai_model`, `report_tone`, `project_name`.

---

### Story 1.3: CLI Entry Point, Runtime Flags & .gitignore

As a PM,
I want to run `jira-report` with zero arguments or optional flags, and see clear help documentation,
So that I can control the tool at runtime without editing `config.yaml`.

**Acceptance Criteria:**

**Given** the Typer app is wired in `cli.py`,
**When** I run `jira-report --help`,
**Then** all four flags are listed with descriptions: `--week`, `--project`, `--output`, `--dry-run` (FR23).

**Given** no flags are provided,
**When** `jira-report` is invoked,
**Then** all values default to `config.yaml` settings: `output_dir`, `project_key`, auto-calculated week range (FR22).

**Given** `--week 2026-04-21` is provided,
**When** `jira-report` is invoked,
**Then** that date is used as week start override instead of the auto-calculated range (FR6).

**Given** `--project ALPHA` or `--output ./reports/` are provided,
**When** `jira-report` is invoked,
**Then** each flag overrides the corresponding `config.yaml` value for that run (FR7, FR19, FR24).

**Given** `jira-report` runs in a directory with a `.git/` ancestor,
**When** `_ensure_gitignore()` executes,
**Then** `config.yaml` is appended to `.gitignore` if not already present (NFR6),
**And** if `.gitignore` does not exist, it is created with the `config.yaml` entry.

**Given** a `JiraReportError` is raised anywhere in the pipeline,
**When** it reaches `cli.py`,
**Then** the error is printed to stderr via `typer.echo(err=True)` (FR21),
**And** the process exits with code 1,
**And** no credential values appear in the output (NFR4).

---

### Story 1.4: Jira Authentication Validation

As a PM,
I want the tool to silently authenticate to Jira on every run and surface a specific, safe error within 5 seconds if auth fails,
So that I'm never surprised mid-run by an authentication problem.

**Acceptance Criteria:**

**Given** valid Jira credentials in `config.yaml`,
**When** `fetch_jira_data()` initializes the Jira client,
**Then** authentication succeeds silently with no credential values printed anywhere (FR4, NFR4).

**Given** an invalid `api_token`,
**When** `fetch_jira_data()` attempts to authenticate,
**Then** a `JiraFetchError` is raised within 5 seconds (NFR7) with message `"Jira authentication failed — check api_token in config.yaml"`,
**And** the token value is NOT present in the error message.

**Given** the Jira URL is unreachable,
**When** `fetch_jira_data()` attempts to connect,
**Then** a `JiraFetchError` is raised within 5 seconds with message `"Network unreachable — check jira_url in config.yaml"`.

**Given** valid credentials but an invalid `project_key`,
**When** `fetch_jira_data()` verifies the project,
**Then** a `JiraFetchError` is raised with message `"Project KEY not found — check project_key in config.yaml"`.

**Given** a successful or failed run,
**When** execution completes,
**Then** only outbound calls to `config.jira_url` and the Anthropic API were made — no other external connections (NFR5).

---

## Epic 2: Jira Data Retrieval

PM can fetch complete, accurate Jira ticket data for any week — Done, In Progress, and Planned — with warnings when data looks thin and full visibility into what was retrieved.

### Story 2.1: Automatic Date Range Calculation & JQL Construction

As a PM,
I want the tool to automatically determine the correct reporting week and build accurate Jira queries from it,
So that I always get data for the right week without calculating dates manually.

**Acceptance Criteria:**

**Given** no `--week` flag is provided,
**When** `_calculate_week_range()` runs on any day of the week,
**Then** `week_start` is set to the most recent Monday and `week_end` to the most recent Sunday (FR5).

**Given** `--week 2026-04-21` is provided,
**When** `_calculate_week_range()` processes the override,
**Then** `week_start = 2026-04-21` and `week_end = 2026-04-27` (FR6).

**Given** a `week_start`, `week_end`, and `project_key`,
**When** JQL strings are constructed for each category,
**Then** the Done JQL includes `status = Done AND updated >= "{week_start}" AND updated <= "{week_end}"` (FR8),
**And** the In Progress JQL includes `status in ("In Progress")` with no date filter (FR9),
**And** the Planned JQL includes `status in ("To Do", "Backlog", "Next")` with no date filter (FR10).

**Given** `--project ALPHA` is provided,
**When** JQL strings are constructed,
**Then** all three queries use `project = ALPHA` instead of `config.project_key` (FR7).

---

### Story 2.2: Parallel Ticket Retrieval & JiraData Assembly

As a PM,
I want the tool to fetch Done, In Progress, and Planned tickets simultaneously,
So that the full data retrieval completes well within 60 seconds.

**Acceptance Criteria:**

**Given** three JQL queries are ready,
**When** `fetch_jira_data()` executes,
**Then** all three queries run concurrently via `concurrent.futures.ThreadPoolExecutor` — not sequentially (NFR1).

**Given** a query returns tickets from Jira,
**When** results are assembled,
**Then** each ticket is represented as `JiraTicket(key, summary, assignee, status)` with no other fields,
**And** the full result is `JiraData(done=[...], in_progress=[...], planned=[...], week_start=..., week_end=...)`.

**Given** all three queries complete successfully,
**When** the fetch returns,
**Then** total elapsed time is under 60 seconds on a standard internet connection (NFR1),
**And** the `jira` library communicates with Jira Cloud REST API v3 (NFR9).

**Given** a query exceeds `DEFAULT_TIMEOUT_SECONDS` (10s),
**When** the connection times out,
**Then** a `JiraFetchError` is raised within 5 seconds surfacing to the user (NFR7) with a message identifying which query timed out.

---

### Story 2.3: Low-Ticket-Count Data Quality Warning

As a PM,
I want the tool to warn me when any ticket section returns suspiciously few results before generating the report,
So that I can confirm data accuracy before a thin report gets sent.

**Acceptance Criteria:**

**Given** any section (done, in_progress, or planned) has fewer than `LOW_TICKET_WARNING_THRESHOLD` (3) tickets,
**When** `fetch_jira_data()` returns,
**Then** `cli.py` emits a warning to stderr naming the section and actual count (FR11),
**And** the warning reads e.g.: `"Warning: Only 2 completed tickets found for Done — verify data accuracy before proceeding"`.

**Given** a warning is emitted,
**When** execution continues,
**Then** report generation proceeds normally — the warning does not stop the pipeline.

**Given** all three sections have 3 or more tickets,
**When** `fetch_jira_data()` returns,
**Then** no warning is emitted.

---

## Epic 3: AI Report Generation

PM can generate a polished, executive-ready report draft from Jira data in a single command — with the right tone, voice, and four structured sections.

### Story 3.1: AI Prompt Construction

As a PM,
I want the tool to package my Jira ticket data into a precisely crafted prompt that sets Claude up to write in executive communication style,
So that the generated report matches my voice and leadership audience expectations.

**Acceptance Criteria:**

**Given** `config.report_tone` and `config.project_name` are set,
**When** the system prompt is assembled,
**Then** it includes the PM role framing, the configured tone, and the project name (FR15).

**Given** a `JiraData` object with done, in_progress, and planned tickets,
**When** the user message is assembled,
**Then** all raw ticket data — `key`, `summary`, `assignee`, `status` for every ticket in all three sections — is included verbatim with no summarization or filtering (FR13).

**Given** the prompt is assembled,
**When** I inspect the instruction section,
**Then** it explicitly requests exactly four output sections: Done, In Progress, Next Plan, Executive Summary,
**And** instructs Claude to write in executive communication language, not Jira operational language (FR12, FR14).

**Given** `config.ai_model` is set,
**When** the API call is prepared,
**Then** that model is used; if `ai_model` is absent, `DEFAULT_MODEL = "claude-sonnet-4-6"` is used as the fallback.

---

### Story 3.2: Claude API Call & ReportSections Assembly

As a PM,
I want the tool to call Claude with my prompt and return a complete, validated report — or fail loudly if anything goes wrong,
So that I always get a usable draft or a clear error, never silent empty output.

**Acceptance Criteria:**

**Given** a fully assembled prompt and `JiraData`,
**When** `generate_report(config, jira_data)` is called,
**Then** a single synchronous call is made to the Anthropic API using the `anthropic` SDK,
**And** `cli.py` prints `"Generating report..."` to stdout before the call begins (NFR3).

**Given** the API call returns a response,
**When** the response is parsed,
**Then** it is mapped into `ReportSections(done_text, in_progress_text, next_plan_text, executive_summary)` (FR12).

**Given** the parsed response has any empty field,
**When** validation runs before returning,
**Then** an `AIGenerationError` is raised identifying which field is empty,
**And** no `ReportSections` object is returned (NFR8).

**Given** the API call fails (connection error, auth failure, rate limit),
**When** the exception is caught,
**Then** an `AIGenerationError` is raised with a specific message describing the failure,
**And** no partial output is returned — the pipeline exits cleanly (NFR8).

**Given** a successful `generate_report()` call,
**When** the returned `ReportSections` text is reviewed,
**Then** each section reads in executive communication language — not raw ticket summaries (FR14).

---

## Epic 4: Report Output & Delivery

PM can save, review, and trust the final HTML report — auto-named, in the right directory, never corrupted, with a clear terminal summary after every run.

### Story 4.1: HTML Report Template & Jinja2 Rendering

As a PM,
I want the generated report rendered as a clean, email-safe HTML file I can paste directly into my email client,
So that the report is ready to send without any formatting work on my part.

**Acceptance Criteria:**

**Given** a `ReportSections` object,
**When** `render_and_write()` renders `report.html.j2` via Jinja2,
**Then** the output is a complete HTML document with inline CSS — no external stylesheets, no JavaScript (FR17).

**Given** `report.html.j2` is inspected,
**When** I review the template structure,
**Then** it contains fixed section headings: Done, In Progress, Next Plan, Executive Summary,
**And** each section has a `{{ }}` slot where the corresponding `ReportSections` field is injected (NFR12).

**Given** the same `ReportSections` input is rendered twice,
**When** the HTML output of both renders is compared,
**Then** the structure — headings, layout, CSS — is identical; only the AI-generated text content varies (NFR12).

**Given** the HTML is opened in an email client,
**When** the content is reviewed,
**Then** formatting renders correctly without broken styles from external dependencies.

---

### Story 4.2: Atomic File Write, Filename Generation & Dry-Run

As a PM,
I want the report saved with an auto-generated date-stamped filename using a safe write process, with a dry-run option to preview without saving,
So that existing reports are never corrupted and I can preview before committing to disk.

**Acceptance Criteria:**

**Given** a successful render and `week_end` date,
**When** `_generate_filename(week_end)` runs,
**Then** the output filename is `report-YYYY-MM-DD.html` using the week end date (FR18).

**Given** the output file is being written,
**When** `render_and_write()` executes the write,
**Then** content is first written to a temp file in the output directory,
**And** `shutil.move()` renames the temp file to the final path only after the write succeeds (NFR10),
**And** if the write fails mid-way, the previously existing report file at that path is not corrupted.

**Given** `--output ./reports/` is provided,
**When** `render_and_write()` determines the output path,
**Then** the report is saved in `./reports/` instead of `config.output_dir` (FR19).

**Given** `--dry-run` is set,
**When** `render_and_write(config, sections, dry_run=True)` is called,
**Then** the rendered HTML is printed to stdout,
**And** no file is written to disk under any circumstances (FR16, NFR11),
**And** `render_and_write()` returns `None`.

**Given** `--dry-run` is set and the output directory does not exist,
**When** `render_and_write()` runs,
**Then** no error is raised — dry-run completes successfully regardless of output path validity (NFR11).

---

### Story 4.3: Terminal Run Summary

As a PM,
I want to see a clear summary in my terminal after each run showing what was retrieved and where the report was saved,
So that I can confirm the run succeeded and locate the output file immediately.

**Acceptance Criteria:**

**Given** a successful pipeline run,
**When** `render_and_write()` completes,
**Then** `cli.py` prints a summary to stdout showing ticket counts per section and the full output file path (FR20),
**And** the summary reads e.g.: `"Done: 7 tickets | In Progress: 4 tickets | Planned: 5 tickets\nReport saved: ./reports/report-2026-04-27.html"`.

**Given** a `--dry-run` run,
**When** execution completes,
**Then** the terminal summary shows ticket counts but states `"Dry run — no file written"` instead of a file path (FR20).

**Given** a failed run (any `JiraReportError` subclass),
**When** the error reaches `cli.py`,
**Then** the error message is the only output — no partial summary is printed (FR21).

**Given** the full pipeline runs successfully,
**When** all status messages are reviewed in order,
**Then** they appear as: `"Authenticating..."` → `"Fetching Jira data..."` → `"Generating report..."` → `"Writing output..."` → `"Done. Report saved: {path}"` (NFR3).
