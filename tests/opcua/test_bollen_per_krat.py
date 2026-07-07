"""Unit tests for the bollen-per-krat picklist lookup."""

from types import SimpleNamespace

import pytest

from production_control.opcua.protocol.scan_cycle import (
    DEFAULT_BOLLEN_PER_KRAT,
    bollen_per_krat_for,
)


class FakeRepository:
    def __init__(self, record=None, exc=None):
        self.record = record
        self.exc = exc
        self.requested_ids = []

    def get_by_id(self, id):
        self.requested_ids.append(id)
        if self.exc is not None:
            raise self.exc
        return self.record


def record(bollen, bakken):
    return SimpleNamespace(aantal_bollen=bollen, aantal_bakken=bakken)


def test_integer_division_of_bollen_over_bakken():
    repo = FakeRepository(record(1000.0, 3.0))
    assert bollen_per_krat_for(27978, repository=repo) == 333
    assert repo.requested_ids == [27978]


def test_exact_division():
    assert bollen_per_krat_for(1, repository=FakeRepository(record(1300.0, 2.0))) == 650


@pytest.mark.parametrize(
    "rec",
    [
        None,  # unknown partij
        record(None, 3.0),
        record(1000.0, None),
        record(0.0, 3.0),
        record(1000.0, 0.0),  # zero kratten: no division
    ],
)
def test_missing_or_null_data_returns_default(rec):
    assert bollen_per_krat_for(1, repository=FakeRepository(rec)) == DEFAULT_BOLLEN_PER_KRAT


def test_nan_fields_return_default():
    assert (
        bollen_per_krat_for(1, repository=FakeRepository(record(float("nan"), 3.0)))
        == DEFAULT_BOLLEN_PER_KRAT
    )


def test_result_below_one_returns_default():
    # fewer bulbs than crates → integer division yields 0
    assert (
        bollen_per_krat_for(1, repository=FakeRepository(record(2.0, 3.0)))
        == DEFAULT_BOLLEN_PER_KRAT
    )


def test_lookup_error_returns_default():
    repo = FakeRepository(exc=RuntimeError("dremio down"))
    assert bollen_per_krat_for(1, repository=repo) == DEFAULT_BOLLEN_PER_KRAT


def test_default_overridable_via_env(monkeypatch):
    monkeypatch.setenv("VINEAPP_BOLLEN_PER_KRAT_DEFAULT", "450")
    assert bollen_per_krat_for(1, repository=FakeRepository(None)) == 450


def test_invalid_env_default_falls_back_to_builtin(monkeypatch):
    monkeypatch.setenv("VINEAPP_BOLLEN_PER_KRAT_DEFAULT", "many")
    assert bollen_per_krat_for(1, repository=FakeRepository(None)) == DEFAULT_BOLLEN_PER_KRAT


def test_repository_construction_failure_returns_default(monkeypatch):
    # No injected repository + unusable connection string → default, no raise.
    monkeypatch.setenv("VINEAPP_DB_CONNECTION", "")
    assert bollen_per_krat_for(1) == DEFAULT_BOLLEN_PER_KRAT
