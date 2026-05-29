"""Tests for the Zulip-facing FastAPI app (bot.server)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from production_control.bot import answer as answer_mod
from production_control.bot import server


TOKEN = "test-token-abc"
BOT_NAME = "Insights Bot"


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
