"""Synthetic expressibility checker; no production IR or runtime actions."""
import itertools
import json

PREDICATES = ["authority", "current", "effect_safe", "dependencies_acyclic", "reversible"]


def diagnose(rows, vocabulary):
    if (not rows or not vocabulary or
            any(type(index) is not int or index < 0 or index >= 5 for index in vocabulary) or
            len(set(vocabulary)) != len(vocabulary)):
        raise ValueError("nonempty rows and distinct semantic predicate indices required")
    groups = {}
    seen_ids = set()
    for row in rows:
        if (type(row) is not dict or set(row) != {"case_id", "concrete", "required"} or
                type(row["case_id"]) is not str or not row["case_id"] or
                row["case_id"] in seen_ids or type(row["concrete"]) is not list or
                len(row["concrete"]) != 5 or
                any(type(value) is not bool for value in row["concrete"]) or
                row["required"] not in ("FAIL", "PASS")):
            raise ValueError("invalid modeled observation")
        seen_ids.add(row["case_id"])
        visible = tuple(row["concrete"][index] for index in vocabulary)
        groups.setdefault(visible, []).append(row)
    conflicts, decisions = [], []
    for visible, members in sorted(groups.items()):
        labels = sorted({row["required"] for row in members})
        if len(labels) > 1:
            conflicts.append({"visible": list(visible),
                              "members": sorted(row["case_id"] for row in members),
                              "required": labels})
        else:
            decisions.append({"visible": list(visible), "required": labels[0]})
    return {"vocabulary": [PREDICATES[index] for index in vocabulary],
            "status": "ONTOLOGY_INSUFFICIENT" if conflicts else "EXPRESSIBLE",
            "observable_class_count": len(groups),
            "conflicting_classes": conflicts, "decisions": None if conflicts else decisions}


def build_artifact():
    rows = [{"case_id": f"case_{number:03d}", "concrete": list(vector),
             "required": "PASS" if all(vector) else "FAIL"}
            for number, vector in enumerate(itertools.product((False, True), repeat=5))]
    return {"schema": "verification-ir-alias-boundary-v1", "predicates": PREDICATES.copy(),
            "oracle": "PASS iff all five predicates are true", "rows": rows,
            "restricted": diagnose(rows, [0, 1, 2, 3]),
            "complete": diagnose(rows, [0, 1, 2, 3, 4])}


if __name__ == "__main__":
    print(json.dumps(build_artifact(), indent=2, allow_nan=False))
