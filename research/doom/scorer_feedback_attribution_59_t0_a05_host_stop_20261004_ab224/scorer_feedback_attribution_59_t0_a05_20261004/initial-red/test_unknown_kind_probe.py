"""T0 A05 probe: unknown kind must not be promoted to a useful envelope."""
from scorer_feedback_attribution_v3 import attribute_positive_events


def main():
    samples = [
        {"schema": "independent-progress-sample-v2", "sample_ns": 100},
        {"schema": "independent-progress-sample-v2", "sample_ns": 200},
    ]
    event = {
        "schema": "independent-progress-event-v2",
        "event_sequence": 1,
        "observed_ns": 200,
        "kind": "BANANA_UNREGISTERED",
        "polarity": "positive",
        "useful": True,
        "controller_visible": False,
    }
    interval = {
        "intent_token": "intent-a",
        "key": "ATTACK",
        "admitted_ns": 90,
        "release_sync_ns": 210,
        "release_verified": True,
    }
    try:
        rows = attribute_positive_events(samples, [event], [interval])
    except ValueError:
        return 0
    assert rows[0]["status"] == "UNRESOLVED", rows[0]
    assert rows[0]["intent_token"] is None, rows[0]
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
