#!/usr/bin/env python3
"""Independent raw-only replay and complete-denominator scorer."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

POLICIES = (
    "DUAL", "NOVELTY_ONLY", "EFFECT_ONLY", "5435_SEVERITY_ONLY",
    "5435_SAFE_IDENTITY_BATCH", "CHRONOLOGICAL",
)


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def audit_selection(rows, selected_optional, budget):
    ids = [row["event_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate event_id")
    if len(selected_optional) > budget or len(selected_optional) != len(set(selected_optional)):
        raise ValueError("selection duplicate or budget overflow")
    lookup = {row["event_id"]: row for row in rows}
    if any(item not in lookup or lookup[item]["mandatory"] for item in selected_optional):
        raise ValueError("selection references absent/mandatory row")
    mandatory = {row["event_id"] for row in rows if row["mandatory"]}
    failures = {row["event_id"] for row in rows
                if not row["mandatory"] and row["failure"]}
    found = failures.intersection(selected_optional)
    return {
        "population_size": len(rows),
        "mandatory_selected": sorted(mandatory),
        "optional_selected": list(selected_optional),
        "optional_budget_used": len(selected_optional),
        "optional_failure_total": len(failures),
        "optional_failures_found": len(found),
        "optional_failures_missed": len(failures - found),
    }


def _linked_effect(row):
    value = row["effect"]
    if value is None:
        return -1
    if row.get("action_id") != row.get("effect_action_id"):
        return 0
    return 1 if value == 1 else 0


def _reference_choice(events, policy, budget):
    optional = [event for event in events if not event["mandatory"]]
    if policy == "DUAL":
        optional.sort(key=lambda e: (-_linked_effect(e), -e["novelty"], e["event_id"]))
    elif policy == "NOVELTY_ONLY":
        optional.sort(key=lambda e: (-e["novelty"], e["event_id"]))
    elif policy == "EFFECT_ONLY":
        optional.sort(key=lambda e: (-_linked_effect(e), e["event_id"]))
    elif policy == "5435_SEVERITY_ONLY":
        optional = [event for event in optional if event["severity"] >= 2]
    elif policy == "5435_SAFE_IDENTITY_BATCH":
        published, seen = [], set()
        for event in optional:
            score = event.get("score")
            suppress = (event["severity"] < 2 and score is not None and score <= 0.1
                        and event["entity_id"] in seen)
            if not suppress:
                published.append(event)
                seen.add(event["entity_id"])
        optional = published
    elif policy == "CHRONOLOGICAL":
        optional.sort(key=lambda e: (e["time"], e["event_id"]))
    else:
        raise ValueError("unknown frozen policy")
    return [event["event_id"] for event in optional[:budget]]


def _validate(raw, stream, outcomes, freeze):
    if set(raw) != {"schema", "stream_sha256", "population_size", "mandatory_event_ids",
                    "optional_audit_budget", "decisions", "scope"}:
        raise ValueError("raw schema/label-leak mismatch")
    if raw["schema"] != "issue-5764-triage-selection-v1":
        raise ValueError("wrong raw schema")
    if _sha("preaudit_stream.json") != freeze["preaudit_stream_sha256"]:
        raise ValueError("frozen stream hash mismatch")
    if _sha("sealed_outcomes.json") != freeze["sealed_outcomes_sha256"]:
        raise ValueError("frozen outcome hash mismatch")
    if _sha("run.py") != freeze["run_py_sha256"] or _sha("runner.py") != freeze["runner_py_sha256"]:
        raise ValueError("frozen candidate source hash mismatch")
    if _sha("audit.py") != freeze["audit_py_sha256"]:
        raise ValueError("frozen auditor source hash mismatch")

    events = stream["events"]
    event_ids = {event["event_id"] for event in events}
    if len(event_ids) != len(events) or set(outcomes["outcomes"]) != event_ids:
        raise ValueError("incomplete/duplicate population or scorer coverage")
    labels = outcomes["outcomes"]
    scored = [{**event, "failure": labels[event["event_id"]]["failure"]}
              for event in events]
    if raw["stream_sha256"] != _sha("preaudit_stream.json"):
        raise ValueError("candidate raw is bound to another stream")
    if raw["population_size"] != len(events):
        raise ValueError("population denominator mismatch")
    mandatory = sorted(e["event_id"] for e in events if e["mandatory"])
    if raw["mandatory_event_ids"] != mandatory:
        raise ValueError("mandatory lane lost or changed")
    budget = stream["optional_audit_budget"]
    if raw["optional_audit_budget"] != budget or set(raw["decisions"]) != set(POLICIES):
        raise ValueError("budget or comparator family mismatch")

    metrics = {}
    for policy in POLICIES:
        expected = _reference_choice(events, policy, budget)
        observed = raw["decisions"][policy]
        if observed != expected:
            raise ValueError(f"selection mismatch for {policy}")
        metrics[policy] = audit_selection(scored, observed, budget)
    return metrics


def _mutation_controls(raw, stream, outcomes, freeze):
    cases = {}
    altered = copy.deepcopy(raw)
    altered["decisions"]["DUAL"][0] = "forged-id"
    cases["changed_selection"] = altered
    altered = copy.deepcopy(raw)
    altered["mandatory_event_ids"] = []
    cases["dropped_mandatory_lane"] = altered
    altered = copy.deepcopy(raw)
    altered["sealed_outcomes"] = outcomes["outcomes"]
    cases["outcome_leak"] = altered
    altered_stream = copy.deepcopy(stream)
    altered_stream["events"].pop(6)
    cases["unknown_row_omitted"] = (raw, altered_stream, outcomes)
    altered_outcomes = copy.deepcopy(outcomes)
    altered_outcomes["outcomes"].pop("familiar-harm-01")
    cases["familiar_failure_omitted"] = (raw, stream, altered_outcomes)
    altered = copy.deepcopy(raw)
    altered["decisions"]["DUAL"].append(altered["decisions"]["DUAL"][0])
    cases["duplicate_selection"] = altered

    rejected = []
    for name, case in cases.items():
        try:
            if isinstance(case, tuple):
                _validate(case[0], case[1], case[2], freeze)
            else:
                _validate(case, stream, outcomes, freeze)
        except (KeyError, ValueError, TypeError):
            rejected.append(name)
    return {"rejected": rejected, "total": len(cases), "pass": len(rejected) == len(cases)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    freeze = json.loads(Path("FREEZE.json").read_text(encoding="utf-8"))
    raw = json.loads(Path(args.raw).read_text(encoding="utf-8"))
    stream = json.loads(Path("preaudit_stream.json").read_text(encoding="utf-8"))
    outcomes = json.loads(Path("sealed_outcomes.json").read_text(encoding="utf-8"))
    metrics = _validate(raw, stream, outcomes, freeze)
    controls = _mutation_controls(raw, stream, outcomes, freeze)
    if not controls["pass"]:
        raise SystemExit("independent mutation controls did not all reject")
    result = {
        "schema": "issue-5764-independent-audit-v1",
        "selection_replay": "PASS",
        "population_size": len(stream["events"]),
        "mandatory_failures": sum(bool(outcomes["outcomes"][item]["failure"])
                                   for item in raw["mandatory_event_ids"]),
        "optional_budget": stream["optional_audit_budget"],
        "metrics": metrics,
        "mutations": controls,
        "scope": "independent deterministic audit of authored synthetic stream only",
    }
    rendered = json.dumps(result, sort_keys=True, indent=2) + "\n"
    Path(args.output).write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
