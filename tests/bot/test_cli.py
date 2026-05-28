"""Smoke tests for the bot CLI entrypoint."""

from __future__ import annotations

from production_control.bot import answer as answer_mod
from production_control.bot import cli


def test_no_args_prints_usage_and_returns_2(capsys):
    rc = cli.main([])
    assert rc == 2
    err = capsys.readouterr().err
    assert "usage" in err


def test_happy_path_prints_text_sql_and_footer(monkeypatch, capsys):
    fake = answer_mod.AnswerResult(
        text="Het antwoord is 42.",
        sql=["SELECT 42 AS x"],
        model="fake/model",
        latency_ms=10,
        tokens=12,
        iterations=2,
        rows=1,
        error=None,
    )
    monkeypatch.setattr(answer_mod, "answer", lambda *a, **kw: fake)

    rc = cli.main(["wat", "is", "het", "antwoord"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "Het antwoord is 42." in out
    assert "SELECT 42 AS x" in out
    assert "fake/model" in out  # footer


def test_error_result_returns_nonzero_exit(monkeypatch, capsys):
    fake = answer_mod.AnswerResult(
        text="boom",
        sql=[],
        model="m",
        error="something broke",
    )
    monkeypatch.setattr(answer_mod, "answer", lambda *a, **kw: fake)

    rc = cli.main(["x"])
    assert rc == 1
