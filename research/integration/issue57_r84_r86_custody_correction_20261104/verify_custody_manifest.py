#!/usr/bin/env python3
"""Verify observed bytes listed in CUSTODY_MANIFEST.json; do not upgrade custody status."""
import hashlib, json, pathlib, sys
manifest_path=pathlib.Path(__file__).with_name("CUSTODY_MANIFEST.json")
manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
root=manifest_path.parents[3]
errors=[]
for run, data in manifest["runs"].items():
    records=[data["freeze_manifest"], *data["source_files"], *data["attempt_outputs"]]
    for item in records:
        path=root/item["path"]
        if not path.is_file():
            errors.append(f"missing: {item['path']}")
            continue
        actual=hashlib.sha256(path.read_bytes()).hexdigest()
        want=item.get("observed_sha256", item.get("expected_sha256_from_sidecar"))
        if actual != want:
            errors.append(f"hash mismatch: {item['path']} expected recorded {want}, got {actual}")
        if item.get("status") == "exact" and item.get("expected_sha256") and actual != item["expected_sha256"]:
            errors.append(f"frozen hash mismatch: {item['path']}")
    counts=data["source_counts"]
    if counts["exact"]+counts["mismatch_unrecovered"] != len(data["source_files"]):
        errors.append(f"bad source counts: {run}")
if errors:
    print("FAIL_CUSTODY_MAP")
    print("\n".join(errors))
    sys.exit(1)
print("PASS_CUSTODY_MAP")
for run,data in manifest["runs"].items():
    c=data["source_counts"]
    print(f"{run}: frozen exact={c['exact']} mismatch_unrecovered={c['mismatch_unrecovered']} attempt_files={len(data['attempt_outputs'])}")
