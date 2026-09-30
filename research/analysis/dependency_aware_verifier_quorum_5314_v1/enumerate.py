import itertools
import json
from pathlib import Path

OUT = Path(__file__).parent / "raw.json"
N = 5
K = 3


def partitions(items):
    if not items:
        yield []
        return
    first, *rest = items
    for tail in partitions(rest):
        yield [[first], *[list(group) for group in tail]]
        for i in range(len(tail)):
            changed = [list(group) for group in tail]
            changed[i] = [first, *changed[i]]
            yield changed


def decision(votes, groups, threshold=K):
    pass_domains = sum(1 for group in groups if votes[group[0]])
    fail_domains = len(groups) - pass_domains
    if pass_domains >= threshold:
        return "PASS"
    if fail_domains >= threshold:
        return "FAIL"
    return "UNCERTAIN"


def label_decision(votes, labels, threshold=K):
    yes = {labels[i] for i, vote in enumerate(votes) if vote}
    no = {labels[i] for i, vote in enumerate(votes) if not vote}
    if len(yes) >= threshold:
        return "PASS"
    if len(no) >= threshold:
        return "FAIL"
    return "UNCERTAIN"


def canonical(groups):
    return sorted([sorted(g) for g in groups], key=lambda g: g[0])


rows = []
for groups0 in partitions(list(range(N))):
    groups = canonical(groups0)
    for domain_bits in itertools.product((False, True), repeat=len(groups)):
        votes = [False] * N
        for group, bit in zip(groups, domain_bits):
            for member in group:
                votes[member] = bit
        case_id = f"p{len(rows)//2:03d}"
        for truth in (False, True):
            actual_labels = [f"d{next(i for i,g in enumerate(groups) if v in g)}" for v in range(N)]
            outputs = {
                "COUNT_QUORUM": "PASS" if sum(votes) >= K else "FAIL",
                "DECLARED_INDEPENDENT": label_decision(votes, actual_labels),
                "DEPENDENCY_AWARE": decision(votes, groups),
                "FAIL_CLOSED_UNKNOWN_DEPENDENCY": decision(votes, groups),
            }
            rows.append({
                "case_id": case_id,
                "truth": truth,
                "groups": groups,
                "votes": ["PASS" if v else "FAIL" for v in votes],
                "dependency_labels": actual_labels,
                "declared_labels": actual_labels,
                "metadata_known": [True] * N,
                "outputs": outputs,
            })

raw = {
    "study": "dependency-aware-verifier-quorums-5314-v1",
    "intake_main": "b0190453a787102189429e4b8c32032cf60efd17",
    "n": N,
    "threshold": K,
    "partition_count": len({json.dumps(r["groups"]) for r in rows}),
    "case_count": len(rows),
    "construction": "complete set-partition enumeration × all binary domain-vote assignments × both truth labels",
    "rows": rows,
}
OUT.write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
print(json.dumps({"rows": len(rows), "partitions": raw["partition_count"], "path": str(OUT)}))
