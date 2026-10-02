"""Independent raw-only evaluator for Issue #6315 finite trace fixtures."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path


def unique_edge_count(rows: list[dict], lo: int, hi: int) -> int | None:
    seen: set[str] = set()
    for row in rows:
        if row.get("kind") != "alarm":
            continue
        if "t_ms" not in row or not isinstance(row["t_ms"], int):
            return None
        if lo <= row["t_ms"] <= hi:
            occurrence = row.get("occurrence_id")
            if not isinstance(occurrence, str) or not occurrence:
                return None
            seen.add(occurrence)
    return len(seen)


def deadline_truth(rows: list[dict], deadline: int) -> bool | None:
    found_ready = False
    for row in rows:
        if "ready" not in row:
            return None
        if "t_ms" not in row or not isinstance(row["t_ms"], int):
            return None
        found_ready |= row["ready"] is True and row["t_ms"] <= deadline
    return found_ready


def deadline_event_truth(rows: list[dict], deadline: int) -> bool | None:
    if any("ready" not in row or "t_ms" not in row or not isinstance(row.get("t_ms"), int)
           for row in rows):
        return None
    prior = False
    for row in rows:
        current = row["ready"] is True
        if current and not prior and row["t_ms"] <= deadline:
            return True
        prior = current
    return False


def compare(case: dict, kept: list[int]) -> dict:
    n = len(case["rows"])
    if any(type(i) is not int or i < 0 or i >= n for i in kept):
        return {"verdict": "INVALID_MAPPING", "source": None, "projection": None,
                "source_epistemic": "UNKNOWN", "witness": None}
    if kept != sorted(set(kept)):
        return {"verdict": "INVALID_MAPPING", "source": None, "projection": None,
                "source_epistemic": "UNKNOWN", "witness": None}
    projection = [case["rows"][i] for i in kept]
    complete = case["coverage"] == "complete"
    prop = case["property"]
    if prop["kind"] == "alarm_count":
        source_value = unique_edge_count(case["rows"], prop["lo_ms"], prop["hi_ms"])
        projected_value = unique_edge_count(projection, prop["lo_ms"], prop["hi_ms"])
        known = complete and source_value is not None
        source_epistemic = "KNOWN" if complete and source_value is not None else "UNKNOWN"
        witness = {"source_occurrences": sorted({r["occurrence_id"] for r in case["rows"]
                    if r.get("kind") == "alarm" and "occurrence_id" in r}),
                   "projected_occurrences": sorted({r["occurrence_id"] for r in projection
                    if r.get("kind") == "alarm" and "occurrence_id" in r})}
    elif prop["kind"] == "deadline_ready":
        source_value = deadline_truth(case["rows"], prop["deadline_ms"])
        projected_value = deadline_truth(projection, prop["deadline_ms"])
        known = complete and source_value is not None
        source_epistemic = "KNOWN" if complete and source_value is not None else "UNKNOWN"
        witness = {"source_ready_times": [r["t_ms"] for r in case["rows"]
                    if r.get("ready") is True and isinstance(r.get("t_ms"), int)],
                   "projected_ready_times": [r["t_ms"] for r in projection
                    if r.get("ready") is True and isinstance(r.get("t_ms"), int)]}
    elif prop["kind"] == "deadline_event":
        source_value = deadline_event_truth(case["rows"], prop["deadline_ms"])
        projected_value = deadline_event_truth(projection, prop["deadline_ms"])
        known = complete and source_value is not None
        source_epistemic = "KNOWN" if complete and source_value is not None else "UNKNOWN"
        witness = {"source_rising_edges": [r["t_ms"] for i, r in enumerate(case["rows"])
                    if r.get("ready") is True and (i == 0 or case["rows"][i-1].get("ready") is not True)],
                   "projected_rising_edges": [r["t_ms"] for i, r in enumerate(projection)
                    if r.get("ready") is True and (i == 0 or projection[i-1].get("ready") is not True)]}
    elif prop["kind"] == "untimed_invariant":
        source_value = all(r.get("safe") is True for r in case["rows"])
        projected_value = all(r.get("safe") is True for r in projection)
        known = complete and all("safe" in r for r in case["rows"] + projection)
        source_epistemic = "KNOWN" if complete and all("safe" in r for r in case["rows"]) else "UNKNOWN"
        witness = {"source_length": len(case["rows"]), "projected_length": len(projection)}
    else:
        raise ValueError("unknown property")
    if not known:
        verdict = "UNKNOWN"
    else:
        verdict = "PRESERVED" if source_value == projected_value else "NOT_PRESERVED"
    return {"verdict": verdict, "source": source_value, "projection": projected_value,
            "source_epistemic": source_epistemic, "witness": witness}


def apply_mutation(raw: dict, mutation: dict) -> dict:
    result = copy.deepcopy(raw)
    target = tuple(mutation["target"])
    records = [r for r in result["records"] if (r["case_id"], r["mode"]) == target]
    if len(records) != 1:
        return result
    record = records[0]
    op = mutation["op"]
    if op == "delete_index":
        idx = mutation["index"]
        if 0 <= idx < len(record["kept_indices"]):
            del record["kept_indices"][idx]
    elif op == "drop_index":
        record["kept_indices"] = [idx for idx in record["kept_indices"]
                                  if idx != mutation["drop_index"]]
    elif op == "swap_index":
        indices = record["kept_indices"]
        a, b = mutation["positions"]
        indices[a], indices[b] = indices[b], indices[a]
    elif op == "duplicate_record":
        result["records"].append(copy.deepcopy(record))
    elif op == "reverse_indices":
        record["kept_indices"].reverse()
    return result


def audit(fixture: dict, raw: dict) -> dict:
    expected = {(c["case_id"], mode) for c in fixture["cases"] for mode in c["modes"]}
    records = raw.get("records", [])
    indexed = {(r.get("case_id"), r.get("mode")): r for r in records}
    if len(indexed) != len(records) or set(indexed) != expected:
        return {"status": "HOLD_AUDIT", "reason": "case_mode_coverage_or_duplicate"}
    outcomes = []
    by_id = {c["case_id"]: c for c in fixture["cases"]}
    for key in sorted(expected):
        result = compare(by_id[key[0]], indexed[key].get("kept_indices", []))
        outcomes.append({"case_id": key[0], "mode": key[1], **result})
    checks = []
    for mutation_name, mutation in fixture["mutations"]:
        altered = apply_mutation(raw, mutation)
        checks.append({"name": mutation_name,
                       "rejected": not _structurally_valid(fixture, altered)})
    passed = all(item["rejected"] for item in checks)
    return {"status": "PASS_METHOD_SCOPED" if passed else "HOLD_AUDIT",
            "case_mode_count": len(outcomes), "outcomes": outcomes,
            "mutation_controls": checks}


def _structurally_valid(fixture: dict, raw: dict) -> bool:
    expected = {(c["case_id"], mode) for c in fixture["cases"] for mode in c["modes"]}
    records = raw.get("records", [])
    keys = [(r.get("case_id"), r.get("mode")) for r in records]
    if len(keys) != len(set(keys)) or set(keys) != expected:
        return False
    cases = {c["case_id"]: c for c in fixture["cases"]}
    for record in records:
        case = cases[record["case_id"]]
        indices = record.get("kept_indices")
        if not isinstance(indices, list) or any(type(i) is not int or i < 0 or i >= len(case["rows"]) for i in indices):
            return False
        if indices != sorted(set(indices)):
            return False
        if record["mode"] == "retain_critical_edges":
            if case["property"]["kind"] == "alarm_count":
                required_edges = {row.get("occurrence_id") for row in case["rows"]
                                  if row.get("kind") == "alarm"}
                retained_edges = {case["rows"][i].get("occurrence_id") for i in indices
                                  if case["rows"][i].get("kind") == "alarm"}
                if required_edges != retained_edges:
                    return False
            elif case["property"]["kind"] == "deadline_ready":
                required_ready = {i for i, row in enumerate(case["rows"])
                                  if row.get("ready") is True and row.get("t_ms", 10**30) <= case["property"]["deadline_ms"]}
                if not required_ready.issubset(set(indices)):
                    return False
            elif case["property"]["kind"] == "deadline_event":
                required_edges = {i for i, row in enumerate(case["rows"])
                                  if row.get("ready") is True
                                  and (i == 0 or case["rows"][i-1].get("ready") is not True)
                                  and row.get("t_ms", 10**30) <= case["property"]["deadline_ms"]}
                if not required_edges.issubset(set(indices)):
                    return False
    return True


def main() -> int:
    fixture_path, raw_path, out_path = map(Path, sys.argv[1:4])
    fixture = json.loads(fixture_path.read_text())
    raw = json.loads(raw_path.read_text())
    result = audit(fixture, raw)
    out_path.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
