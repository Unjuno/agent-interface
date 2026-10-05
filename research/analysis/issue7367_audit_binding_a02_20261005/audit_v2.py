"""Read-only A02 auditor for the retained A01 evidence bundle."""

import argparse
import hashlib
import json
from pathlib import Path


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def canonical_sha(value):
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return sha256(payload)


def audit(root, raw_path):
    root = Path(root)
    freeze = json.loads((root / "PRE-RUN.json").read_text(encoding="utf-8-sig"))
    workload_bytes = (root / "workload.json").read_bytes()
    workload = json.loads(workload_bytes.decode("utf-8-sig"))
    raw = json.loads(Path(raw_path).read_text(encoding="utf-8-sig"))

    checks = {
        "workload_matches_prerun_sha256": sha256(workload_bytes)
        == freeze["source_sha256"]["workload.json"],
        "candidate_workload_hash_matches_bytes": raw.get("workload_sha256")
        == sha256(workload_bytes),
        "frozen_run_source_matches": sha256((root / "run_a01.py").read_bytes())
        == freeze["source_sha256"]["run_a01.py"],
        "frozen_auditor_source_matches": sha256((root / "audit_a01.py").read_bytes())
        == freeze["source_sha256"]["audit_a01.py"],
    }

    records = workload["records"]
    by_id = {record["id"]: record for record in records}
    required = set()
    continuation_uses = {}
    references_valid = True
    for continuation in workload["continuations"]:
        used = set()
        for node in continuation["nodes"]:
            if node not in workload["nodes"]:
                references_valid = False
                continue
            for evidence_id, field in workload["nodes"][node].get("uses", []):
                if evidence_id not in by_id or field not in by_id[evidence_id].get("fields", {}):
                    references_valid = False
                used.add(evidence_id)
        continuation_uses[continuation["id"]] = sorted(used)
        required.update(used)

    base = raw["base_analysis"]
    selected = set(base["selected_ids"])
    checks.update({
        "frozen_continuation_references_valid": references_valid,
        "all_frozen_future_uses_retained": required <= selected,
        "selected_ids_match_frozen_oracle": selected == required,
        "dead_eviction_is_outside_frozen_oracle": set(base["evicted_ids"])
        <= (set(by_id) - required),
        "canonical_records_match_raw": all(
            canonical_sha(record) == raw["canonical_record_sha256"].get(record["id"])
            for record in records
        ),
    })

    passed = all(checks.values())
    result = {
        "schema": "issue7367-a02-freeze-binding-audit-v1",
        "passed": passed,
        "classification": "PASS_RETAINED_BYTES_SCOPED" if passed else "FAIL_FREEZE_BINDING",
        "checks": checks,
        "continuation_uses": continuation_uses,
        "independent_required_ids": sorted(required),
        "scope": "read-only re-audit of retained A01 bytes; candidate was not rerun",
    }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--raw", required=True)
    args = parser.parse_args()
    result = audit(args.root, args.raw)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
