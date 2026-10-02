"""Independent raw-only integrity and invariant audit; does not import experiment.py."""
import json
import sys
from copy import deepcopy
from collections import Counter
from pathlib import Path


def violations(state):
    found = []
    live_authority = set(state["grants"]) - set(state["revocations"])
    if len(live_authority) > 1:
        found.append("authority_capacity")
    if len(state["reservations"]) > 1:
        found.append("quota_capacity")
    expired = [pair for pair in state["admissions"]
               if pair[0] not in state["invalidated"] and pair[1] != state["epoch"]]
    if expired:
        found.append("stale_admission_active")
    effects = Counter(pair[1] for pair in state["commits"])
    if any(count > 1 for count in effects.values()):
        found.append("duplicate_semantic_effect")
    if set(state["revocations"]) & live_authority:
        found.append("revoked_authority_active")
    return sorted(found)


def audit(raw, expected):
    errors = []
    if raw.get("schema") != "issue-5547-invariant-confluence-raw-v1":
        errors.append("schema")
    if raw.get("source_main") != "59ffec5d551b0adcf11057eee6da814237a748c8":
        errors.append("source_main")
    rows = raw.get("pair_rows")
    if not isinstance(rows, list) or len(rows) != raw.get("ordered_pair_count"):
        return ["pair_rows_count"]
    seen = set()
    actual_command_pairs = set()
    observed_conflicts = set()
    serial_safe = True
    for i, row in enumerate(rows):
        left = row.get("left")
        right = row.get("right")
        if not isinstance(left, dict) or not isinstance(right, dict):
            errors.append(f"row:{i}:command_shape")
            continue
        key = json.dumps([left, right], sort_keys=True, separators=(",", ":"))
        if key in seen:
            errors.append(f"row:{i}:duplicate_ordered_pair")
        seen.add(key)
        actual_command_pairs.add(key)
        expected_join = {
            "evidence": sorted(set(row["left_state"]["evidence"]) | set(row["right_state"]["evidence"])),
            "grants": sorted(set(row["left_state"]["grants"]) | set(row["right_state"]["grants"])),
            "revocations": sorted(set(row["left_state"]["revocations"]) | set(row["right_state"]["revocations"])),
            "epoch": max(row["left_state"]["epoch"], row["right_state"]["epoch"]),
            "admissions": sorted({tuple(x) for x in row["left_state"]["admissions"]} | {tuple(x) for x in row["right_state"]["admissions"]}),
            "invalidated": sorted(set(row["left_state"]["invalidated"]) | set(row["right_state"]["invalidated"])),
            "reservations": sorted(set(row["left_state"]["reservations"]) | set(row["right_state"]["reservations"])),
            "commits": sorted({tuple(x) for x in row["left_state"]["commits"]} | {tuple(x) for x in row["right_state"]["commits"]}),
        }
        expected_join["admissions"] = [list(x) for x in expected_join["admissions"]]
        expected_join["commits"] = [list(x) for x in expected_join["commits"]]
        if row.get("join_lr") != expected_join or row.get("join_rl") != expected_join:
            errors.append(f"row:{i}:join_reconstruction")
        actual_errors = violations(expected_join)
        if row.get("join_invariant_errors") != actual_errors:
            errors.append(f"row:{i}:join_invariant_receipt")
        if actual_errors:
            observed_conflicts.add(tuple(sorted((left["kind"], right["kind"]))))
        for name in ("serial_lr_state", "serial_rl_state"):
            serial_errors = violations(row[name])
            if serial_errors:
                serial_safe = False
            if serial_errors and not row.get("serial_invariant_errors"):
                errors.append(f"row:{i}:serial_receipt")
    expected_pairs = {tuple(x) for x in expected["conflict_families"]}
    expected_sorted = [list(x) for x in sorted(expected_pairs)]
    actual_sorted = [list(x) for x in sorted(observed_conflicts)]
    if actual_sorted != expected_sorted or raw.get("actual_conflict_families") != actual_sorted:
        errors.append("conflict_matrix")
    participants = {name for pair in observed_conflicts for name in pair}
    computed_classes = {name: ("coordination_required" if name in participants else "monotone_safe")
                        for name in ("ADD_EVIDENCE", "ADMIT_EFFECT", "COMMIT_EFFECT", "GRANT_TOKEN",
                                     "REFRESH_EPOCH", "RESERVE_QUOTA", "REVOKE_CLAIM")}
    computed_classes["UNKNOWN_SCHEMA"] = "coordination_required"
    if raw.get("classifications") != computed_classes:
        errors.append("classifications")
    commands = expected.get("commands", [])
    frozen_command_pairs = {
        json.dumps([left, right], sort_keys=True, separators=(",", ":"))
        for left in commands for right in commands
    }
    if actual_command_pairs != frozen_command_pairs or len(commands) != expected.get("command_count"):
        errors.append("frozen_command_matrix")
    if not serial_safe or raw.get("serial_baseline_invariant_safe") is not serial_safe:
        errors.append("serial_baseline")
    safe_families = {"ADD_EVIDENCE", "REVOKE_CLAIM"}
    safe_pairs_safe = all(
        not row.get("join_invariant_errors")
        for row in rows
        if row["left"]["kind"] in safe_families or row["right"]["kind"] in safe_families
    )
    if raw.get("safe_operation_pairs_invariant_safe") is not safe_pairs_safe or not safe_pairs_safe:
        errors.append("safe_join_summary")
    commutative = all(row.get("join_lr") == row.get("join_rl") for row in rows)
    if raw.get("all_join_argument_orders_equal") is not commutative or not commutative:
        errors.append("join_order_summary")
    if raw.get("disposition") != "PASS_BOUNDED_FINITE_MODEL":
        errors.append("disposition")
    if raw.get("ordered_pair_count") != expected.get("ordered_pair_count"):
        errors.append("frozen_pair_count")
    return errors


def mutation_controls(raw, expected):
    mutations = {}
    bad = deepcopy(raw)
    bad["pair_rows"].pop()
    mutations["drop_pair_row"] = bad
    bad = deepcopy(raw)
    bad["pair_rows"][0]["join_lr"]["epoch"] += 1
    mutations["corrupt_join_epoch"] = bad
    bad = deepcopy(raw)
    bad["actual_conflict_families"].pop()
    mutations["remove_conflict_family"] = bad
    bad = deepcopy(raw)
    bad["classifications"]["REVOKE_CLAIM"] = "coordination_required"
    mutations["misclassify_safe_operation"] = bad
    bad = deepcopy(raw)
    bad["serial_baseline_invariant_safe"] = False
    mutations["flip_serial_baseline_summary"] = bad
    return {name: bool(audit(mutant, expected)) for name, mutant in mutations.items()}


if __name__ == "__main__":
    try:
        payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        frozen = json.loads((Path(__file__).resolve().parent / "expected.json").read_text(encoding="utf-8"))
    except Exception as exc:
        print(json.dumps({"passed": False, "errors": [f"input:{type(exc).__name__}"]}, sort_keys=True))
        raise SystemExit(2)
    found = audit(payload, frozen)
    controls = mutation_controls(payload, frozen)
    missed = [name for name, rejected in controls.items() if not rejected]
    result = {"passed": not found and not missed, "errors": found,
              "ordered_pair_count": payload.get("ordered_pair_count"),
              "mutation_controls": {"rejected": sum(controls.values()), "total": len(controls),
                                    "results": controls}, "missed_mutations": missed}
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["passed"] else 1)
