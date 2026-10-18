"""Independent finite-fixture audit; intentionally does not import candidate.py."""

import argparse
import copy
import hashlib
import json
from pathlib import Path


POLICIES = ("GLOBAL_UNION", "EXECUTED_PATH", "PATH_CERTIFICATE")
FIELDS = ("route", "alpha", "beta")
SAFE_CASES = {
    "stable_path_a",
    "stable_path_b",
    "unexecuted_branch_changed_a",
    "unexecuted_branch_unknown_b",
}
CHECKED_FIELDS = {
    "GLOBAL_UNION": [
        "route", "alpha", "beta", "source_epoch", "producer_generation", "deadline_ms", "complete", "predicate_provenance",
    ],
    "EXECUTED_PATH": ["route", "ACTIVE", "source_epoch", "producer_generation", "deadline_ms", "predicate_provenance"],
    "PATH_CERTIFICATE": [
        "route", "ACTIVE", "source_epoch", "producer_generation", "deadline_ms", "complete", "predicate_provenance", "result_binding",
    ],
}


def _fixture(case_id, initial, current, initial_versions=None, current_versions=None,
             source_epoch=(4, 4), producer_generation=(9, 9), now_ms=20,
             deadline_ms=100, complete=True, predicate_provenance=True):
    initial_versions = initial_versions or {field: 1 for field in FIELDS}
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


# Literal independent oracle fixture. The hidden state is deliberately absent;
# only this auditor knows that its value changed in hidden_read_incomplete.
FROZEN_FIXTURES = (
    _fixture("stable_path_a", {"route": "A", "alpha": 7, "beta": 11}, {"route": "A", "alpha": 7, "beta": 11}),
    _fixture("stable_path_b", {"route": "B", "alpha": 7, "beta": 11}, {"route": "B", "alpha": 7, "beta": 11}),
    _fixture(
        "unexecuted_branch_changed_a",
        {"route": "A", "alpha": 7, "beta": 11},
        {"route": "A", "alpha": 7, "beta": 99},
        current_versions={"route": 1, "alpha": 1, "beta": 2},
    ),
    _fixture(
        "unexecuted_branch_unknown_b",
        {"route": "B", "alpha": 7, "beta": 11},
        {"route": "B", "alpha": None, "beta": 11},
        current_versions={"route": 1, "alpha": 2, "beta": 1},
    ),
    _fixture(
        "executed_leaf_changed",
        {"route": "A", "alpha": 7, "beta": 11},
        {"route": "A", "alpha": 8, "beta": 11},
        current_versions={"route": 1, "alpha": 2, "beta": 1},
    ),
    _fixture(
        "predicate_changed",
        {"route": "A", "alpha": 7, "beta": 11},
        {"route": "B", "alpha": 7, "beta": 11},
        current_versions={"route": 2, "alpha": 1, "beta": 1},
    ),
    _fixture(
        "unknown_predicate",
        {"route": "A", "alpha": 7, "beta": 11},
        {"route": None, "alpha": 7, "beta": 11},
        current_versions={"route": 2, "alpha": 1, "beta": 1},
    ),
    _fixture(
        "unknown_active_input",
        {"route": "A", "alpha": 7, "beta": 11},
        {"route": "A", "alpha": None, "beta": 11},
        current_versions={"route": 1, "alpha": 2, "beta": 1},
    ),
    _fixture(
        "hidden_read_incomplete",
        {"route": "A", "alpha": 7, "beta": 11},
        {"route": "A", "alpha": 7, "beta": 11},
        complete=False,
    ),
    _fixture(
        "predicate_provenance_unknown",
        {"route": "A", "alpha": 7, "beta": 11},
        {"route": "A", "alpha": 7, "beta": 11},
        predicate_provenance=False,
    ),
    _fixture("aba_source_epoch", {"route": "A", "alpha": 7, "beta": 11}, {"route": "A", "alpha": 7, "beta": 11}, source_epoch=(4, 6)),
    _fixture(
        "producer_generation_changed",
        {"route": "A", "alpha": 7, "beta": 11},
        {"route": "A", "alpha": 7, "beta": 11},
        producer_generation=(9, 10),
    ),
    _fixture("deadline_expired", {"route": "A", "alpha": 7, "beta": 11}, {"route": "A", "alpha": 7, "beta": 11}, now_ms=101, deadline_ms=100),
)


def _expected_binding(branch, active_field, active_value, source_epoch, producer_generation, deadline_ms, result):
    payload = {
        "active_field": active_field,
        "active_value": active_value,
        "branch": branch,
        "deadline_ms": deadline_ms,
        "producer_generation": producer_generation,
        "result": result,
        "source_epoch": source_epoch,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _common_reason(fixture, branch, active_field):
    if not fixture["predicate_provenance"]:
        return "predicate_provenance_unknown"
    current = fixture["current"]
    if current["route"] not in ("A", "B"):
        return "unknown_predicate"
    if current["route"] != branch or fixture["current_versions"]["route"] != fixture["initial_versions"]["route"]:
        return "predicate_changed"
    if current[active_field] is None:
        return "unknown_active_input"
    if current[active_field] != fixture["initial"][active_field] or fixture["current_versions"][active_field] != fixture["initial_versions"][active_field]:
        return "active_dependency_changed"
    if fixture["source_epoch"]["current"] != fixture["source_epoch"]["initial"]:
        return "source_epoch_changed"
    if fixture["producer_generation"]["current"] != fixture["producer_generation"]["initial"]:
        return "producer_generation_changed"
    if fixture["now_ms"] > fixture["deadline_ms"]:
        return "deadline_expired"
    return None


def _expected_reason(fixture, policy, branch, active_field, binding):
    reason = _common_reason(fixture, branch, active_field)
    if reason is not None:
        return reason
    if policy == "GLOBAL_UNION":
        if not fixture["certificate_complete"]:
            return "incomplete_dependency_certificate"
        if any(
            fixture["current"].get(field) != fixture["initial"].get(field)
            or fixture["current_versions"].get(field) != fixture["initial_versions"].get(field)
            for field in FIELDS
        ):
            return "global_union_changed"
        return None
    if policy == "EXECUTED_PATH":
        return None
    if policy == "PATH_CERTIFICATE":
        if not fixture["certificate_complete"]:
            return "incomplete_dependency_certificate"
        if not fixture["predicate_provenance"]:
            return "predicate_provenance_unknown"
        expected_result = f"{branch}:{fixture['initial'][active_field]}"
        expected_hash = _expected_binding(
            branch,
            active_field,
            fixture["initial"][active_field],
            fixture["source_epoch"]["initial"],
            fixture["producer_generation"]["initial"],
            fixture["deadline_ms"],
            expected_result,
        )
        if binding != expected_hash:
            return "result_binding_invalid"
        return None
    raise ValueError("unrecognized policy in auditor")


def _validate_rows(rows):
    if not isinstance(rows, list):
        raise ValueError("candidate rows must be a list")
    expected_ids = {fixture["case_id"] for fixture in FROZEN_FIXTURES}
    if len(rows) != len(FROZEN_FIXTURES) * len(POLICIES):
        raise ValueError("candidate row count differs from the frozen matrix")
    by_key = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("candidate row is not an object")
        key = (row.get("case_id"), row.get("policy"))
        if key in by_key:
            raise ValueError("duplicate candidate case/policy row")
        by_key[key] = row
    if set(by_key) != {(case_id, policy) for case_id in expected_ids for policy in POLICIES}:
        raise ValueError("candidate coverage differs from frozen cases or policies")

    fixture_by_id = {fixture["case_id"]: fixture for fixture in FROZEN_FIXTURES}
    checked_counts = {policy: 0 for policy in POLICIES}
    false_accepts = {policy: 0 for policy in POLICIES}
    false_invalidations = {policy: 0 for policy in POLICIES}
    safe_salvages = set()

    for case_id, fixture in fixture_by_id.items():
        branch = fixture["initial"]["route"]
        active_field = "alpha" if branch == "A" else "beta"
        result = f"{branch}:{fixture['initial'][active_field]}"
        expected_complete = fixture["certificate_complete"]
        expected_provenance = fixture["predicate_provenance"]
        expected_checked = {
            "GLOBAL_UNION": [*FIELDS, "source_epoch", "producer_generation", "deadline_ms", "complete", "predicate_provenance"],
            "EXECUTED_PATH": ["route", active_field, "source_epoch", "producer_generation", "deadline_ms", "predicate_provenance"],
            "PATH_CERTIFICATE": ["route", active_field, "source_epoch", "producer_generation", "deadline_ms", "complete", "predicate_provenance", "result_binding"],
        }
        binding = _expected_binding(
            branch, active_field, fixture["initial"][active_field], fixture["source_epoch"]["initial"],
            fixture["producer_generation"]["initial"], fixture["deadline_ms"], result,
        )

        for policy in POLICIES:
            row = by_key[(case_id, policy)]
            for field in (
                "initial", "current", "initial_versions", "current_versions", "source_epoch",
                "producer_generation", "now_ms", "deadline_ms",
            ):
                expected = fixture[field] if field in fixture else None
                if row.get(field) != expected:
                    raise ValueError(f"candidate changed frozen fixture field {field}")

            cert = row.get("certificate")
            if not isinstance(cert, dict):
                raise ValueError("path certificate evidence is missing")
            expected_cert = {
                "branch": branch,
                "predicate_field": "route",
                "active_field": active_field,
                "checked_fields": expected_checked[policy],
                "complete": expected_complete,
                "predicate_provenance": expected_provenance,
                "source_epoch": fixture["source_epoch"]["initial"],
                "producer_generation": fixture["producer_generation"]["initial"],
                "deadline_ms": fixture["deadline_ms"],
                "result": result,
                "result_binding": binding,
            }
            if cert != expected_cert:
                raise ValueError("certificate branch, dependencies, provenance, generation, deadline or result binding mismatch")

            wanted_reason = _expected_reason(fixture, policy, branch, active_field, cert["result_binding"])
            wanted_accept = wanted_reason is None
            if row.get("accepted") is not wanted_accept:
                raise ValueError("candidate acceptance differs from independent fixture oracle")
            if row.get("reason") != ("accepted" if wanted_accept else wanted_reason):
                raise ValueError("candidate refusal reason differs from independent fixture oracle")

            checked_counts[policy] += len(expected_checked[policy])
            oracle_safe = case_id in SAFE_CASES
            if wanted_accept and not oracle_safe:
                false_accepts[policy] += 1
            if oracle_safe and not wanted_accept:
                false_invalidations[policy] += 1

    for case_id in SAFE_CASES:
        if (
            by_key[(case_id, "PATH_CERTIFICATE")]["accepted"]
            and not by_key[(case_id, "GLOBAL_UNION")]["accepted"]
        ):
            safe_salvages.add(case_id)

    return {
        "rows": len(rows),
        "safe_salvages": safe_salvages,
        "false_accepts": false_accepts,
        "false_invalidations": false_invalidations,
        "checked_counts": checked_counts,
    }


def audit_candidate(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get("rows"), list):
        raise ValueError("candidate payload must contain a rows list")
    stats = _validate_rows(payload["rows"])
    mutations = []

    drop_predicate = copy.deepcopy(payload["rows"])
    row = next(row for row in drop_predicate if row["case_id"] == "unexecuted_branch_changed_a" and row["policy"] == "PATH_CERTIFICATE")
    row["certificate"]["checked_fields"].remove("route")
    mutations.append(drop_predicate)

    wrong_path = copy.deepcopy(payload["rows"])
    row = next(row for row in wrong_path if row["case_id"] == "stable_path_a" and row["policy"] == "PATH_CERTIFICATE")
    row["certificate"]["branch"] = "B"
    mutations.append(wrong_path)

    missing_generation = copy.deepcopy(payload["rows"])
    row = next(row for row in missing_generation if row["case_id"] == "stable_path_a" and row["policy"] == "PATH_CERTIFICATE")
    del row["certificate"]["source_epoch"]
    mutations.append(missing_generation)

    rejected = 0
    for mutation in mutations:
        try:
            _validate_rows(mutation)
        except ValueError:
            rejected += 1
    if rejected != 3:
        raise ValueError("one or more path-certificate mutation controls escaped")
    if stats["false_accepts"]["PATH_CERTIFICATE"]:
        status = "FAIL_FALSE_ACCEPT"
    elif not stats["safe_salvages"]:
        status = "NO_ADVANTAGE"
    else:
        status = "PASS_PATH_CONDITIONED_READSET_SCOPED"
    return {
        "status": status,
        "rows": stats["rows"],
        "safe_salvages_vs_global_union": len(stats["safe_salvages"]),
        "false_accepts_by_policy": stats["false_accepts"],
        "false_invalidations_by_policy": stats["false_invalidations"],
        "checked_fields_by_policy": stats["checked_counts"],
        "mutation_rejections": rejected,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    payload = json.loads(Path(args.candidate).read_text(encoding="utf-8"))
    report = audit_candidate(payload)
    target = Path(args.output)
    with target.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, sort_keys=True, separators=(",", ":"))
        stream.write("\n")
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
