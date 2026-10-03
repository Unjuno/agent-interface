"""One deterministic pilot selection, recorded before evaluation."""
import datetime
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
audit_path=ROOT/"runs/pilot_auditor/audit.json"
raw_path=ROOT/"runs/pilot_candidate/raw.json"
audit=json.loads(audit_path.read_text())
assert audit["status"]=="PASS_SAVED_SOURCE_AND_ARITHMETIC_AUDIT" and audit["phase"]=="pilot"
winner=max(("red","red_excess"),key=lambda name:audit["counts"][name]["exact"])
record={"created_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"selected":winner,"pilot_counts":audit["counts"],"pilot_raw_sha256":hashlib.sha256(raw_path.read_bytes()).hexdigest(),"pilot_audit_sha256":hashlib.sha256(audit_path.read_bytes()).hexdigest(),"tie_order":["red","red_excess"]}
with (ROOT/"SELECTION.json").open("x") as output: json.dump(record,output,indent=2); output.write("\n")
print(json.dumps(record))
