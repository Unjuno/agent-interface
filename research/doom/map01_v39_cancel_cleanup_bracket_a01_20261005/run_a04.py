"""Replay retained cleanup evidence through the exact v39 release receipt method."""
import ast
import hashlib
import json
import sys
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FREEZE_PATH = HERE / "FREEZE-A04.json"
OUT = HERE / "results" / "a04"
GUARD_SOURCE = ROOT / "research" / "live_control" / "running_action_guard_v3.py"
INPUT = HERE / "results" / "a03" / "candidate-events.jsonl"


def main():
    if OUT.exists():
        raise SystemExit("STOP: A04 candidate output already exists")
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    for name, record in freeze["sources"].items():
        path = {"running_action_guard_v3.py": GUARD_SOURCE,
                "a03_candidate_events.jsonl": INPUT,
                "run_a04.py": HERE / "run_a04.py",
                "audit_a04.py": HERE / "audit_a04.py"}[name]
        if hashlib.sha256(path.read_bytes()).hexdigest() != record["sha256"]:
            raise SystemExit(f"STOP: frozen source mismatch: {name}")
    if sys.version.split()[0] != freeze["python_version"]:
        raise SystemExit("STOP: Python runtime mismatch")

    tree = ast.parse(GUARD_SOURCE.read_bytes())
    method = next(node for node in ast.walk(tree)
                  if isinstance(node, ast.FunctionDef)
                  and node.name == "record_input_released")
    namespace = {"deepcopy": deepcopy}
    code = compile(ast.Module(body=[method], type_ignores=[]),
                   str(GUARD_SOURCE) + "::record_input_released", "exec")
    exec(code, namespace)

    class ReceiptHarness:
        record_input_released = namespace["record_input_released"]

        def receipt(self):
            return {"early_releases": deepcopy(self.early_releases),
                    "current_input_authority": False}

    rows = [json.loads(line) for line in INPUT.read_text(encoding="utf-8").splitlines() if line]
    cleanup = next(row for row in rows if row.get("event") == "owner_release")
    down_event = next(row for row in rows if row.get("event") == "input_admission")
    source_result = json.loads((HERE / "results" / "a03" / "RESULT.json").read_text())
    token = down_event["physical_key_measurement"]["bracket"]["intent_token"]
    event = {
        "event": "input_released",
        "id": "hold-a03",
        "intent_token": token,
        "owner_release": cleanup,
        "published_ns": source_result["finished_ns"],
        "program_terminal_pending": True,
        "grants_input_authority": False,
    }
    harness = ReceiptHarness()
    harness.guard = SimpleNamespace(
        state="CANCEL_REQUIRED",
        cancellation={"requested_ns": source_result["started_ns"]},
    )
    harness.active_intent = {"id": event["id"], "intent_token": token}
    harness.early_releases = []
    receipt = harness.record_input_released(event)
    encoded = json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode()
    OUT.mkdir(parents=True)
    (OUT / "release-receipt.json").write_bytes(encoded + b"\n")
    result = {
        "run_id": freeze["run_id"],
        "status": "PASS_CLEANUP_MEASUREMENT_RECEIPT_FLOW_SCOPED",
        "input_sha256": hashlib.sha256(INPUT.read_bytes()).hexdigest(),
        "receipt_sha256": hashlib.sha256(encoded + b"\n").hexdigest(),
        "early_release_count": len(receipt["early_releases"]),
        "per_key_release_count": len(receipt["early_releases"][0]["owner_release"]["per_key_release_measurements"]),
        "current_input_authority": receipt["current_input_authority"],
        "exact_guard_method_source_sha256": freeze["sources"]["running_action_guard_v3.py"]["sha256"],
        "scope": "source-extracted receipt method replay over retained fake-display cleanup; no runtime or game",
    }
    (OUT / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
