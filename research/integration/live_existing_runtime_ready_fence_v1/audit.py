#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_BLOBS = {
    "interactive_v27.py": "9a012c825bcdc995a87185d423ecc496dc399094",
    "event_socket_v11.py": "fe71be94c9284af0ae7c0b4db0b47dd8b1a86522",
    "session_v16.py": "c188b3653ef4bec9b1a846296b003b0415f3f173",
}


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    header = b"blob " + str(len(data)).encode("ascii") + bytes([0])
    return hashlib.sha1(header + data).hexdigest()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--formal", type=Path, required=True)
    parser.add_argument("--experiment-dir", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    args = parser.parse_args()

    errors = []
    details = []
    invocation = json.loads((args.formal / "FORMAL_INVOCATION.json").read_text())
    if invocation.get("formal_invocations") != 1:
        errors.append("formal invocation count")

    schedule = json.loads((args.experiment_dir / "schedule.json").read_text())
    live = args.artifact_root / "source/research/live_control"
    core_blobs = {name: git_blob_sha(live / name) for name in EXPECTED_BLOBS}
    if core_blobs != EXPECTED_BLOBS:
        errors.append("core source blobs")

    freeze = json.loads((args.experiment_dir / "FREEZE.json").read_text())
    for name, expected in freeze["sha256"].items():
        if sha256(args.experiment_dir / name) != expected:
            errors.append("frozen sha " + name)

    baseline_count = 0
    candidate_count = 0
    for spec in schedule["cases"]:
        case_id = spec["case_id"]
        case_path = args.formal / case_id / "case.json"
        case_errors = []
        if not case_path.exists():
            errors.append("missing " + case_id)
            continue

        result = json.loads(case_path.read_text())
        if result.get("policy") != spec["policy"] or result.get("seed") != spec["seed"]:
            case_errors.append("schedule identity")

        ready = result.get("ready_event")
        initial = result.get("initial_observation")
        clock_event = result.get("clock_event")
        owners = result.get("owner_events", [])
        if not ready or ready.get("decision_evidence_schema", {}).get("authority") != "none; ordinary admission required":
            case_errors.append("ready authority/schema")
        if not initial:
            case_errors.append("initial observation missing")
        if result.get("wrapper_exit") != 0:
            case_errors.append("wrapper exit")
        if result.get("clock", {}).get("authority") != "none":
            case_errors.append("clock result authority")
        if result.get("source_blobs") != EXPECTED_BLOBS:
            case_errors.append("case source blobs")

        runtime_events = load_jsonl(args.formal / case_id / "runtime/events.jsonl")
        if any(event.get("event") in {"accepted", "step", "terminal"} for event in runtime_events):
            case_errors.append("task program event observed")

        releases = [record for record in owners if record.get("event") == "owner_release"]
        if not releases:
            case_errors.append("owner release missing")
        else:
            release = releases[-1]
            if not release.get("verified") or release.get("keys_down") or release.get("buttons_down"):
                case_errors.append("owner not neutral")

        if spec["policy"] == "endpoint_only":
            baseline_count += 1
            ready_ns = ready.get("emit_started_ns", -1) if ready else -1
            if not (result.get("endpoint_receipt_ns", 0) < ready_ns):
                case_errors.append("baseline endpoint not before ready")
            if result.get("clock", {}).get("status") != "timeout":
                case_errors.append("baseline clock not timeout")
        else:
            candidate_count += 1
            trace = result.get("ready_trace") or {}
            if result.get("clock", {}).get("status") != "boundary":
                case_errors.append("candidate clock not boundary")
            values = [
                ready.get("emit_started_ns") if ready else None,
                trace.get("ready_append_ns"),
                trace.get("endpoint_publish_ns"),
                initial.get("emit_started_ns") if initial else None,
                clock_event.get("emit_started_ns") if clock_event else None,
            ]
            if any(value is None for value in values) or not (
                values[0] <= values[1] <= values[2] < values[3] <= values[4]
            ):
                case_errors.append("candidate ordering")

        if case_errors:
            errors.extend(case_id + ": " + error for error in case_errors)
        details.append(
            {
                "case_id": case_id,
                "policy": spec["policy"],
                "clock_status": result.get("clock", {}).get("status"),
                "errors": case_errors,
            }
        )

    if baseline_count != 3:
        errors.append("baseline count")
    if candidate_count != 3:
        errors.append("candidate count")

    decision = "FAIL_AUDIT" if errors else "PASS_EXISTING_RUNTIME_READY_FENCE_SCOPED"
    output = {
        "decision": decision,
        "errors": errors,
        "details": details,
        "formal_invocations": invocation.get("formal_invocations"),
        "formal_reruns": 0,
        "core_blobs": core_blobs,
    }
    (args.formal / "AUDIT.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"decision": decision, "errors": len(errors)}, sort_keys=True))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
