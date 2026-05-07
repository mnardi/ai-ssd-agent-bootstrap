import re
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from jira_report.renderer import (
    _atomic_write,
    _generate_filename,
    _render_html,
    render_and_write,
)
from jira_report.config import OutputError
from jira_report.jira_client import ReportSections


WEEK_END = date(2026, 4, 27)


# ── _render_html ───────────────────────────────────────────────────────────────

def test_render_html_returns_string(sample_config, sample_sections):
    result = _render_html(sample_config, sample_sections)
    assert isinstance(result, str)
    assert len(result) > 0


def test_render_html_includes_all_four_section_headers(sample_config, sample_sections):
    result = _render_html(sample_config, sample_sections)
    for header in ("Done", "In Progress", "Next Plan", "Executive Summary"):
        assert header in result


def test_render_html_includes_all_four_section_texts(sample_config, sample_sections):
    result = _render_html(sample_config, sample_sections)
    assert "Done body." in result
    assert "IP body." in result
    assert "NP body." in result
    assert "ES body." in result


def test_render_html_includes_project_name(sample_config, sample_sections):
    result = _render_html(sample_config, sample_sections)
    assert sample_config.project_name in result


def test_render_html_no_external_stylesheets(sample_config, sample_sections):
    result = _render_html(sample_config, sample_sections).lower()
    assert '<link rel="stylesheet"' not in result
    assert "<style>" not in result
    assert "<style " not in result


def test_render_html_no_javascript(sample_config, sample_sections):
    result = _render_html(sample_config, sample_sections).lower()
    assert "<script" not in result
    assert "onclick=" not in result
    assert "onload=" not in result
    assert "onerror=" not in result
    assert "javascript:" not in result


def test_render_html_has_doctype_and_html_root(sample_config, sample_sections):
    result = _render_html(sample_config, sample_sections)
    assert result.lstrip().lower().startswith("<!doctype html>")
    assert "<html" in result.lower()
    assert "</html>" in result.lower()


def test_render_html_has_charset_meta(sample_config, sample_sections):
    result = _render_html(sample_config, sample_sections).lower()
    assert '<meta charset="utf-8">' in result


def test_render_html_uses_inline_styles(sample_config, sample_sections):
    result = _render_html(sample_config, sample_sections)
    # Inline CSS confirmation: at least 3 style="..." occurrences (h1, h2, p)
    assert len(re.findall(r'style="', result)) >= 3


def test_render_html_escapes_html_in_section_text(sample_config):
    sections = ReportSections(
        done_text="<script>alert(1)</script>",
        in_progress_text="ip",
        next_plan_text="np",
        executive_summary="es",
    )
    result = _render_html(sample_config, sections)
    assert "<script>alert(1)</script>" not in result
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in result


def test_render_html_escapes_ampersand(sample_config):
    sections = ReportSections(
        done_text="A & B",
        in_progress_text="ip",
        next_plan_text="np",
        executive_summary="es",
    )
    result = _render_html(sample_config, sections)
    assert "A &amp; B" in result
    assert "A & B" not in result


def test_render_html_deterministic_for_same_input(sample_config, sample_sections):
    first = _render_html(sample_config, sample_sections)
    second = _render_html(sample_config, sample_sections)
    assert first == second


def test_render_html_section_order_matches_template(sample_config, sample_sections):
    result = _render_html(sample_config, sample_sections)
    i_done = result.index("Done body.")
    i_ip = result.index("IP body.")
    i_np = result.index("NP body.")
    i_es = result.index("ES body.")
    assert i_done < i_ip < i_np < i_es


# ── _generate_filename ─────────────────────────────────────────────────────────

def test_generate_filename():
    assert _generate_filename(date(2026, 4, 27)) == "report-2026-04-27.html"


# ── render_and_write — write path ──────────────────────────────────────────────

def test_render_and_write_writes_file_and_returns_path(tmp_path, sample_config, sample_sections):
    cfg = sample_config.model_copy(update={"output_dir": str(tmp_path / "reports")})
    result = render_and_write(cfg, sample_sections, WEEK_END)
    assert result is not None
    assert result.exists()
    content = result.read_text(encoding="utf-8")
    assert "Done body." in content
    assert "<!DOCTYPE" in content


def test_render_and_write_filename_uses_week_end(tmp_path, sample_config, sample_sections):
    cfg = sample_config.model_copy(update={"output_dir": str(tmp_path)})
    result = render_and_write(cfg, sample_sections, WEEK_END)
    assert result is not None
    assert result.name == "report-2026-04-27.html"


def test_render_and_write_creates_output_dir_if_missing(tmp_path, sample_config, sample_sections):
    new_dir = tmp_path / "newdir"
    assert not new_dir.exists()
    cfg = sample_config.model_copy(update={"output_dir": str(new_dir)})
    render_and_write(cfg, sample_sections, WEEK_END)
    assert new_dir.is_dir()


def test_render_and_write_uses_output_dir_from_config(tmp_path, sample_config, sample_sections):
    custom = tmp_path / "custom"
    cfg = sample_config.model_copy(update={"output_dir": str(custom)})
    result = render_and_write(cfg, sample_sections, WEEK_END)
    assert result is not None
    assert result.parent == custom


# ── render_and_write — dry-run path ────────────────────────────────────────────

def test_render_and_write_dry_run_returns_none(tmp_path, sample_config, sample_sections, capsys):
    cfg = sample_config.model_copy(update={"output_dir": str(tmp_path)})
    result = render_and_write(cfg, sample_sections, WEEK_END, dry_run=True)
    assert result is None


def test_render_and_write_dry_run_writes_no_file(tmp_path, sample_config, sample_sections, capsys):
    cfg = sample_config.model_copy(update={"output_dir": str(tmp_path)})
    render_and_write(cfg, sample_sections, WEEK_END, dry_run=True)
    assert list(tmp_path.glob("*.html")) == []


def test_render_and_write_dry_run_prints_html_to_stdout(tmp_path, sample_config, sample_sections, capsys):
    cfg = sample_config.model_copy(update={"output_dir": str(tmp_path)})
    render_and_write(cfg, sample_sections, WEEK_END, dry_run=True)
    captured = capsys.readouterr()
    assert "Done body." in captured.out
    assert "<!DOCTYPE" in captured.out


def test_render_and_write_dry_run_with_nonexistent_output_dir(sample_config, sample_sections, capsys):
    cfg = sample_config.model_copy(update={"output_dir": "/path/that/definitely/does/not/exist"})
    # NFR11: dry-run completes successfully regardless of output path validity
    result = render_and_write(cfg, sample_sections, WEEK_END, dry_run=True)
    assert result is None


# ── Atomic write ───────────────────────────────────────────────────────────────

def test_atomic_write_uses_tempfile_then_move(tmp_path, sample_config, sample_sections):
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    cfg = sample_config.model_copy(update={"output_dir": str(output_dir)})

    call_order = []
    real_mkstemp_returns = []

    real_mkstemp = __import__("tempfile").mkstemp

    def tracking_mkstemp(**kwargs):
        call_order.append(("mkstemp", kwargs))
        result = real_mkstemp(**kwargs)
        real_mkstemp_returns.append(result)
        return result

    def tracking_move(src, dst):
        call_order.append(("move", src, dst))
        # Use os.rename directly — bypasses the patched shutil.move (avoids recursion)
        import os
        os.rename(src, dst)

    with patch("jira_report.renderer.tempfile.mkstemp", side_effect=tracking_mkstemp), \
         patch("jira_report.renderer.shutil.move", side_effect=tracking_move):
        render_and_write(cfg, sample_sections, WEEK_END)

    assert call_order[0][0] == "mkstemp"
    assert call_order[0][1]["dir"] == str(output_dir)
    assert call_order[1][0] == "move"
    # second arg of move is the final path
    assert call_order[1][2] == str(output_dir / "report-2026-04-27.html")


def test_atomic_write_preserves_existing_file_on_failure(tmp_path, sample_config, sample_sections):
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    final_path = output_dir / "report-2026-04-27.html"
    final_path.write_text("OLD", encoding="utf-8")

    cfg = sample_config.model_copy(update={"output_dir": str(output_dir)})

    with patch("jira_report.renderer.shutil.move", side_effect=OSError("move failed")):
        with pytest.raises(OutputError):
            render_and_write(cfg, sample_sections, WEEK_END)

    # Original content must be intact
    assert final_path.read_text(encoding="utf-8") == "OLD"


# ── OutputError mapping ────────────────────────────────────────────────────────

def test_render_and_write_raises_output_error_on_mkdir_failure(tmp_path, sample_config, sample_sections):
    cfg = sample_config.model_copy(update={"output_dir": str(tmp_path / "x")})
    with patch("jira_report.renderer.Path.mkdir", side_effect=PermissionError("denied")):
        with pytest.raises(OutputError, match="Cannot create output directory"):
            render_and_write(cfg, sample_sections, WEEK_END)


def test_render_and_write_raises_output_error_on_write_failure(tmp_path, sample_config, sample_sections):
    cfg = sample_config.model_copy(update={"output_dir": str(tmp_path)})
    with patch("jira_report.renderer._atomic_write", side_effect=OSError("disk full")):
        with pytest.raises(OutputError, match="Failed to write report"):
            render_and_write(cfg, sample_sections, WEEK_END)
