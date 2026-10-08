from __future__ import annotations
import hashlib, importlib.util, json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parents[1]
sys.path.insert(0, str(PACKAGE))
import audit_results
from make_dataset import build

source_path = PACKAGE / "audit_results.py"
source = source_path.read_text(encoding="utf-8")
needle = '        return f"{op}:{reason}" if reason in reasons[op] else None\n'
replacement = '        return f"{op}:{reason}" if isinstance(reason, str) and reason in reasons[op] else None\n'
assert source.count(needle) == 1
fixed_source = source.replace(needle, replacement, 1)
fixed_path = HERE / "audit_results_guarded.py"
fixed_path.write_text(fixed_source, encoding="utf-8")
spec = importlib.util.spec_from_file_location("audit_results_guarded", fixed_path)
guarded = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guarded)

seed = 73194111
support_seed = 51829177
allocation = "qwen5139-construction-only-fixture"
clean = build(seed, support_seed, allocation)
clean_errors = audit_results._dataset_errors(clean)
assert not clean_errors, clean_errors
cases = [
    ("support_pool", "yield", {"bad": "object"}),
    ("support_pool", "no_action", ["bad", "list"]),
    ("heldout_pool", "yield", ["bad", "list"]),
    ("heldout_pool", "no_action", {"bad": "object"}),
]
rows = []
for pool_name, op, malformed_reason in cases:
    data = build(seed, support_seed, allocation)
    row = next(item for item in data[pool_name] if item["intent"].get("op") == op)
    case_id = row["case_id"]
    row["intent"]["reason"] = malformed_reason
    try:
        vulnerable_errors = audit_results._dataset_errors(data)
        vulnerable = {"outcome": "RETURNED_ERRORS", "error_count": len(vulnerable_errors), "first_errors": vulnerable_errors[:3]}
    except Exception as exc:
        vulnerable = {"outcome": "UNCAUGHT_EXCEPTION", "exception_type": type(exc).__name__, "message": str(exc)}
    try:
        guarded_errors = guarded._dataset_errors(data)
        fixed = {"outcome": "REJECTED_WITH_ERRORS", "error_count": len(guarded_errors), "has_pool_class_mismatch": any(e.startswith(("support_class_mismatch:", "heldout_class_mismatch:")) for e in guarded_errors)}
    except Exception as exc:
        fixed = {"outcome": "UNCAUGHT_EXCEPTION", "exception_type": type(exc).__name__, "message": str(exc)}
    rows.append({"pool": pool_name, "op": op, "reason_type": type(malformed_reason).__name__, "case_id": case_id, "vulnerable_auditor": vulnerable, "guarded_diagnostic": fixed})

result = {
    "schema": "qwen5139-malformed-reason-control-v1",
    "result": "FAIL_AUDITOR_EXCEPTION_ON_JSON_MALFORMED_REASON",
    "candidate_branch": "research/qwen5139-current-main-recheck-20260928",
    "candidate_head": "8869c42a6c5cf2f8e870684431d70b26e1b6e645",
    "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
    "guarded_diagnostic_sha256": hashlib.sha256(fixed_path.read_bytes()).hexdigest(),
    "python": sys.version.split()[0],
    "clean_fixture_errors": len(clean_errors),
    "cases": rows,
    "scope": "Host-CPU synthetic dataset-integrity/auditor robustness only; no raw prediction arms, model, GPU, CUDA, Docker, GUI, or formal allocation",
    "limits": "The diagnostic patch is not applied to the shared candidate branch; this control covers four fixed malformed JSON reason values only.",
}
out = HERE / "result.json"
out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(out.read_text(encoding="utf-8"), end="")

