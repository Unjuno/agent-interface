"""Independent exact enumerator for the frozen finite decision-regret fixture."""

import argparse
import json
from pathlib import Path


EXPECTED = {
    "age_tie_stable": ("SCORED", 0, [3, 4, 5]),
    "age_tie_changed": ("SCORED", 3, [3, 4, 5]),
    "fresh_misleading": ("SCORED", 1, [0]),
    "no_open_opportunity": ("NOT_APPLICABLE", None, []),
    "action_set_change": ("SCORED", 2, [2, 3, 4, 5]),
    "hard_safety_control": ("FAIL_HARD_SAFETY", None, [0]),
    "causal_use_unidentified": ("SCORED", 0, [0]),
    "unknown_truth_clock": ("UNKNOWN", None, [None]),
}


def _candidate_rows(raw):
    rows = raw.get("rows")
    if not isinstance(rows, list):
        return None
    keyed = {}
    for row in rows:
        key = (row.get("case_id"), row.get("tick"))
        if key in keyed:
            return None
        keyed[key] = row
    return keyed


def _expected_candidate_row(case_id, tick):
    comparable = tick.get("clock_comparable") is True
    observed = tick.get("observation_tick")
    now = tick.get("tick")
    age = now - observed if comparable and isinstance(now, int) and isinstance(observed, int) and now >= observed else None
    delivered = tick.get("delivered_state")
    selected = delivered if delivered in ("A", "B") else "ABSTAIN"
    return {
        "case_id": case_id,
        "tick": now,
        "opportunity_open": tick.get("opportunity_open"),
        "delivered_state": delivered,
        "observation_tick": observed,
        "clock_comparable": tick.get("clock_comparable"),
        "evidence_age": age,
        "admissible_actions": tick.get("admissible_actions"),
        "selected_action": selected,
        "causal_use_identifiable": tick.get("causal_use_identifiable"),
        "delivered_observation_ids": tick.get("delivered_observation_ids", []),
    }


def _loss(action, state, loss_table):
    return loss_table[action][state]


def audit_payload(visible, truth, raw, _run_mutations=True):
    errors = []
    rows = _candidate_rows(raw)
    if rows is None:
        rows = {}
        errors.append("candidate rows are missing, malformed, or duplicated")

    cases = {}
    safety_violations = 0
    comparator_cards = {}
    loss_table = truth.get("loss_table", {})
    visible_cases = visible.get("cases", [])
    visible_ids = [case.get("case_id") for case in visible_cases]
    if len(set(visible_ids)) != len(visible_ids):
        errors.append("duplicate visible case id")
    expected_keys = set()
    for case in visible_cases:
        case_id = case.get("case_id")
        ticks = case.get("ticks", [])
        truths = truth.get("cases", {}).get(case_id, {})
        state_by_tick = truths.get("state_by_tick", {})
        hard_ticks = set(truths.get("hard_safety_event_ticks", []))
        scored = []
        ages = []
        unknown = False
        hard_failure = False
        for tick in ticks:
            tick_id = tick.get("tick")
            key = (case_id, tick_id)
            expected_keys.add(key)
            expected = _expected_candidate_row(case_id, tick)
            observed = rows.get(key)
            if observed != expected:
                errors.append(f"candidate/output mismatch at {case_id}:{tick_id}")
            if not tick.get("opportunity_open"):
                continue
            age = expected["evidence_age"]
            ages.append(age)
            allowed = tick.get("admissible_actions")
            action = expected["selected_action"]
            state = state_by_tick.get(str(tick_id))
            if tick_id in hard_ticks or action not in allowed:
                hard_failure = True
                safety_violations += 1
            if age is None or state not in ("A", "B"):
                unknown = True
                continue
            if not isinstance(allowed, list) or not allowed:
                errors.append(f"empty or malformed admissible set at {case_id}:{tick_id}")
                unknown = True
                continue
            try:
                best_loss = min(_loss(candidate_action, state, loss_table) for candidate_action in allowed)
                scored.append(_loss(action, state, loss_table) - best_loss)
            except (KeyError, TypeError):
                errors.append(f"loss table missing finite action/state at {case_id}:{tick_id}")
                unknown = True

        if not ticks:
            errors.append(f"case {case_id} has no ticks")
        if not any(tick.get("opportunity_open") for tick in ticks):
            status, integral = "NOT_APPLICABLE", None
        elif hard_failure:
            status, integral = "FAIL_HARD_SAFETY", None
        elif unknown or len(scored) != sum(bool(t.get("opportunity_open")) for t in ticks):
            status, integral = "UNKNOWN", None
        else:
            status, integral = "SCORED", sum(scored)
        causal = "IDENTIFIABLE" if all(
            tick.get("causal_use_identifiable") is True
            for tick in ticks if tick.get("opportunity_open")
        ) else "NOT_IDENTIFIED"
        cases[case_id] = {
            "status": status,
            "integrated_regret_units": integral,
            "age_sequence": ages,
            "causal_attribution": causal,
        }
        open_ticks = [tick for tick in ticks if tick.get("opportunity_open")]
        comparator_cards[case_id] = {
            "age_only_sum": sum(
                _expected_candidate_row(case_id, tick)["evidence_age"]
                for tick in open_ticks
                if _expected_candidate_row(case_id, tick)["evidence_age"] is not None
            ) if open_ticks and all(_expected_candidate_row(case_id, tick)["evidence_age"] is not None for tick in open_ticks) else None,
            "toy_unsafe_exposure_ticks": sum(
                tick.get("tick") in set(truths.get("unsafe_exposure_ticks", []))
                for tick in open_ticks
            ),
        }

    if set(rows) != expected_keys:
        errors.append("candidate row keys differ from finite input grid")

    for case_id, (status, integral, ages) in EXPECTED.items():
        actual = cases.get(case_id)
        if actual is None:
            errors.append(f"missing frozen case {case_id}")
            continue
        if (actual["status"], actual["integrated_regret_units"], actual["age_sequence"]) != (status, integral, ages):
            errors.append(f"frozen expected gate mismatch: {case_id}")
    if set(cases) != set(EXPECTED):
        errors.append("visible case set differs from frozen case set")
    if cases.get("causal_use_unidentified", {}).get("causal_attribution") != "NOT_IDENTIFIED":
        errors.append("causal non-identification control was not preserved")
    if comparator_cards.get("age_tie_stable") != {"age_only_sum": 12, "toy_unsafe_exposure_ticks": 0}:
        errors.append("stable primary comparator cards mismatch")
    if comparator_cards.get("age_tie_changed") != {"age_only_sum": 12, "toy_unsafe_exposure_ticks": 0}:
        errors.append("changed primary comparator cards mismatch")
    if comparator_cards.get("hard_safety_control", {}).get("toy_unsafe_exposure_ticks") != 1:
        errors.append("toy unsafe-exposure control mismatch")

    mutations = _mutation_controls(visible, truth, raw) if _run_mutations else []
    if _run_mutations and (len(mutations) != 7 or not all(item["rejected"] for item in mutations)):
        errors.append("one or more auditor mutation controls escaped detection")
    return {
        "schema": "decision-regret-8528-independent-audit-v1",
        "disposition": "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD",
        "errors": errors,
        "cases": cases,
        "comparator_cards": comparator_cards,
        "hard_safety_violations": safety_violations,
        "mutation_controls": mutations,
        "note": "Finite synthetic method evidence only; toy unit loss is not user/task utility and does not support causal claims.",
    }


def _mutation_controls(visible, truth, raw):
    import copy

    probes = []
    changed_truth = copy.deepcopy(truth)
    changed_truth["cases"]["age_tie_changed"]["state_by_tick"]["3"] = "A"
    probes.append(("truth_flip", visible, changed_truth, raw))

    changed_visible = copy.deepcopy(visible)
    next(c for c in changed_visible["cases"] if c["case_id"] == "age_tie_changed")["ticks"][3]["opportunity_open"] = False
    probes.append(("opportunity_close", changed_visible, truth, raw))

    changed_visible = copy.deepcopy(visible)
    next(c for c in changed_visible["cases"] if c["case_id"] == "action_set_change")["ticks"][0]["admissible_actions"] = ["A"]
    probes.append(("action_set_change", changed_visible, truth, raw))

    changed_visible = copy.deepcopy(visible)
    next(c for c in changed_visible["cases"] if c["case_id"] == "age_tie_changed")["ticks"][3]["clock_comparable"] = False
    probes.append(("clock_unknown", changed_visible, truth, raw))

    changed_truth = copy.deepcopy(truth)
    changed_truth["cases"]["hard_safety_control"]["hard_safety_event_ticks"] = []
    probes.append(("safety_event_removed", visible, changed_truth, raw))

    changed_truth = copy.deepcopy(truth)
    changed_truth["loss_table"]["A"]["B"] = 0
    probes.append(("loss_mutation", visible, changed_truth, raw))

    changed_visible = copy.deepcopy(visible)
    next(c for c in changed_visible["cases"] if c["case_id"] == "causal_use_unidentified")["ticks"][0]["causal_use_identifiable"] = True
    probes.append(("lineage_mutation", changed_visible, truth, raw))

    outcomes = []
    for name, probe_visible, probe_truth, probe_raw in probes:
        mutated = audit_payload(probe_visible, probe_truth, probe_raw, _run_mutations=False)
        outcomes.append({"name": name, "rejected": bool(mutated["errors"])})
    return outcomes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=Path, default=Path(__file__).parent)
    args = parser.parse_args()
    root = args.dir
    visible = json.loads((root / "visible.json").read_text(encoding="utf-8"))
    truth = json.loads((root / "truth.json").read_text(encoding="utf-8"))
    raw = json.loads((root / "candidate.json").read_text(encoding="utf-8"))
    report = audit_payload(visible, truth, raw)
    (root / "AUDIT.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{report['disposition']} errors={len(report['errors'])} mutations={sum(x['rejected'] for x in report['mutation_controls'])}/{len(report['mutation_controls'])}")
    return 0 if report["disposition"] == "PASS_METHOD_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
