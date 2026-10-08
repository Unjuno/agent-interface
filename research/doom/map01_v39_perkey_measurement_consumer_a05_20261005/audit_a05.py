from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
A04 = HERE / "SOURCE/A04"

class AuditFailure(ValueError):
    pass

def need(ok: bool, message: str) -> None:
    if not ok:
        raise AuditFailure(message)

def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("a04_audit_source", path)
    if spec is None or spec.loader is None:
        raise AuditFailure("cannot load frozen A04 audit")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def audit_result(raw: dict, result: dict, a03_oracle) -> dict:
    count = result.get("candidate_invocations")
    need(type(count) is int and count == 1,
         "candidate_invocations must be exact integer 1")
    prior = load_module(A04 / "audit.py")
    return prior.audit_result(raw, result, a03_oracle)

def verify_frozen_a04() -> tuple[dict, dict, dict, object]:
    freeze_bytes = (A04 / "FREEZE.json").read_bytes()
    freeze = json.loads(freeze_bytes)
    for relative, expected in freeze["source_sha256"].items():
        actual = hashlib.sha256((A04 / relative).read_bytes()).hexdigest()
        need(actual == expected, f"A04 frozen source mismatch: {relative}")
    raw_bytes = (A04 / "SOURCE/BRIDGE_RAW_A01.json").read_bytes()
    need(hashlib.sha256(raw_bytes).hexdigest() == freeze["input_sha256"],
         "A04 frozen input mismatch")
    result_bytes = (A04 / "RESULT.json").read_bytes()
    result = json.loads(result_bytes)
    need(result.get("input_sha256") == freeze["input_sha256"], "A04 result input mismatch")
    need(result.get("freeze_sha256") == hashlib.sha256(freeze_bytes).hexdigest(),
         "A04 result freeze mismatch")
    source_spec = importlib.util.spec_from_file_location(
        "a03_auditor", A04 / "SOURCE/audit_a03.py")
    need(source_spec is not None and source_spec.loader is not None,
         "cannot load frozen A03 auditor")
    source_module = importlib.util.module_from_spec(source_spec)
    source_spec.loader.exec_module(source_module)
    return freeze, json.loads(raw_bytes), result, source_module.independently_reconstruct

def main() -> None:
    freeze_bytes = (HERE / "FREEZE.json").read_bytes()
    freeze = json.loads(freeze_bytes)
    for relative, expected in freeze["source_sha256"].items():
        actual = hashlib.sha256((HERE / relative).read_bytes()).hexdigest()
        need(actual == expected, f"A05 frozen source mismatch: {relative}")
    a04_freeze, raw, result, oracle = verify_frozen_a04()
    verdict = audit_result(raw, result, oracle)
    audit = {
        "schema": "map01_v39_perkey_measurement_consumer_a05_audit_v1",
        "disposition": "PASS_A04_INVOCATION_COUNT_EXACT_TYPE_GUARD_SCOPED",
        "a04_run_id": a04_freeze["run_id"],
        "a04_result_sha256": hashlib.sha256((A04 / "RESULT.json").read_bytes()).hexdigest(),
        "a04_freeze_sha256": hashlib.sha256((A04 / "FREEZE.json").read_bytes()).hexdigest(),
        "candidate_invocations": 1,
        "authority_granted": False,
        "application_effect_observed": False,
        "scope": "audit metadata exact-type mutation only; retained A04 candidate not rerun",
        "a04_disposition": verdict["disposition"],
    }
    (HERE / "AUDIT.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n",
                                     encoding="utf-8", newline="\n")
    print(json.dumps(audit, sort_keys=True))

if __name__ == "__main__":
    main()
