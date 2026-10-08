#!/usr/bin/env python3
"""Independent raw-only GUI-trace auditor; imports neither candidate nor fixture."""

import argparse
import copy
import json
from pathlib import Path

ARMS = ("adaptive", "no_probe", "one_step")
FAMILIES = {
    "separable": {"A", "B"},
    "action_equivalent": {"C", "D"},
    "impossible": {"E", "F"},
    "stale": {"G", "H"},
    "convergent": {"I", "J"},
}
STATE_FAMILY = {state: family for family, states in FAMILIES.items() for state in states}


def expected_signal(state: str, probes: list[str]) -> str:
    if not probes:
        return "READY"
    if probes == ["P"]:
        return "READY"
    if probes != ["P", "Q"]:
        return "INVALID_SEQUENCE"
    return {
        "A": "LEFT", "B": "RIGHT", "C": "READY", "D": "READY",
        "E": "UNKNOWN", "F": "UNKNOWN", "G": "EXPIRED_LEFT", "H": "EXPIRED_RIGHT",
        "I": "BOTH", "J": "BOTH",
    }[state]


def expected_terminal_state(state: str, probes: list[str]) -> str:
    if state in ("I", "J") and "Q" in probes:
        return "Z"
    if state in ("G", "H") and "Q" in probes:
        return "TARGET_EXPIRED_LEFT" if state == "G" else "TARGET_EXPIRED_RIGHT"
    return f"{state}{len(probes)}"


def expected_trial(family: str, state: str, arm: str) -> tuple[list[str], str, str | None]:
    if family == "action_equivalent":
        probes = ["P"] if arm == "one_step" else []
        return probes, "ACT_COMMON", "EFFECT_OK"
    if family == "convergent" and arm == "adaptive":
        return ["P", "Q"], "ACT_COMMON", "EFFECT_OK"
    if arm == "no_probe":
        return [], "YIELD", None
    if arm == "one_step":
        return ["P"], "YIELD", None
    if arm == "adaptive":
        if family == "separable":
            action = "ACT_LEFT" if state == "A" else "ACT_RIGHT"
            return ["P", "Q"], action, "EFFECT_OK"
        return ["P", "Q"], "YIELD", None
    return [], "YIELD", None


def audit_arm(candidate_rows: list[dict], oracle_rows: list[dict], arm: str) -> tuple[list[str], dict]:
    errors: list[str] = []
    allowed_events = {
        "ENVIRONMENT", "CASE_START", "SAFE_PROBE", "UNSAFE_PROBE", "ACTION",
        "CASE_END", "FIXTURE_END", "IGNORED_CLICK", "PROBE_ORDER_ERROR",
    }
    unknown_events = sorted({row.get("event") for row in oracle_rows} - allowed_events)
    if unknown_events:
        errors.append(f"{arm}:unknown_oracle_events:{unknown_events}")
    for event in oracle_rows:
        if event.get("event") in ("IGNORED_CLICK", "PROBE_ORDER_ERROR"):
            errors.append(f"{arm}:invalid_gui_interaction:{event.get('event')}")
    starts = {row["trial_index"]: row for row in oracle_rows if row.get("event") == "CASE_START"}
    ends = {row["trial_index"]: row for row in oracle_rows if row.get("event") == "CASE_END"}
    probes_by_trial: dict[int, list[str]] = {}
    unsafe_by_trial: dict[int, list[dict]] = {}
    actions_by_trial: dict[int, list[dict]] = {}
    for event in oracle_rows:
        idx = event.get("trial_index")
        if idx is None:
            continue
        if event.get("event") == "SAFE_PROBE":
            probes_by_trial.setdefault(idx, []).append(event.get("probe"))
        elif event.get("event") == "UNSAFE_PROBE":
            unsafe_by_trial.setdefault(idx, []).append(event)
        elif event.get("event") == "ACTION":
            actions_by_trial.setdefault(idx, []).append(event)

    if len(candidate_rows) != 10:
        errors.append(f"{arm}:candidate_row_count:{len(candidate_rows)}")
    if len(starts) != 10 or len(ends) != 10:
        errors.append(f"{arm}:oracle_case_count:{len(starts)}/{len(ends)}")
    if sum(row.get("event") == "FIXTURE_END" for row in oracle_rows) != 1:
        errors.append(f"{arm}:fixture_end_count")

    seen_states: list[str] = []
    effect_count = 0
    probe_count = 0
    families_seen: list[str] = []
    family_effects = {family: 0 for family in FAMILIES}
    for expected_index, candidate in enumerate(candidate_rows):
        idx = candidate.get("trial_index")
        if idx != expected_index:
            errors.append(f"{arm}:candidate_index:{expected_index}:{idx}")
        if candidate.get("arm") != arm:
            errors.append(f"{arm}:candidate_arm_mismatch:{expected_index}")
        if any(key in candidate for key in ("state_id", "hidden_state", "truth", "oracle")):
            errors.append(f"{arm}:candidate_contains_hidden_field:{expected_index}")
        start, end = starts.get(idx), ends.get(idx)
        if start is None or end is None:
            errors.append(f"{arm}:missing_oracle_boundary:{idx}")
            continue
        state, family = start.get("state_id"), start.get("family")
        if STATE_FAMILY.get(state) != family or candidate.get("family") != family:
            errors.append(f"{arm}:family_binding:{idx}")
        seen_states.append(state)
        families_seen.append(family)
        if end.get("state_id") != state:
            errors.append(f"{arm}:end_state_mismatch:{idx}")
        expected_terminal = expected_terminal_state(state, probes_by_trial.get(idx, []))
        if end.get("terminal_state") != expected_terminal:
            errors.append(f"{arm}:terminal_state_mismatch:{idx}")
        actual_probes = probes_by_trial.get(idx, [])
        if actual_probes != candidate.get("probes"):
            errors.append(f"{arm}:probe_trace_mismatch:{idx}")
        if unsafe_by_trial.get(idx) or end.get("unsafe_probe_count") != 0:
            errors.append(f"{arm}:unsafe_probe:{idx}")
        if actual_probes != end.get("probes"):
            errors.append(f"{arm}:end_probe_mismatch:{idx}")

        case_events = [row for row in oracle_rows if row.get("trial_index") == idx]
        expected_event_kinds = ["CASE_START"] + ["SAFE_PROBE"] * len(actual_probes)
        expected_event_kinds += ["ACTION"] * len(actions_by_trial.get(idx, [])) + ["CASE_END"]
        if [row.get("event") for row in case_events] != expected_event_kinds:
            errors.append(f"{arm}:oracle_event_order_or_cardinality:{idx}")
        start_generation = start.get("generation")
        if start_generation is not None and start_generation != 0:
            errors.append(f"{arm}:initial_generation:{idx}:{start_generation}")
        probe_events = [row for row in case_events if row.get("event") == "SAFE_PROBE"]
        for expected_generation, probe_event in zip(
            (0 if name == "P" else 1 for name in actual_probes), probe_events
        ):
            if probe_event.get("generation") != expected_generation:
                errors.append(f"{arm}:probe_generation:{idx}:{expected_generation}")

        expected_probes, expected_choice, expected_effect = expected_trial(family, state, arm)
        if candidate.get("probes") != expected_probes:
            errors.append(f"{arm}:protocol_probe_mismatch:{idx}")
        if candidate.get("choice") != expected_choice:
            errors.append(f"{arm}:decision_mismatch:{idx}")
        if candidate.get("effect_signal") != expected_effect:
            errors.append(f"{arm}:effect_signal_mismatch:{idx}")
        if end.get("actions") != ([expected_choice.removeprefix("ACT_")] if expected_choice.startswith("ACT_") else []):
            errors.append(f"{arm}:oracle_action_mismatch:{idx}")
        if len(actions_by_trial.get(idx, [])) != (1 if expected_choice.startswith("ACT_") else 0):
            errors.append(f"{arm}:action_event_count:{idx}")
        for action_event in actions_by_trial.get(idx, []):
            expected_generation = int("Q" in expected_probes)
            if action_event.get("generation") != expected_generation:
                errors.append(f"{arm}:action_generation:{idx}")

        observations = candidate.get("observations", [])
        expected_observations = ["READY"]
        prefix: list[str] = []
        for probe in expected_probes:
            prefix.append(probe)
            expected_observations.append(expected_signal(state, prefix))
        if observations != expected_observations:
            errors.append(f"{arm}:pixel_observation_mismatch:{idx}:{observations}")

        current_actions = set()
        if state in ("C", "D"):
            current_actions.add("COMMON")
        elif expected_terminal == "A2":
            current_actions.add("LEFT")
        elif expected_terminal == "B2":
            current_actions.add("RIGHT")
        elif expected_terminal == "Z":
            current_actions.add("COMMON")
        actual_events = actions_by_trial.get(idx, [])
        for action_event in actual_events:
            if action_event.get("terminal_state") != expected_terminal:
                errors.append(f"{arm}:action_not_scored_at_current_terminal_state:{idx}")
            if action_event.get("action") not in current_actions:
                errors.append(f"{arm}:unsafe_or_wrong_effect_attempt:{idx}")
            if action_event.get("allowed") != sorted(current_actions):
                errors.append(f"{arm}:oracle_allowed_set_mismatch:{idx}")
            if action_event.get("outcome") != "VERIFIED_EFFECT":
                errors.append(f"{arm}:effect_not_verified:{idx}")
        if actual_events:
            effect_count += 1
            family_effects[family] += len(actual_events)
        probe_count += len(actual_probes)

    if set(seen_states) != set("ABCDEFGHIJ") or len(seen_states) != len(set(seen_states)):
        errors.append(f"{arm}:matched_state_coverage:{sorted(seen_states)}")
    if sorted(families_seen) != sorted([family for family in FAMILIES for _ in range(2)]):
        errors.append(f"{arm}:family_coverage")
    metrics = {"arm": arm, "rows": len(candidate_rows), "effects": effect_count,
               "effects_by_family": family_effects, "safe_probes": probe_count,
               "unsafe_probes": sum(map(len, unsafe_by_trial.values()))}
    return errors, metrics


def parse_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def audit_all(root: Path) -> tuple[list[str], list[dict]]:
    errors: list[str] = []
    metrics = []
    for arm in ARMS:
        candidate_path = root / arm / "candidate.jsonl"
        oracle_path = root / arm / "oracle.jsonl"
        if not candidate_path.is_file() or not oracle_path.is_file():
            errors.append(f"{arm}:raw_missing")
            continue
        arm_errors, arm_metrics = audit_arm(parse_jsonl(candidate_path), parse_jsonl(oracle_path), arm)
        errors.extend(arm_errors)
        metrics.append(arm_metrics)
    return errors, metrics


def mutation_controls(root: Path) -> dict[str, bool]:
    controls: dict[str, bool] = {}
    originals = {
        arm: (parse_jsonl(root / arm / "candidate.jsonl"), parse_jsonl(root / arm / "oracle.jsonl"))
        for arm in ARMS
    }

    changed = copy.deepcopy(originals)
    changed["adaptive"][0].pop(0)
    controls["drop_candidate_row"] = bool(audit_arm(*changed["adaptive"], "adaptive")[0])

    changed = copy.deepcopy(originals)
    changed["no_probe"][0][0]["state_id"] = "A"
    controls["forge_candidate_hidden_state"] = bool(audit_arm(*changed["no_probe"], "no_probe")[0])

    changed = copy.deepcopy(originals)
    b_row = next(i for i, row in enumerate(changed["adaptive"][0]) if row["family"] == "separable" and
                 "RIGHT" in row["observations"])
    changed["adaptive"][0][b_row]["choice"] = "ACT_LEFT"
    controls["swap_distinguishing_branch"] = bool(audit_arm(*changed["adaptive"], "adaptive")[0])

    changed = copy.deepcopy(originals)
    oracle = changed["adaptive"][1]
    target = next(row for row in oracle if row.get("event") == "CASE_START" and row.get("state_id") == "E")
    oracle.append({"event": "UNSAFE_PROBE", "trial_index": target["trial_index"], "probe": "U"})
    controls["inject_unsafe_probe"] = bool(audit_arm(*changed["adaptive"], "adaptive")[0])

    changed = copy.deepcopy(originals)
    stale_row = next(i for i, row in enumerate(changed["adaptive"][0]) if row["family"] == "stale")
    changed["adaptive"][0][stale_row]["choice"] = "ACT_LEFT"
    controls["act_after_expiry"] = bool(audit_arm(*changed["adaptive"], "adaptive")[0])
    return controls


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    errors, metrics = audit_all(args.root)
    controls = mutation_controls(args.root) if not errors else {}
    if controls and not all(controls.values()):
        errors.append("one_or_more_mutation_controls_not_rejected")
    gates = {row["arm"]: row for row in metrics}
    hypothesis = (
        gates.get("adaptive", {}).get("effects_by_family", {}).get("separable", 0) == 2
        and gates.get("no_probe", {}).get("effects_by_family", {}).get("separable", 0) == 0
        and gates.get("one_step", {}).get("effects_by_family", {}).get("separable", 0) == 0
        and gates.get("adaptive", {}).get("effects_by_family", {}).get("convergent", 0) == 2
        and gates.get("no_probe", {}).get("effects_by_family", {}).get("convergent", 0) == 0
        and gates.get("one_step", {}).get("effects_by_family", {}).get("convergent", 0) == 0
        and gates.get("adaptive", {}).get("unsafe_probes", 1) == 0
    ) if not errors else False
    result = {
        "audit": "PASS_RAW_REPLAY" if not errors else "FAIL_AUDIT",
        "hypothesis": "H_PASS_SCOPED" if hypothesis else "H_FAIL_SCOPED" if not errors else "NOT_EVALUATED",
        "metrics": metrics,
        "mutation_controls_rejected": controls,
        "errors": errors,
        "scope": "disposable deterministic Xvfb GUI fixture only; no user app, model, authority, external effect, or general GUI claim",
    }
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
