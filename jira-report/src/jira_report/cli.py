from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from jira_report.config import JiraReportError, load_config
from jira_report.jira_client import fetch_jira_data, JiraData, LOW_TICKET_WARNING_THRESHOLD
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
        _warn_low_ticket_counts(jira_data)

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


def _warn_low_ticket_counts(jira_data: JiraData) -> None:
    for label, tickets in [
        ("Done", jira_data.done),
        ("In Progress", jira_data.in_progress),
        ("Planned", jira_data.planned),
    ]:
        if len(tickets) < LOW_TICKET_WARNING_THRESHOLD:
            typer.echo(
                f"Warning: Only {len(tickets)} ticket(s) found for {label}"
                " — verify data accuracy before proceeding",
                err=True,
            )
