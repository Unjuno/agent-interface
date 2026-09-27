"""Raw-only verifier; deliberately imports neither runner nor candidate."""
import hashlib
import json
import copy
from pathlib import Path


EXPECTED_RAW_SHA256 = "5f48e0274f9fd800ac26af3dd70bd52171700b32ce159f3cdbe0f28c7ec35e7d"
EXPECTED_CANARIES = (
    "cost.A", "drift_grid[0]", "distributions[-1].alpha", "rows[1].state_id",
    "rows[0].truth.A", "rows[0].NAIVE.evaluations",
    "rows[0].NAIVE.semantic_mismatches",
)
CANARY_MUTATIONS = (
    ("cost.A", ("cost", "A"), True),
    ("drift_grid[0]", ("drift_grid", 0), False),
    ("distributions[-1].alpha", ("distributions", -1, "alpha"), True),
    ("rows[1].state_id", ("distributions", 0, "rows", 1, "state_id"), True),
    ("rows[0].truth.A", ("distributions", 0, "rows", 0, "truth", "A"), 0),
    ("rows[0].NAIVE.evaluations", ("distributions", 0, "rows", 0,
                                   "NAIVE", "evaluations"), True),
    ("rows[0].NAIVE.semantic_mismatches",
     ("distributions", 0, "summaries", "NAIVE", "semantic_mismatches"), False),
)
SOURCE_PATHS = (
    "/src/audit_hardened.py", "/src/candidate.py", "/src/runner.py",
    "/src/independent_audit.py", "/src/manifest_probe.py", "/src/test_protocol.py",
    "/src/formal_entry.sh", "/src/audit_entry.sh", "/src/manifest_entry.sh",
    "/src/probe_baseline.py", "/src/allocation_entry.sh",
)
OUTPUT_PATHS = (
    "/input/RAW.json", "/input/AUDIT.json", "/evidence/runner_result.json",
    "/audit/AUDIT.json",
)


def main():
    raw_path = Path("/input/RAW.json")
    formal_path = Path("/evidence/runner_result.json")
    audit_path = Path("/evidence/AUDIT.json")
    raw_bytes = raw_path.read_bytes()
    raw = json.loads(raw_bytes.decode("utf-8"))
    actual_raw = hashlib.sha256(raw_bytes).hexdigest()
    result = json.loads(formal_path.read_text(encoding="utf-8"))
    errors = []
    if actual_raw != EXPECTED_RAW_SHA256:
        errors.append("raw_sha256")
    if result.get("raw_sha256") != actual_raw:
        errors.append("formal_raw_binding")
    if result.get("raw_bytes") != len(raw_bytes):
        errors.append("raw_length")
    baseline = result.get("baseline", {})
    if (baseline.get("status") != "PASS_AUDIT_HARDENING_SCOPED" or
            baseline.get("rows") != 336 or baseline.get("distributions") != 21):
        errors.append("baseline_reconstruction")
    rows = result.get("canaries", [])
    if [row.get("canary") for row in rows] != list(EXPECTED_CANARIES):
        errors.append("canary_order_or_count")
    for row, (label, path, replacement) in zip(rows, CANARY_MUTATIONS):
        mutated = copy.deepcopy(raw)
        target = mutated
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = replacement
        canonical = json.dumps(mutated, sort_keys=True, separators=(",", ":"),
                               ensure_ascii=False).encode("utf-8")
        if row.get("path") != list(path):
            errors.append("canary_path:" + label)
        if row.get("replacement_type") != type(replacement).__name__:
            errors.append("canary_replacement_type:" + label)
        if row.get("mutation_sha256") != hashlib.sha256(canonical).hexdigest():
            errors.append("canary_mutation_hash:" + label)
    if any(row.get("baseline_accepts") is not True for row in rows):
        errors.append("baseline_canary_acceptance")
    if any(row.get("candidate_accepts") is not False for row in rows):
        errors.append("strict_canary_rejection")
    if result.get("decision") != "PASS_AUDIT_BOUNDARY_REPAIRED_SCOPED":
        errors.append("runner_decision")
    audit = {"status": "PASS_RAW_AUDIT" if not errors else "HOLD_RAW_AUDIT",
             "raw_sha256": actual_raw, "raw_bytes": len(raw_bytes),
             "rows": baseline.get("rows"), "distributions": baseline.get("distributions"),
             "canaries": len(rows), "canary_rejections": sum(
                 row.get("candidate_accepts") is False for row in rows),
             "errors": errors}
    audit_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n",
                          encoding="utf-8", newline="\n")
    manifest = {
        "schema": "predicate-order-exact-path-manifest-v1",
        "source_sha256": {path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
                          for path in SOURCE_PATHS},
        "output_sha256": {path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
                          for path in OUTPUT_PATHS},
    }
    Path("/audit/manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8", newline="\n")
    print(audit["status"])
    if errors:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
