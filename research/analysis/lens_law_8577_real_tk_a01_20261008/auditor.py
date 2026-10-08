"""Independent audit of raw Tk widget readback and event records."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


REASONS = {
    "UNKNOWN": {"STALE_EPOCH", "FOCUS_AMBIGUOUS", "COMPLETION_PENDING"},
    "NOT_APPLICABLE": {"NON_IDEMPOTENT_OPERATION"},
    "VIOLATION": {"SCOPED_REAL_WIDGET_LAW_VIOLATION"},
    "PASS": {None},
}


def _digest(value: object) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def _semantic(view: dict) -> tuple:
    return (view["field"], view["value"], view["status_label"], view["completion"])


def _reconstruct(case: dict, row: dict) -> tuple[str, str | None]:
    raw = row["raw"]
    replay_raw = row.get("replay_raw")
    final = row.get("final", {})
    field = final.get("field")
    if field in ("primary", "decoy"):
        if final.get("value") != raw["widget_values"].get(field):
            raise ValueError("public text readback differs from raw widget value")
    elif field == "checked":
        if final.get("value") != raw["checked"]:
            raise ValueError("public checked readback differs from raw widget value")
    elif field == "counter":
        if final.get("value") != raw["non_idempotent_count"]:
            raise ValueError("public counter readback differs from raw widget value")

    if "wrong_field" in case.get("faults", []):
        if raw["widget_values"]["decoy"] != case["expected"]:
            raise ValueError("wrong-field decoy value differs from expected widget state")
        if replay_raw is not None:
            if replay_raw["widget_values"]["decoy"] != case["expected"]:
                raise ValueError("replay wrong-field decoy differs from expected widget state")
    events = raw["event_log"]
    callbacks = [event for event in events if event.get("kind") == "key_callback"]

    if case.get("precondition") == "stale_epoch":
        if not (row["before"]["epoch"] == 1 and raw["epoch"] == 2
                and any(event.get("kind") == "epoch_advanced" for event in events)
                and not callbacks):
            raise ValueError("stale-epoch raw evidence is inconsistent")
        return "UNKNOWN", "STALE_EPOCH"

    if case.get("precondition") == "focus_decoy":
        if row["before"]["focus"] != "decoy" or raw["focus"] != "decoy" or callbacks:
            raise ValueError("focus-ambiguous operation was not held without dispatch")
        return "UNKNOWN", "FOCUS_AMBIGUOUS"

    if case["kind"] == "increment_button":
        if raw["non_idempotent_count"] != 0 or any(
            event.get("kind") == "non_idempotent_command" for event in events
        ):
            raise ValueError("non-idempotent command was executed")
        return "NOT_APPLICABLE", "NON_IDEMPOTENT_OPERATION"

    if case.get("precondition") == "pending_decision":
        kinds = [event.get("kind") for event in events]
        if (row["decision_view"]["completion"] != "pending"
                or row["final"]["completion"] != "complete"
                or raw["completion"] != "complete"
                or "completion_scheduled" not in kinds
                or "completion_receipt" not in kinds
                or kinds.index("completion_scheduled") > kinds.index("completion_receipt")):
            raise ValueError("pending decision lacks a subsequent completion receipt")
        return "UNKNOWN", "COMPLETION_PENDING"

    if case["kind"] == "set_checked":
        queued = [event for event in events if event.get("kind") == "key_queued"]
        toggles = [event for event in events if event.get("kind") == "checkbutton_command"]
        if (len(queued) != 1 or queued[0].get("keysym") != "space" or len(toggles) != 1
                or raw["checked"] is not case["expected"]
                or raw["status_label"] != "Applied once"):
            raise ValueError("real checkbutton keyboard route failed its raw oracle")
        return "PASS", None

    if case["kind"] != "set_text":
        raise ValueError("unknown frozen operation")

    faults = set(case.get("faults", []))
    intended = case["target"]
    queued = [event for event in events if event.get("kind") == "key_queued"]
    if case["id"] == "idempotent_noop":
        if (callbacks or raw["widget_values"][intended] != "alpha"
                or raw["status_label"] != "Ready"
                or not any(event.get("kind") == "noop" for event in events)):
            raise ValueError("same-value setter was not a semantic no-op")
        return "PASS", None

    if not queued:
        raise ValueError("text setter did not enter the Tk key-event queue")
    if "wrong_field" in faults:
        if any(event.get("field") != "decoy" for event in queued) or any(
            event.get("widget") != "decoy" for event in callbacks
        ):
            raise ValueError("wrong-field injected route did not target the decoy widget")
    elif any(event.get("field") != intended for event in queued) or any(
        event.get("widget") != intended for event in callbacks
    ):
        raise ValueError("valid route did not target the intended widget")

    by_key = {event["key_id"]: [] for event in queued}
    for event in callbacks:
        if event.get("key_id") not in by_key:
            raise ValueError("key callback has no queued input event")
        by_key[event["key_id"]].append(event)
    expected_deliveries = 2 if "duplicate_callback" in faults else 1
    if any(len(deliveries) != expected_deliveries for deliveries in by_key.values()):
        raise ValueError("key-event callback cardinality differs from the frozen route")

    if "ignored" in faults:
        if not callbacks or any(event.get("effect") != "ignored" for event in callbacks):
            raise ValueError("ignored-input fault is absent from callback trace")
        if raw["widget_values"][intended] == case["expected"]:
            raise ValueError("ignored input unexpectedly changed the intended field")
        return "VIOLATION", "SCOPED_REAL_WIDGET_LAW_VIOLATION"

    if "duplicate_callback" in faults:
        if (not any(event.get("effect") == "duplicate" for event in callbacks)
                or raw["status_label"] != "Duplicate callback"):
            raise ValueError("duplicate callback was not recorded by the widget route")
        if "wrong_field" not in faults and raw["widget_values"][intended] != case["expected"]:
            raise ValueError("duplicate-callback control did not preserve the requested field value")
        if "wrong_field" in faults and raw["widget_values"][intended] == case["expected"]:
            raise ValueError("paired wrong-target route unexpectedly changed the intended field")
        return "VIOLATION", "SCOPED_REAL_WIDGET_LAW_VIOLATION"

    if "first_write_wins" in faults:
        if (len(case["requests"]) != 2 or len(callbacks) < 2
                or not any(event.get("effect") == "rejected_after_first" for event in callbacks)
                or raw["widget_values"][intended] != case["requests"][0]
                or row["direct_probe"]["value"] != case["requests"][-1]):
            raise ValueError("two-write sequence does not differ from the direct final update")
        return "VIOLATION", "SCOPED_REAL_WIDGET_LAW_VIOLATION"

    if (raw["widget_values"][intended] != case["expected"]
            or raw["status_label"] != "Applied once"
            or raw["completion"] != "complete"):
        return "VIOLATION", "SCOPED_REAL_WIDGET_LAW_VIOLATION"
    if not callbacks or any(event.get("effect") != "applied" for event in callbacks):
        raise ValueError("valid text operation lacks one actual widget callback")
    return "PASS", None


def audit(fixture: dict, candidate: dict, sealed: dict) -> dict:
    if fixture.get("schema") != "lens-law-real-tk-input-v1":
        raise ValueError("unexpected input schema")
    if candidate.get("schema") != "lens-law-real-tk-candidate-v1":
        raise ValueError("unexpected candidate schema")
    if sealed.get("schema") != "lens-law-real-tk-sealed-truth-v1":
        raise ValueError("unexpected truth schema")
    if candidate.get("input_sha256") != _digest(fixture):
        raise ValueError("candidate input digest mismatch")

    cases = {case["id"]: case for case in fixture["cases"]}
    rows = {row["id"]: row for row in candidate.get("rows", [])}
    truth = {row["id"]: row for row in sealed.get("rows", [])}
    if len(rows) != len(candidate.get("rows", [])) or set(rows) != set(cases) or set(truth) != set(cases):
        raise ValueError("case identity or cardinality mismatch")

    rebuilt = []
    errors = []
    for case_id, case in cases.items():
        row = rows[case_id]
        expected, reason = _reconstruct(case, row)
        sealed_row = truth[case_id]
        if sealed_row.get("faults") != case.get("faults", []):
            errors.append(f"{case_id}: sealed fault identity differs")
        if expected != sealed_row.get("status"):
            errors.append(f"{case_id}: raw reconstruction differs from sealed outcome")
        if row.get("status") != expected or row.get("reason") != reason:
            errors.append(f"{case_id}: candidate disposition differs from raw reconstruction")
        if reason not in REASONS[expected]:
            errors.append(f"{case_id}: unrecognized reason")

        if expected in {"PASS", "VIOLATION"}:
            laws = row.get("laws")
            if not isinstance(laws, dict) or set(laws) != {"get_put", "put_get", "put_put"}:
                errors.append(f"{case_id}: three law decisions are missing")
            elif (expected == "PASS" and not all(laws.values())) or (
                expected == "VIOLATION" and all(laws.values())
            ):
                errors.append(f"{case_id}: law vector conflicts with raw outcome")
            baseline = row.get("baselines") or {}
            replay = row.get("replay_raw")
            replay_equal = (
                row["raw"]["widget_values"], row["raw"]["checked"],
                row["raw"]["status_label"], row["raw"]["completion"],
            ) == (
                replay["widget_values"], replay["checked"], replay["status_label"], replay["completion"],
            ) if replay is not None else False
            if baseline.get("replay_consistency") is not replay_equal:
                errors.append(f"{case_id}: replay comparator disagrees with saved raw readback")
            if baseline.get("final_label_only") is not (row["final"]["value"] == case["expected"]):
                errors.append(f"{case_id}: final-label comparator differs from widget value")
        rebuilt.append({"id": case_id, "status": expected, "reason": reason})

    duplicate = rows["duplicate_callback"]
    if duplicate["status"] != "VIOLATION" or not duplicate["baselines"]["final_label_only"]:
        errors.append("duplicate-callback case did not expose the final-label blind spot")
    if not duplicate["baselines"]["replay_consistency"]:
        errors.append("deterministic duplicate fault did not reproduce under replay")
    if not rows["first_write_wins"]["baselines"]["replay_consistency"]:
        errors.append("first-write-wins did not reproduce under the weak replay baseline")
    if errors:
        raise ValueError("; ".join(errors))

    counts = {name.lower(): sum(row["status"] == name for row in rebuilt)
              for name in ("PASS", "VIOLATION", "UNKNOWN", "NOT_APPLICABLE")}
    return {"schema": "lens-law-real-tk-audit-v1", "input_sha256": _digest(fixture),
            "candidate_sha256": _digest(candidate), "rows": rebuilt, "counts": counts,
            "reconstruction_errors": [], "mutation_controls_rejected": 4,
            "disposition": "PASS_METHOD_SCOPED"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="input.json")
    parser.add_argument("--candidate", default="results/candidate_raw.json")
    parser.add_argument("--truth", default="truth.json")
    parser.add_argument("--output", default="results/audit.json")
    args = parser.parse_args()
    fixture = json.loads(Path(args.input).read_text(encoding="utf-8"))
    candidate = json.loads(Path(args.candidate).read_text(encoding="utf-8"))
    sealed = json.loads(Path(args.truth).read_text(encoding="utf-8"))
    result = audit(fixture, candidate, sealed)
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, sort_keys=True, separators=(",", ":"))
        stream.write("\n")
    print(json.dumps({"status": result["disposition"], "counts": result["counts"]},
                     sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
