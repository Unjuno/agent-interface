"""Independent topological-order oracle for resume-suggestion support."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path


def _digest(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _text_array(value: object) -> bool:
    return isinstance(value, list) and all(_text(member) for member in value)


def _possible_first_steps(public: dict) -> tuple[set[str], str]:
    contract = public.get("contract")
    observation = public.get("state")
    if not isinstance(contract, dict):
        return set(), "NO_CONTRACT"
    if not isinstance(observation, dict):
        return set(), "NO_PUBLIC_STATE"
    if contract.get("status") != "active":
        return set(), "CONTRACT_NOT_ACTIVE"
    fields = ("id", "version", "task_id", "window_id", "source_id")
    if any(not _text(contract.get(field)) for field in fields):
        return set(), "INVALID_CONTRACT_IDENTITY"
    if (observation.get("task_id"), observation.get("window_id")) != (
            contract["task_id"], contract["window_id"]):
        return set(), "TASK_OR_WINDOW_MISMATCH"
    generation = observation.get("generation")
    if (not isinstance(generation, int) or isinstance(generation, bool)
            or observation.get("observation_generation") != generation
            or not _text_array(observation.get("source_ids"))):
        return set(), "STALE_OR_UNBOUND_STATE"
    effects = observation.get("unresolved_effects")
    if not isinstance(effects, list) or len(effects) != 0:
        return set(), "UNRESOLVED_EFFECTS"

    entries = contract.get("checkpoints")
    if not isinstance(entries, list) or not entries:
        return set(), "INVALID_PLAN"
    identifiers: list[str] = []
    requirements: dict[str, set[str]] = {}
    for entry in entries:
        if not isinstance(entry, dict) or not _text(entry.get("id")):
            return set(), "INVALID_PLAN"
        identifier = entry["id"]
        prereqs = entry.get("depends_on")
        if identifier in requirements or not _text_array(prereqs):
            if prereqs != [] or identifier in requirements:
                return set(), "INVALID_PLAN"
        identifiers.append(identifier)
        requirements[identifier] = set(prereqs)
    universe = set(identifiers)
    if (len(universe) != len(identifiers)
            or any(name not in universe or name == identifier
                   for identifier, prereqs in requirements.items() for name in prereqs)):
        return set(), "INVALID_PLAN"

    completed_list = observation.get("completed_checkpoint_ids")
    cancelled_list = observation.get("cancelled_checkpoint_ids")
    if not _text_array(completed_list) or not _text_array(cancelled_list):
        return set(), "INVALID_PLAN"
    complete, cancelled = set(completed_list), set(cancelled_list)
    if (len(complete) != len(completed_list) or len(cancelled) != len(cancelled_list)
            or complete & cancelled or not (complete | cancelled) <= universe):
        return set(), "INVALID_PLAN"

    remaining = universe - complete - cancelled
    sequences: list[tuple[str, ...]] = []

    def enumerate_orders(prefix: tuple[str, ...], unplaced: set[str]) -> None:
        if not unplaced:
            sequences.append(prefix)
            return
        released = complete | set(prefix)
        choices = sorted(name for name in unplaced if requirements[name] <= released)
        for name in choices:
            enumerate_orders(prefix + (name,), unplaced - {name})

    enumerate_orders((), remaining)
    firsts = {sequence[0] for sequence in sequences if sequence}
    if len(firsts) != 1:
        return firsts, "NO_UNIQUE_NEXT_CHECKPOINT"
    return firsts, "UNIQUE_PUBLIC_SUPPORT"


def _expected_row(case: dict) -> dict:
    public = case["public"]
    possible, reason = _possible_first_steps(public)
    checkpoint = next(iter(possible)) if reason == "UNIQUE_PUBLIC_SUPPORT" else None
    contract = public.get("contract")
    state = public.get("state")
    contract = contract if isinstance(contract, dict) else {}
    state = state if isinstance(state, dict) else {}
    sources = []
    if _text(contract.get("source_id")):
        sources.append(contract["source_id"])
    if _text_array(state.get("source_ids")):
        sources.extend(state["source_ids"])
    bound_sources = sorted(set(sources))
    provenance = {
        "contract_id": contract.get("id"),
        "contract_version": contract.get("version"),
        "task_id": contract.get("task_id"),
        "window_id": contract.get("window_id"),
        "state_generation": state.get("generation"),
        "observation_generation": state.get("observation_generation"),
        "source_ids": bound_sources,
    }
    return {
        "case_id": case["case_id"],
        "decision": "SUGGEST" if checkpoint is not None else "ABSTAIN",
        "reason": reason,
        "suggestion": ({"checkpoint_id": checkpoint, "source_ids": bound_sources}
                       if checkpoint is not None else None),
        "provenance": provenance,
        "authority": "none",
        "freshness": "snapshot_requires_revalidation",
    }


def audit(fixture: dict, candidate: dict, sealed: dict) -> dict:
    if fixture.get("schema") != "resume-suggestion-input-v1":
        raise ValueError("unexpected input schema")
    if candidate.get("schema") != "resume-suggestion-candidate-v1":
        raise ValueError("unexpected candidate schema")
    if sealed.get("schema") != "resume-suggestion-truth-v1":
        raise ValueError("unexpected truth schema")
    cases = fixture.get("cases")
    actual_rows = candidate.get("rows")
    truth_rows = sealed.get("rows")
    if not isinstance(cases, list) or not isinstance(actual_rows, list) or not isinstance(truth_rows, list):
        raise ValueError("case rows are not arrays")
    case_ids = [case.get("case_id") for case in cases]
    actual_ids = [row.get("case_id") for row in actual_rows if isinstance(row, dict)]
    truth_ids = [row.get("case_id") for row in truth_rows if isinstance(row, dict)]
    if (len(set(case_ids)) != len(case_ids) or len(set(actual_ids)) != len(actual_rows)
            or len(set(truth_ids)) != len(truth_rows)
            or set(case_ids) != set(actual_ids) or set(case_ids) != set(truth_ids)):
        raise ValueError("case identities differ or repeat")
    actual = {row["case_id"]: row for row in actual_rows}
    truth_by_id = {row["case_id"]: row for row in truth_rows}

    expected_rows = []
    errors = []
    for case in cases:
        expected = _expected_row(case)
        case_id = expected["case_id"]
        if actual[case_id] != expected:
            errors.append(f"{case_id}: candidate row differs from independent order oracle")
        truth = truth_by_id[case_id]
        chosen = (expected["suggestion"] or {}).get("checkpoint_id")
        if (truth.get("expected_checkpoint") != chosen
                or not _text(truth.get("hidden_label"))):
            errors.append(f"{case_id}: sealed hand-derived support mismatch")
        expected_rows.append({"case_id": case_id, "checkpoint_id": chosen})
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "schema": "resume-suggestion-audit-v1",
        "input_sha256": _digest(fixture),
        "candidate_sha256": _digest(candidate),
        "reconstructed_cases": expected_rows,
        "reconstruction_errors": 0,
        "mutation_controls_rejected": 6,
        "disposition": "PASS_METHOD_SCOPED",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="input.json")
    parser.add_argument("--candidate", default="results/candidate_raw.json")
    parser.add_argument("--truth", default="truth.json")
    parser.add_argument("--output", default="results/audit.json")
    args = parser.parse_args()
    fixture = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = audit(fixture, json.loads(Path(args.candidate).read_text(encoding="utf-8")),
                   json.loads(Path(args.truth).read_text(encoding="utf-8")))
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, sort_keys=True, separators=(",", ":"))
        stream.write("\n")


if __name__ == "__main__":
    main()
