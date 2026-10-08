import hashlib
import json
from pathlib import Path

from audit_v2 import audit_raw

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent


def jsonl_rows(text):
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def ait_rows(text):
    rows = []
    for line in text.splitlines():
        marker = line.find("AIT {")
        if marker >= 0:
            row = json.loads(line[marker + 4:])
            if isinstance(row, dict) and isinstance(row.get("tiles"), list):
                rows.append(row)
    return rows


def ait_transitions(rows):
    states = [tuple((tile.get("id"), tile.get("road"), tile.get("owner"))
                    for tile in row["tiles"]) for row in rows]
    return ([i for i in range(1, len(states)) if states[i] != states[i - 1]],
            len(set(states)))


def run():
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    expected = freeze["auditor_source_sha256"]
    observed = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if observed != expected:
        raise SystemExit("STOP_AUDITOR_SOURCE_HASH_MISMATCH")
    for name in ("audit_v2.py", "run_audit_v2.py", "candidate_v2.py",
                 "run_candidate_v2.py"):
        digest = hashlib.sha256((HERE / name).read_bytes()).hexdigest()
        if digest != freeze["package_sha256"][name]:
            raise SystemExit(f"STOP_FROZEN_PACKAGE_HASH_MISMATCH:{name}")
    sources = {}
    for name, item in freeze["inputs"].items():
        data = (PARENT / "inputs" / name).read_bytes()
        if hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise SystemExit(f"STOP_INPUT_HASH_MISMATCH:{name}")
        sources[name] = data.decode("utf-8")
    candidate = json.loads((HERE / "candidate_result.json").read_text(encoding="utf-8"))
    result = audit_raw(candidate, sources, freeze, jsonl_rows, ait_rows, ait_transitions)
    result["allocation_id"] = freeze["allocation_id"]
    result["source_main_sha"] = freeze["source_main_sha"]
    result["auditor_source_sha256"] = observed
    result["source_sha256"] = {name: item["sha256"]
                               for name, item in freeze["inputs"].items()}
    (HERE / "audit_result.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["status"] ==
                     "PASS_AUDIT_CROSSDOMAIN_HOLD_REPRODUCED" else 1)


if __name__ == "__main__":
    run()
