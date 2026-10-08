"""Independent raw-only reconstruction for the #6509 finite trace experiment."""
import hashlib
import json
import sys
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def reconstruct(scenario, policy, spec):
    finished = []
    time_ms = 0
    seen = {}
    collision = False
    invalid = False
    for item in scenario["receipts"]:
        check, value, generation, durable = item
        time_ms += spec["service_ms"][check]
        if time_ms > min(scenario["cut_ms"], spec["deadline_ms"]):
            break
        if not durable:
            continue
        claim = scenario.get("claim_override", spec["claim"])
        old = seen.get((check, generation))
        collision |= old is not None and old != value
        seen[(check, generation)] = value
        invalid |= generation != spec["generation"] or claim != spec["claim"]
        finished.append({"check": check, "value": value, "generation": generation,
                         "claim": claim, "completed_ms": time_ms, "durable": True})
    names = {receipt["check"] for receipt in finished}
    outcome_by_name = {receipt["check"]: receipt["value"] for receipt in finished}
    elapsed_cut = min(time_ms, scenario["cut_ms"], spec["deadline_ms"])
    if collision or invalid:
        expected, expected_time = "PARTIAL_UNKNOWN", elapsed_cut
    elif policy == "UNSAFE_SCALAR_PROGRESS":
        first_positive = next((r for r in finished if r["value"]), None)
        expected = "ALLOW" if first_positive else "PARTIAL_UNKNOWN"
        expected_time = first_positive["completed_ms"] if first_positive else elapsed_cut
    elif policy == "CLAIM_LADDER" and any(r["check"] in ("identity", "effect") and not r["value"] for r in finished):
        negative = next(r for r in finished if r["check"] in ("identity", "effect") and not r["value"])
        expected, expected_time = "COUNTEREXAMPLE", negative["completed_ms"]
    elif set(spec["mandatory"]).issubset(names):
        expected = "COMPLETE_VERDICT" if all(outcome_by_name[name] for name in spec["mandatory"]) else "COUNTEREXAMPLE"
        expected_time = max(r["completed_ms"] for r in finished if r["check"] in spec["mandatory"])
    else:
        expected, expected_time = "PARTIAL_UNKNOWN", elapsed_cut
    if policy == "ALL_OR_NOTHING_TIMEOUT" and expected in ("COUNTEREXAMPLE", "COMPLETE_VERDICT") and not set(spec["mandatory"]).issubset(names):
        expected, expected_time = "PARTIAL_UNKNOWN", elapsed_cut
    expected_replays = 0
    if scenario.get("crash_after"):
        crash_check = scenario["crash_after"]
        crash_index = next((i for i, r in enumerate(finished) if r["check"] == crash_check), None)
        if crash_index is not None:
            expected_replays = len({(r["check"], r["generation"], r["claim"], r["completed_ms"])
                                    for r in finished[:crash_index + 1]})
    if scenario.get("replay_receipts") and "effect" in names:
        expected_replays += len(finished)
    return expected, finished, expected_replays, collision, invalid, expected_time


def audit(spec_path, raw_path):
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    raw = json.loads(Path(raw_path).read_text(encoding="utf-8"))
    errors = []
    if raw.get("schema") != "claim-scoped-verdict-raw-v1": errors.append("schema")
    if raw.get("spec_sha256") != sha(spec_path): errors.append("spec_hash")
    if raw.get("scenario_count") != len(spec["scenarios"]): errors.append("scenario_count")
    expected_count = len(spec["scenarios"]) * len(spec["policies"])
    rows = raw.get("rows", [])
    if len(rows) != expected_count or raw.get("row_count") != expected_count: errors.append("row_count")
    index = 0
    observed = {policy: {"allow": 0, "reject": 0, "unknown": 0, "unsafe_partial_allow": 0,
                         "decision_ms": []} for policy in spec["policies"]}
    for scenario in spec["scenarios"]:
        for policy in spec["policies"]:
            if index >= len(rows): break
            row = rows[index]; index += 1
            if row.get("scenario") != scenario["id"] or row.get("policy") != policy:
                errors.append(f"row_{index-1}_identity")
            expected, receipts, replay_count, collision, invalid, expected_time = reconstruct(scenario, policy, spec)
            if row.get("disposition") != expected: errors.append(f"row_{index-1}_disposition")
            if row.get("decision_ms") != expected_time: errors.append(f"row_{index-1}_decision_time")
            if row.get("durable_receipts") != receipts: errors.append(f"row_{index-1}_receipt_replay")
            if row.get("recovery_replays") != replay_count: errors.append(f"row_{index-1}_recovery_count")
            if row.get("final_commit_count") != (1 if expected == "COMPLETE_VERDICT" else 0):
                errors.append(f"row_{index-1}_commit_idempotency")
            if row.get("consumer_authority") is not False or row.get("consumer_side_effects") != 0:
                errors.append(f"row_{index-1}_consumer_boundary")
            if policy == "CLAIM_LADDER" and expected == "PARTIAL_UNKNOWN" and row.get("disposition") == "ALLOW":
                errors.append(f"row_{index-1}_partial_allow")
            if policy != "UNSAFE_SCALAR_PROGRESS" and expected == "ALLOW" and set(spec["mandatory"]) - {r["check"] for r in receipts}:
                errors.append(f"row_{index-1}_incomplete_allow")
            s = observed[policy]
            s["allow"] += row.get("disposition") == "ALLOW" or row.get("disposition") == "COMPLETE_VERDICT"
            s["reject"] += row.get("disposition") == "COUNTEREXAMPLE"
            s["unknown"] += row.get("disposition") == "PARTIAL_UNKNOWN"
            s["unsafe_partial_allow"] += row.get("reason") == "UNSAFE_SCALAR_PARTIAL_POSITIVE"
            s["decision_ms"].append(row.get("decision_ms"))
    audit = {"schema":"claim-scoped-verdict-audit-v1", "status":"PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT",
             "errors":errors, "rows":len(rows), "scenario_count":len(spec["scenarios"]),
             "policies":observed, "consumer_side_effects":sum(r.get("consumer_side_effects", -1) for r in rows),
             "scope":"finite authored deterministic trace model only; not a GUI/runtime/safety result"}
    return audit


if __name__ == "__main__":
    result = audit(sys.argv[1], sys.argv[2])
    if len(sys.argv) > 3:
        Path(sys.argv[3]).write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    raise SystemExit(0 if result["status"] == "PASS_METHOD_SCOPED" else 2)
