"""SPEC-000 AC-5: the CLI runs and exits zero."""

from __future__ import annotations

from typer.testing import CliRunner

from harnesslab.cli import app

runner = CliRunner()


def test_help_exits_zero() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "HarnessLab" in result.stdout


def test_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "harnesslab" in result.stdout


def test_config_prints_no_secret(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("GROQ_API_KEY", "gsk-must-not-be-printed")
    result = runner.invoke(app, ["config"])
    assert result.exit_code == 0
    assert "must-not-be-printed" not in result.stdout


def test_models_lists_the_grid() -> None:
    result = runner.invoke(app, ["models", "--grid"])
    assert result.exit_code == 0
    assert "gemini-flash-lite" in result.stdout


def test_models_warns_about_the_pending_gate() -> None:
    """Until SPEC-010 runs, the pooled grid is not sweep-ready and the CLI has
    to say so rather than look complete."""
    result = runner.invoke(app, ["models", "--grid"])
    assert "SPEC-010" in result.stdout
