"""Smoke tests for the interactive bot console."""

from __future__ import annotations

from production_control.bot import answer as answer_mod
from production_control.bot import console


def test_empty_line_exits_immediately(monkeypatch, capsys):
    inputs = iter([""])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(inputs))
    monkeypatch.setattr(answer_mod, "answer", lambda *a, **kw: None)  # never called
    rc = console.main()
    out = capsys.readouterr().out
    assert rc == 0
    assert "model:" in out  # banner printed


def test_eof_exits(monkeypatch, capsys):
    def raise_eof(_prompt):
        raise EOFError

    monkeypatch.setattr("builtins.input", raise_eof)
    rc = console.main()
    assert rc == 0


def test_one_question_then_empty_line(monkeypatch, capsys):
    inputs = iter(["hoeveel partijen?", ""])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(inputs))

    fake = answer_mod.AnswerResult(
        text="Vier.",
        sql=["SELECT COUNT(*) FROM t"],
        model="fake/model",
        latency_ms=5,
        tokens=10,
        iterations=2,
    )
    monkeypatch.setattr(answer_mod, "answer", lambda *a, **kw: fake)

    rc = console.main()
    out = capsys.readouterr().out
    assert rc == 0
    assert "Vier." in out
    assert "SELECT COUNT(*) FROM t" in out
    assert "fake/model" in out  # footer
