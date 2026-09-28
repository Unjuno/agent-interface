"""Raw-only v4 audit, including pinned corpus and effect-identity lineage."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PINNED = HERE.parent / "map01_task_effect_contract_5126_v1" / "result.json"
PINNED_SHA = "536de27a25cdc7b9936235dc1ef900cf174f2acbf16239a696474ede5f69fa9f"
ALLOCATION = "MAP01-TASK-EFFECT-LINEAGE-5126-20260928-04"
_SPEC = importlib.util.spec_from_file_location("v3_raw_auditor", HERE.parent / "map01_task_effect_contract_5126_v3" / "audit.py")
_BASE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_BASE)


def audit(path):
    path = Path(path)
    doc = json.loads(path.read_text())
    errors = []
    pinned_bytes = PINNED.read_bytes()
    if hashlib.sha256(pinned_bytes).hexdigest() != PINNED_SHA:
        errors.append("pinned_corpus_hash")
    pinned_rows = json.loads(pinned_bytes).get("cases", [])
    rows = doc.get("cases", [])
    if doc.get("input_corpus_sha256") != PINNED_SHA:
        errors.append("declared_corpus_hash")
    expected = [(r.get("case_id"), r.get("raw")) for r in pinned_rows]
    actual = [(r.get("case_id"), r.get("raw")) for r in rows]
    if actual != expected:
        errors.append("corpus_rows_mismatch")
    if doc.get("allocation") != ALLOCATION or doc.get("schema") != "map01-task-effect-contract-result-v5":
        errors.append("identity")
    base = _BASE.audit(path)
    errors.extend("raw_contract:" + e for e in base["errors"] if e not in ("schema", "allocation"))
    for row in rows:
        qualified = []
        raw = row.get("raw", {})
        physical = raw.get("physical") or {}
        edge_ids = {(physical.get(k) or {}).get("source_event_id") for k in ("down", "up")}
        for event in raw.get("task_effects", []):
            sid, eid = event.get("source_event_id"), event.get("effect_id")
            if (isinstance(sid, str) and sid and sid not in edge_ids
                    and isinstance(eid, str) and eid and event.get("scored") is True
                    and event.get("scorer_independent") is True and event.get("controller_visible") is False
                    and event.get("scorer_source") == "independent_progress_clock_v2"
                    and event.get("kind") in ("KILL_COUNT_INCREASE", "DEATH_COUNT_INCREASE", "MAP_EXIT", "PROGRESS")
                    and event.get("polarity") in ("useful", "harmful")):
                qualified.append(eid)
        expected_id = qualified[0] if row.get("candidate", {}).get("task_effect") == "TASK_EFFECT_SCOPED" and len(qualified) == 1 else None
        if row.get("candidate", {}).get("effect_id") != expected_id:
            errors.append("candidate_effect_identity:" + str(row.get("case_id")))
        if row.get("oracle", {}).get("effect_id") != expected_id:
            errors.append("oracle_effect_identity:" + str(row.get("case_id")))
    return {"status": "PASS_PINNED_CORPUS_AND_EFFECT_LINEAGE" if not errors else "FAIL_PINNED_CORPUS_AND_EFFECT_LINEAGE",
            "errors": errors, "cases": len(rows), "result_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "formal_allocations": 1, "live_allocations": 0}


if __name__ == "__main__":
    result = audit(sys.argv[1] if len(sys.argv) > 1 else HERE / "result.json")
    (HERE / "audit_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["status"].startswith("PASS") else 1)
