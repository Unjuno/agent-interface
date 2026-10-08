from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys

for parent in Path(__file__).resolve().parents:
    if (parent / "make_dataset.py").is_file() and (parent / "protocol.py").is_file():
        sys.path.insert(0, str(parent))
        break
else:
    raise RuntimeError("prepared #5139 source package not found")

import make_dataset
from protocol import FIELDS, make_rows
from sampler import CLASSES, COUNTS


def rank(seed, cls, case):
    return hashlib.sha256(
        b"support-row-rank-v1\n"
        + str(seed).encode("ascii")
        + b"\n"
        + cls.encode()
        + b"\n"
        + case.encode()
    ).digest()


def run(seed):
    pool = make_dataset.annotate(make_rows(seed, "support", 128))
    groups = defaultdict(list)
    for row in pool:
        groups[row["class"]].append(row)

    cells = defaultdict(list)
    for row in groups["set"]:
        i = int(row["case_id"].split("-")[1])
        q, k = divmod(i, 8)
        cells[(q % 4, (q + k) % 4)].append(row)
    assert len(cells) == 16 and all(len(rows) == 4 for rows in cells.values())

    # Preregisterable design: both arms use one fixed perfect matching of four cells.
    offset = seed % 4
    selected_cells = [(template, (template + offset) % 4) for template in range(4)]
    ranked_by_cell = {
        cell: sorted(
            cells[cell],
            key=lambda row: (rank(seed, "set", row["case_id"]), row["case_id"].encode()),
        )
        for cell in selected_cells
    }
    arms = {"imbalanced": [], "balanced": []}
    for cell in selected_cells:
        # 16-row arm uses four candidates/cell; 4-row arm takes one nested row/cell.
        arms["imbalanced"].extend(
            sorted(cells[cell], key=lambda row: row["case_id"].encode())
        )
        arms["balanced"].append(ranked_by_cell[cell][0])

    for cls in CLASSES:
        if cls == "set":
            continue
        ranked = sorted(
            groups[cls],
            key=lambda row: (rank(seed, cls, row["case_id"]), row["case_id"].encode()),
        )
        for arm in arms:
            arms[arm].extend(ranked[: COUNTS[arm][cls]])

    assert len(arms["balanced"]) == len(arms["imbalanced"]) == 32
    for cls in CLASSES:
        balanced_ids = {
            row["case_id"] for row in arms["balanced"] if row["class"] == cls
        }
        imbalanced_ids = {
            row["case_id"] for row in arms["imbalanced"] if row["class"] == cls
        }
        if COUNTS["balanced"][cls] <= COUNTS["imbalanced"][cls]:
            assert balanced_ids <= imbalanced_ids, (seed, cls)
        else:
            assert imbalanced_ids <= balanced_ids, (seed, cls)

    cellsets = {}
    for arm, selected in arms.items():
        rows = [row for row in selected if row["class"] == "set"]
        joint, template_counts, field_counts = set(), Counter(), Counter()
        for row in rows:
            i = int(row["case_id"].split("-")[1])
            q, k = divmod(i, 8)
            cell = (q % 4, (q + k) % 4)
            joint.add(cell)
            template_counts[cell[0]] += 1
            field_counts[FIELDS[cell[1]]] += 1

        per_cell = 1 if arm == "balanced" else 4
        assert len(rows) == COUNTS[arm]["set"]
        assert joint == set(selected_cells)
        assert sorted(template_counts.values()) == [per_cell] * 4
        assert sorted(field_counts.values()) == [per_cell] * 4
        cellsets[arm] = joint

    assert cellsets["balanced"] == cellsets["imbalanced"]
    balanced_set_ids = {
        row["case_id"] for row in arms["balanced"] if row["class"] == "set"
    }
    imbalanced_set_ids = {
        row["case_id"] for row in arms["imbalanced"] if row["class"] == "set"
    }
    assert balanced_set_ids <= imbalanced_set_ids
    return selected_cells


permutations = [run(seed) for seed in range(1, 129)]
counts = Counter(tuple(cells) for cells in permutations)
print(json.dumps({
    "status": "PASS_JOINT_AND_MARGINAL_MATCHED_SET_FEASIBILITY_ONLY",
    "sentinels": 128,
    "all_per_class_nesting_checks": True,
    "same_four_joint_cells_in_both_arms": True,
    "balanced_set_rows_per_joint_cell": 1,
    "imbalanced_set_rows_per_joint_cell": 4,
    "all_four_templates_and_fields_in_each_arm": True,
    "seed_permutation_counts": {
        " | ".join(f"{template}:{field}" for template, field in cells): count
        for cells, count in counts.items()
    },
    "limitations": [
        "The 16-vs-4 set arms still differ in individual rows and row multiplicity within each matched joint cell.",
        "The four-cell diagonal is support-seed dependent and must be preregistered, never chosen from outcomes.",
        "Other semantic-class quotas remain as defined by the existing protocol.",
        "Candidate protocol/generator constructs the synthetic pool; this is not formal inference or model-quality evidence.",
        "No model, CUDA, GPU, Docker, fit, or formal allocation used.",
    ],
}, sort_keys=True))
