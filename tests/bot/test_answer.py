"""Tests for the bot's tool-use loop and audit record."""

from __future__ import annotations

import json
from datetime import date
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine

from production_control.bot import answer


@pytest.fixture()
def sqlite_engine():
    eng = create_engine("sqlite:///:memory:")
    with eng.connect() as c:
        c.exec_driver_sql("CREATE TABLE t (id INTEGER, naam TEXT)")
        c.exec_driver_sql("INSERT INTO t VALUES (1, 'aap'), (2, 'noot')")
        c.commit()
    return eng


def _fake_response(content=None, tool_calls=None, total_tokens=50):
    msg = SimpleNamespace(content=content, tool_calls=tool_calls)
    choice = SimpleNamespace(message=msg)
    usage = SimpleNamespace(total_tokens=total_tokens)
    return SimpleNamespace(choices=[choice], usage=usage)


def _tool_call(call_id, name, arguments):
    return SimpleNamespace(
        id=call_id,
        function=SimpleNamespace(name=name, arguments=arguments),
    )


def test_text_only_terminates_immediately(tmp_path):
    audit_file = tmp_path / "audit.jsonl"

    def fake_chat(**_):
        return _fake_response(content="Hier is je antwoord.")

    result = answer.answer(
        "hoeveel partijen?",
        llm_chat=fake_chat,
        audit_path=str(audit_file),
    )
    assert result.text == "Hier is je antwoord."
    assert result.iterations == 1
    assert result.error is None
    assert audit_file.exists()
    rec = json.loads(audit_file.read_text().splitlines()[0])
    assert rec["question"] == "hoeveel partijen?"
    assert rec["error"] is None


def test_tool_call_then_text(tmp_path, sqlite_engine):
    calls = []

    def fake_chat(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            return _fake_response(
                tool_calls=[
                    _tool_call(
                        "c1",
                        "run_dremio_sql",
                        '{"query": "SELECT id, naam FROM t ORDER BY id"}',
                    )
                ]
            )
        return _fake_response(content="Klaar.")

    result = answer.answer(
        "lijst eens",
        engine=sqlite_engine,
        llm_chat=fake_chat,
        audit_path=str(tmp_path / "audit.jsonl"),
    )
    assert result.text == "Klaar."
    assert len(calls) == 2
    assert any("SELECT id, naam FROM t" in q for q in result.sql)
    assert result.rows == 2
    assert result.error is None


def test_caps_iterations(tmp_path, sqlite_engine):
    def fake_chat(**_):
        return _fake_response(
            tool_calls=[_tool_call("c", "run_dremio_sql", '{"query": "SELECT 1 AS x"}')]
        )

    result = answer.answer(
        "loop forever",
        engine=sqlite_engine,
        llm_chat=fake_chat,
        audit_path=str(tmp_path / "audit.jsonl"),
    )
    assert result.iterations == answer.MAX_TOOL_ITERATIONS
    assert result.error
    assert "iteratielimiet" in result.text


def test_llm_exception_recorded_in_audit(tmp_path):
    audit_file = tmp_path / "audit.jsonl"

    def fake_chat(**_):
        raise RuntimeError("boom")

    result = answer.answer(
        "anything",
        llm_chat=fake_chat,
        audit_path=str(audit_file),
    )
    assert result.error and "boom" in result.error
    rec = json.loads(audit_file.read_text().splitlines()[0])
    assert rec["error"]
    assert "boom" in rec["error"]


def test_unknown_tool_returns_error_to_model(tmp_path):
    """Loop continues if the model calls a tool that doesn't exist."""
    saw_tool_message = []

    def fake_chat(**kwargs):
        msgs = kwargs["messages"]
        # On the second call, capture whatever role=tool message the loop appended
        for m in msgs:
            if m.get("role") == "tool":
                saw_tool_message.append(m["content"])
        if len(saw_tool_message) == 0:
            return _fake_response(tool_calls=[_tool_call("c1", "does_not_exist", "{}")])
        return _fake_response(content="ok")

    result = answer.answer(
        "x",
        llm_chat=fake_chat,
        audit_path=str(tmp_path / "audit.jsonl"),
    )
    assert any("unknown tool" in m for m in saw_tool_message)
    assert result.text == "ok"


def test_footer_contains_model_latency_tokens():
    r = answer.AnswerResult(text="x", model="m", latency_ms=42, tokens=100, iterations=2)
    f = answer.footer(r)
    assert "m" in f
    assert "42" in f
    assert "100" in f
    assert "2 step" in f


def test_audit_path_env_var(monkeypatch, tmp_path):
    """If BOT_AUDIT_PATH is set, append() honours it."""
    p = tmp_path / "envaudit.jsonl"
    monkeypatch.setenv("BOT_AUDIT_PATH", str(p))

    def fake_chat(**_):
        return _fake_response(content="ok")

    answer.answer("x", llm_chat=fake_chat)
    assert p.exists()


def test_injected_now_flows_into_system_prompt(tmp_path):
    """A `now=...` kwarg into answer() reaches the LLM via the system message."""
    captured: list[dict] = []

    def fake_chat(**kwargs):
        captured.append(kwargs)
        return _fake_response(content="ok")

    answer.answer(
        "wat speelt er deze week?",
        llm_chat=fake_chat,
        audit_path=str(tmp_path / "audit.jsonl"),
        now=date(2026, 5, 28),
    )
    system_msg = captured[0]["messages"][0]
    assert system_msg["role"] == "system"
    content = system_msg["content"]
    # Week-date form of today + week bounds visible.
    assert "2026-W22-4" in content
    assert "2026-W22-1" in content
    assert "2026-W22-7" in content
    assert "2026-05-28" in content


def test_system_prompt_names_all_three_languages(tmp_path):
    """The language rule must explicitly name Dutch, English, and Polish."""
    captured: list[dict] = []

    def fake_chat(**kwargs):
        captured.append(kwargs)
        return _fake_response(content="ok")

    answer.answer(
        "anything",
        llm_chat=fake_chat,
        audit_path=str(tmp_path / "audit.jsonl"),
        now=date(2026, 5, 28),
    )
    content = captured[0]["messages"][0]["content"]
    assert "Dutch" in content
    assert "English" in content
    assert "Polish" in content


def test_audit_record_has_iso_timestamp(tmp_path):
    audit_file = tmp_path / "audit.jsonl"

    def fake_chat(**_):
        return _fake_response(content="ok")

    answer.answer("x", llm_chat=fake_chat, audit_path=str(audit_file))
    rec = json.loads(audit_file.read_text().splitlines()[0])
    # ISO 8601 with timezone — must parse via fromisoformat.
    from datetime import datetime

    dt = datetime.fromisoformat(rec["ts"])
    assert dt.tzinfo is not None
