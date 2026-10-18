#!/usr/bin/env python3
"""Pre-freeze WSLc schema smoke; not the formal A04 evidence audit."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OLD = ROOT / "predecessor_a02"

candidate = json.loads((OLD / "CANDIDATE_CLEANUP.json").read_text(encoding="utf-8"))
auditor = json.loads((OLD / "AUDITOR_CLEANUP.json").read_text(encoding="utf-8"))
checks = auditor["targeted_inspect_checks"]
assert candidate["absence_verified"] is True
assert len(checks) == 2
assert checks[0]["used_for_verification"] is False
assert checks[1]["attempt"] == "exact CID from AUDITOR_CID.txt"
assert checks[1]["absence_verified"] is True
assert candidate["container_id"] == (OLD / "CANDIDATE_CID.txt").read_text().strip()
assert auditor["container_id"] == (OLD / "AUDITOR_CID.txt").read_text().strip()
print(json.dumps({
    "schema": "wslc-local-smoke-7924-a04-preflight-v1",
    "status": "PASS_PREFLIGHT_RECEIPT_SHAPES",
    "candidate_absence_field": "top-level",
    "auditor_absence_field": "targeted_inspect_checks[1]",
    "a02_candidate_or_auditor_reruns": 0,
    "formal_audit": False,
}, sort_keys=True))
