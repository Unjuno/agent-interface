#!/usr/bin/env python3
"""Corrected independent source/hash verifier for Issue #4795; stdlib only."""
import copy
import hashlib
import json
import sys

EXPECTED_NAMES = {
    "README.md", "COMMANDS.md", "PREFLIGHT.json", "audit.py",
    "test_audit.py", "AUDIT.json", "VERIFICATION.json", "SHA256SUMS",
}
MANIFEST_NAMES = EXPECTED_NAMES - {"SHA256SUMS"}
INVENTORY_NAMES = {"CACHE_INVENTORY.json", "cache_inventory.json", "checkpoint_inventory.json"}

def sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def git_blob_sha(text):
    raw = text.encode("utf-8")
    header = b"blob " + str(len(raw)).encode("ascii") + b"\0"
    return hashlib.sha1(header + raw).hexdigest()

def audit(bundle):
    errors = []
    files = bundle.get("files", {})
    if set(files) != EXPECTED_NAMES:
        errors.append("frozen_input_set_mismatch")
    blob_mismatches = []
    for name in sorted(EXPECTED_NAMES & set(files)):
        item = files[name]
        if git_blob_sha(item["content"]) != item["blob_sha"]:
            blob_mismatches.append(name)
    if blob_mismatches:
        errors.append("git_blob_mismatch")
    sums = {}
    for line in files.get("SHA256SUMS", {}).get("content", "").splitlines():
        fields = line.split()
        if len(fields) == 2:
            sums[fields[1]] = fields[0]
    if set(sums) != MANIFEST_NAMES:
        errors.append("checksum_manifest_population_mismatch")
    rows = []
    for name in sorted(MANIFEST_NAMES & set(files)):
        expected = sums.get(name)
        actual = sha256(files[name]["content"])
        rows.append({"path": name, "expected": expected, "actual": actual, "match": expected == actual})
    mismatches = [r["path"] for r in rows if not r["match"]]
    try:
        pre = json.loads(files["PREFLIGHT.json"]["content"])
        checkpoint = pre["checkpoint"]
    except (KeyError, TypeError, ValueError):
        checkpoint = {}
        errors.append("preflight_unparseable")
    # Faithful replay of the old auditor's key condition (not a proof of host absence).
    published_auditor_accepts_absence = (
        checkpoint.get("expected_present") is False
        and checkpoint.get("observed_exact_sha256") is None
        and checkpoint.get("observed_exact_bytes") is None
    )
    raw_inventory = sorted(INVENTORY_NAMES & set(files))
    evidence_supports_absence = bool(raw_inventory) and any(
        "expected_absent_path" in files[n]["content"] for n in raw_inventory
    )
    # Source/input integrity errors take precedence over all scientific classifications.
    if errors:
        decision = "HOLD_SOURCE_OR_AUDIT_MISMATCH"
    elif len(mismatches) == 7 and published_auditor_accepts_absence and not evidence_supports_absence:
        decision = "PASS_SOURCE_BOUND_CHECKSUM_DISCREPANCY_REPRODUCED"
    elif mismatches:
        decision = "HOLD_SOURCE_OR_AUDIT_MISMATCH"
    elif not evidence_supports_absence:
        decision = "HOLD_CHECKPOINT_ABSENCE_UNSUPPORTED"
    else:
        decision = "PASS_STOP_EVIDENCE_INDEPENDENTLY_VERIFIABLE"
    return {
        "schema": "stop-evidence-4678-independent-revalidation-v1",
        "decision": decision,
        "source_commit": bundle.get("source_commit"),
        "source_blob_mismatches": blob_mismatches,
        "checksum_rows": rows,
        "checksum_mismatches": mismatches,
        "published_auditor_accepts_checkpoint_absence": published_auditor_accepts_absence,
        "raw_cache_inventory_files": raw_inventory,
        "checkpoint_absence_supported_by_raw_inventory": evidence_supports_absence,
        "errors": errors,
    }

def main():
    bundle = json.load(sys.stdin)
    result = audit(bundle)
    controls = []
    altered = copy.deepcopy(bundle)
    altered["files"]["PREFLIGHT.json"]["content"] += " "
    controls.append(bool(audit(altered)["errors"]))
    altered = copy.deepcopy(bundle)
    altered["files"]["PREFLIGHT.json"]["blob_sha"] = "0" * 40
    controls.append(bool(audit(altered)["errors"]))
    altered = copy.deepcopy(bundle)
    altered["files"].pop("COMMANDS.md")
    controls.append("frozen_input_set_mismatch" in audit(altered)["errors"])
    altered = copy.deepcopy(bundle)
    altered["files"]["CACHE_INVENTORY.json"] = {"blob_sha": "0" * 40, "content": "{\"expected_absent_path\":\"synthetic\"}"}
    controls.append("frozen_input_set_mismatch" in audit(altered)["errors"])
    altered = copy.deepcopy(bundle)
    altered["files"]["SHA256SUMS"]["content"] += "\n"
    controls.append(bool(audit(altered)["errors"]))
    result["mutation_controls"] = {"rejected": sum(controls), "total": len(controls)}
    if sum(controls) != len(controls):
        result["decision"] = "HOLD_SOURCE_OR_AUDIT_MISMATCH"
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    raise SystemExit(0 if sum(controls) == len(controls) else 2)

if __name__ == "__main__":
    main()
