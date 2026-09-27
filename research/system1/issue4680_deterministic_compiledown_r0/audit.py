"""Raw-only independent verifier; does not import study/compiler/policy/oracle."""
import argparse
import hashlib
import json
from pathlib import Path

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--result", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--freeze", required=True)
    args = ap.parse_args()
    frozen = json.loads(Path(args.freeze).read_text(encoding="utf-8"))
    r = json.loads(Path(args.result).read_text(encoding="utf-8"))
    rows = r.get("records", [])
    errors = []
    keys = [tuple(sorted(item.get("row", {}).items())) for item in rows]
    if len(rows) != 256 or len(set(keys)) != 256 or r.get("row_count") != 256 or r.get("unique_state_count") != 256:
        errors.append("STATE_SPACE_CARDINALITY")
    if any(item.get("direct") != item.get("compiled") or item.get("direct") != item.get("oracle") or item.get("match") is not True for item in rows):
        errors.append("DECISION_DISAGREEMENT")
    if r.get("mismatch_count") != 0:
        errors.append("REPORTED_MISMATCH_COUNT")
    required = {"missing_yields", "ambiguous_yields", "stale_evidence_yields", "stale_generation_yields", "forbidden_effect_yields", "invalid_intent_yields", "authority_expansion_rejected", "failed_activation_preserves_active"}
    controls = r.get("controls", {})
    if set(controls) != required or any(v is not True for v in controls.values()):
        errors.append("BOUNDARY_CONTROL_FAILURE")
    if r.get("decision") != "PASS_DETERMINISTIC_COMPILEDOWN_EQUIVALENCE_SCOPED" or r.get("formal_study_invocations") != 1:
        errors.append("FORMAL_DISPOSITION_OR_COUNT")
    if r.get("latency_measured") is not False or r.get("adaptation_prerequisite_met") is not False or r.get("fast_backend_prerequisite_met") is not False:
        errors.append("SCOPE_OVERRUN")
    expected=frozen.get("source_sha256",{})
    if r.get("source_sha256") != expected:
        errors.append("RESULT_FREEZE_SOURCE_BINDING")
    for name,digest in expected.items():
        if sha(Path("/study")/name) != digest:
            errors.append("SOURCE_HASH:"+name)
    out={"schema":"issue4680-deterministic-compiledown-independent-audit-r0","decision":"PASS_INDEPENDENT_AUDIT" if not errors else "FAIL_INDEPENDENT_AUDIT","errors":errors,"rows_rechecked":len(rows),"source_files_rechecked":len(expected),"result_sha256":sha(args.result)}
    Path(args.output).write_text(json.dumps(out,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")
    print(json.dumps(out,sort_keys=True))
    return 0 if not errors else 1

if __name__ == "__main__":
    raise SystemExit(main())
