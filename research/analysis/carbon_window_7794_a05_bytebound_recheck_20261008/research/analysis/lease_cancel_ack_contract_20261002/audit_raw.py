"""Independent audit of frozen Lease cancellation contract raw JSONL."""
import json
import sys
from pathlib import Path

EXPECTED = {
    "cancel_before_deadline": ["cancel_set", "wait_return", "worker_terminal"],
    "deadline_without_cancel": ["wait_expired", "worker_terminal"],
    "cancel_at_deadline": ["cancel_set", "wait_expired", "worker_terminal"],
}


def audit(rows):
    errors = []
    fixtures = [r for r in rows if r.get("event") == "fixture"]
    if len(fixtures) != 1 or fixtures[0].get("scope") != "host-real-Lease-synthetic-clock":
        errors.append("fixture identity/scope invalid")
    for case, event_order in EXPECTED.items():
        cr = [r for r in rows if r.get("case") == case]
        events = [r.get("event") for r in cr if r.get("event") != "case_start"]
        if events != event_order:
            errors.append(f"{case}: event order mismatch")
            continue
        start = next((r for r in cr if r.get("event") == "case_start"), {})
        terminal = next((r for r in cr if r.get("event") == "worker_terminal"), {})
        if case == "cancel_before_deadline":
            ack = next((r for r in cr if r.get("event") == "wait_return"), {})
            cancel = next((r for r in cr if r.get("event") == "cancel_set"), {})
            if ack.get("cancel_ack") is not True or terminal.get("status") != "cancelled":
                errors.append("pre-deadline true acknowledgement was not consumed as cancellation")
            if not (start.get("now_ns", 0) <= cancel.get("now_ns", -1) < start.get("deadline_ns", 0)):
                errors.append("pre-deadline cancellation timing inconsistent")
        elif case == "deadline_without_cancel":
            expired = next((r for r in cr if r.get("event") == "wait_expired"), {})
            if expired.get("now_ns", -1) < start.get("deadline_ns", 0) or terminal.get("status") != "expired":
                errors.append("uncancelled lease expiry misclassified")
        else:
            expired = next((r for r in cr if r.get("event") == "wait_expired"), {})
            cancel = next((r for r in cr if r.get("event") == "cancel_set"), {})
            if cancel.get("now_ns") != start.get("deadline_ns") or expired.get("now_ns") != start.get("deadline_ns"):
                errors.append("deadline-boundary schedule mismatch")
            if terminal.get("status") != "expired":
                errors.append("deadline-boundary expiry must not be called cancel acknowledgement")
    if len([r for r in rows if r.get("event") == "worker_terminal"]) != 3:
        errors.append("expected exactly three worker terminal rows")
    return {"decision": "PASS_LEASE_CANCEL_ACK_CONTRACT_SCOPED" if not errors else "FAIL_LEASE_CANCEL_ACK_CONTRACT",
            "cases": 3, "rows": len(rows), "errors": errors,
            "scope": "actual Lease primitive with synthetic clock; no executor timing or external effect"}


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: audit_raw.py RAW.jsonl OUT.json")
    rows = [json.loads(x) for x in Path(argv[1]).read_text(encoding="utf-8").splitlines() if x]
    result = audit(rows)
    Path(argv[2]).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["decision"].startswith("PASS_") else 1)


if __name__ == "__main__":
    main(sys.argv)
