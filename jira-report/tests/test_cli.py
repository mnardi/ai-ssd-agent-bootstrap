import pytest
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner

from jira_report.cli import app, _ensure_gitignore
from jira_report.config import ConfigError
from jira_report.jira_client import JiraData, JiraTicket, LOW_TICKET_WARNING_THRESHOLD

runner = CliRunner()


# ── AC 1: --help lists all flags ────────────────────────────────────────────

def test_help_lists_all_flags():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "--week" in result.output
    assert "--project" in result.output
    assert "--output" in result.output
    assert "--dry-run" in result.output


# ── AC 5: _ensure_gitignore() ───────────────────────────────────────────────

def test_ensure_gitignore_creates_file(tmp_path, monkeypatch):
    (tmp_path / ".git").mkdir()
    monkeypatch.chdir(tmp_path)
    _ensure_gitignore()
    assert (tmp_path / ".gitignore").read_text(encoding="utf-8") == "config.yaml\n"


def test_ensure_gitignore_appends_entry(tmp_path, monkeypatch):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".gitignore").write_text("*.pyc\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    _ensure_gitignore()
    content = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert "config.yaml" in content
    assert "*.pyc" in content


def test_ensure_gitignore_idempotent(tmp_path, monkeypatch):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".gitignore").write_text("config.yaml\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    _ensure_gitignore()
    lines = (tmp_path / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert lines.count("config.yaml") == 1


def test_ensure_gitignore_no_git_repo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _ensure_gitignore()
    assert not (tmp_path / ".gitignore").exists()


# ── AC 6: JiraReportError → stderr + exit 1 ─────────────────────────────────

def test_jira_report_error_to_stderr_exit_1(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with patch("jira_report.cli._ensure_gitignore"), \
         patch("jira_report.cli.load_config", side_effect=ConfigError("missing api_token")):
        result = runner.invoke(app, [], catch_exceptions=False)
    assert result.exit_code == 1
    assert "missing api_token" in result.output


# ── AC 3 & 4: flag overrides passed through ─────────────────────────────────

def test_project_flag_overrides_config(tmp_path, monkeypatch, sample_config):
    monkeypatch.chdir(tmp_path)
    captured = {}

    def fake_fetch(config, week_override=None):
        captured["project_key"] = config.project_key
        raise ConfigError("stop pipeline")

    with patch("jira_report.cli._ensure_gitignore"), \
         patch("jira_report.cli.load_config", return_value=sample_config), \
         patch("jira_report.cli.fetch_jira_data", side_effect=fake_fetch):
        runner.invoke(app, ["--project", "ALPHA"])

    assert captured.get("project_key") == "ALPHA"


def test_output_flag_overrides_config(tmp_path, monkeypatch, sample_config):
    monkeypatch.chdir(tmp_path)
    captured = {}

    def fake_fetch(config, week_override=None):
        captured["output_dir"] = config.output_dir
        raise ConfigError("stop pipeline")

    with patch("jira_report.cli._ensure_gitignore"), \
         patch("jira_report.cli.load_config", return_value=sample_config), \
         patch("jira_report.cli.fetch_jira_data", side_effect=fake_fetch):
        runner.invoke(app, ["--output", "./custom/"])

    assert captured.get("output_dir") == "./custom/"


def test_dry_run_flag(tmp_path, monkeypatch, sample_config, sample_jira_data):
    monkeypatch.chdir(tmp_path)
    captured = {}

    def fake_render(config, sections, week_end, dry_run=False):
        captured["dry_run"] = dry_run
        return None

    with patch("jira_report.cli._ensure_gitignore"), \
         patch("jira_report.cli.load_config", return_value=sample_config), \
         patch("jira_report.cli.fetch_jira_data", return_value=sample_jira_data), \
         patch("jira_report.cli.generate_report", return_value=MagicMock()), \
         patch("jira_report.cli.render_and_write", side_effect=fake_render):
        result = runner.invoke(app, ["--dry-run"])

    assert captured.get("dry_run") is True
    assert "Dry run" in result.output


def test_week_flag_passed_to_fetch(tmp_path, monkeypatch, sample_config):
    monkeypatch.chdir(tmp_path)
    captured = {}

    def fake_fetch(config, week_override=None):
        captured["week_override"] = week_override
        raise ConfigError("stop pipeline")

    with patch("jira_report.cli._ensure_gitignore"), \
         patch("jira_report.cli.load_config", return_value=sample_config), \
         patch("jira_report.cli.fetch_jira_data", side_effect=fake_fetch):
        runner.invoke(app, ["--week", "2026-04-21"])

    assert captured.get("week_override") == "2026-04-21"


def test_success_prints_saved_path(tmp_path, monkeypatch, sample_config, sample_jira_data):
    monkeypatch.chdir(tmp_path)
    saved_path = Path("./reports/report-2026-04-27.html")

    with patch("jira_report.cli._ensure_gitignore"), \
         patch("jira_report.cli.load_config", return_value=sample_config), \
         patch("jira_report.cli.fetch_jira_data", return_value=sample_jira_data), \
         patch("jira_report.cli.generate_report", return_value=MagicMock()), \
         patch("jira_report.cli.render_and_write", return_value=saved_path):
        result = runner.invoke(app, [])

    assert result.exit_code == 0
    assert "Done. Report saved:" in result.output
    assert str(saved_path) in result.output


# ── Low-ticket-count warnings ──────────────────────────────────────────────────

def _make_jira_data(done_count=3, in_progress_count=3, planned_count=3):
    ticket = JiraTicket(key="T-1", summary="s", assignee="a", status="s")
    return JiraData(
        done=[ticket] * done_count,
        in_progress=[ticket] * in_progress_count,
        planned=[ticket] * planned_count,
        week_start=date(2026, 4, 21),
        week_end=date(2026, 4, 27),
    )


def test_low_ticket_threshold_constant():
    assert LOW_TICKET_WARNING_THRESHOLD == 3


def test_warning_emitted_for_low_done_count(tmp_path, monkeypatch, sample_config):
    monkeypatch.chdir(tmp_path)
    with patch("jira_report.cli._ensure_gitignore"), \
         patch("jira_report.cli.load_config", return_value=sample_config), \
         patch("jira_report.cli.fetch_jira_data", return_value=_make_jira_data(done_count=2)), \
         patch("jira_report.cli.generate_report", return_value=MagicMock()), \
         patch("jira_report.cli.render_and_write", return_value=Path("./r.html")):
        result = runner.invoke(app, [])
    assert "Warning" in result.output
    assert "Done" in result.output


def test_warning_emitted_for_low_in_progress_count(tmp_path, monkeypatch, sample_config):
    monkeypatch.chdir(tmp_path)
    with patch("jira_report.cli._ensure_gitignore"), \
         patch("jira_report.cli.load_config", return_value=sample_config), \
         patch("jira_report.cli.fetch_jira_data", return_value=_make_jira_data(in_progress_count=1)), \
         patch("jira_report.cli.generate_report", return_value=MagicMock()), \
         patch("jira_report.cli.render_and_write", return_value=Path("./r.html")):
        result = runner.invoke(app, [])
    assert "Warning" in result.output
    assert "In Progress" in result.output


def test_warning_emitted_for_low_planned_count(tmp_path, monkeypatch, sample_config):
    monkeypatch.chdir(tmp_path)
    with patch("jira_report.cli._ensure_gitignore"), \
         patch("jira_report.cli.load_config", return_value=sample_config), \
         patch("jira_report.cli.fetch_jira_data", return_value=_make_jira_data(planned_count=0)), \
         patch("jira_report.cli.generate_report", return_value=MagicMock()), \
         patch("jira_report.cli.render_and_write", return_value=Path("./r.html")):
        result = runner.invoke(app, [])
    assert "Warning" in result.output
    assert "Planned" in result.output


def test_no_warning_when_all_sections_meet_threshold(tmp_path, monkeypatch, sample_config):
    monkeypatch.chdir(tmp_path)
    with patch("jira_report.cli._ensure_gitignore"), \
         patch("jira_report.cli.load_config", return_value=sample_config), \
         patch("jira_report.cli.fetch_jira_data", return_value=_make_jira_data()), \
         patch("jira_report.cli.generate_report", return_value=MagicMock()), \
         patch("jira_report.cli.render_and_write", return_value=Path("./r.html")):
        result = runner.invoke(app, [])
    assert "Warning" not in result.output


def test_multiple_sections_can_warn(tmp_path, monkeypatch, sample_config):
    monkeypatch.chdir(tmp_path)
    with patch("jira_report.cli._ensure_gitignore"), \
         patch("jira_report.cli.load_config", return_value=sample_config), \
         patch("jira_report.cli.fetch_jira_data", return_value=_make_jira_data(done_count=2, in_progress_count=1)), \
         patch("jira_report.cli.generate_report", return_value=MagicMock()), \
         patch("jira_report.cli.render_and_write", return_value=Path("./r.html")):
        result = runner.invoke(app, [])
    assert "Done" in result.output
    assert "In Progress" in result.output


def test_warning_goes_to_stderr_not_stdout(tmp_path, monkeypatch, sample_config):
    monkeypatch.chdir(tmp_path)
    with patch("jira_report.cli._ensure_gitignore"), \
         patch("jira_report.cli.load_config", return_value=sample_config), \
         patch("jira_report.cli.fetch_jira_data", return_value=_make_jira_data(done_count=1)), \
         patch("jira_report.cli.generate_report", return_value=MagicMock()), \
         patch("jira_report.cli.render_and_write", return_value=Path("./r.html")):
        result = runner.invoke(app, [])
    assert "Warning" in result.stderr
    assert "Warning" not in result.stdout


def test_pipeline_continues_after_warning(tmp_path, monkeypatch, sample_config):
    monkeypatch.chdir(tmp_path)
    generate_called = {}

    def fake_generate(config, jira_data):
        generate_called["called"] = True
        return MagicMock()

    with patch("jira_report.cli._ensure_gitignore"), \
         patch("jira_report.cli.load_config", return_value=sample_config), \
         patch("jira_report.cli.fetch_jira_data", return_value=_make_jira_data(done_count=0)), \
         patch("jira_report.cli.generate_report", side_effect=fake_generate), \
         patch("jira_report.cli.render_and_write", return_value=Path("./r.html")):
        result = runner.invoke(app, [])

    assert generate_called.get("called") is True
    assert result.exit_code == 0
