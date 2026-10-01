import argparse
import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

def alter(result, name):
    item = copy.deepcopy(result)
    if name == "drop_input_row":
        item["input_sha256"].pop("accepted", None)
    elif name == "input_digest":
        item["input_sha256"]["accepted"]["sha256"] = "0" * 64
    elif name == "role_path":
        item["provenance"]["audit_plan_freeze_key"] = "PLAN.md"
    elif name == "baseline_digest":
        item["baseline"]["accepted_sha256"] = "0" * 64
    elif name == "accepted_mutation":
        item["mutations"]["accepted_same_length_path_change"]["rejected_by_receipt_hash"] = False
    elif name == "prefix_length":
        item["mutations"]["delivered_prefix_23_to_22_bytes"]["rejected_by_receipt_length"] = False
    elif name == "prefix_sha":
        item["mutations"]["delivered_prefix_23_to_22_bytes"]["rejected_by_receipt_hash"] = False
    elif name == "disposition":
        item["disposition"] = "PASS_UNSCOPED"
    return item

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", required=True)
    parser.add_argument("--freeze", required=True)
    parser.add_argument("--result", required=True)
    parser.add_argument("--audit", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    result = json.loads(Path(args.result).read_bytes())
    names = ["drop_input_row", "input_digest", "role_path", "baseline_digest",
             "accepted_mutation", "prefix_length", "prefix_sha", "disposition"]
    rows = []
    for name in names:
        with tempfile.TemporaryDirectory(prefix="i3809-control-") as temp:
            candidate = Path(temp) / "RESULT.json"
            candidate.write_text(json.dumps(alter(result, name), sort_keys=True), encoding="utf-8")
            cp = subprocess.run(
                [sys.executable, "-B", args.audit, "--input-root", args.input_root,
                 "--freeze", args.freeze, "--result", str(candidate)],
                capture_output=True, text=True, timeout=15
            )
            try:
                audit = json.loads(cp.stdout)
            except Exception:
                audit = {}
            rejected = (
                cp.returncode == 1
                and audit.get("decision") == "FAIL"
                and bool(audit.get("errors"))
                and not any(str(x).startswith("AUDITOR_EXCEPTION") for x in audit.get("errors", []))
                and not cp.stderr
            )
            rows.append({
                "name": name, "rejected": rejected, "exit": cp.returncode,
                "audit_errors": audit.get("errors", []), "stderr": cp.stderr
            })
    output = {"schema": "issue3809-corruption-controls-v1", "rows": rows,
              "all_rejected": all(row["rejected"] for row in rows)}
    with Path(args.out).open("x", encoding="utf-8") as f:
        json.dump(output, f, sort_keys=True, indent=2)
        f.write("\n")
        f.flush()
    print(json.dumps({"all_rejected": output["all_rejected"], "count": len(rows)}))
    return 0 if output["all_rejected"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
