import json
from pathlib import Path

HERE = Path(__file__).parent
x = json.loads((HERE / "SOURCE_INTEGRITY_READBACK.json").read_text())

rows = []
for f in x["files"]:
    blob = f["expected_blob"] == f["actual_blob"]
    size = f["expected_bytes"] == f["actual_bytes"]
    rows.append({**f, "blob_match": blob, "byte_length_match": size, "source_match": blob and size})

mismatch = [r["name"] for r in rows if not r["source_match"]]
formal_eligible = (not x["formal_result_present"]) and not mismatch
decision = "FORMAL_ELIGIBLE" if formal_eligible else "HOLD_SOURCE_GAP"

out = {
    "task": x["task"],
    "issue": x["issue"],
    "freeze_commit": x["freeze_commit"],
    "formal_result_present": x["formal_result_present"],
    "files_checked": len(rows),
    "source_matches": sum(r["source_match"] for r in rows),
    "source_mismatches": mismatch,
    "formal_eligible": formal_eligible,
    "decision": decision,
    "rows": rows,
    "rule": "Do not execute the frozen formal analysis unless all frozen source blobs and byte lengths match exact readback."
}

(HERE / "SOURCE_INTEGRITY_AUDIT.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
print(json.dumps(out, indent=2, sort_keys=True))
