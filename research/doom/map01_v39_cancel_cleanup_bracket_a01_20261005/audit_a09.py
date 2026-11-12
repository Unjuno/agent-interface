"""Independently verify nested cleanup evidence through session JSONL transport."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = HERE / "results/a09"
INPUT = HERE / "results/a08/published-events.jsonl"
SOURCES = {
    "session_map01_v12.py": ROOT / "research/doom/session_map01_v12.py",
    "map01_overlap_controller_v39.py": ROOT / "research/doom/map01_overlap_controller_v39.py",
    "a08_published_event.jsonl": INPUT,
    "run_a09.py": HERE / "run_a09.py",
    "audit_a09.py": HERE / "audit_a09.py",
}


def main():
    errors = []
    freeze = json.loads((HERE / "FREEZE-A09.json").read_text(encoding="utf-8"))
    for name, expected in freeze["sources"].items():
        if hashlib.sha256(SOURCES[name].read_bytes()).hexdigest() != expected["sha256"]:
            errors.append(f"frozen source mismatch: {name}")
    original = json.loads(INPUT.read_text(encoding="utf-8"))
    rows = {}
    for name in ("events.jsonl", "delivered.jsonl", "stdout.jsonl"):
        raw = (OUT / name).read_bytes()
        if not raw.endswith(b"\n") or raw.count(b"\n") != 1:
            errors.append(f"{name}: expected exactly one JSONL row")
        rows[name] = json.loads(raw)
    if rows["events.jsonl"] != rows["delivered.jsonl"] or rows["events.jsonl"] != rows["stdout.jsonl"]:
        errors.append("session JSONL logs and stdout differ")
    expected_written = dict(original, emit_ns=rows["events.jsonl"].get("emit_ns"))
    if rows["events.jsonl"] != expected_written:
        errors.append("session writer changed release fields beyond its emit timestamp")
    received = json.loads((OUT / "received-event.json").read_text(encoding="utf-8"))
    if received != rows["stdout.jsonl"]:
        errors.append("controller reader/wait changed decoded event")
    if received.get("owner_release") != original.get("owner_release"):
        errors.append("nested owner_release changed in transit")
    if len(received.get("owner_release", {}).get("per_key_release_measurements", [])) != 2:
        errors.append("expected two per-key release measurements after transport")
    if received.get("grants_input_authority") is not False:
        errors.append("transported release event grants authority")
    result = json.loads((OUT / "RESULT.json").read_text(encoding="utf-8"))
    for field, filename in (("writer_log_sha256", "events.jsonl"),
                            ("delivered_log_sha256", "delivered.jsonl"),
                            ("stdout_sha256", "stdout.jsonl"),
                            ("received_sha256", "received-event.json")):
        if result.get(field) != hashlib.sha256((OUT / filename).read_bytes()).hexdigest():
            errors.append(f"artifact hash mismatch: {field}")
    audit = {
        "run_id": freeze["run_id"],
        "disposition": "PASS_RECONSTRUCTED_SCOPED" if not errors else "FAIL_MISMATCH",
        "per_key_release_count": len(received.get("owner_release", {}).get("per_key_release_measurements", [])),
        "received_sha256": hashlib.sha256((OUT / "received-event.json").read_bytes()).hexdigest(),
        "errors": errors,
        "scope": "independent equality audit of exact session writer/controller reader-wait composition",
    }
    (OUT / "AUDIT.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n",
                                    encoding="utf-8", newline="\n")
    print(json.dumps(audit, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
