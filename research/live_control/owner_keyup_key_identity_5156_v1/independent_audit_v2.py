"""Separate raw-only audit for run_key_identity.py; consumes base64 JSON argv."""
import base64, json, sys
if len(sys.argv) != 2:
    raise SystemExit("usage: audit_run.py RUN_JSON_B64")
r=json.loads(base64.b64decode(sys.argv[1],validate=True))
c=r["checks"]
expected={
 "candidate_pristine": [],
 "candidate_explicit_key_tamper": ["release_identity_mismatch:explicit-a-01"],
 "candidate_cleanup_key_tamper": ["release_identity_mismatch:cleanup-b-01"],
 "candidate_missing_key": ["expected_release_missing:explicit-a-01","record:0:missing:key"],
 "candidate_missing_row": ["expected_release_missing:explicit-a-01"],
 "legacy_explicit_key_tamper": [],
 "legacy_cleanup_key_tamper": [],
}
checks={
 "runner_status":r.get("status")=="PASS_KEY_IDENTITY_AUDIT_HOST_ONLY",
 "hashes_present":set(r.get("source_hashes",{}))=={"candidate_auditor","legacy_auditor","expected_inventory","raw_input"},
 "exact_decisions":all(sorted(c.get(k,[]))==sorted(v) for k,v in expected.items()),
 "legacy_gap_reproduced":r.get("legacy_fail_open_reproduced") is True,
 "explicit_tamper_rejected":r.get("candidate_rejects_explicit_key") is True,
 "cleanup_tamper_rejected":r.get("candidate_rejects_cleanup_key") is True,
 "missing_key_rejected":r.get("candidate_rejects_missing_key") is True,
 "missing_row_rejected":r.get("candidate_rejects_missing_row") is True,
}
audit={"status":"PASS_INDEPENDENT_RAW_ONLY_AUDIT" if all(checks.values()) else "FAIL_INDEPENDENT_AUDIT","checks":checks,"errors":[k for k,v in checks.items() if not v]}
print(json.dumps(audit,sort_keys=True))
raise SystemExit(0 if not audit["errors"] else 1)
