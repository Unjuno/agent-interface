"""Read-only independent recheck; does not import meta_audit.py."""
import hashlib
import json
from pathlib import Path
from jsonschema import Draft202012Validator

SOURCE = Path("/source")
EVIDENCE = Path("/evidence")
OUT = Path("/audit-out/independent-audit.json")
EXPECTED = {
    "schema_sha256": "3ca91926d9e362e02dd0272a03b67e2d65b46199bcfb1bb8f55c29cfe92f6d76",
    "cases_sha256": "6a693f06b1b4be15a8da35ec3aaf806d7fb3601091c8ef638c516069d1b4e95f",
}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    schema_path, cases_path = SOURCE / "event-schema.json", SOURCE / "trace-cases.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    raw = json.loads(cases_path.read_text(encoding="utf-8"))
    result_path = EVIDENCE / "audit.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    identities = {"schema_sha256": sha(schema_path), "cases_sha256": sha(cases_path)}
    if identities != EXPECTED or result.get("identities") != identities:
        raise SystemExit("raw source/result hash mismatch")
    if result.get("disposition") != "PASS_DRAFT2020_12_METASCHEMA_AND_TRACE_CONFORMANCE_SCOPED":
        raise SystemExit("candidate result is not PASS")
    Draft202012Validator.check_schema(schema)
    v = Draft202012Validator(schema)
    trace_ids = []
    for c in raw["cases"]:
        inst = {"schema_version": "useful-control-trace-v2", "trace_id": c["case_id"],
                "clock_domains": c["clock_domains"], "events": c["events"]}
        v.validate(inst)
        trace_ids.append(c["case_id"])
    if trace_ids != result.get("valid_trace_cases") or len(trace_ids) != 8:
        raise SystemExit("trace case reconciliation mismatch")
    if len(result.get("schema_mutations_rejected", [])) != 7 or len(result.get("instance_mutations_rejected", [])) != 7:
        raise SystemExit("mutation counts mismatch")
    report = {"disposition": "PASS_INDEPENDENT_DRAFT2020_12_RECHECK_SCOPED",
              "identities": identities, "trace_count": len(trace_ids), "trace_ids": trace_ids,
              "candidate_result_sha256": sha(result_path),
              "rechecked_meta_schema": True, "rechecked_trace_instances": True,
              "rechecked_mutation_counts": {"schema": 7, "instance": 7},
              "scope": "standards/schema and synthetic instance recheck only"}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        raise SystemExit("refusing to overwrite prior independent audit")
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"disposition": report["disposition"], "trace_count": len(trace_ids)}))

if __name__ == "__main__":
    main()
