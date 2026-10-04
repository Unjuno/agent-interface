"""Independent raw-only audit for the v39 owner-cleanup composition control."""
import copy
import json
import sys
from pathlib import Path


def evaluate(raw):
    checks = {}
    events = raw.get("events", [])
    receipts = [row for row in events if row.get("event") == "input_release_transition"]
    admissions = [row for row in events if row.get("event") == "input_admission"]
    owner_cleanup = [row for row in raw.get("owner_events", [])
                     if row.get("event") == "owner_release"]
    checks["v39_backend_selected"] = raw.get("backend_class") == \
        "doom_typed_release_backend_v3.Backend"
    checks["wrapper_selected"] = raw.get("wrapper_class") == \
        "input_transition_owner_v3.InputOwner"
    checks["one_admission_and_release_receipt"] = len(admissions) == 1 and len(receipts) == 1
    if len(receipts) == 1:
        row = receipts[0]
        checks["snapshot_preceded_cleanup"] = row.get("cancel_requested_at_request") is False
        checks["owner_cleanup_correlated"] = (
            row.get("owner_release_history_complete") is True and
            row.get("owner_cleanup_intervened") is True)
        checks["fail_closed_batch_publication"] = (
            row.get("ordinary_release_candidate") is False and
            row.get("owner_transition_verified") is False and
            row.get("owned_keycodes_after_batch") == [] and
            row.get("release_batch_size") == 1 and
            row.get("release_batch_position") == 0)
    else:
        checks["snapshot_preceded_cleanup"] = False
        checks["owner_cleanup_correlated"] = False
        checks["fail_closed_batch_publication"] = False
    checks["one_verified_cleanup"] = (
        len(owner_cleanup) == 1 and owner_cleanup[0].get("reason") == "cancelled" and
        owner_cleanup[0].get("verified") is True and owner_cleanup[0].get("keys_down") == [])
    checks["one_keypress_one_keyrelease"] = (
        raw.get("xtest_events") == [[2, 38], [3, 38]])
    checks["no_key_left_down"] = raw.get("down_after") == []
    return checks


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("candidate.raw.json")
    raw = json.loads(path.read_text(encoding="utf-8"))
    checks = evaluate(raw)
    mutated = copy.deepcopy(raw)
    row = next((r for r in mutated.get("events", [])
                if r.get("event") == "input_release_transition"), None)
    if row:
        row["owner_transition_verified"] = True
    checks["mutation_verified_claim_rejected"] = not all(evaluate(mutated).values())
    report = {"schema": "v39-owner-cleanup-composition-audit-v1",
              "gate": "PASS_CONSTRUCTION_OWNER_CLEANUP_FAIL_CLOSED" if all(checks.values())
                      else "FAIL_OR_HOLD_COMPOSITION_CONTROL",
              "checks": checks,
              "failed_checks": sorted(name for name, value in checks.items() if not value)}
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["gate"] == "PASS_CONSTRUCTION_OWNER_CLEANUP_FAIL_CLOSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
