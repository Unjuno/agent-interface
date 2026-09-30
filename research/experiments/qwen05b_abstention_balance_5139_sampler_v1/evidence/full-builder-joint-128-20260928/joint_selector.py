from collections import defaultdict
from sampler import CLASSES, COUNTS, row_rank

def _cell(row):
    case_id = row.get("case_id")
    if not isinstance(case_id, str) or not case_id.startswith("support-"):
        raise ValueError("invalid_support_case_id")
    try:
        index = int(case_id.split("-")[1])
    except (IndexError, ValueError) as exc:
        raise ValueError("invalid_support_case_id") from exc
    q, k = divmod(index, 8)
    return q % 4, (q + k) % 4

def select_support_joint(rows, seed):
    grouped = defaultdict(list)
    seen = set()
    for row in rows:
        class_name, case_id = row.get("class"), row.get("case_id")
        if class_name not in CLASSES:
            raise ValueError(f"unknown_class:{class_name!r}")
        if not isinstance(case_id, str) or not case_id or case_id in seen:
            raise ValueError("invalid_or_duplicate_case_id")
        seen.add(case_id)
        grouped[class_name].append(row)
    if any(name not in grouped for name in CLASSES):
        raise ValueError("missing_class")

    cells = defaultdict(list)
    for row in grouped["set"]:
        cells[_cell(row)].append(row)
    if len(cells) != 16 or any(len(cell_rows) != 4 for cell_rows in cells.values()):
        raise ValueError("unexpected_set_cell_support")
    selected_cells = [(t, (t + seed % 4) % 4) for t in range(4)]
    arms = {"imbalanced": {}, "balanced": {}}
    for cell in selected_cells:
        rows_in_cell = cells[cell]
        arms["imbalanced"]["set"] = arms["imbalanced"].get("set", []) + sorted(rows_in_cell, key=lambda r:r["case_id"].encode("utf-8"))
        selected = min(rows_in_cell, key=lambda r:(row_rank(seed,"set",r["case_id"]),r["case_id"].encode("utf-8")))
        arms["balanced"]["set"] = arms["balanced"].get("set", []) + [selected]
    for class_name in CLASSES:
        if class_name == "set":
            continue
        ranked = sorted(grouped[class_name],key=lambda r:(row_rank(seed,class_name,r["case_id"]),r["case_id"].encode("utf-8")))
        for arm in arms:
            need = COUNTS[arm][class_name]
            if len(ranked) < need:
                raise ValueError(f"pool_short:{class_name}")
            arms[arm][class_name] = ranked[:need]
    return arms["imbalanced"], arms["balanced"]

