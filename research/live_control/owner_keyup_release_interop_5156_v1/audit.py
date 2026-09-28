"""Independent raw-result auditor for the Issue #5156 compatibility probe."""
import argparse
import hashlib
import json
from pathlib import Path

EXPECTED = {
    "main": "53b93cd5dcb0fbbedee1db23ddf550ba1eb289e0",
    "owner": "341b3c01649943ddaad5f28431a792c4889cc36e",
    "wrapper": "0ea631abcf6272f0538a9ef9198ad8069b47b464",
    "protocol": "55272e127073a84c9eb541bc650fee74f3fc7123",
}
OWNER_REASONS = {"cancelled", "expired", "focus_changed", "stop_requested", "surface_changed", "thread_exit"}
CONTRACT_REASONS = {"cancelled", "focus_invalid", "lease_expired", "owner_close", "owner_stop"}
EXPECTED_MISMATCHES = {f"owner_reason:{x}" for x in OWNER_REASONS - CONTRACT_REASONS}
EXPECTED_MISMATCHES.add("owner_button_up_integer_identity")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("result", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    value = json.loads(args.result.read_text(encoding="utf-8"))
    checks = value.get("checks", [])
    seen = {r.get("case") for r in checks if r.get("accepted") != r.get("expected")}
    all_rows_valid = all(r.get("expected") is True and type(r.get("accepted")) is bool for r in checks)
    ok = (
        value.get("schema") == "issue-5156-release-protocol-interop-probe-v1"
        and value.get("classification") == "CONSTRUCTION_COMPATIBILITY_DIAGNOSTIC_NOT_FORMAL_X11"
        and value.get("decision") == "FAIL_RELEASE_RECEIPT_INTEROP"
        and value.get("pins", {}).get("main") == EXPECTED["main"]
        and value.get("source_git_blobs") == {"owner": EXPECTED["owner"], "wrapper": EXPECTED["wrapper"], "protocol": EXPECTED["protocol"]}
        and set(value.get("owner_autonomous_reasons", [])) == OWNER_REASONS
        and set(value.get("protocol_autonomous_reasons", [])) == CONTRACT_REASONS
        and seen == EXPECTED_MISMATCHES
        and len(checks) == 7 and all_rows_valid
        and value.get("authority_grants") == 0
        and value.get("x11_or_input_used") is False
    )
    audit = {
        "schema": "issue-5156-release-interop-audit-v1",
        "status": "PASS_EXPECTED_COMPATIBILITY_FAILURES_REPRODUCED" if ok else "FAIL_AUDIT",
        "errors": [] if ok else ["raw result does not match independently frozen source/expected mismatch set"],
        "result_sha256": sha(args.result),
        "expected_mismatch_count": len(EXPECTED_MISMATCHES),
        "observed_mismatches": sorted(seen),
        "authority_grants": 0,
        "x11_or_input_used": False,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2, sort_keys=True))
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
