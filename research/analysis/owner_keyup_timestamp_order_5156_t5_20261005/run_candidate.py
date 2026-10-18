"""Run one deterministic ordering corpus through a selected analyzer source."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def run(source_path, phase):
    source_path = Path(source_path)
    cases_path = HERE / "cases.json"
    cases = json.loads(cases_path.read_text(encoding="utf-8"))["cases"]
    spec = importlib.util.spec_from_file_location(f"candidate_{phase}", source_path)
    candidate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(candidate)
    results = []
    for case in cases:
        events = [
            {"event": "input_admission", "intent_token": case["id"], "key": "Up",
             "admitted_ns": case["admitted_ns"], "input_ack_ns": case["input_ack_ns"]},
            {"event": "input_release_transition", "intent_token": case["id"],
             "operation": "up", "key": "Up",
             "release_call_started_ns": case["release_call_started_ns"],
             "release_call_returned_ns": case["release_call_returned_ns"],
             "owner_transition_verified": True},
        ]
        result = candidate.analyze(events)
        results.append({"id": case["id"], "expected_ready": case["expected_ready"],
                        "measurement_ready": result["measurement_ready"],
                        "hold_count": result["hold_count"],
                        "invalid_release_count": result["invalid_release_count"],
                        "unmatched_admission_count": result["unmatched_admission_count"]})
    return {"schema": "owner-keyup-timestamp-order-raw-v1", "phase": phase,
            "base_commit": "e561b25b700680df4e6ffd2b92faf1dde1682ef7",
            "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
            "cases_sha256": hashlib.sha256(cases_path.read_bytes()).hexdigest(),
            "results": results}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--phase", choices=("baseline", "repaired"), required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    raw = run(args.source, args.phase)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"phase": args.phase, "case_count": len(raw["results"]),
                      "source_sha256": raw["source_sha256"], "out": str(args.out)}))


if __name__ == "__main__":
    main()
