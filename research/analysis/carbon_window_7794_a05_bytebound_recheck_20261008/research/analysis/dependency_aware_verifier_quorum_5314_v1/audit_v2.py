"""Independent raw-only audit including exhaustive-universe coverage checks."""
from __future__ import annotations

import copy
import hashlib
import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
RAW_SHA256 = "ec2ee61f24064dbd4902cda060889f85a15230a418d7b2a66a055515777fcffd"
N = 5
K = 3
POLICIES = (
    "COUNT_QUORUM",
    "DECLARED_INDEPENDENT",
    "DEPENDENCY_AWARE",
    "FAIL_CLOSED_UNKNOWN_DEPENDENCY",
)


def rgs_partitions(n: int):
    """Enumerate set partitions by restricted-growth strings, not v1 recursion."""
    if n <= 0:
        return
    labels = [0] * n

    def visit(position: int, largest: int):
        if position == n:
            groups = [[] for _ in range(largest + 1)]
            for member, label in enumerate(labels):
                groups[label].append(member)
            yield groups
            return
        for label in range(largest + 2):
            labels[position] = label
            yield from visit(position + 1, max(largest, label))

    yield from visit(1, 0)


def row_key(groups, votes, truth):
    normalized = tuple(tuple(group) for group in groups)
    return normalized, tuple(votes), bool(truth)


def expected_universe():
    expected = set()
    partitions = 0
    for groups in rgs_partitions(N):
        partitions += 1
        for domain_votes in itertools.product(("FAIL", "PASS"), repeat=len(groups)):
            votes = ["FAIL"] * N
            for group, vote in zip(groups, domain_votes):
                for member in group:
                    votes[member] = vote
            for truth in (False, True):
                expected.add(row_key(groups, votes, truth))
    return expected, partitions


def domain_outcome(votes, labels, known):
    if not all(known):
        return "UNCERTAIN"
    yes = {labels[i] for i, vote in enumerate(votes) if vote == "PASS"}
    no = {labels[i] for i, vote in enumerate(votes) if vote == "FAIL"}
    if len(yes) >= K:
        return "PASS"
    if len(no) >= K:
        return "FAIL"
    return "UNCERTAIN"


def policy_outputs(votes, declared, verified, known):
    count = "PASS" if votes.count("PASS") >= K else "FAIL"
    return {
        "COUNT_QUORUM": count,
        "DECLARED_INDEPENDENT": domain_outcome(votes, declared, [True] * N),
        "DEPENDENCY_AWARE": domain_outcome(votes, verified, [True] * N),
        "FAIL_CLOSED_UNKNOWN_DEPENDENCY": domain_outcome(votes, verified, known),
    }


def audit(raw):
    errors = []
    expected, expected_partitions = expected_universe()
    observed = set()
    seen_rows = set()
    observed_partitions = set()
    totals = {p: {"false_pass": 0, "false_fail": 0, "uncertain": 0, "correct": 0} for p in POLICIES}
    rows = raw.get("rows")
    if raw.get("study") != "dependency-aware-verifier-quorums-5314-v1":
        errors.append("study_identity_mismatch")
    if raw.get("intake_main") != "b0190453a787102189429e4b8c32032cf60efd17":
        errors.append("frozen_intake_main_mismatch")
    if not isinstance(rows, list):
        rows = []
        errors.append("rows_not_list")
    for row_index, row in enumerate(rows):
        try:
            groups = [list(group) for group in row["groups"]]
            votes = row["votes"]
            truth = row["truth"]
            declared = row["declared_labels"]
            verified = row["dependency_labels"]
            known = row["metadata_known"]
        except (KeyError, TypeError):
            errors.append(f"row_{row_index}_missing_or_malformed_required_field")
            continue
        normalized_groups = [sorted(group) for group in groups]
        canonical_groups = sorted(normalized_groups, key=lambda group: group[0] if group else -1)
        flattened = [member for group in normalized_groups for member in group]
        if canonical_groups != groups or sorted(flattened) != list(range(N)):
            errors.append(f"row_{row_index}_invalid_partition_shape")
            continue
        if len(votes) != N or len(declared) != N or len(verified) != N or len(known) != N:
            errors.append(f"row_{row_index}_invalid_vector_length")
            continue
        if any(vote not in ("PASS", "FAIL") for vote in votes):
            errors.append(f"row_{row_index}_invalid_vote")
            continue
        if type(truth) is not bool or any(type(value) is not bool for value in known):
            errors.append(f"row_{row_index}_invalid_boolean")
            continue
        for domain_index, group in enumerate(groups):
            if len({votes[member] for member in group}) != 1:
                errors.append(f"row_{row_index}_domain_vote_not_constant")
                break
        expected_labels = [None] * N
        for domain_index, group in enumerate(groups):
            for member in group:
                expected_labels[member] = f"d{domain_index}"
        if verified != expected_labels:
            errors.append(f"row_{row_index}_dependency_labels_disagree_with_partition")
        if declared != expected_labels:
            errors.append(f"row_{row_index}_declared_labels_disagree_with_verified_dependencies")
        if not all(known):
            errors.append(f"row_{row_index}_unknown_metadata_in_frozen_universe")
        signature = row_key(groups, votes, truth)
        if signature in seen_rows:
            errors.append(f"row_{row_index}_duplicate_case")
        seen_rows.add(signature)
        observed.add(signature)
        observed_partitions.add(tuple(tuple(group) for group in groups))
        expected_outputs = policy_outputs(votes, declared, expected_labels, known)
        if row.get("outputs") != expected_outputs:
            errors.append(f"row_{row_index}_policy_output_mismatch")
        for policy, output in expected_outputs.items():
            bucket = totals[policy]
            if output == "UNCERTAIN":
                bucket["uncertain"] += 1
            elif output == "PASS" and not truth:
                bucket["false_pass"] += 1
            elif output == "FAIL" and truth:
                bucket["false_fail"] += 1
            else:
                bucket["correct"] += 1

    missing = expected - observed
    extra = observed - expected
    if missing:
        errors.append(f"coverage_missing_cases:{len(missing)}")
    if extra:
        errors.append(f"coverage_extra_cases:{len(extra)}")
    if len(observed_partitions) != expected_partitions:
        errors.append(f"partition_coverage:{len(observed_partitions)}_of_{expected_partitions}")
    if len(rows) != len(expected):
        errors.append(f"row_count:{len(rows)}_expected_{len(expected)}")
    if raw.get("case_count") != len(expected):
        errors.append("declared_case_count_mismatch")
    if raw.get("partition_count") != expected_partitions:
        errors.append("declared_partition_count_mismatch")
    if raw.get("n") != N or raw.get("threshold") != K:
        errors.append("frozen_contract_header_mismatch")
    return {
        "rows_checked": len(rows),
        "expected_rows": len(expected),
        "partitions_checked": len(observed_partitions),
        "expected_partitions": expected_partitions,
        "totals": totals,
        "discrepancies": errors,
    }


def run_controls(raw):
    mutations = []

    changed = copy.deepcopy(raw)
    changed["rows"].pop()
    mutations.append(("drop_case", changed))

    changed = copy.deepcopy(raw)
    changed["rows"].append(copy.deepcopy(changed["rows"][0]))
    mutations.append(("duplicate_case", changed))

    changed = copy.deepcopy(raw)
    changed["rows"][0]["outputs"]["COUNT_QUORUM"] = "INVALID"
    mutations.append(("corrupt_policy_output", changed))

    changed = copy.deepcopy(raw)
    changed["rows"][0]["dependency_labels"][0] = "forged-independent-domain"
    mutations.append(("forge_dependency_label", changed))

    changed = copy.deepcopy(raw)
    changed["rows"][0]["declared_labels"][0] = "forged-independent-domain"
    mutations.append(("forge_declared_domain", changed))

    changed = copy.deepcopy(raw)
    changed["rows"][0]["metadata_known"][0] = False
    mutations.append(("erase_dependency_provenance", changed))

    changed = copy.deepcopy(raw)
    changed["intake_main"] = "unfrozen-main"
    mutations.append(("change_frozen_main", changed))

    changed = copy.deepcopy(raw)
    multi = next(row for row in changed["rows"] if any(len(group) > 1 for group in row["groups"]))
    group = next(group for group in multi["groups"] if len(group) > 1)
    member = group[1]
    multi["votes"][member] = "PASS" if multi["votes"][member] == "FAIL" else "FAIL"
    mutations.append(("split_shared_domain_vote", changed))

    results = [{"name": name, "rejected": bool(audit(changed)["discrepancies"])} for name, changed in mutations]
    return results


def main():
    raw_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "raw.json"
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "audit_v2.json"
    raw_bytes = raw_path.read_bytes()
    raw = json.loads(raw_bytes)
    result = audit(raw)
    controls = run_controls(raw)
    actual_sha = hashlib.sha256(raw_bytes).hexdigest()
    gate = (
        actual_sha == RAW_SHA256
        and not result["discrepancies"]
        and len(controls) == 8
        and all(control["rejected"] for control in controls)
    )
    result.update({
        "study": "dependency-aware-verifier-quorums-5314-v1-audit-v2",
        "raw_sha256": actual_sha,
        "controls": controls,
        "mutation_controls_passed": sum(control["rejected"] for control in controls),
        "mutation_controls_total": len(controls),
        "disposition": "PASS_FINITE_CONTRACT_ONLY" if gate else "HOLD_AUDIT",
        "limits": [
            "enumeration counts are not probabilities",
            "dependency domains are stipulated complete and correct",
            "no empirical independence or deployment efficacy demonstrated",
        ],
    })
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
