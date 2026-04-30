---
stepsCompleted: ['step-01-init', 'step-02-discovery', 'step-02b-vision', 'step-02c-executive-summary', 'step-03-success', 'step-04-journeys', 'step-05-domain', 'step-06-innovation', 'step-07-project-type', 'step-08-scoping', 'step-09-functional', 'step-10-nonfunctional', 'step-11-polish', 'step-12-complete']
classification:
  projectType: cli_tool
  domain: general
  complexity: medium
  projectContext: greenfield
  futurePhase: web_app
inputDocuments: ['_bmad-output/brainstorming/brainstorming-session-2026-04-17-001.md']
workflowType: 'prd'
---

# Product Requirements Document — Jira Weekly Report CLI

**Author:** Nardi
**Date:** 2026-04-29

## Executive Summary

A personal CLI tool that auto-generates weekly executive status reports from Jira data, eliminating 2 hours of manual writing per week. The PM runs one command, reviews a polished AI-generated draft, adds 10 minutes of human context (absences, client nuance, tone), and ships. No manual Jira queries, no blank-page writing, no translation work.

**Target user:** A single PM who owns weekly status reporting to leadership and spends 2 hours writing reports whose source data already lives entirely in Jira.

**Problem:** Jira contains every fact needed for a status report. The gap is translation — operational ticket data → executive communication language. That translation costs 2 hours of cognitive effort every week.

**V1:** CLI tool — one command → Jira data pull → AI-generated HTML report → PM review and send.
**Future:** Web app with review UI, one-click send, and audience-tailored email delivery.

### What Makes This Special

The PM's value is judgment, not writing. Jira holds the data. AI performs the translation. The PM shifts from *author* (2 hours) to *editor* (10 minutes) — adding only what a human can: team absences, delivery risks, client relationship nuance.

**Differentiators:**
- Single command triggers full report generation — zero manual data gathering
- AI prompt engineered for executive communication language, not ticket summaries
- Human-in-the-loop by design — PM reviews and enriches before output is final
- One Jira pull → four audience-tailored outputs (Executive, Boss, PM, Account Manager) in V2

## Project Classification

- **Type:** CLI tool (V1) → Web app (future)
- **Domain:** General — Business Productivity / PM Tooling
- **Complexity:** Medium (Jira API, AI generation, multi-audience output)
- **Context:** Greenfield — personal tool, single user

## Success Criteria

### User Success
- CLI produces a complete, sendable report in under 1 minute
- AI output is send-ready as-is — matches PM's voice and executive communication standard
- PM time: ~2 hours → ~10 minutes (review + minor context additions)

### Technical Success
- Jira API authentication is silent and reliable after initial setup
- JQL queries return accurate data for the correct date range automatically
- All report sections are coherent and factually grounded in ticket data
- All failures (auth errors, empty data, API failures) surface immediately on stderr

### Measurable Outcomes
- Week 1: Tool runs end-to-end successfully on real Jira board
- Week 4: PM has used it for 4 consecutive weekly reports without reverting to manual writing
- Ongoing: Report produced in < 1 min; review time < 10 min

## Product Scope

### MVP — Phase 1

**MVP Approach:** Prove the core pipeline end-to-end before optimizing output quality. V1 ships with AI output requiring light editing; prompt quality improves through weekly use.

**Resource:** Solo developer (Nardi), 3–4 days. Dependencies: Jira API access + AI provider API key.

**Must-Have Capabilities:**
- `config.yaml`: Jira URL, API token, project key, AI provider, report tone, project name
- Auto date range (last Mon–Sun), no manual input
- 3 JQL queries: Done / In Progress / Planned (ticket subject + assignee per section)
- AI generates all sections + Executive Summary in one call
- HTML output with auto-stamped filename
- CLI flags: `--week`, `--project`, `--output`, `--dry-run`, `--help`
- Fail-loud error handling on stderr

### Growth — Phase 2

- Human review UI with structured context fields (absences, holidays, client notes)
- Email delivery to stakeholders
- Audience-tailored outputs: one pull → four versions (Executive, Boss, PM, Account Manager)
- Scheduled auto-send (Friday 8am cron)

### Vision — Phase 3

- Web app with review UI and one-click send
- Learning loop: approved outputs inform next week's AI prompt
- RAG status auto-calculated per project area
- Multi-project support

### Risk Mitigation

| Risk | Severity | Mitigation |
|---|---|---|
| AI output quality below send-ready | Medium | Accept light editing in V1; iterate on prompt weekly |
| Jira API auth breaks silently | High | Validate auth before every run; fail loudly on stderr |
| JQL returns wrong date range | High | Log exact queries + date range to terminal on every run |
| AI hallucinates ticket details | High | Pass raw Jira data as full context; no pre-summarization |

## User Journeys

### Journey 1: First-Time Setup *(one-time)*

**Opening scene:** Sunday evening. Nardi decides to stop spending 2 hours every Friday writing reports. She has a Jira API token and 15 minutes.

**Rising action:** She creates `config.yaml`, enters Jira URL, API token, and project key. First CLI run authenticates silently, fires 3 JQL queries, outputs a draft report to terminal.

**Climax:** First draft appears. Structure is right, facts are accurate. She recognizes her project's tickets in natural language.

**Resolution:** Setup done. Friday just got 110 minutes shorter.

*Requirements revealed: config.yaml schema, Jira auth validation on startup, clear error messages on misconfiguration.*

---

### Journey 2: Weekly Happy Path *(every Friday)*

**Opening scene:** Friday 9am. Nardi has 10 minutes before her leadership sync. She runs one command.

**Rising action:** CLI completes in under 60 seconds. HTML file opens. Executive Summary already sounds like her. She adds two lines: "Maria was out Wednesday–Thursday" and "Client Alpha delivery at risk due to vendor dependency."

**Climax:** She copies the enriched report and sends it. Total time: 9 minutes.

**Resolution:** Leadership gets the report before the meeting. Nardi walks in prepared.

*Requirements revealed: < 1 min execution, HTML output to file, clean AI voice.*

---

### Journey 3: Empty Data / Light Sprint *(edge case)*

**Opening scene:** Friday morning. New sprint started Monday — almost nothing in Done.

**Rising action:** CLI runs. Done section returns 2 tickets. Tool warns: *"Only 2 completed tickets found — short sprint or data gap?"* Nardi confirms it's accurate.

**Resolution:** Executive Summary notes: *"Lighter delivery week — team transitioned to new sprint mid-week."* She adds one sentence of context and sends. No panic, no silent failure.

*Requirements revealed: data completeness check before generation, graceful low-data handling, clear warning output.*

---

### Journey 4: The Executive Receives the Report *(V2 recipient)*

**Opening scene:** Monday morning. CTO sees: *"✅ Project Alpha — Week 17: On Track."*

**Rising action:** She opens it. First paragraph answers her question: on track? RAG status visible in the first sentence. She reads 3 bullets, closes the email.

**Resolution:** She replies: *"Thanks, looks good."* No follow-up questions.

*Requirements revealed (V2): audience-tailored output, email subject as status signal, executive-first structure.*

---

### Journey Requirements Summary

| Capability | Source |
|---|---|
| `config.yaml` validation + auth check | Journey 1 |
| JQL auto date range | Journeys 1–2 |
| < 1 min execution, HTML output | Journey 2 |
| AI voice matching PM tone | Journey 2 |
| Data completeness check + warning | Journey 3 |
| Audience-tailored output (V2) | Journey 4 |
| Email subject as status signal (V2) | Journey 4 |

## Innovation & Novel Patterns

### Detected Innovation Areas

**1. AI as Language Translation Layer**
The innovation is not Jira connectivity (solved) or text generation (solved). It is the specific translation: operational ticket language → executive communication language, automated and audience-aware. The AI prompt encodes PM expertise — tone, structure, what executives care about — making the prompt the product's core IP.

**2. Prompt Engineering as Competitive Moat**
A generic Jira-to-report tool produces summaries. This tool produces communication. That difference lives entirely in the prompt design — audience profiles, delivery style, risk language.

**3. Author-to-Editor Paradigm**
Existing tools automate data gathering. This tool automates the translation step that previously required PM expertise to execute manually. PM shifts from production to quality control.

### Validation Approach

- Week 1: Does AI output sound like Nardi, or like a robot summarizing tickets?
- Week 2–4: Does leadership respond with fewer follow-up questions?
- Quality bar: Output is send-ready as-is — if rewriting is needed, the prompt needs tuning, not the code

## CLI Tool Specification

### Command Structure

```bash
jira-report                          # Reads all config from config.yaml
jira-report --week 2026-04-21        # Override date range (start of week)
jira-report --project ALPHA          # Override project key
jira-report --output ./reports/      # Override output directory
jira-report --dry-run                # Pull Jira data + show report, don't save
jira-report --help                   # Usage instructions
```

### Config Schema (`config.yaml`)

```yaml
jira_url: https://yourcompany.atlassian.net
api_token: your-token-here
project_key: PROJ
output_dir: ./reports
ai_provider: openai          # or anthropic, etc.
ai_model: gpt-4o
report_tone: professional    # informs AI prompt
project_name: Project Alpha  # used in report header and AI prompt
```

### Output

- **Primary:** `.html` file — formatted report ready to copy into email client; auto-stamped filename (e.g., `report-2026-04-25.html`)
- **Terminal:** Ticket counts per section + output file path after each run
- **Errors:** stderr — auth failures, empty data warnings, API errors

## Functional Requirements

*Complete capability inventory. Every feature built must trace to an FR below.*

### Configuration & Setup

- **FR1:** PM configures the tool via `config.yaml` specifying Jira connection, AI provider, project name, and output preferences
- **FR2:** PM validates configuration and Jira authentication via CLI before generating a report
- **FR3:** The system reports specific, actionable errors when configuration is missing or invalid
- **FR4:** The system authenticates to Jira silently on every run without prompting for credentials

### Jira Data Retrieval

- **FR5:** The system calculates the report date range (last Monday–Sunday) automatically at runtime
- **FR6:** PM overrides the report date range via `--week` flag
- **FR7:** PM overrides the target Jira project via `--project` flag
- **FR8:** The system retrieves completed tickets (Done) for the date range including ticket subject and assignee
- **FR9:** The system retrieves in-progress tickets at time of run including ticket subject and assignee
- **FR10:** The system retrieves planned tickets (Next/To Do) at time of run including ticket subject and assignee
- **FR11:** The system warns when a data section returns unusually low ticket counts before generating the report

### Report Generation

- **FR12:** The system generates a report with four sections: Done, In Progress, Next Plan, Executive Summary
- **FR13:** The system passes raw Jira ticket data as full context to the AI with no pre-summarization
- **FR14:** The system generates report text in executive communication language, not Jira operational language
- **FR15:** The system uses configurable tone and project name to align AI output with PM's voice and context
- **FR16:** PM previews report output without saving to file via `--dry-run` flag

### Output & Delivery

- **FR17:** The system saves the generated report as an HTML file formatted for copy-paste into an email client
- **FR18:** The system auto-generates the output filename with a date stamp
- **FR19:** PM overrides the output directory via `--output` flag
- **FR20:** The system displays a terminal summary after each run: ticket counts per section + output file path
- **FR21:** The system routes all errors and warnings to stderr, separate from report content

### CLI Interface

- **FR22:** PM runs the tool with zero arguments using defaults from `config.yaml`
- **FR23:** PM accesses usage instructions and flag descriptions via `--help`
- **FR24:** PM overrides key parameters at runtime without editing `config.yaml`

### Post-MVP Capabilities *(Phase 2)*

- **FR25:** PM adds structured context (absences, holidays, client notes) before the report is finalized
- **FR26:** The system delivers audience-tailored report versions to multiple recipients in a single run
- **FR27:** The system sends reports via email to configured recipients
- **FR28:** PM schedules automated report generation and delivery

## Non-Functional Requirements

### Performance

- **NFR1:** End-to-end execution (auth → data retrieval → AI generation → file output) completes in under 60 seconds on a standard internet connection
- **NFR2:** CLI startup and config validation completes in under 2 seconds before any external API calls
- **NFR3:** Terminal feedback is progressive — PM sees status updates during execution, not silence followed by output

### Security

- **NFR4:** Jira API token is stored only in `config.yaml` on the local filesystem; never logged, printed to terminal, or included in output files
- **NFR5:** The tool makes no outbound network calls except to the configured Jira instance and AI provider
- **NFR6:** `config.yaml` is excluded from version control by default (`.gitignore` entry generated on first run)

### Integration

- **NFR7:** Jira API connection failures surface within 5 seconds with a specific error message (auth failure vs. network unreachable vs. project not found)
- **NFR8:** AI provider API failures do not silently produce empty or partial output — the tool exits with a clear error and no file is written
- **NFR9:** Compatible with Jira Cloud REST API v3 (Atlassian hosted instances)

### Reliability

- **NFR10:** A failed run never overwrites or corrupts a previously generated report file
- **NFR11:** `--dry-run` always exits without writing any files, regardless of execution outcome
- **NFR12:** The tool produces identical output structure for the same input data (deterministic section headings, consistent HTML formatting)
