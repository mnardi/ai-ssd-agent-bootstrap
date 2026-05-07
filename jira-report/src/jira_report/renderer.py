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
    template = _jinja_env.get_template("report.html.j2")
    return template.render(
        project_name=config.project_name,
        done_text=sections.done_text,
        in_progress_text=sections.in_progress_text,
        next_plan_text=sections.next_plan_text,
        executive_summary=sections.executive_summary,
    )
