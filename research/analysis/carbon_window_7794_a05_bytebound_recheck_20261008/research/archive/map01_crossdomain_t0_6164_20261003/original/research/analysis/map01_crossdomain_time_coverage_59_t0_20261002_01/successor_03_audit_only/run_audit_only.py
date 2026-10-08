import hashlib
import json
from pathlib import Path

from audit_only import audit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PREDECESSOR = ROOT / "successor_02"


def main():
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    package = freeze["package_sha256"]
    for name, expected in package.items():
        observed = hashlib.sha256((HERE / name).read_bytes()).hexdigest()
        if observed != expected:
            raise SystemExit(f"STOP_AUDIT_SOURCE_HASH_MISMATCH:{name}")
    pred_freeze_bytes = (PREDECESSOR / "FREEZE.json").read_bytes()
    pred_candidate_bytes = (PREDECESSOR / "candidate_result.json").read_bytes()
    pred_run_bytes = (PREDECESSOR / "RUN.json").read_bytes()
    for data, key in ((pred_freeze_bytes, "predecessor_freeze_sha256"),
                      (pred_candidate_bytes, "predecessor_candidate_result_sha256"),
                      (pred_run_bytes, "predecessor_run_sha256")):
        if hashlib.sha256(data).hexdigest() != freeze[key]:
            raise SystemExit(f"STOP_PREDECESSOR_HASH_MISMATCH:{key}")
    pred_freeze = json.loads(pred_freeze_bytes)
    pred_run = json.loads(pred_run_bytes)
    if (pred_freeze.get("allocation_id") != freeze["predecessor_allocation_id"]
            or pred_run.get("candidate", {}).get("invocations") != 1
            or pred_run.get("candidate", {}).get("exit_code") != 0):
        raise SystemExit("STOP_PREDECESSOR_CANDIDATE_RECEIPT_MISMATCH")
    sources = {}
    for name, item in freeze["inputs"].items():
        data = (ROOT / "inputs" / name).read_bytes()
        if hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise SystemExit(f"STOP_INPUT_HASH_MISMATCH:{name}")
        sources[name] = data.decode("utf-8")
    candidate = json.loads(pred_candidate_bytes)
    result = audit(candidate, sources, pred_freeze)
    result["allocation_id"] = freeze["allocation_id"]
    result["source_main_sha"] = freeze["source_main_sha"]
    result["predecessor_allocation_id"] = freeze["predecessor_allocation_id"]
    result["predecessor_candidate_result_sha256"] = freeze["predecessor_candidate_result_sha256"]
    result["source_sha256"] = {name: item["sha256"]
                               for name, item in freeze["inputs"].items()}
    (HERE / "audit_result.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["status"] ==
                     "PASS_AUDIT_CROSSDOMAIN_HOLD_REPRODUCED" else 1)


if __name__ == "__main__":
    main()
