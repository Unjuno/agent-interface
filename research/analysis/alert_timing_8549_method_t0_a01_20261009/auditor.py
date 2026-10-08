#!/usr/bin/env python3
"""Independent read-only reconstruction. Deliberately imports no candidate code."""
import argparse
import hashlib
import itertools
import json
import random
from pathlib import Path


def canonical_sha(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def expected_trial(protocol, fixture, block, demand, gap, position):
    truth = {x["event_id"]: x for x in fixture["truth"]}
    p = protocol["primary_factorial"]
    cell_index = p["first_event_demand"].index(demand) * len(p["gap_ms"]) + p["gap_ms"].index(gap)
    order = ["E1", "E2"] if block % 2 == 0 else ["E2", "E1"]
    first, second = order
    first_position = "upper" if (block + cell_index) % 2 == 0 else "lower"
    trial_id = f"B{block + 1:02d}-D{demand}-G{gap:04d}"
    return {
        "trial_id": trial_id, "block": block + 1,
        "position": position + 1, "demand": demand,
        "demand_instruction": ("identify_and_reconcile_first" if demand == "process"
                               else "observe_first_but_do_not_reconcile"),
        "gap_ms": gap, "event_count": 2,
        "event_onset_ms": [0, gap],
        "first_event_id": first, "second_event_id": second,
        "source_ids": [fixture["source_id"], fixture["source_id"]],
        "fact_ids": [truth[first]["fact_id"], truth[second]["fact_id"]],
        "messages": [truth[first]["message"], truth[second]["message"]],
        "salience": [protocol["primary_factorial"]["salience"]] * 2,
        "visual_duration_ms": [protocol["primary_factorial"]["visual_duration_ms"]] * 2,
        "t2_deadline_ms": protocol["primary_factorial"]["t2_deadline_after_arrival_ms"],
        "event_positions": [first_position, "lower" if first_position == "upper" else "upper"],
        "schedule_sha256": canonical_sha([trial_id, first, second, gap, demand]),
    }


def inspect(raw, protocol, fixture):
    errors = []
    p = protocol["primary_factorial"]
    expected = []
    rng = random.Random(fixture["random_seed"])
    for block in range(p["matched_blocks"]):
        cells = list(itertools.product(p["first_event_demand"], p["gap_ms"]))
        rng.shuffle(cells)
        for position, (demand, gap) in enumerate(cells):
            expected.append(expected_trial(protocol, fixture, block, demand, gap, position))
    got = raw.get("factorial_trials")
    if not isinstance(got, list) or len(got) != len(expected):
        errors.append("factorial_row_count")
        got = got if isinstance(got, list) else []
    expected_keys = {(x["block"], x["demand"], x["gap_ms"]) for x in expected}
    got_keys = [(x.get("block"), x.get("demand"), x.get("gap_ms")) for x in got if isinstance(x, dict)]
    if len(got_keys) != len(set(got_keys)) or set(got_keys) != expected_keys:
        errors.append("factorial_assignment");
    expected_order = [(x["block"], x["position"], x["demand"], x["gap_ms"]) for x in expected]
    got_order = [(x.get("block"), x.get("position"), x.get("demand"), x.get("gap_ms"))
                 for x in got if isinstance(x, dict)]
    if got_order != expected_order:
        errors.append("randomized_order")
    for row in got:
        if not isinstance(row, dict):
            errors.append("malformed_trial"); continue
        block = row.get("block")
        demand = row.get("demand")
        gap = row.get("gap_ms")
        position = row.get("position")
        if not isinstance(block, int) or not 1 <= block <= p["matched_blocks"] or not isinstance(position, int):
            errors.append("invalid_assignment_fields"); continue
        canonical = expected_trial(protocol, fixture, block - 1, demand, gap, position - 1)
        for key, value in canonical.items():
            if row.get(key) != value:
                errors.append("schedule_" + key)
        if row.get("first_event_id") == row.get("second_event_id"):
            errors.append("duplicate_event_identity")
        if len(row.get("source_ids", [])) != 2 or len(row.get("fact_ids", [])) != 2:
            errors.append("source_or_fact_binding")
    expected_classes = {"correct": True, "wrong_event": False, "wrong_source": False,
                        "wrong_fact": False, "late": False, "missing": False}
    if raw.get("control_labels") != [{"control": name, **protocol["control_definitions"][name],
                                      "purpose": "detectability_or_review_control", "not_in_factorial": True}
                                     for name in protocol["controls"]]:
        errors.append("control_labels")
    scores = raw.get("response_scores")
    if not isinstance(scores, list) or len(scores) != len(fixture["response_cases"]):
        errors.append("response_score_count"); scores = scores if isinstance(scores, list) else []
    truth = {x["event_id"]: x for x in fixture["truth"]}
    for case, score in zip(fixture["response_cases"], scores):
        target = next((row for row in got if isinstance(row, dict) and row.get("trial_id") == case["trial_id"]), None)
        latency = case["latency_after_t2_ms"]
        want = (target is not None and case["event_id"] == target.get("second_event_id")
                and case["source_id"] == fixture["source_id"]
                and case["fact_id"] == target.get("fact_ids", [None, None])[1] and type(latency) is int
                and 0 <= latency <= p["t2_deadline_after_arrival_ms"])
        if score != {"case_id": case["case_id"], "target_trial_id": case["trial_id"], "correct_t2": want,
                     "reason": "correct" if want else case["class"]}:
            errors.append("response_score_" + case["case_id"])
    if raw.get("fixture_id") != fixture["fixture_id"] or raw.get("scope") != protocol["scope"]:
        errors.append("fixture_or_scope_identity")
    return errors


def mutations(raw, protocol, fixture):
    checks = []
    cases = []
    for name, mutate in [
        ("drop_trial", lambda x: x["factorial_trials"].pop()),
        ("alter_deadline", lambda x: x["factorial_trials"][0].update(t2_deadline_ms=1)),
        ("alter_salience", lambda x: x["factorial_trials"][0]["salience"].__setitem__(0, 99)),
        ("alter_source", lambda x: x["response_scores"][0].update(correct_t2=False, reason="wrong_source")),
    ]:
        changed = json.loads(json.dumps(raw)); mutate(changed)
        detected = bool(inspect(changed, protocol, fixture))
        checks.append({"mutation": name, "rejected": detected})
        if not detected: cases.append(name)
    return checks, cases


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    protocol = json.loads(args.protocol.read_text()); fixture = json.loads(args.fixture.read_text())
    raw_bytes = args.raw.read_bytes(); raw = json.loads(raw_bytes)
    errors = inspect(raw, protocol, fixture)
    mutation_results, mutation_errors = mutations(raw, protocol, fixture)
    report = {"status": "PASS_METHOD_SCOPED" if not errors and not mutation_errors else "FAIL_METHOD",
              "independently_reconstructed_factorial_rows": len(raw.get("factorial_trials", [])),
              "independently_scored_response_cases": len(raw.get("response_scores", [])),
              "errors": errors, "mutation_controls": mutation_results,
              "candidate_raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
              "scope": "method-only synthetic fixture; no human-effect inference"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(report, sort_keys=True, indent=2) + "\n"
    args.output.write_text(encoded)
    print(json.dumps({"status": report["status"], "errors": len(errors),
                      "mutations_rejected": sum(x["rejected"] for x in mutation_results),
                      "audit_sha256": hashlib.sha256(encoded.encode()).hexdigest()}, sort_keys=True))


if __name__ == "__main__":
    main()
