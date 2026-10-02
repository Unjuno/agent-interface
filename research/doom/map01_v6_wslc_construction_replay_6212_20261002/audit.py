"""Independent auditor for the WSLc construction-portability replay."""
import hashlib
import json
import pathlib
import sys

EXPECTED = [
    ("test_map01_recovery_cover_mechanism_v6.py", "PASS total 3"),
    ("test_map01_recovery_cover_mechanism_v5.py", "PASS total 4"),
    ("test_audit_map01_recovery_cover_mechanism_v5.py", "PASS total 3"),
    ("test_audit_map01_recovery_cover_mechanism_v6.py", "PASS total 3"),
    ("test_audit_map01_recovery_cover_mechanism_v6_bound.py", "PASS_V6_BOUND_BINDINGS 6/6"),
]

def audit(evidence_dir, source_dir):
    evidence_dir = pathlib.Path(evidence_dir)
    source_dir = pathlib.Path(source_dir)
    errors = []
    result = json.loads((evidence_dir / "candidate_result.json").read_text())
    manifest = json.loads((evidence_dir / "SOURCE_MANIFEST.json").read_text())
    if result.get("schema") != "wslc-construction-replay-v1": errors.append("schema")
    if result.get("all_children_exit_zero") is not True: errors.append("aggregate_exit")
    rows = result.get("children", [])
    if len(rows) != len(EXPECTED): errors.append("row_count")
    for i, (name, marker) in enumerate(EXPECTED):
        if i >= len(rows): break
        row = rows[i]
        if row.get("script") != name: errors.append(f"script_order:{i}")
        if row.get("exit_code") != 0: errors.append(f"exit:{name}")
        if marker not in row.get("stdout", ""): errors.append(f"expected_marker:{name}")
        if row.get("wall_ms", 0) <= 0: errors.append(f"wall:{name}")
    cg = result.get("cgroup", {})
    if cg.get("cpu.max") != "200000 100000": errors.append("cpu_limit")
    if cg.get("memory.max") != "536870912": errors.append("memory_limit")
    peak = int(cg.get("memory.peak", "0"))
    if peak <= 0 or peak >= 536870912: errors.append("memory_peak")
    # `max` plus the WSLc warning means swap limiting is unavailable; do not
    # claim a finite swap budget.
    if cg.get("memory.swap.max") != "max": errors.append("unexpected_swap_limit_claim")
    if len(manifest.get("files", [])) != 10: errors.append("source_manifest_count")
    for entry in manifest.get("files", []):
        path = source_dir / entry.get("path", "")
        try:
            data = path.read_bytes()
        except OSError:
            errors.append(f"missing_source:{entry.get('path')}")
            continue
        git_blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        sha256 = hashlib.sha256(data).hexdigest()
        if git_blob != entry.get("blob_sha1"): errors.append(f"git_blob:{entry.get('path')}")
        if sha256 != entry.get("sha256"): errors.append(f"sha256:{entry.get('path')}")
    return {"decision": "PASS_WSLC_CONSTRUCTION_PORTABILITY_SCOPED" if not errors else "FAIL_AUDIT",
            "errors": errors, "rows_audited": len(rows), "sources_audited": len(manifest.get("files", [])),
            "cgroup_memory_peak_bytes": peak, "cgroup_swap_limit": "unbounded_or_unavailable"}

if __name__ == "__main__":
    outcome = audit(sys.argv[1], sys.argv[2])
    print(json.dumps(outcome, sort_keys=True, separators=(",", ":")))
    raise SystemExit(bool(outcome["errors"]))
