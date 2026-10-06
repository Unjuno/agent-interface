#!/usr/bin/env python3
"""Independent raw-only auditor; deliberately does not import candidate.py."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected(case, delay, presentation):
    effect = case["effect"]
    events = [{"kind": "action", **a} for a in case["actions"]]
    row = {"kind": "effect", "effect_id": effect["effect_id"],
           "target": effect["target"], "time_ms": effect["observed_at_ms"]}
    if presentation == "SOURCE_BOUND_RECEIPT":
        row.update({"causal_link_status": effect["causal_link_status"],
                    "source_action_id": effect["source_action_id"],
                    "source_actor": effect["source_actor"], "evidence_id": effect["evidence_id"]})
    events.append(row)
    events.sort(key=lambda item: (item["time_ms"], item["kind"], item.get("action_id", item.get("effect_id", ""))))
    return {"case_id": case["case_id"], "display_delay_ms": delay,
            "effect_display_at_ms": effect["observed_at_ms"] + delay,
            "presentation": presentation, "events": events}


def audit_records(ledger, records):
    expected_keys = {(case["case_id"], delay, fmt)
                     for case in ledger["cases"] for delay in (300, 1500)
                     for fmt in ("CHRONOLOGICAL_SUMMARY", "SOURCE_BOUND_RECEIPT")}
    seen = set()
    errors = []
    by_id = {case["case_id"]: case for case in ledger["cases"]}
    for index, record in enumerate(records):
        key = (record.get("case_id"), record.get("display_delay_ms"), record.get("presentation"))
        if key in seen:
            errors.append(f"duplicate record {key}")
        seen.add(key)
        case = by_id.get(record.get("case_id"))
        if case is None:
            errors.append(f"unknown case at row {index}")
            continue
        want = expected(case, record.get("display_delay_ms"), record.get("presentation"))
        if record != want:
            errors.append(f"row {index} differs from independently rendered frozen-ledger projection")
    if seen != expected_keys:
        errors.append(f"condition coverage mismatch missing={len(expected_keys-seen)} extra={len(seen-expected_keys)}")
    return errors


def controls(ledger, records):
    base = copy.deepcopy(records)
    index = next(i for i, r in enumerate(base) if r["presentation"] == "SOURCE_BOUND_RECEIPT" and r["case_id"] == "agent_linked")
    controls = {}
    for name, mutate in (
        ("actor", lambda rows: rows[index]["events"][-1].__setitem__("source_actor", "human")),
        ("action_id", lambda rows: rows[index]["events"][-1].__setitem__("source_action_id", "a_external")),
        ("target", lambda rows: rows[index]["events"][-1].__setitem__("target", "doc_wrong")),
        ("effect_id", lambda rows: rows[index]["events"][-1].__setitem__("effect_id", "e_wrong")),
        ("event_order", lambda rows: rows[index]["events"].reverse()),
        ("causal_link_status", lambda rows: rows[index]["events"][-1].__setitem__("causal_link_status", "UNKNOWN")),
    ):
        changed = copy.deepcopy(base)
        mutate(changed)
        controls[name] = bool(audit_records(ledger, changed))
    unknown = next(i for i, r in enumerate(base) if r["presentation"] == "SOURCE_BOUND_RECEIPT" and r["case_id"] == "unknown_conflicting_provenance")
    unknown_event = base[unknown]["events"][-1]
    controls["unknown_not_relabelled"] = (unknown_event["causal_link_status"] == "UNKNOWN"
                                          and unknown_event["source_action_id"] is None
                                          and unknown_event["source_actor"] == "UNKNOWN")
    return controls


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    ledger_path = HERE / "frozen_ledger.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    raw_path = args.out / "presentations.jsonl"
    records = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines() if line]
    errors = audit_records(ledger, records)
    control_results = controls(ledger, records)
    result = {
        "status": "PASS_METHOD_SCOPED" if not errors and all(control_results.values()) else "FAIL_METHOD_SCOPED",
        "audited_records": len(records), "errors": errors,
        "mutation_controls_rejected": sum(v for k, v in control_results.items() if k != "unknown_not_relabelled"),
        "mutation_controls_total": 6,
        "unknown_control_preserved": control_results["unknown_not_relabelled"],
        "controls": control_results,
        "ledger_sha256": sha(ledger_path), "raw_sha256": sha(raw_path),
        "scope": "synthetic provenance/presentation method only; no human interpretation, GUI, model, causality discovery, authorization, or product result",
    }
    audit_path = args.out / "audit.json"
    audit_path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS_METHOD_SCOPED" else 1)


if __name__ == "__main__":
    main()
