"""Independent live X11 and decision oracle; imports no v2 candidate adapter."""
import collections
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
V1 = HERE.parent / "o3_live_receipt_transport_2692_v1"
sys.path.insert(0, str(V1))
from independent_oracle import verify_x11, frame_path


def lines(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines()]


def main(out_arg):
    root = Path(out_arg)
    manifest = json.loads((root / "manifest.json").read_text())
    schedule = json.loads((HERE / "case_schedule.json").read_text())
    raw = lines(root / "raw_events.jsonl")
    deliveries = lines(root / "deliveries.jsonl")
    decisions = lines(root / "decisions.jsonl")
    errors = []
    if not (len(raw) == len(deliveries) == len(decisions) == schedule["expected_rows"]):
        errors.append("denominator_mismatch")
    raw_by_id = {row["capture_id"]: row for row in raw}
    if len(raw_by_id) != len(raw):
        errors.append("duplicate_capture_id")
    live_checks = 0
    for event in raw:
        surface = event["surface"]
        identity = manifest["surfaces"][surface]
        try:
            verify_x11(manifest["display"], identity["xid"], identity["pid"],
                       identity["title"], event, root)
            live_checks += 1
        except Exception as exc:
            errors.append(f"live_oracle:{event['capture_id']}:{type(exc).__name__}:{exc}")
    counts = collections.Counter()
    admitted = 0
    negative_admitted = 0
    for delivery, decision in zip(deliveries, decisions):
        case = delivery["case"]
        counts[case] += 1
        event = raw_by_id.get(delivery["source_capture_id"])
        if event is None:
            errors.append(f"missing_source:{case}")
            continue
        req = delivery["request"]
        if req["observation_id"] != event["request"]["observation_id"] or req["intent_epoch"] != event["request"]["intent_epoch"]:
            errors.append(f"request_lineage:{case}")
        expected = case == "complete_current"
        if decision.get("admitted") is not expected:
            errors.append(f"admission:{case}:{decision.get('admitted')}")
        if decision.get("model_escalation_eligible") is not (not expected):
            errors.append(f"escalation:{case}")
        if decision.get("action_emissions") != 0:
            errors.append(f"action_emission:{case}")
        if case != "complete_current" and decision.get("reason") == "admitted":
            errors.append(f"malformed_control_silently_admitted:{case}")
        admitted += int(bool(decision.get("admitted")))
        if case != "complete_current":
            negative_admitted += int(bool(decision.get("admitted")))
    expected_counts = {case: 4 for case in schedule["cases"]}
    if counts != expected_counts:
        errors.append(f"case_counts:{dict(counts)}")
    if len({event["request"]["observation_id"] for event in raw}) != len(raw):
        errors.append("observation_ids_not_unique")
    if len({event["request"]["intent_epoch"] for event in raw}) != len(raw):
        errors.append("intent_epochs_not_unique")
    if manifest.get("adapter_module") != "adapter" or manifest.get("adapter_calls") != len(decisions):
        errors.append("candidate_adapter_invocation_unproven")
    if manifest["actual_rows"] != len(raw) or manifest["model_calls"] != 0 or manifest["input_events"] != 0 or manifest["action_emissions"] != 0:
        errors.append("manifest_boundary_or_denominator")
    result = {"schema": "issue-2692-live-clock-typeguard-independent-audit-v2",
              "decision": "PASS_LIVE_MALFORMED_CLOCK_FAIL_OPEN_SCOPED" if not errors else "FAIL_TYPEGUARD_OR_INTEGRITY",
              "raw_capture_rows": len(raw), "delivered_rows": len(deliveries),
              "x11_independent_checks": live_checks, "case_counts": dict(counts),
              "admitted": admitted, "negative_admitted": negative_admitted,
              "model_calls": manifest["model_calls"], "input_events": manifest["input_events"],
              "action_emissions": manifest["action_emissions"], "errors": errors}
    (root / "AUDIT_RESULT.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main(sys.argv[1])
