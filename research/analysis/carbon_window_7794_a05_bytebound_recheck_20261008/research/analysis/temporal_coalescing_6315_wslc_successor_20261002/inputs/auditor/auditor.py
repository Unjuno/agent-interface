"""Independent raw-only oracle for the frozen Issue #6315 finite fixture."""
import copy
import json
import sys
from pathlib import Path


def _truth(case, rows):
    prop = case["property"]
    kind = prop["kind"]
    if kind == "alarm_count":
        occurrences = set()
        for row in rows:
            if row.get("kind") != "alarm":
                continue
            timestamp = row.get("t_ms")
            occurrence = row.get("occurrence_id")
            if type(timestamp) is not int or not isinstance(occurrence, str) or not occurrence:
                return None
            if prop["lo_ms"] <= timestamp <= prop["hi_ms"]:
                occurrences.add(occurrence)
        return len(occurrences)
    if kind == "deadline_ready":
        if any(type(row.get("t_ms")) is not int or type(row.get("ready")) is not bool for row in rows):
            return None
        return any(row["ready"] and row["t_ms"] <= prop["deadline_ms"] for row in rows)
    if kind == "deadline_event":
        if any(type(row.get("t_ms")) is not int or type(row.get("ready")) is not bool for row in rows):
            return None
        prior = False
        for row in rows:
            current = row["ready"]
            if current and not prior and row["t_ms"] <= prop["deadline_ms"]:
                return True
            prior = current
        return False
    if kind == "untimed_invariant":
        if any(type(row.get("safe")) is not bool for row in rows):
            return None
        return all(row["safe"] for row in rows)
    raise ValueError("unrecognized property kind: " + kind)


def _expected(case, indices):
    rows = case["rows"]
    if not isinstance(indices, list) or any(type(i) is not int or i < 0 or i >= len(rows) for i in indices):
        return {"verdict": "INVALID_MAPPING", "source": None, "projection": None}
    if indices != sorted(set(indices)):
        return {"verdict": "INVALID_MAPPING", "source": None, "projection": None}
    source = _truth(case, rows)
    projection = _truth(case, [rows[i] for i in indices])
    if case["coverage"] != "complete" or source is None or projection is None:
        verdict = "UNKNOWN"
    else:
        verdict = "PRESERVED" if source == projection else "NOT_PRESERVED"
    return {"verdict": verdict, "source": source, "projection": projection}


def _expected_keys(fixture):
    return {(case["case_id"], mode) for case in fixture["cases"] for mode in case["modes"]}


def _valid(fixture, raw):
    if raw.get("schema") != "temporal-coalescing-candidate.v1" or not isinstance(raw.get("records"), list):
        return False
    records = raw["records"]
    keys = [(r.get("case_id"), r.get("mode")) for r in records]
    if len(keys) != len(set(keys)) or set(keys) != _expected_keys(fixture):
        return False
    cases = {case["case_id"]: case for case in fixture["cases"]}
    indexed = {(r["case_id"], r["mode"]): r for r in records}
    for key, record in indexed.items():
        case = cases[key[0]]
        indices = record.get("kept_indices")
        if _expected(case, indices)["verdict"] == "INVALID_MAPPING":
            return False
        if key[1] == "retain_critical_edges":
            must_keep = {i for i, row in enumerate(case["rows"])
                         if row.get("critical_edge") or
                         (case["property"]["kind"] == "alarm_count" and row.get("kind") == "alarm")}
            if not must_keep.issubset(indices):
                return False
        result = _expected(case, indices)
        if case["case_id"] == "count_drop" and key[1] == "exact_full_stutter" and result["verdict"] != "NOT_PRESERVED":
            return False
        if case["case_id"] == "deadline_drop" and key[1] == "exact_full_stutter" and result["verdict"] != "NOT_PRESERVED":
            return False
    return True


def _mutate(raw, mutation):
    result = copy.deepcopy(raw)
    spec = mutation
    target = tuple(spec["target"])
    matched = [r for r in result["records"] if (r["case_id"], r["mode"]) == target]
    if len(matched) != 1:
        return result
    record = matched[0]
    if spec["op"] == "drop_index":
        record["kept_indices"] = [i for i in record["kept_indices"] if i != spec["drop_index"]]
    elif spec["op"] == "duplicate_record":
        result["records"].append(copy.deepcopy(record))
    elif spec["op"] == "swap_index":
        a, b = spec["positions"]
        record["kept_indices"][a], record["kept_indices"][b] = record["kept_indices"][b], record["kept_indices"][a]
    else:
        raise ValueError("unknown frozen mutation")
    return result


def audit(fixture, raw):
    if not _valid(fixture, raw):
        raise ValueError("candidate raw schema, mapping, or required-edge policy is invalid")
    by_key = {(r["case_id"], r["mode"]): r for r in raw["records"]}
    outcomes = []
    for case in fixture["cases"]:
        for mode in case["modes"]:
            outcome = _expected(case, by_key[(case["case_id"], mode)]["kept_indices"])
            outcomes.append({"case_id": case["case_id"], "mode": mode, **outcome})
    verdicts = {(x["case_id"], x["mode"]): x["verdict"] for x in outcomes}
    expected = {
        ("benign_stutter", "identity"): "PRESERVED",
        ("benign_stutter", "exact_full_stutter"): "PRESERVED",
        ("benign_stutter", "latest_state_only"): "PRESERVED",
        ("count_drop", "identity"): "PRESERVED",
        ("count_drop", "exact_full_stutter"): "NOT_PRESERVED",
        ("count_drop", "retain_critical_edges"): "PRESERVED",
        ("deadline_drop", "identity"): "PRESERVED",
        ("deadline_drop", "exact_full_stutter"): "NOT_PRESERVED",
        ("deadline_drop", "retain_critical_edges"): "PRESERVED",
        ("missing_time", "identity"): "UNKNOWN",
        ("coverage_gap", "identity"): "UNKNOWN",
        ("deadline_control", "identity"): "PRESERVED",
        ("deadline_control", "exact_full_stutter"): "PRESERVED",
        ("deadline_control", "retain_critical_edges"): "PRESERVED",
    }
    if verdicts != expected:
        raise ValueError("14 frozen case/mode outcomes mismatch")
    controls = [{"name": name, "rejected": not _valid(fixture, _mutate(raw, mutation))}
                for name, mutation in fixture["mutations"]]
    if len(controls) != 4 or not all(item["rejected"] for item in controls):
        raise ValueError("one or more of the four frozen mutations was accepted")
    return {"status": "PASS_METHOD_SCOPED", "case_mode_count": len(outcomes),
            "outcomes": outcomes, "mutation_controls": controls}


def main(fixture_path, candidate_path, output_path):
    fixture = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
    raw = json.loads(Path(candidate_path).read_text(encoding="utf-8"))
    result = audit(fixture, raw)
    Path(output_path).write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(result["status"] + " cases=" + str(result["case_mode_count"]) + " mutations=4/4")


if __name__ == "__main__":
    main(*sys.argv[1:4])
