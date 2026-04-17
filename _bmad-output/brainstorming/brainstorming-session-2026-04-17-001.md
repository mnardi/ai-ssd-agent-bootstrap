---
stepsCompleted: [1, 2, 3, 4]
inputDocuments: []
session_topic: 'Application to auto-generate weekly executive status reports from Jira data'
session_goals: 'Explore ideas for a Jira-connected app that produces structured reports (Done / In Progress / Next Plan + Executive Summary) to eliminate manual report writing for leadership'
selected_approach: 'user-selected'
techniques_used: ['Mind Mapping']
ideas_generated: [32]
context_file: ''
session_active: false
workflow_completed: true
---

# Brainstorming Session Results

**Facilitator:** Nardi
**Date:** 2026-04-17

---

## Session Overview

**Topic:** Application to auto-generate weekly executive status reports from Jira data
**Goals:** Explore ideas for a Jira-connected app that produces structured reports (Done / In Progress / Next Plan + Executive Summary) to eliminate manual report writing for leadership

**Approach:** User-Selected Techniques
**Technique Used:** Mind Mapping
**Total Ideas Generated:** 32

---

## Technique Selection

**Approach:** User-Selected Techniques
**Selected Technique:** Mind Mapping — Branch ideas visually from a central concept to discover connections and expand thinking. Central node: "Weekly Jira Executive Status Report App."

---

## Technique Execution Results

### Mind Mapping — Full Idea Inventory

**Central Node:** Weekly Jira Executive Status Report App

---

#### Branch 1: WHO Receives the Report (Audience)

- **[1.A] Executive RAG Status** — Executive needs risk signals and delivery confidence, not task lists. App auto-calculates Red/Amber/Green status per project area. *Novelty: Health readable in 10 seconds, no reading required.*
- **[1.B] PM Operational Detail** — Principal PM needs blockers, dependencies, velocity. App auto-generates a "blockers needing escalation" section from overdue/flagged tickets. *Novelty: Operational view built directly from Jira flags.*
- **[1.C] Account Manager Client Translation** — Client-facing audience needs business value language, not Jira jargon. App auto-translates ticket titles into outcome language ("3 features shipped" vs "12 story points"). *Novelty: Jargon gap closed automatically.*
- **[1.D] Boss + PM Commentary** — Boss wants team performance signals plus PM narrative. A PM commentary field lets you add 2 sentences of context, making the report yours. *Novelty: Automation handles data, human adds interpretation.*
- **[1.E] One-Report Problem** — Currently one report serves four completely different needs, leaving everyone underserved. App generates one data pull, four tailored outputs. *Novelty: Zero extra work, four perfectly targeted reports.*

---

#### Branch 2: WHAT Data Comes from Jira

- **[2.A] Assignee + Subject = Accountability** — Knowing who did what transforms the report into a team visibility tool. Auto-group by assignee: "Maria closed 4 tickets: login bug fix, payment flow..." *Novelty: Individual contribution visible without anyone asking.*
- **[2.B] Team Workload Map** — Visualize who carries the most load vs who has capacity, surfaced from In Progress tickets per assignee. *Novelty: Flags overloaded team members before they become a delivery risk.*
- **[2.C] Contributor Recognition** — Auto-highlight team members who closed most tickets or resolved critical blockers. *Novelty: Gives the report a human story, not just numbers.*
- **[2.D] Accountability Without Micromanagement** — Account Manager sees "Feature X assigned to João, In Progress since Monday" — answers client questions before they're asked. *Novelty: Eliminates the "what's the status of X?" email.*
- **[2.E] Date Range as Source of Truth** — App calculates last Mon–Sun automatically on every run. No manual date input, no sprint dependency. *Novelty: Works even if sprints don't align with calendar weeks.*
- **[2.F] Three Parallel JQL Queries** — Three simultaneous queries: Done (last week) · In Progress (now) · Planned (next). Each section independently accurate. *Novelty: No bleed between statuses.*
- **[2.G] Confidence Scoring** — AI flags sections with insufficient data: "Only 2 tickets found for Next Plan — is this complete?" before sending. *Novelty: Catches data gaps before your boss sees them.*
- **[2.H] Risk Signal Surfacing** — Auto-surface overdue tickets, long-running In Progress items (ticket age), and blocked dependencies as risk indicators. *Novelty: Silent risks become explicit, visible signals.*

---

#### Branch 3: HOW It's Delivered

- **[3.A] Email as Delivery Channel** — Report auto-generated and sent to each stakeholder's inbox. Zero manual steps after setup. *Novelty: Fully autonomous reporter after initial configuration.*
- **[3.B] Audience-Tailored Email Bodies** — Four different emails sent simultaneously from one Jira pull. Each recipient thinks you wrote their report personally. *Novelty: Personalization at scale, zero extra effort.*
- **[3.C] Email Subject as Status Signal** — Subject auto-reflects project health: "✅ Project Alpha — Week 16: On Track" vs "⚠️ Week 16: 2 Blockers Need Attention." *Novelty: Executives know RAG status before opening.*
- **[3.D] Reply-to-Comment Feedback Loop** — Recipients reply with questions; app logs them as context for next week's report. *Novelty: Each report gets smarter from stakeholder engagement.*
- **[3.E] Scheduled + On-Demand** — Auto-send every Friday 8am, plus manual trigger for mid-week requests. *Novelty: "Can you send a quick status?" answered with one click.*

---

#### Branch 4: HOW the App Works (Technical)

- **[4.A] API Token Authentication** — User generates Jira API token once, stored in config. App authenticates silently on every run. *Novelty: Zero friction after initial setup.*
- **[4.B] OAuth 2.0 Login** — Browser-based Jira login for enterprise/SSO environments. *Novelty: No token management, Jira handles session security.*
- **[4.C] Config File Setup** — Simple `config.yaml` stores Jira URL, project key, board ID, recipients, schedule. *Novelty: Non-technical PMs can reconfigure without code.*
- **[4.D] Auto JQL Generation** — App builds JQL query automatically from date range. PM never writes JQL. *Novelty: Technical complexity hidden completely.*
- **[4.E] Full AI Generation** — All sections + executive summary generated by AI from raw Jira data. *Novelty: Report reads like PM wrote it — zero minutes of effort.*
- **[4.F] Prompt Engineering as Secret Weapon** — AI prompt includes role, audience profiles, project name, preferred tone. "Write as a senior PM reporting to a CTO who cares about delivery risk." *Novelty: Sounds like YOUR voice, not a generic robot.*
- **[4.G] Audience-Aware AI Prompts** — Four separate AI calls, each with a different system prompt per audience. *Novelty: One data pull → four perfectly targeted outputs.*
- **[4.H] Learning from Your Edits** — App saves PM edits as style examples. Next week's prompt includes last week's approved version as reference. *Novelty: App gets smarter every week.*
- **[4.I] Absence-Aware Velocity Commentary** — PM enters "3 team members on vacation." AI regenerates summary: "Despite reduced capacity, team delivered X — strong performance." *Novelty: Contextualizes data that Jira can never know.*
- **[4.J] Human-in-the-Loop Review** — App generates draft, PM reviews before sending. PM adds holidays, vacations, client context. *Novelty: Automation handles 90%, PM adds the 10% that matters.*
- **[4.K] Pre-Built Context Fields** — Review screen includes structured fields: "Team absences:", "Holidays:", "Additional context:" — prompts you to add the right information. *Novelty: Turns manual additions into structured data for AI.*
- **[4.L] One-Click Send** — After review, one click sends all tailored emails simultaneously. *Novelty: PM shifts from author to editor — completely different cognitive load.*

---

## Idea Organization and Prioritization

### Thematic Organization (5 Themes, 32 Ideas)

| Theme | Ideas | Core Value |
|-------|-------|-----------|
| Audience Intelligence | 8 | Right message to right person automatically |
| Data Intelligence | 8 | Surface what matters from Jira noise |
| AI Generation Engine | 5 | Human-quality writing, zero time |
| Human-in-the-Loop & Delivery | 7 | PM stays in control, effort minimal |
| Technical Architecture | 4 | Simple to configure, reliable to run |

### Prioritization Results

**Top Priority — MVP Core (Version 1):**
> Connect to Jira → Extract data (Done / In Progress / Planned) with assignee + ticket subject → AI generates single polished report with Executive Summary

**Why:** Everything else is an enhancement on top of this. Prove the core works, then layer intelligence.

**Version 2 Enhancements:**
- Email delivery to recipients
- Human review UI with context fields (holidays, vacations)
- Audience-tailored versions — four outputs from one pull

**Breakthrough Concept:**
> The shift from "author" to "editor" — PM spends 10 minutes reviewing instead of 2 hours writing. Same output quality, radically different effort.

---

## Action Plan — Version 1 (MVP)

| Step | What to Build | Effort |
|------|--------------|--------|
| 1 | `config.yaml`: Jira URL, API token, project key, date range | 1 hour |
| 2 | Jira API connection + 3 JQL queries (Done / In Progress / Planned) | 1 day |
| 3 | Extract: ticket subject + assignee + status per section | Half day |
| 4 | AI prompt → generates single polished report (all sections + Executive Summary) | 1 day |
| 5 | Output to screen or text file for PM review | Half day |

**Realistic V1 Timeline: 3–4 days of focused development**

---

## Session Summary and Insights

**Key Achievements:**
- 32 ideas generated across 5 themes in one Mind Mapping session
- Full app pipeline defined: Connect → Retrieve → Generate → Review → Send
- MVP scope clearly identified and bounded
- V1 → V2 roadmap established naturally from session

**Breakthrough Moment:**
The discovery that one report serving four audiences is the root pain — and that one Jira pull can generate four tailored outputs automatically was the single biggest insight of the session.

**Key Decision:**
Full AI generation (not templates) chosen for all report sections — enabling natural narrative, business language, and audience adaptation.

**Human Element Preserved:**
Human-in-the-loop review step ensures PM context (holidays, vacations, client nuance) is always included — the app augments the PM, it doesn't replace their judgment.

### Creative Facilitation Narrative

Nardi came in knowing what they wanted to build. The Mind Mapping session revealed the WHY behind the tool — the gap between Jira operational data and executive communication language — and surfaced 32 distinct ideas that transformed a simple "report generator" into a multi-audience intelligence platform. The session moved efficiently from audience mapping → data extraction → AI generation → delivery architecture, with clear decisions made at each branch.

**Next Steps:**
1. Begin V1 development with config + Jira API connection
2. Test JQL queries against real board data
3. Iterate on AI prompt until report tone matches PM's voice
4. Add email delivery and review UI in V2
