# jira-report

A CLI tool that auto-generates weekly executive status reports from Jira data.

## Setup

1. Copy `config.yaml.example` to `config.yaml` and fill in your credentials:
   ```bash
   cp config.yaml.example config.yaml
   ```

2. Install the tool globally:
   ```bash
   uv tool install .
   ```

## Usage

```bash
jira-report                        # generate report using config.yaml defaults
jira-report --week 2026-04-21      # override date range (start of week)
jira-report --project ALPHA        # override project key
jira-report --output ./reports/    # override output directory
jira-report --dry-run              # preview report without saving
jira-report --help                 # usage instructions
```

## Requirements

- Python 3.12+
- uv package manager
- Jira Cloud API token
- Anthropic API key
