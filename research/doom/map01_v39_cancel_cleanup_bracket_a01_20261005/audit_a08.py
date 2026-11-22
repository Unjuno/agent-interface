"""Independently verify cleanup payload identity through the A05 artifacts."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "results/a08"
INPUT = HERE / "results/a03/candidate-events.jsonl"
SOURCES = {
    "lease_cause_v1.py": HERE.parents[2] / "research/live_control/lease_cause_v1.py",
    "lease_cause_v2.py": HERE.parents[2] / "research/live_control/lease_cause_v2.py",
    "lease_release_v1.py": HERE.parents[2] / "research/live_control/lease_release_v1.py",
    "executor_v12.py": HERE.parents[2] / "research/live_control/executor_v12.py",
    "map01_overlap_controller_v39.py": HERE.parents[2] / "research/doom/map01_overlap_controller_v39.py",
    "running_action_guard_v3.py": HERE.parents[2] / "research/live_control/running_action_guard_v3.py",
    "a03_candidate_events.jsonl": INPUT,
    "a03_result.json": HERE / "results/a03/RESULT.json",
    "run_a08.py": HERE / "run_a08.py",
    "audit_a08.py": HERE / "audit_a08.py",
}


def main():
    errors = []
    freeze = json.loads((HERE / "FREEZE-A08.json").read_text(encoding="utf-8"))
    for name, expected in freeze["sources"].items():
        if hashlib.sha256(SOURCES[name].read_bytes()).hexdigest() != expected["sha256"]:
            errors.append(f"frozen source mismatch: {name}")
    rows = [json.loads(line) for line in INPUT.read_text(encoding="utf-8").splitlines() if line]
    expected = next(row for row in rows if row.get("event") == "owner_release")
    published = json.loads((OUT / "published-events.jsonl").read_text(encoding="utf-8"))
    handoff = json.loads((OUT / "controller-handoff.json").read_text(encoding="utf-8"))
    receipt = json.loads((OUT / "release-receipt.json").read_text(encoding="utf-8"))
    terminal = json.loads((OUT / "terminal-receipt.json").read_text(encoding="utf-8"))
    if published.get("event") != "input_released" or published.get("owner_release") != expected:
        errors.append("executor publication did not preserve exact owner cleanup")
    if handoff != published:
        errors.append("controller selected handoff differs from published event")
    early = receipt.get("early_releases", [])
    if len(early) != 1 or early[0] != published:
        errors.append("guard receipt did not preserve full published event")
    if len(expected.get("per_key_release_measurements", [])) != 2:
        errors.append("A03 source cleanup does not contain two per-key measurements")
    for measurement in expected.get("per_key_release_measurements", []):
        if (measurement.get("actuation_id") is None or
                measurement.get("classification") != "CONFIRMED_PHYSICAL_UP" or
                measurement.get("bracket", {}).get("physical_up_interval") is None):
            errors.append("source per-key measurement lacks expected release evidence")
    if published.get("grants_input_authority") is not False:
        errors.append("publisher event grants input authority")
    if receipt.get("current_input_authority") is not False:
        errors.append("release receipt grants input authority")
    if receipt.get("program_terminal_pending") is not True:
        errors.append("release receipt did not retain terminal-pending state")
    if terminal.get("program_terminal_pending") is not False:
        errors.append("terminal receipt did not close pending lifecycle")
    if hashlib.sha256(INPUT.read_bytes()).hexdigest() != freeze["sources"]["a03_candidate_events.jsonl"]["sha256"]:
        errors.append("A03 raw input hash differs from freeze")
    result = json.loads((OUT / "RESULT.json").read_text(encoding="utf-8"))
    for field, filename in (("published_event_sha256", "published-events.jsonl"),
                            ("controller_handoff_sha256", "controller-handoff.json"),
                            ("release_receipt_sha256", "release-receipt.json")):
        if result.get(field) != hashlib.sha256((OUT / filename).read_bytes()).hexdigest():
            errors.append(f"result artifact hash mismatch: {field}")
    audit = {
        "run_id": freeze["run_id"],
        "disposition": "PASS_RECONSTRUCTED_SCOPED" if not errors else "FAIL_MISMATCH",
        "per_key_release_count": len(expected.get("per_key_release_measurements", [])),
        "published_event_sha256": hashlib.sha256((OUT / "published-events.jsonl").read_bytes()).hexdigest(),
        "release_receipt_sha256": hashlib.sha256((OUT / "release-receipt.json").read_bytes()).hexdigest(),
        "errors": errors,
        "scope": "independent exact-data equality and authority/lifecycle audit; source composition is not runtime execution",
    }
    (OUT / "AUDIT.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n",
                                    encoding="utf-8", newline="\n")
    print(json.dumps(audit, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
