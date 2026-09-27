#!/usr/bin/env python3
"""Independent audit of the frozen public Issue #4678 STOP bundle; stdlib only."""
import copy
import hashlib
import json
import sys

EXPECTED_NAMES = {
    "README.md", "COMMANDS.md", "PREFLIGHT.json", "audit.py",
    "test_audit.py", "AUDIT.json", "VERIFICATION.json", "SHA256SUMS",
}
MANIFEST_NAMES = EXPECTED_NAMES - {"SHA256SUMS"}

def blob_sha(content):
    raw = content.encode("utf-8")
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\\0" + raw).hexdigest()

def inspect_bundle(bundle):
    errors = []
    files = bundle.get("files", {})
    if set(files) != EXPECTED_NAMES:
        errors.append("frozen_input_set_mismatch")
    for name, item in files.items():
        if blob_sha(item.get("content", "")) != item.get("blob_sha"):
            errors.append("git_blob_mismatch:" + name)
    sums = {}
    for line in files.get("SHA256SUMS", {}).get("content", "").splitlines():
        fields = line.split()
        if len(fields) == 2:
            sums[fields[1]] = fields[0]
    if set(sums) != MANIFEST_NAMES:
        errors.append("checksum_manifest_population_mismatch")
    digest_rows = []
    for name in sorted(MANIFEST_NAMES & set(files)):
        actual = hashlib.sha256(files[name]["content"].encode("utf-8")).hexdigest()
        expected = sums.get(name)
        digest_rows.append({"path": name, "expected": expected, "actual": actual, "match": expected == actual})
    checksum_mismatches = [row["path"] for row in digest_rows if not row["match"]]
    try:
        preflight = json.loads(files["PREFLIGHT.json"]["content"])
        checkpoint = preflight["checkpoint"]
    except (KeyError, ValueError, TypeError):
        errors.append("preflight_unparseable")
        preflight, checkpoint = {}, {}
    # Faithful replay of the published audit's checkpoint-absence predicate.
    published_auditor_accepts_absence = (
        checkpoint.get("expected_present") is False
        and checkpoint.get("observed_exact_sha256") is None
        and checkpoint.get("observed_exact_bytes") is None
    )
    raw_inventory = any(
        name in files
        for name in ("CACHE_INVENTORY.json", "cache_inventory.json", "checkpoint_inventory.json")
    )
    absence_supported = raw_inventory and "expected_absent_path" in files.get(
        "checkpoint_inventory.json", {}
    ).get("content", "")
    # The source set is immutable and public-source-only; a prose command log is not raw command output.
    if checksum_mismatches:
        decision = "FAIL_PUBLISHED_CHECKSUM_MANIFEST"
    elif published_auditor_accepts_absence and not absence_supported:
        decision = "HOLD_CHECKPOINT_ABSENCE_UNSUPPORTED"
    elif errors:
        decision = "HOLD_FROZEN_SOURCE_INTEGRITY"
    else:
        decision = "PASS_STOP_EVIDENCE_INDEPENDENTLY_VERIFIABLE"
    return {
        "schema": "stop-evidence-4678-audit-result-v1",
        "decision": decision,
        "source_commit": bundle.get("source_commit"),
        "frozen_input_set_exact": set(files) == EXPECTED_NAMES,
        "git_blob_mismatches": [e for e in errors if e.startswith("git_blob_mismatch:")],
        "checksum_rows": digest_rows,
        "checksum_mismatches": checksum_mismatches,
        "published_auditor_accepts_checkpoint_absence": published_auditor_accepts_absence,
        "raw_cache_inventory_retained": raw_inventory,
        "checkpoint_absence_supported_by_raw_inventory": absence_supported,
        "errors": errors,
    }

def main():
    bundle = json.load(sys.stdin)
    result = inspect_bundle(bundle)
    controls = []
    mutated = copy.deepcopy(bundle)
    mutated["files"]["PREFLIGHT.json"]["content"] += " "
    controls.append(inspect_bundle(mutated)["errors"] != [])
    mutated = copy.deepcopy(bundle)
    mutated["files"]["SHA256SUMS"]["content"] += "\n"
    controls.append(inspect_bundle(mutated)["errors"] != [])
    mutated = copy.deepcopy(bundle)
    mutated["files"].pop("COMMANDS.md")
    controls.append("frozen_input_set_mismatch" in inspect_bundle(mutated)["errors"])
    mutated = copy.deepcopy(bundle)
    mutated["files"]["CACHE_INVENTORY.json"] = {"blob_sha": "synthetic", "content": "{\\\"complete\\\":true}"}
    controls.append("frozen_input_set_mismatch" in inspect_bundle(mutated)["errors"])
    result["mutation_controls"] = {"rejected": sum(controls), "total": len(controls)}
    if sum(controls) != len(controls):
        result["decision"] = "HOLD_MUTATION_CONTROLS"
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    raise SystemExit(0 if sum(controls) == len(controls) else 2)

if __name__ == "__main__":
    main()
