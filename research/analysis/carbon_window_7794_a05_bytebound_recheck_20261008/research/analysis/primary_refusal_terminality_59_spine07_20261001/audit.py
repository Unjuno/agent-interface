#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

root = Path(__file__).parent
raw_bytes = (root / "RAW.json").read_bytes()
raw = json.loads(raw_bytes)
source = (root / "primary-policy.mjs").read_bytes()
checks = {
    "source_blob": hashlib.sha1(b"blob " + str(len(source)).encode() + b"\0" + source).hexdigest()
        == raw["candidate_git_blob_sha"],
    "one_process_two_attempts": raw["process_runs"] == 1 and raw["caller_attempts"] == 2,
    "first_parse_exception": raw["raw_stdout"]["firstError"].startswith("TypeError:"),
    "no_latch_after_bad_reply": raw["raw_stdout"]["stoppedAfterMalformed"] is None,
    "second_call_reached_host": raw["raw_stdout"]["callsAtHost"] == 2,
    "second_call_completed": json.loads(raw["raw_stdout"]["secondCall"])["status"] == "completed",
    "terminal_latch_too_late": raw["raw_stdout"]["finalStopped"] is not None,
    "disposition_matches_gate": raw["disposition"] == "FAIL_UNCERTAIN_DELIVERY_REPLAY",
}
errors = [name for name, ok in checks.items() if not ok]
audit = {"schema": "primary-caller-malformed-envelope-audit-v1",
         "checks": checks, "errors": errors,
         "audit": "PASS" if not errors else "FAIL"}
(root / "AUDIT.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n")
print(json.dumps(audit, sort_keys=True))
raise SystemExit(0 if not errors else 1)
