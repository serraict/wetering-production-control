"""Tests for opcua.healthcheck: fresh→0, stale→1 with role named, missing→1."""

from __future__ import annotations

import os
import time

import pytest

from production_control.opcua import healthcheck, heartbeat


@pytest.fixture(autouse=True)
def _isolated_heartbeat_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("VINEAPP_OPCUA_HEARTBEAT_DIR", str(tmp_path))
    monkeypatch.delenv("VINEAPP_OPCUA_HEARTBEAT_MAX_AGE_S", raising=False)
    return tmp_path


def _touch(role: str, age_s: float = 0.0) -> None:
    path = heartbeat.path_for(role)
    path.touch()
    if age_s:
        mtime = time.time() - age_s
        os.utime(path, (mtime, mtime))


def test_check_returns_empty_when_both_fresh():
    _touch("plc")
    _touch("leuze")
    assert healthcheck.check() == []


def test_check_reports_missing_file():
    _touch("plc")
    problems = healthcheck.check()
    assert len(problems) == 1
    assert "leuze" in problems[0]
    assert "missing" in problems[0]


def test_check_reports_stale_file(monkeypatch):
    monkeypatch.setenv("VINEAPP_OPCUA_HEARTBEAT_MAX_AGE_S", "5")
    _touch("plc")
    _touch("leuze", age_s=120)
    problems = healthcheck.check()
    assert len(problems) == 1
    assert "leuze" in problems[0]
    assert "stale" in problems[0]


def test_check_reports_both_when_both_bad(monkeypatch):
    monkeypatch.setenv("VINEAPP_OPCUA_HEARTBEAT_MAX_AGE_S", "5")
    _touch("plc", age_s=120)
    # leuze missing
    problems = healthcheck.check()
    assert len(problems) == 2
    assert any("plc" in p and "stale" in p for p in problems)
    assert any("leuze" in p and "missing" in p for p in problems)


def test_main_exit_zero_when_healthy():
    _touch("plc")
    _touch("leuze")
    assert healthcheck.main() == 0


def test_main_exit_one_when_unhealthy(capsys):
    _touch("plc")
    # leuze missing
    assert healthcheck.main() == 1
    captured = capsys.readouterr()
    assert "unhealthy" in captured.err
    assert "leuze" in captured.err
