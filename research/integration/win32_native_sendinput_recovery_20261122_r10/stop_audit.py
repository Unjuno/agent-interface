"""Post-hoc custody audit for an R10 pre-dispatch readiness stop."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACKET = Path(__file__).resolve().parent
RUN = PACKET / "run"


def verify_manifest(path, base):
    errors = []
    rows = path.read_text(encoding="ascii").splitlines()
    for row in rows:
        expected, relative = row.split("  ", 1)
        target = base / relative
        actual = hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else None
        if actual != expected:
            errors.append({"path": relative, "expected": expected, "actual": actual})
    return {"entries": len(rows), "errors": errors}


pretrial = verify_manifest(PACKET / "PRETRIAL_SHA256SUMS", ROOT)
raw = verify_manifest(RUN / "SHA256SUMS", RUN)
d = json.loads((RUN / "result.json").read_text(encoding="utf-8"))
events = [json.loads(line) for line in
    (RUN / "fixture" / "events.jsonl").read_text(encoding="utf-8").splitlines()]
meta = json.loads((RUN / "fixture" / "meta.json").read_text(encoding="utf-8"))
server_requests = list((RUN / "server").rglob("request.json"))
checks = {
    "frozen_attempt_id": d.get("attempt_id") == "win32-native-sendinput-r10-20261122",
    "stopped_at_fixture_preflight": d.get("error") ==
        "fresh owned fixture/foreground/SHIFT-up preflight failed; no input sent",
    "no_public_dispatch_or_call": not server_requests and "call_id" not in d
        and "public_observation" not in d,
    "no_fixture_effect": not (RUN / "fixture" / "effect.json").exists()
        and events == [{"hwnd": meta["hwnd"], "kind": "ready"}],
    "cleanup_completed": d.get("cleanup", {}).get("fixture_exit_code") == 0
        and d["cleanup"].get("foreground_before")
            == d["cleanup"].get("foreground_after_restore"),
    "first_outcome_retained_without_retry": d.get("classification") ==
        "FAIL_OR_UNKNOWN_FIRST_OUTCOME_RETAINED"
        and len(list(RUN.rglob("result.json"))) == 1,
    "pretrial_and_raw_hashes_valid": not pretrial["errors"] and not raw["errors"],
}
audit = {"attempt_id": d.get("attempt_id"), "disposition": "EXCLUDED_PRE_DISPATCH",
    "checks": checks, "pretrial_hash_audit": pretrial, "raw_hash_audit": raw,
    "custody_and_exclusion_audit_pass": all(checks.values()),
    "experiment_acceptance_pass": False,
    "note": "This audit classifies and preserves a readiness-stop only. It does not qualify an authority-expiry/recovery trial."}
(PACKET / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n",
    encoding="utf-8", newline="\n")
print(json.dumps(audit, indent=2, sort_keys=True))
if not audit["custody_and_exclusion_audit_pass"]:
    raise SystemExit(1)
