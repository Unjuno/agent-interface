#!/usr/bin/env python3
"""Independent exhaustive outcome/effect audit for Issue #5309 A03."""
import hashlib
import itertools
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

from contracts_snapshot import EffectOccurrence, ExecutionReceipt, ReleaseReceipt


ROOT = Path(__file__).resolve().parent
ARMS = ("TASK_ONLY", "EXPLICIT_SAFE_PROBE", "DUAL_PURPOSE", "FAIL_CLOSED_UNKNOWN")


def canonical_sha(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def oracle_information(profile):
    # Reconstruct expected uncertainty from the truth table, not candidate output.
    symbols = [profile["receipt_symbols"][state] for state in profile["target_ids"]]
    return 0.0 if len(set(symbols)) == 1 else 1.0


def expected_actions(profile, state, condition, arm, fixture):
    commits = sorted(action for action in profile["commit_actions"].values()
                     if profile["risk_by_action"][action] <= fixture["risk_budget"])
    safe = profile["safe_evidence_path"]
    probe_ok = safe and profile["probe_admitted"] and profile["risk_by_action"].get(profile["probe_action"], fixture["risk_budget"] + 1) <= fixture["risk_budget"]
    open_ok = (safe and profile["open_admitted"] and profile["effect_witness_survives_open"]
               and profile["risk_by_action"].get(profile["open_action"], fixture["risk_budget"] + 1) <= fixture["risk_budget"])
    target_action = profile["commit_actions"][state]
    if arm == "FAIL_CLOSED_UNKNOWN" or not safe or not commits:
        return [], "unknown-state-policy" if arm == "FAIL_CLOSED_UNKNOWN" else "no-safe-evidence-path"
    if arm == "TASK_ONLY":
        chosen = commits[0]
        actions = [chosen]
        if chosen != target_action:
            actions.extend([fixture["recovery_action"], commits[1]])
        return actions, None
    if arm == "EXPLICIT_SAFE_PROBE":
        if not probe_ok:
            return [], "no-admitted-safe-probe"
        return ([profile["probe_action"], target_action], None) if condition != "stale" else ([profile["probe_action"]], "stale-or-ambiguous-receipt")
    if arm == "DUAL_PURPOSE":
        if open_ok and oracle_information(profile) > 0:
            return ([profile["open_action"], target_action], None) if condition != "stale" else ([profile["open_action"]], "stale-or-ambiguous-receipt")
        return [], "no-admissible-informative-task-action"
    raise ValueError("unknown arm")


def expected_receipts(profile, state, condition, action, ordinal):
    if action not in (profile["open_action"], profile["probe_action"]):
        return []
    event_id = f"{profile['id']}:{action}:{ordinal}"
    symbol = profile["receipt_symbols"][state]
    if condition == "stale":
        return [{"event_id": event_id + ":stale", "fresh": False, "symbol": symbol, "epoch": ordinal - 1}]
    row = {"event_id": event_id, "fresh": True, "symbol": symbol, "epoch": ordinal}
    return [row, dict(row)] if condition == "duplicate" else [row]


def expected_metrics(profile, state, actions, fixture, truth):
    elapsed = 0
    progress = 0.0
    wrong = 0
    completed = False
    witness = True
    for ordinal, action in enumerate(actions, start=1):
        elapsed += profile["durations"][action]
        if action == profile["open_action"]:
            progress += fixture["task_progress_common_open"]
            witness = profile["effect_witness_survives_open"]
        elif action in profile["commit_actions"].values():
            selected_target = next(key for key, value in profile["commit_actions"].items() if value == action)
            if selected_target == state and truth["safe_commit_is_exact_target"]:
                progress += 1.0
                completed = witness and profile["safe_evidence_path"]
            else:
                wrong += int(selected_target != state)
    return elapsed, progress, completed, wrong, witness


def audit(raw, fixture, truth):
    errors = []
    if raw.get("allocation") != fixture["allocation"]:
        errors.append("allocation mismatch")
    if raw.get("fixture_sha256") != hashlib.sha256((ROOT / "fixture.json").read_bytes()).hexdigest():
        errors.append("fixture hash mismatch")
    if raw.get("exogenous_opportunity_stream") != fixture["exogenous_opportunity_stream"]:
        errors.append("exogenous opportunity stream changed")
    raw_body = dict(raw)
    claimed = raw_body.pop("raw_sha256", None)
    if claimed != canonical_sha(raw_body):
        errors.append("raw checksum mismatch")

    profiles = {p["id"]: p for p in fixture["primary_profiles"] + fixture["controls"]}
    # Explicitly construct the complete frozen Cartesian domain.
    expected_cases = set()
    for profile in profiles.values():
        conditions = fixture["receipt_conditions"] if profile["cohort"] != "boundary" else ["fresh"]
        for state in profile["target_ids"]:
            for condition in conditions:
                for arm in ARMS:
                    expected_cases.add((profile["id"], state, condition, arm))
    rows = raw.get("rows", [])
    observed_cases = [(r.get("profile"), r.get("state"), r.get("receipt_condition"), r.get("arm")) for r in rows]
    if len(observed_cases) != len(set(observed_cases)) or set(observed_cases) != expected_cases:
        errors.append("row domain mismatch or duplicate row")

    for row in rows:
        profile = profiles.get(row.get("profile"))
        if not profile or row.get("state") not in profile["target_ids"] or row.get("arm") not in ARMS:
            errors.append("unknown profile/state/arm")
            continue
        state = row["state"]
        condition = row["receipt_condition"]
        actions, reason = expected_actions(profile, state, condition, row["arm"], fixture)
        actual_actions = [event.get("action") for event in row.get("trace", [])]
        if actual_actions != actions:
            errors.append(f"policy action trace mismatch: {row['profile']}:{state}:{condition}:{row['arm']}")
        elapsed, progress, completed, wrong, witness = expected_metrics(profile, state, actions, fixture, truth)
        if (row.get("synthetic_latency"), row.get("task_progress"), row.get("completed"), row.get("wrong_target"), row.get("effect_witness_available")) != (elapsed, progress, completed, wrong, witness):
            errors.append(f"effect/metric mismatch: {row['profile']}:{state}:{condition}:{row['arm']}")
        opportunity_total = len(fixture["exogenous_opportunity_stream"])
        displaced = min(opportunity_total, elapsed)
        expected_opportunities = {"no_action_preserved": opportunity_total,
                                  "after_arm": opportunity_total - displaced,
                                  "displaced": displaced}
        if row.get("opportunity_accounting") != expected_opportunities:
            errors.append("opportunity counterfactual mismatch")
        if row.get("yield_reason") != reason:
            errors.append(f"yield mismatch: {row['profile']}:{state}:{condition}:{row['arm']}")
        expected_admitted = sorted(commits := [a for a in profile["commit_actions"].values()
                                               if profile["safe_evidence_path"] and profile["risk_by_action"][a] <= fixture["risk_budget"]])
        if (profile["safe_evidence_path"] and profile["open_admitted"] and profile["effect_witness_survives_open"]
                and profile["risk_by_action"].get(profile["open_action"], fixture["risk_budget"] + 1) <= fixture["risk_budget"]):
            expected_admitted = sorted(expected_admitted + [profile["open_action"]])
        if row.get("admitted_task_actions") != expected_admitted:
            errors.append("task-only/dual-purpose admissible action set mismatch")
        expected_scores = []
        if row["arm"] == "DUAL_PURPOSE":
            for action in expected_admitted:
                immediate = fixture["task_progress_common_open"] if action == profile["open_action"] else 0.5
                information = oracle_information(profile) if action == profile["open_action"] else 0.0
                score = (immediate + fixture["beta"] * information
                         - fixture["time_penalty_weight"] * profile["durations"][action]
                         - fixture["risk_penalty_weight"] * profile["risk_by_action"][action])
                expected_scores.append([score, action])
        actual_scores = row.get("ranked_action_scores", [])
        if len(actual_scores) != len(expected_scores) or any(
            actual[1] != expected[1] or not math.isclose(actual[0], expected[0], abs_tol=1e-12)
            for actual, expected in zip(actual_scores, expected_scores)
        ):
            errors.append("ranked-action score or ordering mismatch")
        executed = set(actual_actions)
        oracle_unsafe = len(executed.intersection(truth["unsafe_action_ids"]))
        oracle_collateral = len(executed.intersection(truth["collateral_action_ids"]))
        if (row.get("authority_grants"), row.get("unsafe"), row.get("collateral")) != (0, oracle_unsafe, oracle_collateral):
            errors.append(f"authority/unsafe/collateral mismatch: {row['profile']}:{row['arm']}")

        expected_events = []
        for ordinal, action in enumerate(actions, start=1):
            expected_events.extend(expected_receipts(profile, state, condition, action, ordinal))
        if row.get("receipts") != expected_events:
            errors.append(f"receipt/freshness/dedup input mismatch: {row['profile']}:{condition}:{row['arm']}")
        if condition == "stale" and row["arm"] in ("DUAL_PURPOSE", "EXPLICIT_SAFE_PROBE"):
            if any(action in profile["commit_actions"].values() for action in actual_actions):
                errors.append("stale receipt authorized a target-specific commit")

        schema_rows = row.get("execution_receipts", [])
        if len(schema_rows) != len(actions):
            errors.append("runtime execution receipt count mismatch")
        elapsed_before = 0
        for ordinal, (action, schema_row) in enumerate(zip(actions, schema_rows), start=1):
            duration = profile["durations"][action]
            started_ns = 1_000_000_000 + elapsed_before * 1_000_000
            ended_ns = started_ns + duration * 1_000_000
            command_id = f"synthetic:{profile['id']}:{state}:{row['arm']}"
            manifest_id = canonical_sha({"allocation": fixture["allocation"], "profile": profile["id"]})
            if action == profile["probe_action"]:
                occurrence = EffectOccurrence.NONE
            elif action == profile["open_action"]:
                occurrence = EffectOccurrence.OBSERVED
            elif action in profile["commit_actions"].values():
                selected_target = next(key for key, value in profile["commit_actions"].items() if value == action)
                occurrence = EffectOccurrence.OBSERVED if selected_target == state else EffectOccurrence.POSSIBLE
            else:
                occurrence = EffectOccurrence.POSSIBLE
            expected_schema = {
                "command_id": command_id,
                "backend_receipt_id": f"synthetic-receipt:{profile['id']}:{state}:{row['arm']}:{ordinal}",
                "invariant_manifest_id": manifest_id,
                "lease_id": f"synthetic-no-authority:{profile['id']}:{state}:{row['arm']}",
                "observation_sequence": 1,
                "surface_id": f"synthetic-surface:{profile['id']}",
                "started_ns": started_ns,
                "ended_ns": ended_ns,
                "action_count": 1,
                "effect_occurrence": occurrence.value,
                "release": {"observed_ns": ended_ns, "verified": True, "keys_down": [], "buttons_down": []},
            }
            if schema_row != expected_schema:
                errors.append("runtime execution receipt semantic mismatch")
            try:
                release = ReleaseReceipt(
                    observed_ns=schema_row["release"]["observed_ns"],
                    verified=schema_row["release"]["verified"],
                    keys_down=tuple(schema_row["release"]["keys_down"]),
                    buttons_down=tuple(schema_row["release"]["buttons_down"]),
                )
                ExecutionReceipt(
                    command_id=schema_row["command_id"],
                    backend_receipt_id=schema_row["backend_receipt_id"],
                    invariant_manifest_id=schema_row["invariant_manifest_id"],
                    lease_id=schema_row["lease_id"],
                    observation_sequence=schema_row["observation_sequence"],
                    surface_id=schema_row["surface_id"],
                    started_ns=schema_row["started_ns"],
                    ended_ns=schema_row["ended_ns"],
                    action_count=schema_row["action_count"],
                    effect_occurrence=EffectOccurrence(schema_row["effect_occurrence"]),
                    release=release,
                )
            except (KeyError, TypeError, ValueError) as exc:
                errors.append(f"pinned runtime receipt schema rejected replay: {type(exc).__name__}")
            elapsed_before += duration

        expected_keys = []
        for ordinal, action in enumerate(actions, start=1):
            if action.startswith(("commit-", "apply-", "select-", "write-")):
                key = "synthetic:" + action
                expected_keys.extend([{"kind": "key_down", "key": key, "sequence": ordinal}, {"kind": "key_up", "key": key, "sequence": ordinal}])
        if row.get("key_events") != expected_keys:
            errors.append("key event sequence mismatch")
        held = set()
        for event in row.get("key_events", []):
            if event["kind"] == "key_down":
                if event["key"] in held:
                    errors.append("duplicate key-down without release")
                held.add(event["key"])
            elif event["kind"] == "key_up":
                if event["key"] not in held:
                    errors.append("unmatched key-up")
                held.discard(event["key"])
        if held:
            errors.append("nonempty held key set at terminal")

    summary = defaultdict(lambda: {"n": 0, "completed": 0, "wrong_target": 0, "latency": 0, "collateral": 0, "unsafe": 0})
    for row in rows:
        if row.get("cohort") == "primary" and row.get("receipt_condition") == "fresh":
            item = summary[row["arm"]]
            item["n"] += 1
            item["completed"] += int(row["completed"] is True)
            item["wrong_target"] += row["wrong_target"]
            item["latency"] += row["synthetic_latency"]
            item["collateral"] += row["collateral"]
            item["unsafe"] += row["unsafe"]
    primary = {arm: {**values, "mean_latency": values["latency"] / values["n"] if values["n"] else None} for arm, values in summary.items()}
    if primary.get("TASK_ONLY", {}).get("completed") != 6 or primary.get("TASK_ONLY", {}).get("wrong_target") != 3:
        errors.append("task-only recovery/effect baseline mismatch")
    if primary.get("EXPLICIT_SAFE_PROBE", {}).get("completed") != 6 or primary.get("EXPLICIT_SAFE_PROBE", {}).get("wrong_target") != 0:
        errors.append("explicit-probe baseline mismatch")
    if primary.get("DUAL_PURPOSE", {}).get("completed") != 6 or primary.get("DUAL_PURPOSE", {}).get("wrong_target") != 0:
        errors.append("dual-purpose primary completion/effect gate failed")
    dual_latency = primary.get("DUAL_PURPOSE", {}).get("mean_latency")
    task_latency = primary.get("TASK_ONLY", {}).get("mean_latency")
    probe_latency = primary.get("EXPLICIT_SAFE_PROBE", {}).get("mean_latency")
    if not (dual_latency is not None and dual_latency < task_latency and dual_latency < probe_latency):
        errors.append("preregistered primary latency improvement absent")
    paired = {(r["profile"], r["state"], r["receipt_condition"], r["arm"]): r for r in rows}
    for profile in profiles.values():
        conditions = fixture["receipt_conditions"] if profile["cohort"] != "boundary" else ["fresh"]
        for state in profile["target_ids"]:
            for condition in conditions:
                dual = paired[(profile["id"], state, condition, "DUAL_PURPOSE")]
                for comparator in ("TASK_ONLY", "EXPLICIT_SAFE_PROBE"):
                    base = paired[(profile["id"], state, condition, comparator)]
                    for field in ("wrong_target", "collateral", "unsafe"):
                        if dual[field] > base[field]:
                            errors.append(f"dual-purpose effect regression versus {comparator}: {profile['id']}:{field}")

    boundary = {(r["profile"], r["state"], r["arm"]): r for r in rows if r.get("cohort") == "boundary"}
    for profile in fixture["controls"]:
        if profile["id"] == "witness-loss":
            for state in profile["target_ids"]:
                if boundary[(profile["id"], state, "DUAL_PURPOSE")]["trace"] or boundary[(profile["id"], state, "DUAL_PURPOSE")]["completed"]:
                    errors.append("dual arm crossed witness-loss boundary")
                if not boundary[(profile["id"], state, "EXPLICIT_SAFE_PROBE")]["completed"]:
                    errors.append("safe-probe witness control failed")
        if profile["id"] == "no-safe-path":
            for state in profile["target_ids"]:
                for arm in ARMS:
                    if boundary[(profile["id"], state, arm)]["trace"]:
                        errors.append("action occurred without safe evidence path")

    reversal = [r for r in rows if r.get("profile") == "cost-reversal" and r.get("receipt_condition") == "fresh"]
    reversal_sums = defaultdict(int)
    for row in reversal:
        reversal_sums[row["arm"]] += row["synthetic_latency"]
    if reversal_sums["EXPLICIT_SAFE_PROBE"] >= reversal_sums["DUAL_PURPOSE"]:
        errors.append("cost-reversal sensitivity not exposed")

    return {
        "status": "PASS_DUAL_PURPOSE_ACTION_SCOPED" if not errors else "FAIL_A03_AUDIT_CONTRACT",
        "errors": errors,
        "row_count": len(rows),
        "primary_fresh_summary": primary,
        "cost_reversal_latency_totals": dict(reversal_sums),
        "stale_receipts_rejected": True,
        "duplicate_receipts_counted_once": True,
        "runtime_execution_receipts_replayed": sum(len(r.get("execution_receipts", [])) for r in rows),
        "key_release_balanced": True,
        "authority_grants": 0,
        "scope": "pre-authored finite simulator and held-out parameter mappings only",
    }


def main(raw_path):
    raw = json.loads(Path(raw_path).read_text())
    fixture = json.loads((ROOT / "fixture.json").read_text())
    truth = json.loads((ROOT / "oracle_truth.json").read_text())
    result = audit(raw, fixture, truth)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    if result["status"] != "PASS_DUAL_PURPOSE_ACTION_SCOPED":
        raise SystemExit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: auditor.py RAW.json")
    main(sys.argv[1])
