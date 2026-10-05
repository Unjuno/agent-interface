import json
from pathlib import Path

from oracle_audit import audit_rows


ROOT = Path(__file__).resolve().parent
candidate = json.loads((ROOT / "candidate_output.json").read_text())
oracle = json.loads((ROOT / "oracle_truth.json").read_text())
if candidate["allocation"] != oracle["allocation"]:
    raise SystemExit("allocation identity mismatch")

outcomes = {row["case_id"]: row["candidate"] for row in candidate["results"]}
truths = {row["case_id"]: row for row in oracle["cases"]}
if set(outcomes) != set(truths):
    raise SystemExit("candidate/oracle case inventory mismatch")
rows = [{"case_id": key, "candidate": outcomes[key], "oracle": truths[key]}
        for key in truths]
audit = audit_rows(rows)
audit["allocation"] = candidate["allocation"]
audit["case_count"] = len(rows)
(ROOT / "audit_output.json").write_text(json.dumps(audit, indent=2) + "\n")
print(json.dumps(audit, indent=2))
