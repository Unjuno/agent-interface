"""Independently classify the retained fake-helper run and its guard gap."""
import json
from pathlib import Path

from candidate import SUCCESS_STATUS, audit_refresh

ROOT = Path(__file__).resolve().parent
EXPECTED = {
    "one_tic_acknowledged": True,
    "refresh_no_op": False,
    "refresh_two_tics": False,
    "tic_changes_during_score_read": False,
    "refresh_raises": False,
}


def audit():
    raw = json.loads((ROOT / "raw.json").read_text(encoding="utf-8"))
    errors = []
    if raw.get("schema") != "scorer-checkpoint-tic-ack-t0-raw-v1":
        errors.append("schema")
    rows = raw.get("rows")
    if not isinstance(rows, list) or len(rows) != len(EXPECTED):
        errors.append("row_count")
        rows = rows if isinstance(rows, list) else []
    seen = set()
    guard_gaps = []
    controller_continued_without_ack = []
    for row in rows:
        name = row.get("case")
        if name not in EXPECTED or name in seen:
            errors.append(f"unexpected_or_duplicate:{name}")
            continue
        seen.add(name)
        audited = audit_refresh({
            "status": row.get("helper_status"),
            "tic_before": row.get("tic_before"),
            "tic_after": row.get("tic_after"),
            "tic_after_read": row.get("tic_after_read"),
        })
        if audited["qualified"] is not EXPECTED[name]:
            errors.append(f"decision:{name}")
        helper_claimed_success = row.get("helper_status") == SUCCESS_STATUS
        if helper_claimed_success and not audited["qualified"]:
            guard_gaps.append(name)
        controller_accepts = row.get("controller_gate_accepts_receipt") is True
        if controller_accepts and not audited["qualified"]:
            controller_continued_without_ack.append(name)
        if row.get("public_has_values") is not False:
            errors.append(f"public_score_leak:{name}")
    if seen != set(EXPECTED):
        errors.append("case_completeness")
    if set(guard_gaps) != {"refresh_no_op", "refresh_two_tics", "tic_changes_during_score_read"}:
        errors.append("guard_gap_controls")
    if set(controller_continued_without_ack) != set(guard_gaps):
        errors.append("controller_gate_controls")
    return {
        "schema": "scorer-checkpoint-tic-ack-t0-audit-v1",
        "pass": not errors,
        "errors": errors,
        "helper_returned_pending_status_without_ack_qualification": guard_gaps,
        "controller_continues_without_ack_qualification": controller_continued_without_ack,
        "classification": "PENDING_RECEIPT_ACCEPTED_WITHOUT_TIC_ACK" if not errors and controller_continued_without_ack else "NO_GAP_FOUND",
        "claim_scope": "source-helper behavior with synthetic fakes only",
    }


if __name__ == "__main__":
    result = audit()
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    (ROOT / "audit.json").write_text(text, encoding="utf-8")
    print(text, end="")
    raise SystemExit(0 if result["pass"] else 1)
