"""Public-evidence-only optional next-checkpoint suggestion candidate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _nonempty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _typed_text_list(value: object) -> bool:
    return isinstance(value, list) and all(_nonempty_text(item) for item in value)


def _unique_next(public: dict) -> tuple[str | None, str]:
    contract = public.get("contract")
    state = public.get("state")
    if not isinstance(contract, dict):
        return None, "NO_CONTRACT"
    if not isinstance(state, dict):
        return None, "NO_PUBLIC_STATE"
    if contract.get("status") != "active":
        return None, "CONTRACT_NOT_ACTIVE"
    if (not _nonempty_text(contract.get("id"))
            or not _nonempty_text(contract.get("version"))
            or not _nonempty_text(contract.get("task_id"))
            or not _nonempty_text(contract.get("window_id"))
            or not _nonempty_text(contract.get("source_id"))):
        return None, "INVALID_CONTRACT_IDENTITY"
    if (state.get("task_id") != contract["task_id"]
            or state.get("window_id") != contract["window_id"]):
        return None, "TASK_OR_WINDOW_MISMATCH"
    generation = state.get("generation")
    observed_generation = state.get("observation_generation")
    if (not isinstance(generation, int) or isinstance(generation, bool)
            or generation != observed_generation
            or not _typed_text_list(state.get("source_ids"))):
        return None, "STALE_OR_UNBOUND_STATE"
    effects = state.get("unresolved_effects")
    if not isinstance(effects, list) or effects:
        return None, "UNRESOLVED_EFFECTS"

    checkpoints = contract.get("checkpoints")
    if not isinstance(checkpoints, list) or not checkpoints:
        return None, "INVALID_PLAN"
    ids = []
    dependencies = {}
    for item in checkpoints:
        if not isinstance(item, dict) or not _nonempty_text(item.get("id")):
            return None, "INVALID_PLAN"
        checkpoint_id = item["id"]
        required = item.get("depends_on")
        if checkpoint_id in dependencies or not _typed_text_list(required):
            return None, "INVALID_PLAN"
        ids.append(checkpoint_id)
        dependencies[checkpoint_id] = required
    if any(dependency not in dependencies or dependency == checkpoint_id
           for checkpoint_id, required in dependencies.items() for dependency in required):
        return None, "INVALID_PLAN"

    completed = state.get("completed_checkpoint_ids")
    cancelled = state.get("cancelled_checkpoint_ids")
    if (not _typed_text_list(completed) or not _typed_text_list(cancelled)
            or len(set(completed)) != len(completed)
            or len(set(cancelled)) != len(cancelled)
            or set(completed) & set(cancelled)
            or not (set(completed) | set(cancelled)) <= set(ids)):
        return None, "INVALID_PLAN"

    # A cycle means no checkpoint ordering is entailed by the contract.
    visiting: set[str] = set()
    visited: set[str] = set()

    def acyclic(node: str) -> bool:
        if node in visiting:
            return False
        if node in visited:
            return True
        visiting.add(node)
        if not all(acyclic(parent) for parent in dependencies[node]):
            return False
        visiting.remove(node)
        visited.add(node)
        return True

    if not all(acyclic(node) for node in ids):
        return None, "INVALID_PLAN"

    completed_set = set(completed)
    ready = [
        checkpoint_id for checkpoint_id in ids
        if checkpoint_id not in completed_set and checkpoint_id not in set(cancelled)
        and set(dependencies[checkpoint_id]) <= completed_set
    ]
    if len(ready) != 1:
        return None, "NO_UNIQUE_NEXT_CHECKPOINT"
    return ready[0], "UNIQUE_PUBLIC_SUPPORT"


def run(fixture: dict) -> dict:
    if fixture.get("schema") != "resume-suggestion-input-v1":
        raise ValueError("unexpected input schema")
    rows = []
    for case in fixture["cases"]:
        case_id = case["case_id"]
        public = case["public"]
        checkpoint_id, reason = _unique_next(public)
        contract = public.get("contract") if isinstance(public, dict) else None
        state = public.get("state") if isinstance(public, dict) else None
        state = state if isinstance(state, dict) else {}
        valid_contract = contract if isinstance(contract, dict) else {}
        source_ids = []
        if _nonempty_text(valid_contract.get("source_id")):
            source_ids.append(valid_contract["source_id"])
        if _typed_text_list(state.get("source_ids")):
            source_ids.extend(state["source_ids"])
        provenance = {
            "contract_id": valid_contract.get("id"),
            "contract_version": valid_contract.get("version"),
            "task_id": valid_contract.get("task_id"),
            "window_id": valid_contract.get("window_id"),
            "state_generation": state.get("generation"),
            "observation_generation": state.get("observation_generation"),
            "source_ids": sorted(set(source_ids)),
        }
        rows.append({
            "case_id": case_id,
            "decision": "SUGGEST" if checkpoint_id is not None else "ABSTAIN",
            "reason": reason,
            "suggestion": ({"checkpoint_id": checkpoint_id, "source_ids": provenance["source_ids"]}
                           if checkpoint_id is not None else None),
            "provenance": provenance,
            "authority": "none",
            "freshness": "snapshot_requires_revalidation",
        })
    return {"schema": "resume-suggestion-candidate-v1", "rows": rows}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="input.json")
    parser.add_argument("--output", default="results/candidate_raw.json")
    args = parser.parse_args()
    fixture = json.loads(Path(args.input).read_text(encoding="utf-8"))
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(run(fixture), stream, sort_keys=True, separators=(",", ":"))
        stream.write("\n")


if __name__ == "__main__":
    main()
