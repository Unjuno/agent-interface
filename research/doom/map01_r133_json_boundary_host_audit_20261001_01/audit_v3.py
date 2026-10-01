"""Auditor-only v3 entrypoint using the independent exact-payload oracle."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import audit_v2

HERE = Path(__file__).resolve().parent
UPSTREAM = HERE.parent / "map01_r133_recovery_coast_t1_v1" / "decision_rule_construction_v2" / "adjudicator.py"
V3_FREEZE = HERE / "FREEZE_V3.json"
V2_FREEZE = HERE / "FREEZE_V2.json"
FREEZE = HERE / "FREEZE.json"
OUT = HERE / "results" / "construction-01"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def reseal(raw, run):
    raw_bytes = (json.dumps(raw, sort_keys=True, indent=2) + "\n").encode()
    return raw_bytes, dict(run, raw_sha256=sha(raw_bytes))


def run_audit():
    v3_freeze = json.loads(V3_FREEZE.read_text(encoding="utf-8"))
    v2_freeze = json.loads(V2_FREEZE.read_text(encoding="utf-8"))
    original_freeze_bytes = FREEZE.read_bytes()
    source_errors = []
    for relative, expected in v3_freeze["pinned_sha256"].items():
        if relative == "upstream/adjudicator.py":
            path = UPSTREAM
        else:
            path = HERE / relative
        if sha(path.read_bytes()) != expected:
            source_errors.append("source_hash:" + relative)
    raw_bytes = (OUT / "RAW.json").read_bytes()
    run_bytes = (OUT / "RUN.json").read_bytes()
    if sha(raw_bytes) != v3_freeze["raw_sha256"]:
        source_errors.append("pinned_raw_sha256")
    if sha(run_bytes) != v3_freeze["run_sha256"]:
        source_errors.append("pinned_run_sha256")
    if sha(V2_FREEZE.read_bytes()) != v3_freeze["v2_freeze_sha256"]:
        source_errors.append("v2_freeze_sha256")
    if sha((OUT / "AUDIT.json").read_bytes()) != v3_freeze["audit_v1_sha256"]:
        source_errors.append("audit_v1_sha256")
    if sha((HERE / "AUDIT_V2_ATTEMPT.json").read_bytes()) != v3_freeze["audit_v2_attempt_sha256"]:
        source_errors.append("audit_v2_attempt_sha256")

    raw = json.loads(raw_bytes)
    run = json.loads(run_bytes)
    errors = source_errors + audit_v2.audit_bundle(
        raw, run, raw_bytes, v2_freeze, original_freeze_bytes)
    mutations = [
        ("omitted_case", lambda x: x["cases"].pop()),
        ("duplicate_case", lambda x: x["cases"].__setitem__(-1, copy.deepcopy(x["cases"][0]))),
        ("forged_decision", lambda x: x["cases"][1]["decision"].update(reason="forged")),
        ("altered_bound_identity", lambda x: x.update(upstream_adjudicator_sha256="f" * 64)),
        ("collateral_payload_edit", _collateral_edit),
    ]
    mutation_results = {}
    for name, mutate in mutations:
        altered = copy.deepcopy(raw)
        mutate(altered)
        altered_bytes, altered_run = reseal(altered, run)
        rejected = bool(audit_v2.audit_bundle(
            altered, altered_run, altered_bytes, v2_freeze, original_freeze_bytes))
        mutation_results[name] = {"rejected": rejected}
        if not rejected:
            errors.append("mutation_accepted:" + name)
    return {
        "schema": "map01-json-boundary-host-audit-v3",
        "status": "PASS_HOST_JSON_BOUNDARY_AUDIT_V3" if not errors else "STOP_HOST_AUDIT_V3",
        "errors": sorted(set(errors)), "source_errors": source_errors,
        "case_count": len(audit_v2.expected_cases()),
        "mutation_results": mutation_results,
        "raw_sha256": sha(raw_bytes),
        "audit_v1_false_accept_reproduced": True,
        "audit_v2_attempt": "STOP_AUDITOR_IMPLEMENTATION_ERROR",
        "scope": "auditor-only re-audit of immutable synthetic host-construction raw; not formal Docker or live MAP01 evidence",
    }


def _collateral_edit(raw):
    item = raw["cases"][1]
    item["parsed_rows"][0]["health_loss"] = 1
    item["wire_json"] = audit_v2.canonical(item["parsed_rows"])


def main():
    result = run_audit()
    (OUT / "AUDIT_V3.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if not result["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
