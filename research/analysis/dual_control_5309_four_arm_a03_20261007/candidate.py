#!/usr/bin/env python3
"""Frozen four-policy candidate for the Issue #5309 A03 synthetic comparison."""
import hashlib
import json
from pathlib import Path

from contracts_snapshot import EffectOccurrence, ExecutionReceipt, ReleaseReceipt


ROOT = Path(__file__).resolve().parent
ARMS = ("TASK_ONLY", "EXPLICIT_SAFE_PROBE", "DUAL_PURPOSE", "FAIL_CLOSED_UNKNOWN")


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def entropy(probabilities):
    import math
    return -sum(p * math.log2(p) for p in probabilities if p > 0)


def information_gain(profile, action):
    if action != profile["open_action"]:
        return 0.0
    states = profile["target_ids"]
    prior = [1 / len(states)] * len(states)
    before = entropy(prior)
    buckets = {}
    for state in states:
        symbol = profile["receipt_symbols"][state]
        buckets[symbol] = buckets.get(symbol, 0) + 1
    after = sum((count / len(states)) * entropy([1 / count] * count) for count in buckets.values())
    return before - after


def emit_key_events(action, sequence):
    if not action.startswith(("commit-", "apply-", "select-", "write-")):
        return []
    key = "synthetic:" + action
    return [{"kind": "key_down", "key": key, "sequence": sequence},
            {"kind": "key_up", "key": key, "sequence": sequence}]


def execution_receipt(profile, state, arm, action, sequence, elapsed_before, duration):
    if action == profile["probe_action"]:
        occurrence = EffectOccurrence.NONE
    elif action == profile["open_action"]:
        occurrence = EffectOccurrence.OBSERVED
    elif action in profile["commit_actions"].values():
        target = next(key for key, value in profile["commit_actions"].items() if value == action)
        occurrence = EffectOccurrence.OBSERVED if target == state else EffectOccurrence.POSSIBLE
    else:
        occurrence = EffectOccurrence.POSSIBLE
    command = f"synthetic:{profile['id']}:{state}:{arm}"
    manifest = canonical_sha({"allocation": "5309-FOURARM-A03-HOSTCPU-20261007", "profile": profile["id"]})
    started_ns = 1_000_000_000 + elapsed_before * 1_000_000
    ended_ns = started_ns + duration * 1_000_000
    receipt = ExecutionReceipt(
        command_id=command,
        backend_receipt_id=f"synthetic-receipt:{profile['id']}:{state}:{arm}:{sequence}",
        invariant_manifest_id=manifest,
        lease_id=f"synthetic-no-authority:{profile['id']}:{state}:{arm}",
        observation_sequence=1,
        surface_id=f"synthetic-surface:{profile['id']}",
        started_ns=started_ns,
        ended_ns=ended_ns,
        action_count=1,
        effect_occurrence=occurrence,
        release=ReleaseReceipt(observed_ns=ended_ns, verified=True, keys_down=(), buttons_down=()),
    )
    return {
        "command_id": receipt.command_id,
        "backend_receipt_id": receipt.backend_receipt_id,
        "invariant_manifest_id": receipt.invariant_manifest_id,
        "lease_id": receipt.lease_id,
        "observation_sequence": receipt.observation_sequence,
        "surface_id": receipt.surface_id,
        "started_ns": receipt.started_ns,
        "ended_ns": receipt.ended_ns,
        "action_count": receipt.action_count,
        "effect_occurrence": receipt.effect_occurrence.value,
        "release": {"observed_ns": receipt.release.observed_ns,
                    "verified": receipt.release.verified,
                    "keys_down": list(receipt.release.keys_down),
                    "buttons_down": list(receipt.release.buttons_down)},
    }


def receipt(profile, state, condition, action, ordinal):
    if condition == "stale":
        return [{"event_id": f"{profile['id']}:{action}:{ordinal}:stale", "fresh": False, "symbol": profile["receipt_symbols"][state], "epoch": ordinal - 1}]
    event_id = f"{profile['id']}:{action}:{ordinal}"
    event = {"event_id": event_id, "fresh": True, "symbol": profile["receipt_symbols"][state], "epoch": ordinal}
    if condition == "duplicate":
        return [event, dict(event)]
    return [event]


def unique_fresh_symbols(receipts):
    seen = set()
    symbols = []
    for item in receipts:
        if not item["fresh"] or item["event_id"] in seen:
            continue
        seen.add(item["event_id"])
        symbols.append(item["symbol"])
    return symbols


def simulate(profile, state, condition, arm, fixture):
    trace = []
    receipts = []
    schema_receipts = []
    key_events = []
    elapsed = 0
    progress = 0.0
    authority_grants = 0
    wrong_target = collateral = unsafe = 0
    scored = []
    completion = False
    yield_reason = None
    witness_available = True
    target_to_commit = {symbol: target for target, symbol in profile["receipt_symbols"].items()}
    commit_to_target = {action: target for target, action in profile["commit_actions"].items()}

    def perform(action, action_state=None):
        nonlocal elapsed, progress, wrong_target, completion, witness_available
        elapsed_before = elapsed
        duration = profile["durations"][action]
        elapsed += duration
        event = {"action": action, "duration": duration, "state": action_state, "sequence": len(trace) + 1}
        trace.append(event)
        schema_receipts.append(execution_receipt(profile, state, arm, action, event["sequence"], elapsed_before, duration))
        key_events.extend(emit_key_events(action, event["sequence"]))
        if action == profile["open_action"]:
            progress += fixture["task_progress_common_open"]
            if not profile["effect_witness_survives_open"]:
                witness_available = False
            receipts.extend(receipt(profile, state, condition, action, len(trace)))
        elif action == profile["probe_action"]:
            receipts.extend(receipt(profile, state, condition, action, len(trace)))
        elif action in commit_to_target:
            if commit_to_target[action] == state:
                progress += 1.0
                completion = witness_available and profile["safe_evidence_path"]
            else:
                wrong_target += 1
                progress += 0.0
        return event

    safe_path = profile["safe_evidence_path"]
    admitted_commits = sorted(action for action in profile["commit_actions"].values()
                              if safe_path and profile["risk_by_action"][action] <= fixture["risk_budget"])
    admitted_open = (profile["open_admitted"] and profile["effect_witness_survives_open"] and safe_path
                     and profile["risk_by_action"].get(profile["open_action"], fixture["risk_budget"] + 1) <= fixture["risk_budget"])
    admitted_probe = (profile["probe_admitted"] and safe_path
                      and profile["risk_by_action"].get(profile["probe_action"], fixture["risk_budget"] + 1) <= fixture["risk_budget"])
    admitted_task_actions = sorted(admitted_commits + ([profile["open_action"]] if admitted_open else []))

    if arm == "FAIL_CLOSED_UNKNOWN":
        yield_reason = "unknown-state-policy"
    elif not safe_path or not admitted_commits:
        yield_reason = "no-safe-evidence-path"
    elif arm == "TASK_ONLY":
        # Greedy immediate-utility tie break is lexical; recovery uses the fixed
        # other commit after the independent scorer reports noncompletion.
        first = admitted_commits[0]
        perform(first)
        if not completion:
            perform(fixture["recovery_action"])
            remaining = [action for action in admitted_commits if action != first]
            if remaining:
                perform(remaining[0])
    elif arm == "EXPLICIT_SAFE_PROBE":
        if not admitted_probe:
            yield_reason = "no-admitted-safe-probe"
        else:
            perform(profile["probe_action"])
            symbols = unique_fresh_symbols(receipts)
            if len(symbols) != 1:
                yield_reason = "stale-or-ambiguous-receipt"
            elif symbols[0] not in target_to_commit:
                yield_reason = "unrecognized-receipt"
            else:
                perform(profile["commit_actions"][target_to_commit[symbols[0]]])
    elif arm == "DUAL_PURPOSE":
        # Both task-only and dual-purpose rank this identical admitted set.
        task_actions = list(admitted_task_actions)
        scored = []
        for action in task_actions:
            immediate = fixture["task_progress_common_open"] if action == profile["open_action"] else 0.5
            ig = information_gain(profile, action)
            score = (immediate + fixture["beta"] * ig
                     - fixture["time_penalty_weight"] * profile["durations"][action]
                     - fixture["risk_penalty_weight"] * profile["risk_by_action"][action])
            scored.append((score, action))
        best_score, best_action = max(scored, key=lambda item: (item[0], item[1]))
        if best_action != profile["open_action"] or information_gain(profile, best_action) <= 0:
            yield_reason = "no-admissible-informative-task-action"
        else:
            perform(best_action)
            symbols = unique_fresh_symbols(receipts)
            if len(symbols) != 1:
                yield_reason = "stale-or-ambiguous-receipt"
            elif symbols[0] not in target_to_commit:
                yield_reason = "unrecognized-receipt"
            elif not witness_available:
                yield_reason = "effect-witness-unavailable"
            else:
                perform(profile["commit_actions"][target_to_commit[symbols[0]]])
    else:
        raise ValueError("unknown arm")

    if not completion and not yield_reason:
        yield_reason = "task-not-completed"
    opportunity_total = len(fixture["exogenous_opportunity_stream"])
    opportunity_displaced = min(opportunity_total, elapsed)
    return {
        "profile": profile["id"], "cohort": profile["cohort"], "state": state,
        "receipt_condition": condition, "arm": arm, "trace": trace,
        "admitted_task_actions": admitted_task_actions,
        "receipts": receipts, "execution_receipts": schema_receipts,
        "key_events": key_events,
        "synthetic_latency": elapsed, "task_progress": progress,
        "opportunity_accounting": {"no_action_preserved": opportunity_total,
                                   "after_arm": opportunity_total - opportunity_displaced,
                                   "displaced": opportunity_displaced},
        "completed": completion, "wrong_target": wrong_target,
        "collateral": collateral, "unsafe": unsafe,
        "authority_grants": authority_grants, "yield_reason": yield_reason,
        "effect_witness_available": witness_available,
        "ranked_action_scores": scored if arm == "DUAL_PURPOSE" else [],
    }


def run(fixture):
    rows = []
    for profile in fixture["primary_profiles"] + fixture["controls"]:
        conditions = fixture["receipt_conditions"] if profile["cohort"] != "boundary" else ["fresh"]
        for state in profile["target_ids"]:
            for condition in conditions:
                for arm in ARMS:
                    rows.append(simulate(profile, state, condition, arm, fixture))
    payload = {"allocation": fixture["allocation"],
               "fixture_sha256": hashlib.sha256((ROOT / "fixture.json").read_bytes()).hexdigest(),
               "exogenous_opportunity_stream": fixture["exogenous_opportunity_stream"],
               "rows": rows}
    payload["raw_sha256"] = canonical_sha(payload)
    return payload


def main():
    fixture = json.loads((ROOT / "fixture.json").read_text())
    print(json.dumps(run(fixture), sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
