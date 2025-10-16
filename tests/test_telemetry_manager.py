from __future__ import annotations

from telemetry_manager import TelemetryManager


def test_subscribe_receives_all_events() -> None:
    telemetry = TelemetryManager()
    received: list[dict[str, object]] = []

    telemetry.subscribe(received.append)
    telemetry.record("foo", payload=1)

    assert len(received) == 1
    assert received[0]["type"] == "foo"
    assert received[0]["payload"] == 1


def test_subscribe_filters_by_event_type() -> None:
    telemetry = TelemetryManager()
    received: list[dict[str, object]] = []

    telemetry.subscribe(received.append, event_type="foo")
    telemetry.record("bar", payload=0)
    telemetry.record("foo", payload=2)

    assert len(received) == 1
    assert received[0]["payload"] == 2


def test_unsubscribe_via_returned_callback() -> None:
    telemetry = TelemetryManager()
    received: list[dict[str, object]] = []

    unsubscribe = telemetry.subscribe(received.append)
    telemetry.record("foo")
    unsubscribe()
    telemetry.record("foo")

    assert len(received) == 1


def test_clear_listeners_removes_filtered_bucket() -> None:
    telemetry = TelemetryManager()
    received: list[dict[str, object]] = []

    telemetry.subscribe(received.append, event_type="foo")
    telemetry.clear_listeners("foo")
    telemetry.record("foo", payload=42)

    assert received == []
