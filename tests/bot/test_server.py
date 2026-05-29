"""Tests for the Zulip-facing FastAPI app (bot.server)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from production_control.bot import answer as answer_mod
from production_control.bot import conversation, server


TOKEN = "test-token-abc"
BOT_NAME = "Insights Bot"


@pytest.fixture(autouse=True)
def _clean_conversation_store():
    conversation.clear_all()
    yield
    conversation.clear_all()


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv(server.TOKEN_ENV_VAR, TOKEN)
    return TestClient(server.app)


@pytest.fixture()
def fake_answer(monkeypatch):
    """Replace answer.answer with a deterministic fake; capture the question."""
    captured: dict = {}

    def _fake(question, **_kwargs):
        captured["question"] = question
        return answer_mod.AnswerResult(
            text="Vier partijen.",
            sql=["SELECT COUNT(*) FROM t"],
            model="fake/model",
            latency_ms=12,
            tokens=34,
            iterations=2,
        )

    monkeypatch.setattr(answer_mod, "answer", _fake)
    return captured


def _payload(**overrides) -> dict:
    base = {
        "token": TOKEN,
        "bot_full_name": BOT_NAME,
        "data": f"@**{BOT_NAME}** hoeveel partijen?",
        "message": {"type": "stream"},
    }
    base.update(overrides)
    return base


def test_health_returns_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_happy_path_returns_answer_and_footer(client, fake_answer):
    r = client.post("/zulip", json=_payload())
    assert r.status_code == 200
    body = r.json()["content"]
    assert "Vier partijen." in body
    assert "fake/model" in body  # footer present
    assert fake_answer["question"] == "hoeveel partijen?"  # mention stripped


def test_wrong_token_returns_401(client, fake_answer):
    r = client.post("/zulip", json=_payload(token="wrong"))
    assert r.status_code == 401
    assert "question" not in fake_answer  # answer not called


def test_missing_token_env_returns_401(monkeypatch, fake_answer):
    monkeypatch.delenv(server.TOKEN_ENV_VAR, raising=False)
    c = TestClient(server.app)
    r = c.post("/zulip", json=_payload())
    assert r.status_code == 401


def test_malformed_payload_returns_422(client):
    r = client.post("/zulip", json={"token": TOKEN})  # missing bot_full_name, data
    assert r.status_code == 422


def test_dm_without_mention_passes_text_through(client, fake_answer):
    """DMs don't include @-mention; question is the raw `data`."""
    r = client.post("/zulip", json=_payload(data="wat is de status?"))
    assert r.status_code == 200
    assert fake_answer["question"] == "wat is de status?"


def test_silent_mention_form_is_stripped(client, fake_answer):
    r = client.post(
        "/zulip",
        json=_payload(data=f"@_**{BOT_NAME}** stille vraag"),
    )
    assert r.status_code == 200
    assert fake_answer["question"] == "stille vraag"


def test_empty_after_strip_returns_empty_body(client, fake_answer):
    """Just an @-mention with nothing else → Zulip 'no reply' convention."""
    r = client.post("/zulip", json=_payload(data=f"@**{BOT_NAME}**"))
    assert r.status_code == 200
    assert r.json() == {}
    assert "question" not in fake_answer  # answer not called


def _stream_payload(question="hoeveel?", subject="teelt-discussie", stream_id=42):
    return {
        "token": TOKEN,
        "bot_full_name": BOT_NAME,
        "data": f"@**{BOT_NAME}** {question}",
        "message": {
            "type": "stream",
            "stream_id": stream_id,
            "subject": subject,
        },
    }


def _dm_payload(question="hoeveel?", sender="alice@org"):
    return {
        "token": TOKEN,
        "bot_full_name": BOT_NAME,
        "data": question,  # DMs don't carry an @-mention
        "message": {
            "type": "private",
            "sender_email": sender,
        },
    }


@pytest.fixture()
def history_capturing_answer(monkeypatch):
    """answer.answer that records the `history` it was called with and
    returns a real-ish AnswerResult that exercises new_messages
    population."""
    calls: list[dict] = []

    def _fake(question, *, history=None, **_kwargs):
        calls.append({"question": question, "history": list(history or [])})
        return answer_mod.AnswerResult(
            text=f"reply to: {question}",
            sql=[f"SELECT '{question}' AS q"],
            model="fake/model",
            latency_ms=1,
            tokens=10,
            iterations=1,
            new_messages=[
                {"role": "user", "content": question},
                {"role": "assistant", "content": f"reply to: {question}"},
            ],
        )

    monkeypatch.setattr(answer_mod, "answer", _fake)
    return calls


def test_stream_topic_memory_persists_across_turns(client, history_capturing_answer):
    """Two posts to the same (stream_id, subject) → second sees first turn."""
    client.post("/zulip", json=_stream_payload(question="eerste vraag"))
    client.post("/zulip", json=_stream_payload(question="vervolg"))

    assert history_capturing_answer[0]["history"] == []
    second_history = history_capturing_answer[1]["history"]
    assert second_history == [
        {"role": "user", "content": "eerste vraag"},
        {"role": "assistant", "content": "reply to: eerste vraag"},
    ]


def test_different_topics_have_independent_history(client, history_capturing_answer):
    client.post("/zulip", json=_stream_payload(question="A1", subject="onderwerp-a"))
    client.post("/zulip", json=_stream_payload(question="B1", subject="onderwerp-b"))
    client.post("/zulip", json=_stream_payload(question="A2", subject="onderwerp-a"))

    # Third call is in topic A → should see A1, not B1.
    third_history = history_capturing_answer[2]["history"]
    assert any(m.get("content") == "A1" for m in third_history)
    assert not any(m.get("content") == "B1" for m in third_history)


def test_dm_memory_is_per_sender(client, history_capturing_answer):
    client.post("/zulip", json=_dm_payload(question="hoi", sender="alice@org"))
    client.post("/zulip", json=_dm_payload(question="en jij?", sender="alice@org"))
    client.post("/zulip", json=_dm_payload(question="hoi", sender="bob@org"))

    alice_second = history_capturing_answer[1]["history"]
    assert any(m.get("content") == "hoi" for m in alice_second)

    bob_first = history_capturing_answer[2]["history"]
    assert bob_first == []


def test_dm_history_does_not_leak_into_stream_topic(client, history_capturing_answer):
    client.post("/zulip", json=_dm_payload(question="dm-vraag", sender="alice@org"))
    client.post("/zulip", json=_stream_payload(question="stream-vraag"))

    assert history_capturing_answer[1]["history"] == []


def test_reset_clears_history_and_acks(client, history_capturing_answer):
    client.post("/zulip", json=_stream_payload(question="eerst"))
    r = client.post("/zulip", json=_stream_payload(question="reset"))
    assert r.status_code == 200
    assert "Context gewist" in r.json()["content"]
    # answer() should not have been called for the reset itself.
    assert [c["question"] for c in history_capturing_answer] == ["eerst"]

    # Subsequent question in the same topic starts fresh.
    client.post("/zulip", json=_stream_payload(question="opnieuw"))
    assert history_capturing_answer[-1]["history"] == []


def test_reset_with_leading_slash_also_works(client, history_capturing_answer):
    client.post("/zulip", json=_stream_payload(question="eerst"))
    r = client.post("/zulip", json=_stream_payload(question="/reset"))
    assert r.status_code == 200
    assert "Context gewist" in r.json()["content"]


def test_reset_is_a_no_op_when_no_conversation_key(client, history_capturing_answer):
    """Old-style payload without stream_id/subject still gets the ack."""
    r = client.post(
        "/zulip",
        json={
            "token": TOKEN,
            "bot_full_name": BOT_NAME,
            "data": f"@**{BOT_NAME}** reset",
            "message": {"type": "stream"},  # no stream_id/subject
        },
    )
    assert r.status_code == 200
    assert "Context gewist" in r.json()["content"]


def test_reply_includes_sql_fenced_block(client, history_capturing_answer):
    r = client.post("/zulip", json=_stream_payload(question="hoeveel?"))
    body = r.json()["content"]
    assert "```sql" in body
    assert "SELECT 'hoeveel?' AS q" in body


def test_reply_omits_sql_block_when_no_sql_was_run(client, monkeypatch):
    def _fake(question, *, history=None, **_):
        return answer_mod.AnswerResult(
            text="zonder query",
            sql=[],  # no tool calls
            model="fake/model",
            latency_ms=1,
            tokens=1,
            iterations=1,
            new_messages=[{"role": "user", "content": question}],
        )

    monkeypatch.setattr(answer_mod, "answer", _fake)
    r = client.post("/zulip", json=_stream_payload(question="kun je iets?"))
    assert "```sql" not in r.json()["content"]


def test_failed_answer_does_not_pollute_history(client, monkeypatch, history_capturing_answer):
    """If answer() returned an error, don't persist that turn — the
    next try should still start from the prior good state."""
    # First, one good turn.
    client.post("/zulip", json=_stream_payload(question="goed"))

    def _failing(question, *, history=None, **_):
        return answer_mod.AnswerResult(
            text="iets ging mis",
            error="RuntimeError: boom",
            model="fake/model",
            latency_ms=1,
            tokens=10,
            iterations=1,
            new_messages=[{"role": "user", "content": question}],
        )

    monkeypatch.setattr(answer_mod, "answer", _failing)
    client.post("/zulip", json=_stream_payload(question="fout"))

    # Restore the capturing fake to inspect what history the next turn sees.
    captured: list[dict] = []

    def _capture(question, *, history=None, **_):
        captured.append(list(history or []))
        return answer_mod.AnswerResult(
            text="ok",
            model="fake/model",
            latency_ms=1,
            tokens=1,
            iterations=1,
            new_messages=[{"role": "user", "content": question}],
        )

    monkeypatch.setattr(answer_mod, "answer", _capture)
    client.post("/zulip", json=_stream_payload(question="derde"))
    assert captured[0] == [
        {"role": "user", "content": "goed"},
        {"role": "assistant", "content": "reply to: goed"},
    ]


def test_extra_zulip_payload_fields_ignored(client, fake_answer):
    """Zulip evolves the payload; we don't break on new fields."""
    r = client.post(
        "/zulip",
        json={
            **_payload(),
            "trigger": "mention",
            "bot_email": "bot@org",
            "future_field": {"any": "thing"},
        },
    )
    assert r.status_code == 200
