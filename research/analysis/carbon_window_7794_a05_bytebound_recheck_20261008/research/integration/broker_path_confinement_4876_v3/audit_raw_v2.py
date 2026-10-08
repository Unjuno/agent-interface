"""Independent raw-only reconstruction; does not import the runner/resolver."""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path

ALLOCATION = "broker-path-confinement-4876-20260927-03"
SOURCE_BLOB = "5734f54f318db9ac5e96b2bed6f6bed105ac39ff"
EXPECTED = {
    "repo-alias": (True, "/schema.json"),
    "workspace-alias": (True, "/work"),
    "root-alias": (True, ""),
    "in-root-symlink": (True, "/schema.json"),
    "absolute-host": (False, None),
    "parent-traversal": (False, None),
    "encoded-traversal": (False, None),
    "backslash-traversal": (False, None),
    "external-symlink": (False, None),
    "missing": (False, None),
}

def audit_payload(r: dict) -> list[str]:
    errors = []
    if r.get("allocation") != ALLOCATION: errors.append("allocation")
    if r.get("source_blob") != SOURCE_BLOB: errors.append("source_blob")
    cases = r.get("cases")
    if not isinstance(cases, list) or len(cases) != 10:
        return errors + ["case_count"]
    by_name = {x.get("name"): x for x in cases if isinstance(x, dict)}
    if len(by_name) != len(cases) or set(by_name) != set(EXPECTED):
        errors.append("case_identity")
    repo_roots = set()
    for name, (accept, suffix) in EXPECTED.items():
        row = by_name.get(name)
        if row is None: continue
        if row.get("accepted") is not accept: errors.append("expected_class:" + name)
        if row.get("pass") is not True: errors.append("runner_claim:" + name)
        actual = row.get("actual")
        if accept:
            if not isinstance(actual, str) or not actual.endswith(suffix):
                errors.append("canonical_path:" + name)
            else:
                root = actual[:-len(suffix)] if suffix else actual
                repo_roots.add(root)
                p = Path(actual)
                try: p.relative_to(Path(root))
                except ValueError: errors.append("containment:" + name)
        else:
            if actual is not None: errors.append("rejected_path_has_target:" + name)
            if row.get("reason") not in ("ValueError", "FileNotFoundError"):
                errors.append("rejection_reason:" + name)
    if len(repo_roots) != 1: errors.append("root_consistency")
    if r.get("case_count") != 10 or r.get("all_path_checks_pass") is not True:
        errors.append("summary")
    if r.get("serve_valid_rc") != 0 or r.get("subprocess_calls") != 1:
        errors.append("valid_serve_exactly_once")
    mapped = r.get("valid_mapped_paths")
    if not isinstance(mapped, list) or len(mapped) != 2 or not mapped[0].endswith("/schema.json") or not mapped[1].endswith("/work"):
        errors.append("broker_mapping")
    if r.get("valid_broker_returncode") != 0 or r.get("authority_granted") is not False:
        errors.append("broker_receipt")
    if r.get("decision") != "PASS_PATH_RESOLVER_CONSTRUCTION_SCOPED":
        errors.append("runner_decision")
    return errors

def main(raw: Path, out: Path) -> int:
    data = raw.read_bytes()
    payload = json.loads(data)
    errors = audit_payload(payload)
    result = {
        "schema": "broker-path-confinement-4876-independent-raw-audit-v2",
        "raw_sha256": hashlib.sha256(data).hexdigest(),
        "rows": len(payload.get("cases", [])),
        "errors": errors,
        "decision": "PASS_INDEPENDENT_AUDIT" if not errors else "HOLD_AUDIT",
        "scope": "posthoc read-only reconstruction; no formal runner rerun",
    }
    out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 1

if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]), Path(sys.argv[2])))

