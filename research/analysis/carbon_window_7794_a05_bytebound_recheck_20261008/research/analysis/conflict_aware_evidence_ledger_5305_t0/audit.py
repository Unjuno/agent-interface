"""Independent raw-only finite oracle and corruption controls for #5305 T0."""
from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path


ROOT = Path(__file__).parent
SIGNS = {"s1": 1, "s1dup": 1, "s2": 1, "r1": -1, "sold": 1}
FRESH = {"s1": True, "s1dup": True, "s2": True, "r1": True, "sold": False}
GROUP = {"s1": "g1", "s1dup": "g1", "s2": "g2", "r1": "g3", "sold": "g4"}


def oracle(ids):
    positives, negatives = set(), set()
    for item in ids:
        if not FRESH[item]:
            continue
        (positives if SIGNS[item] > 0 else negatives).add(GROUP[item])
    if positives and negatives:
        label = "CONFLICT"
    elif positives:
        label = "PASS"
    elif negatives:
        label = "FAIL"
    else:
        label = "UNCERTAIN"
    return {"status": label, "support_groups": sorted(positives),
            "refute_groups": sorted(negatives), "stale_count": sum(not FRESH[x] for x in ids)}


def load_raw():
    raw = (ROOT / "raw.json").read_bytes()
    expected = (ROOT / "raw.sha256").read_text().split()[0]
    assert hashlib.sha256(raw).hexdigest() == expected, "raw SHA mismatch"
    obj = json.loads(raw)
    assert obj["schema"] == "conflict-ledger-5305-t0-v1"
    return obj


def validate(obj):
    expected = []
    names = tuple(SIGNS)
    for size in range(1, len(names) + 1):
        expected.extend([list(c) for c in itertools.combinations(names, size)])
    assert obj["case_count"] == len(expected) == 31
    assert len(obj["cases"]) == 31
    seen = set()
    for row, wanted_ids in zip(obj["cases"], expected):
        ids = row["ids"]
        assert ids == wanted_ids, "missing, reordered, or substituted subset"
        assert tuple(ids) not in seen, "duplicate subset"
        seen.add(tuple(ids))
        assert row["candidate"] == oracle(ids), "independent oracle mismatch"
    statuses = [row["candidate"]["status"] for row in obj["cases"]]
    assert statuses.count("CONFLICT") == 14
    assert statuses.count("PASS") == 14
    assert statuses.count("FAIL") == 2
    assert statuses.count("UNCERTAIN") == 1
    # Exact/same-group duplicate support has one support group, not two votes.
    duplicate = next(row for row in obj["cases"] if row["ids"] == ["s1", "s1dup"])
    assert duplicate["candidate"]["support_groups"] == ["g1"]
    collapsed = [row for row in obj["cases"]
                 if row["candidate"]["status"] == "CONFLICT" and row["ternary"] == "UNCERTAIN"]
    assert len(collapsed) == 14
    return {"case_count": 31, "status_counts": {k: statuses.count(k) for k in sorted(set(statuses))},
            "fresh_conflicts_collapsed_by_ternary": len(collapsed)}


def corruption_controls(obj):
    mutations = []
    for name, mutate in (
        ("candidate_sign", lambda x: x["cases"][0]["candidate"].__setitem__("status", "FAIL")),
        ("candidate_freshness", lambda x: x["cases"][4]["candidate"].__setitem__("stale_count", 0)),
        ("duplicate_grouping", lambda x: x["cases"][5]["candidate"].__setitem__("support_groups", ["g1", "g1dup"])),
        ("conflict_projection", lambda x: x["cases"][7]["candidate"].__setitem__("status", "UNCERTAIN")),
    ):
        altered = json.loads(json.dumps(obj))
        mutate(altered)
        try:
            validate(altered)
        except (AssertionError, KeyError, ValueError):
            mutations.append({"control": name, "rejected": True})
        else:
            mutations.append({"control": name, "rejected": False})
    assert all(row["rejected"] for row in mutations), "ineffective corruption control"
    return mutations


def main():
    obj = load_raw()
    summary = validate(obj)
    mutations = corruption_controls(obj)
    audit = {"outcome": "PASS_T0_FINITE_MODEL", "raw_sha256": hashlib.sha256(
        (ROOT / "raw.json").read_bytes()).hexdigest(), **summary,
        "corruption_controls": mutations, "errors": []}
    encoded = json.dumps(audit, sort_keys=True, indent=2) + "\n"
    (ROOT / "audit.json").write_text(encoded)
    print(encoded, end="")


if __name__ == "__main__":
    main()
