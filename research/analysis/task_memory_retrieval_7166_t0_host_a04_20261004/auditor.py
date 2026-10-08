#!/usr/bin/env python3
"""Independent raw-only auditor with explicit non-no-op mutation checks."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def source_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def expected(case):
    if case["task_need"] == "current_only":
        return "NONE"
    if (not case["identity_unique"] or not case["source_hash"] or not case["lineage_linear"]
            or source_digest(case["source"]) != case["source_hash"]):
        return "ABSTAIN"
    return "EVENT_CHAIN"


def audit_rows(cases, rows):
    if len(cases) != 72 or len(rows) != 72:
        return False, "wrong_denominator"
    if len({x.get("case_id") for x in rows}) != 72:
        return False, "duplicate_or_missing_case"
    by_id = {x["case_id"]: x for x in rows}
    for case in cases:
        row = by_id.get(case["case_id"])
        if row is None or row.get("label") != expected(case):
            return False, "label_or_case_mismatch"
        if row.get("source_hash") != case["source_hash"]:
            return False, "provenance_mismatch"
        want_events = case["source"]["event_ids"] if expected(case) == "EVENT_CHAIN" else []
        if row.get("event_ids") != want_events:
            return False, "event_lineage_mismatch"
        if row.get("authority_granted") is not False or row.get("authority_scope") is not None:
            return False, "authority_escalation"
    return True, "PASS"


def mutations():
    return {
        "wrong_label": lambda r: r[0].__setitem__("label", "ABSTAIN"),
        "source_hash_tamper": lambda r: r[12].__setitem__("source_hash", "0" * 64),
        "ambiguous_identity_pick": lambda r: r[24].__setitem__("label", "EVENT_CHAIN"),
        "authority_escalation": lambda r: r[0].__setitem__("authority_granted", True),
        "dropped_history_event": lambda r: r[12].__setitem__("event_ids", ["forged"]),
        "forked_lineage_pick": lambda r: r[48].__setitem__("label", "EVENT_CHAIN"),
    }


def main():
    fixture = json.loads((ROOT / "fixture.json").read_text())
    raw = json.loads((ROOT / "results" / "candidate.json").read_text())
    passed, reason = audit_rows(fixture["cases"], raw["rows"])
    controls = {}
    effective = {}
    before = json.dumps(raw["rows"], sort_keys=True, separators=(",", ":"))
    for name, mutate in mutations().items():
        changed = json.loads(json.dumps(raw["rows"]))
        mutate(changed)
        after = json.dumps(changed, sort_keys=True, separators=(",", ":"))
        effective[name] = before != after
        rejected, _ = audit_rows(fixture["cases"], changed)
        controls[name] = effective[name] and not rejected
    result = {
        "disposition": "PASS_METHOD_SCOPED" if passed and all(effective.values()) and all(controls.values()) else "FAIL_METHOD",
        "base_audit": reason,
        "rows": len(raw["rows"]),
        "mutation_effective": effective,
        "mutation_rejected": controls,
        "scope": "authored deterministic fixture contract only; no model, GUI, retrieval utility, cost, task-effect, latency, or runtime claim",
    }
    (ROOT / "results" / "audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    if result["disposition"] != "PASS_METHOD_SCOPED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
