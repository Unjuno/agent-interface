"""Execute one deterministic CPU construction assay from fixed cases."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scorer_feedback_attribution_v1 import attribute_positive_events


HERE = Path(__file__).resolve().parent


def sample(time_ns):
    return {"schema": "independent-progress-sample-v2", "sample_ns": time_ns}


def positive_event(time_ns, sequence=1):
    return {
        "schema": "independent-progress-event-v2",
        "event_sequence": sequence,
        "observed_ns": time_ns,
        "kind": "KILL_COUNT_INCREASE",
        "polarity": "positive",
        "useful": True,
        "controller_visible": False,
    }


def interval(token, key, start, end, verified=True):
    return {
        "intent_token": token,
        "key": key,
        "admitted_ns": start,
        "release_sync_ns": end,
        "release_verified": verified,
    }


CASES = [
    ("one_intent_full_coverage", [100, 200], [interval("A", "ATTACK", 90, 150), interval("A", "FORWARD", 150, 210)], "TEMPORALLY_UNIQUE"),
    ("one_intent_partial_coverage", [100, 200], [interval("A", "ATTACK", 150, 210)], "UNRESOLVED"),
    ("two_intents_overlap", [100, 200], [interval("A", "ATTACK", 90, 180), interval("B", "FORWARD", 170, 210)], "AMBIGUOUS"),
    ("missing_coverage", [100, 200], [], "UNRESOLVED"),
    ("unverified_other_intent_may_persist", [100, 200], [interval("A", "ATTACK", 90, 210), interval("B", "FORWARD", 50, 80, False)], "AMBIGUOUS"),
    ("same_intent_gap", [100, 200], [interval("A", "ATTACK", 90, 140), interval("A", "FORWARD", 150, 210)], "UNRESOLVED"),
]


def main():
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    source_hashes = {}
    for relative, expected in freeze["sources"].items():
        path = HERE / relative
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise SystemExit(f"source hash mismatch: {relative}: {actual}")
        source_hashes[relative] = actual

    results = []
    for name, times, intervals, expected in CASES:
        output = attribute_positive_events(
            [sample(time_ns) for time_ns in times],
            [positive_event(times[-1])],
            intervals,
        )[0]
        results.append({"case": name, "expected": expected, "observed": output})
    result = {
        "schema": "scorer-feedback-attribution-t0-v1",
        "status": "PASS_SCOPED" if all(r["expected"] == r["observed"]["status"] for r in results) else "FAIL",
        "source_hashes": source_hashes,
        "case_count": len(results),
        "cases": results,
        "causation_claim": "NOT_ESTABLISHED",
        "scope": "synthetic CPU construction only; no retained live outcomes, game, model, GUI, input, or controller integration",
    }
    output = HERE / "RESULT.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["status"] != "PASS_SCOPED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
