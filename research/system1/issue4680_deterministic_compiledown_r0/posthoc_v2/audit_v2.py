"""Independent posthoc reconstruction of the retained #4680 matrix result."""
import argparse
import copy
import hashlib
import itertools
import json
from pathlib import Path

INTENTS = ("TRACK", "STABILIZE", "WATCH_ONLY", "OUT_OF_SCOPE")
EVIDENCE = ("CLEAR", "MISSING", "AMBIGUOUS", "STALE")
BITS = (False, True)
IMAGE = "sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9"
ALLOCATION = "issue4680-deterministic-compiledown-20260927-01"


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha_file(path):
    return sha_bytes(Path(path).read_bytes())


def expected(row):
    """Reconstruct frozen policy without importing candidate source or oracle."""
    intent = row.get("intent")
    evidence = row.get("evidence")
    if intent not in INTENTS or evidence not in EVIDENCE:
        return "YIELD"
    if evidence != "CLEAR" or row.get("generation_fresh") is not True:
        return "YIELD"
    if row.get("forbidden_effect") is True:
        return "YIELD"
    if row.get("completed") is True:
        return "NO_ACTION"
    if intent == "TRACK":
        return "CONTINUE" if row.get("progressing") is True else "CORRECT"
    if intent == "STABILIZE":
        return "CORRECT" if row.get("progressing") is not True else "CONTINUE"
    if intent == "WATCH_ONLY":
        return "WATCH"
    return "YIELD"


def expected_rows():
    for intent, evidence, progressing, completed, fresh, forbidden in itertools.product(
        INTENTS, EVIDENCE, BITS, BITS, BITS, BITS
    ):
        yield {
            "intent": intent,
            "evidence": evidence,
            "progressing": progressing,
            "completed": completed,
            "generation_fresh": fresh,
            "forbidden_effect": forbidden,
        }


def canonical(row):
    return tuple((k, row.get(k)) for k in (
        "intent", "evidence", "progressing", "completed", "generation_fresh", "forbidden_effect"
    ))


def validate_data(r, freeze):
    errors = []
    if r.get("schema") != "issue4680-deterministic-compiledown-r0" or r.get("allocation") != ALLOCATION:
        errors.append("IDENTITY")
    if r.get("image_id") != IMAGE or r.get("image_id") != freeze.get("image_id"):
        errors.append("IMAGE_ID")
    if r.get("formal_study_invocations") != 1:
        errors.append("INVOCATION_COUNT")
    if r.get("latency_measured") is not False or r.get("adaptation_prerequisite_met") is not False or r.get("fast_backend_prerequisite_met") is not False:
        errors.append("SCOPE")
    if r.get("decision") != "PASS_DETERMINISTIC_COMPILEDOWN_EQUIVALENCE_SCOPED":
        errors.append("RUNNER_DISPOSITION")
    if r.get("source_sha256") != freeze.get("source_sha256"):
        errors.append("SOURCE_BINDING")
    records = r.get("records")
    if not isinstance(records, list) or len(records) != 256:
        errors.append("ROW_CARDINALITY")
        return errors
    wanted = {canonical(row) for row in expected_rows()}
    observed = [canonical(x.get("row", {})) for x in records]
    if len(set(observed)) != 256:
        errors.append("DUPLICATE_STATE")
    if set(observed) != wanted:
        errors.append("STATE_SPACE_SET")
    for index, item in enumerate(records):
        row = item.get("row", {})
        exp = expected(row)
        if item.get("direct") != exp:
            errors.append(f"DIRECT_EXPECTED:{index}")
        if item.get("compiled") != exp:
            errors.append(f"COMPILED_EXPECTED:{index}")
        if item.get("oracle") != exp:
            errors.append(f"ORACLE_EXPECTED:{index}")
        if item.get("match") is not True:
            errors.append(f"MATCH_FLAG:{index}")
    controls = r.get("controls", {})
    required = {
        "missing_yields", "ambiguous_yields", "stale_evidence_yields", "stale_generation_yields",
        "forbidden_effect_yields", "invalid_intent_yields", "authority_expansion_rejected",
        "failed_activation_preserves_active",
    }
    if set(controls) != required or any(value is not True for value in controls.values()):
        errors.append("CONTROL_REPORT")
    return errors


def corruption_controls(r, freeze):
    cases = []
    def altered(name, mutate, marker):
        candidate = copy.deepcopy(r)
        mutate(candidate)
        errors = validate_data(candidate, freeze)
        cases.append({"name": name, "rejected": any(e.startswith(marker) for e in errors), "errors": errors[:3]})

    altered("direct_action", lambda x: x["records"][0].__setitem__("direct", "WATCH"), "DIRECT_EXPECTED")
    altered("compiled_action", lambda x: x["records"][0].__setitem__("compiled", "WATCH"), "COMPILED_EXPECTED")
    altered("oracle_action", lambda x: x["records"][0].__setitem__("oracle", "WATCH"), "ORACLE_EXPECTED")
    altered("match_claim", lambda x: x["records"][0].__setitem__("match", False), "MATCH_FLAG")
    altered("row_deletion", lambda x: x["records"].pop(), "ROW_CARDINALITY")
    altered("duplicate_row", lambda x: x["records"].__setitem__(1, copy.deepcopy(x["records"][0])), "DUPLICATE_STATE")
    altered("state_mutation", lambda x: x["records"][0]["row"].__setitem__("evidence", "STALE"), "STATE_SPACE_SET")
    altered("scope_expansion", lambda x: x.__setitem__("latency_measured", True), "SCOPE")
    altered("invocation_count", lambda x: x.__setitem__("formal_study_invocations", 2), "INVOCATION_COUNT")
    altered("image_identity", lambda x: x.__setitem__("image_id", "sha256:" + "0" * 64), "IMAGE_ID")
    return cases


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--freeze", required=True)
    ap.add_argument("--result", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    freeze = json.loads(Path(args.freeze).read_text(encoding="utf-8"))
    raw_bytes = Path(args.result).read_bytes()
    result = json.loads(raw_bytes)
    errors = []
    if sha_bytes(raw_bytes) != freeze.get("raw_result_sha256"):
        errors.append("RAW_RESULT_HASH")
    if sha_file("/study/audit_v2.py") != freeze.get("auditor_source_sha256"):
        errors.append("AUDITOR_SOURCE_HASH")
    errors.extend(validate_data(result, freeze))
    controls = corruption_controls(result, freeze)
    if len(controls) != 10 or any(not item["rejected"] for item in controls):
        errors.append("CORRUPTION_CONTROLS")
    out = {
        "schema": "issue4680-independent-matrix-audit-v2",
        "decision": "PASS_INDEPENDENT_MATRIX_AUDIT_SCOPED" if not errors else "FAIL_INDEPENDENT_MATRIX_AUDIT",
        "errors": errors,
        "rows_independently_reconstructed": 256,
        "semantic_mismatches": sum(1 for item in result.get("records", []) if any(
            item.get(key) != expected(item.get("row", {})) for key in ("direct", "compiled", "oracle")
        )),
        "corruption_controls": controls,
        "active_snapshot_bytes_independently_verified": False,
        "accepted_full_allocation_disposition": "HOLD_ACTIVE_SNAPSHOT_RECEIPT_MISSING",
        "raw_result_sha256": sha_bytes(raw_bytes),
    }
    Path(args.output).write_text(json.dumps(out, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps(out, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
