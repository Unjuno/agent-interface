"""Post-run custody digest of each frozen input/oracle and saved raw row."""

import hashlib
import json
import sys


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


design = json.load(open(sys.argv[1], encoding="utf-8"))
raw = json.load(open(sys.argv[2], encoding="utf-8"))
raw_rows = {row["case_id"]: row for row in raw["rows"]}
entries = []
for case in design["cases"]:
    payload = {"case": case, "raw_row": raw_rows[case["case_id"]]}
    entries.append({"case_id": case["case_id"], "sha256": hashlib.sha256(canonical(payload)).hexdigest()})
json.dump({"schema": "issue-8675-case-custody-hashes-v1", "entries": entries}, sys.stdout,
          sort_keys=True, separators=(",", ":"))
sys.stdout.write("\n")
