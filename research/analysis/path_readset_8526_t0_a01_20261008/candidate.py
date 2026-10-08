"""Finite path-conditioned read-set discriminator for Issue #8526."""

import argparse
import hashlib
import json
from pathlib import Path


POLICIES = ("GLOBAL_UNION", "EXECUTED_PATH", "PATH_CERTIFICATE")
ALL_FIELDS = ("route", "alpha", "beta")


def _case(case_id, initial, current, initial_versions=None, current_versions=None,
          source_epoch=(4, 4), producer_generation=(9, 9), now_ms=20,
          deadline_ms=100, complete=True, predicate_provenance=True):
    initial_versions = initial_versions or {field: 1 for field in ALL_FIELDS}
    current_versions = current_versions or dict(initial_versions)
    return {
        "case_id": case_id,
        "initial": initial,
        "current": current,
        "initial_versions": initial_versions,
        "current_versions": current_versions,
        "source_epoch": {"initial": source_epoch[0], "current": source_epoch[1]},
        "producer_generation": {"initial": producer_generation[0], "current": producer_generation[1]},
        "now_ms": now_ms,
        "deadline_ms": deadline_ms,
        "certificate_complete": complete,
        "predicate_provenance": predicate_provenance,
    }


CASES = (
    _case("stable_path_a", {"route": "A", "alpha": 7, "beta": 11}, {"route": "A", "alpha": 7, "beta": 11}),
    _case("stable_path_b", {"route": "B", "alpha": 7, "beta": 11}, {"route": "B", "alpha": 7, "beta": 11}),
    _case(
        "unexecuted_branch_changed_a",
        {"route": "A", "alpha": 7, "beta": 11},
        {"route": "A", "alpha": 7, "beta": 99},
        current_versions={"route": 1, "alpha": 1, "beta": 2},
    ),
    _case(
        "unexecuted_branch_unknown_b",
        {"route": "B", "alpha": 7, "beta": 11},
        {"route": "B", "alpha": None, "beta": 11},
        current_versions={"route": 1, "alpha": 2, "beta": 1},
    ),
    _case(
        "executed_leaf_changed",
        {"route": "A", "alpha": 7, "beta": 11},
        {"route": "A", "alpha": 8, "beta": 11},
        current_versions={"route": 1, "alpha": 2, "beta": 1},
    ),
    _case(
        "predicate_changed",
        {"route": "A", "alpha": 7, "beta": 11},
        {"route": "B", "alpha": 7, "beta": 11},
        current_versions={"route": 2, "alpha": 1, "beta": 1},
    ),
    _case(
        "unknown_predicate",
        {"route": "A", "alpha": 7, "beta": 11},
        {"route": None, "alpha": 7, "beta": 11},
        current_versions={"route": 2, "alpha": 1, "beta": 1},
    ),
    _case(
        "unknown_active_input",
        {"route": "A", "alpha": 7, "beta": 11},
        {"route": "A", "alpha": None, "beta": 11},
        current_versions={"route": 1, "alpha": 2, "beta": 1},
    ),
    _case(
        "hidden_read_incomplete",
        {"route": "A", "alpha": 7, "beta": 11},
        {"route": "A", "alpha": 7, "beta": 11},
        complete=False,
    ),
    _case(
        "predicate_provenance_unknown",
        {"route": "A", "alpha": 7, "beta": 11},
        {"route": "A", "alpha": 7, "beta": 11},
        predicate_provenance=False,
    ),
    _case("aba_source_epoch", {"route": "A", "alpha": 7, "beta": 11}, {"route": "A", "alpha": 7, "beta": 11}, source_epoch=(4, 6)),
    _case(
        "producer_generation_changed",
        {"route": "A", "alpha": 7, "beta": 11},
        {"route": "A", "alpha": 7, "beta": 11},
        producer_generation=(9, 10),
    ),
    _case("deadline_expired", {"route": "A", "alpha": 7, "beta": 11}, {"route": "A", "alpha": 7, "beta": 11}, now_ms=101, deadline_ms=100),
)


def _binding(branch, active_field, active_value, source_epoch, producer_generation, deadline_ms, result):
    bound = {
        "active_field": active_field,
        "active_value": active_value,
        "branch": branch,
        "deadline_ms": deadline_ms,
        "producer_generation": producer_generation,
        "result": result,
        "source_epoch": source_epoch,
    }
    payload = json.dumps(bound, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _common_refusal(case, branch, active_field):
    current = case["current"]
    if not case["predicate_provenance"]:
        return "predicate_provenance_unknown"
    if current["route"] not in ("A", "B"):
        return "unknown_predicate"
    if current["route"] != branch or case["current_versions"]["route"] != case["initial_versions"]["route"]:
        return "predicate_changed"
    if current[active_field] is None:
        return "unknown_active_input"
    if current[active_field] != case["initial"][active_field] or case["current_versions"][active_field] != case["initial_versions"][active_field]:
        return "active_dependency_changed"
    if case["source_epoch"]["current"] != case["source_epoch"]["initial"]:
        return "source_epoch_changed"
    if case["producer_generation"]["current"] != case["producer_generation"]["initial"]:
        return "producer_generation_changed"
    if case["now_ms"] > case["deadline_ms"]:
        return "deadline_expired"
    return None


def _evaluate(case, policy):
    initial_route = case["initial"]["route"]
    if initial_route not in ("A", "B"):
        raise ValueError("frozen fixture must start with a known route")
    active_field = "alpha" if initial_route == "A" else "beta"
    result = f"{initial_route}:{case['initial'][active_field]}"
    certificate = {
        "branch": initial_route,
        "predicate_field": "route",
        "active_field": active_field,
        "checked_fields": [],
        "complete": case["certificate_complete"],
        "predicate_provenance": case["predicate_provenance"],
        "source_epoch": case["source_epoch"]["initial"],
        "producer_generation": case["producer_generation"]["initial"],
        "deadline_ms": case["deadline_ms"],
        "result": result,
        "result_binding": _binding(
            initial_route,
            active_field,
            case["initial"][active_field],
            case["source_epoch"]["initial"],
            case["producer_generation"]["initial"],
            case["deadline_ms"],
            result,
        ),
    }

    common = _common_refusal(case, initial_route, active_field)
    if policy == "GLOBAL_UNION":
        certificate["checked_fields"] = [
            *ALL_FIELDS, "source_epoch", "producer_generation", "deadline_ms", "complete", "predicate_provenance",
        ]
        if common is None and not certificate["complete"]:
            reason = "incomplete_dependency_certificate"
        elif common is None and any(
            case["current"].get(field) != case["initial"].get(field)
            or case["current_versions"].get(field) != case["initial_versions"].get(field)
            for field in ALL_FIELDS
        ):
            reason = "global_union_changed"
        else:
            reason = common
    elif policy == "EXECUTED_PATH":
        certificate["checked_fields"] = [
            "route", active_field, "source_epoch", "producer_generation", "deadline_ms", "predicate_provenance",
        ]
        reason = common
    elif policy == "PATH_CERTIFICATE":
        certificate["checked_fields"] = [
            "route", active_field, "source_epoch", "producer_generation", "deadline_ms",
            "complete", "predicate_provenance", "result_binding",
        ]
        reason = common
        if reason is None and not certificate["complete"]:
            reason = "incomplete_dependency_certificate"
        if reason is None and not certificate["predicate_provenance"]:
            reason = "predicate_provenance_unknown"
        if reason is None and certificate["result_binding"] != _binding(
            certificate["branch"],
            certificate["active_field"],
            case["initial"][active_field],
            certificate["source_epoch"],
            certificate["producer_generation"],
            certificate["deadline_ms"],
            certificate["result"],
        ):
            reason = "result_binding_invalid"
    else:
        raise ValueError(f"unknown policy: {policy}")

    accepted = reason is None
    return {
        "case_id": case["case_id"],
        "policy": policy,
        "accepted": accepted,
        "reason": "accepted" if accepted else reason,
        "initial": case["initial"],
        "current": case["current"],
        "initial_versions": case["initial_versions"],
        "current_versions": case["current_versions"],
        "source_epoch": case["source_epoch"],
        "producer_generation": case["producer_generation"],
        "now_ms": case["now_ms"],
        "deadline_ms": case["deadline_ms"],
        "certificate": certificate,
    }


def run_matrix():
    return [_evaluate(case, policy) for case in CASES for policy in POLICIES]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    payload = json.dumps({"rows": run_matrix()}, sort_keys=True, separators=(",", ":")) + "\n"
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(payload)
    print(f"candidate_rows={len(CASES) * len(POLICIES)}")


if __name__ == "__main__":
    main()
