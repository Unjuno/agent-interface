"""Allocation-independent constrained-sampler feasibility probe (synthetic only)."""
from collections import Counter, defaultdict
import hashlib
import json

import make_dataset
from protocol import FIELDS, make_rows
from sampler import CLASSES, COUNTS


def rank(seed, cls, case):
    raw = (
        b"support-row-rank-v1\n"
        + str(seed).encode("ascii")
        + b"\n"
        + cls.encode()
        + b"\n"
        + case.encode()
    )
    return hashlib.sha256(raw).digest()


def build(pool, seed):
    groups = defaultdict(list)
    for row in pool:
        groups[row["class"]].append(row)

    cells = defaultdict(list)
    for row in groups["set"]:
        i = int(row["case_id"].split("-")[1])
        q, k = divmod(i, 8)
        cell = (q % 4, (q + k) % 4)
        cells[cell].append(row)

    assert len(cells) == 16 and all(len(rows) == 4 for rows in cells.values())
    # Independently rank each template x field cell, then use fixed quotas.
    set_by_cell = {
        cell: sorted(
            rows,
            key=lambda r: (rank(seed, "set", r["case_id"]), r["case_id"].encode()),
        )[0]
        for cell, rows in cells.items()
    }

    offset = seed % 4
    selected = {"imbalanced": [], "balanced": []}
    selected["imbalanced"].extend(set_by_cell[cell] for cell in sorted(set_by_cell))
    selected["balanced"].extend(
        set_by_cell[(template, (template + offset) % 4)]
        for template in range(4)
    )

    for cls in CLASSES:
        if cls == "set":
            continue
        ranked = sorted(
            groups[cls],
            key=lambda r: (rank(seed, cls, r["case_id"]), r["case_id"].encode()),
        )
        for arm in ("imbalanced", "balanced"):
            assert len(ranked) >= COUNTS[arm][cls], (seed, cls, len(ranked))
            selected[arm].extend(ranked[: COUNTS[arm][cls]])

    return selected


summaries = []
for seed in range(1, 129):
    # Candidate generator/protocol produces the synthetic pool; selection and
    # checks below are separately implemented here and do not import sampler.select.
    pool = make_dataset.annotate(make_rows(seed, "support", 128))
    selected = build(pool, seed)
    assert len(selected["balanced"]) == len(selected["imbalanced"]) == 32

    for cls in CLASSES:
        balanced = {
            r["case_id"] for r in selected["balanced"] if r["class"] == cls
        }
        imbalanced = {
            r["case_id"] for r in selected["imbalanced"] if r["class"] == cls
        }
        # Containment is checked per class because yield quotas reverse direction.
        if COUNTS["balanced"][cls] >= COUNTS["imbalanced"][cls]:
            assert imbalanced <= balanced, (seed, cls)
        else:
            assert balanced <= imbalanced, (seed, cls)

    margins = {}
    for arm, rows in selected.items():
        set_rows = [r for r in rows if r["class"] == "set"]
        template_counts = Counter()
        field_counts = Counter()
        joint_cells = set()
        for row in set_rows:
            i = int(row["case_id"].split("-")[1])
            q, k = divmod(i, 8)
            template = q % 4
            field = (q + k) % 4
            template_counts[template] += 1
            field_counts[FIELDS[field]] += 1
            joint_cells.add((template, field))

        expected = COUNTS[arm]["set"]
        assert len(set_rows) == expected
        expected_each = 1 if arm == "balanced" else 4
        assert sorted(template_counts.values()) == [expected_each] * 4
        assert sorted(field_counts.values()) == [expected_each] * 4
        assert len(joint_cells) == (4 if arm == "balanced" else 16)
        margins[arm] = {
            "template_counts": dict(sorted(template_counts.items())),
            "field_counts": dict(sorted(field_counts.items())),
            "joint_cells": len(joint_cells),
        }
    summaries.append(margins)

print(json.dumps({
    "status": "PASS_STRATIFIED_SUPPORT_MARGINAL_FEASIBILITY_ONLY",
    "runs": len(summaries),
    "sentinel_support_seeds": 128,
    "support_rows_per_arm": 32,
    "all_128_per_class_nesting_checks": True,
    "set_template_marginals": {
        "balanced": "one per each of four templates",
        "imbalanced": "four per each of four templates",
    },
    "set_field_marginals": {
        "balanced": "one per each of four fields",
        "imbalanced": "four per each of four fields",
    },
    "joint_template_field_cells": {
        "balanced": "4 of 16 (one predetermined mapping per support seed)",
        "imbalanced": "16 of 16",
    },
    "unique_cells_per_support_seed": 16,
    "rows_per_cell": 4,
    "limitations": [
        "Does not eliminate joint template-field or individual-row differences.",
        "Candidate protocol/generator constructs the synthetic pool; only selection/audit logic is independent.",
        "Does not demonstrate model efficacy or quality; no model/GPU/Docker operation.",
        "Synthetic construction-seed sweep is not formal allocation or randomized inference.",
    ],
    "source_hashes": {
        "protocol.py": "3d324897c9e99abe453ed500c486780243efe9fcff87441197471b5b47d665b6",
        "sampler.py": "0cdbe3e5b61202ec6ea5bd8810f4734a85141e7a7cbaf22ce886568b0f2c23a6",
        "make_dataset.py": "2aae4ddfa3e01ec2b1d2c4091a8be901070a3167b86aec9f45e74456e64d876f",
    },
}, sort_keys=True))
