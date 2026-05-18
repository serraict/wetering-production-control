"""Unit tests for zulip_chat.topics."""

from dataclasses import dataclass

from production_control.zulip_chat.topics import topic_name_for


@dataclass
class FakeLot:
    id: int


def test_topic_name_is_lot_id_as_string():
    assert topic_name_for(FakeLot(id=12345)) == "12345"


def test_topic_name_handles_string_id():
    @dataclass
    class StrLot:
        id: str

    assert topic_name_for(StrLot(id="abc")) == "abc"
