"""Independent exhaustive raw-only oracle for Issue #6689; imports no candidate."""

import copy
import hashlib
import itertools
import json
import sys
from collections import defaultdict
from pathlib import Path


def dump(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def completions(spec):
    """Generate legal futures by DFS over independent source cursors."""
    result = []
    optional_options = spec["optional_streams"]
    for target, effect, generation, opt in itertools.product(
            spec["mandatory_values"], spec["mandatory_values"],
            spec["generation_values"], optional_options):
        queues = (
            ({"source": "target", "type": "result", "value": target,
              "generation": spec["generation"]},),
            ({"source": "effect", "type": "result", "value": effect,
              "generation": spec["generation"]},),
            ({"source": "generation", "type": "status", "value": generation,
              "generation": spec["generation"]},),
            tuple(opt),
        )

        def visit(indices, prefix):
            if all(indices[i] == len(queues[i]) for i in range(len(queues))):
                result.append(prefix)
                return
            for source_index, queue in enumerate(queues):
                at = indices[source_index]
                if at == len(queue):
                    continue
                advanced = list(indices)
                advanced[source_index] += 1
                visit(tuple(advanced), prefix + (queue[at],))

        visit((0, 0, 0, 0), ())
    return result


def outcome(trace):
    values = {}
    optional = []
    for event in trace:
        if event["source"] == "optional":
            optional.append(event)
        else:
            values[(event["source"], event["type"])] = event["value"]
    if values.get(("generation", "status")) != "CURRENT":
        return "UNKNOWN"
    if any(values.get((source, "result")) == "FAIL"
           for source in ("target", "effect")):
        return "FAIL"
    if any(values.get((source, "result")) != "PASS"
           for source in ("target", "effect")):
        return "UNKNOWN"
    if any(event["value"] == "CONFLICT" and event["type"] == "result"
           for event in optional):
        return "FAIL"
    frontier = next((event["value"] for event in optional
                     if event["type"] == "frontier"), "OPEN")
    return "PASS" if frontier == "COMPLETE" else "UNKNOWN"


def oracle(spec):
    traces = completions(spec)
    by_prefix = defaultdict(list)
    for trace in traces:
        for n in range(len(trace) + 1):
            by_prefix[dump(trace[:n])].append(trace)
    result = {}
    for prefix_json, futures in by_prefix.items():
        prefix = json.loads(prefix_json)
        terminal = sorted({outcome(trace) for trace in futures})
        if len(terminal) == 1:
            classification = "STABLE_FINAL"
        else:
            state = {(event["source"], event["type"]): event["value"]
                     for event in prefix}
            if (state.get(("target", "result")) == "PASS" and
                    state.get(("effect", "result")) == "PASS" and
                    state.get(("generation", "status")) == "CURRENT" and
                    ("optional", "frontier") not in state):
                classification = "CLOSED_FRONTIER_REQUIRED"
            else:
                classification = "PROVISIONAL"
        result[prefix_json] = {
            "classification": classification,
            "reachable_terminal_dispositions": terminal,
            "legal_continuation_count": len(futures),
            "terminal_prefix": all(len(prefix) == len(trace) for trace in futures),
        }
    return traces, result


def validate(spec, raw):
    errors = []
    traces, expected = oracle(spec)
    if raw.get("schema") != "prefix-stability-6689-raw-v1":
        errors.append("schema")
    if raw.get("spec_sha256") != digest(sys.argv[1]):
        errors.append("spec_hash")
    if raw.get("world_count") != 40:
        errors.append("world_count")
    rows = raw.get("rows")
    if not isinstance(rows, list):
        return ["rows_type"]
    observed = {}
    for index, row in enumerate(rows):
        prefix = row.get("prefix")
        if not isinstance(prefix, list):
            errors.append(f"row_{index}_prefix")
            continue
        key = dump(prefix)
        if key in observed:
            errors.append(f"row_{index}_duplicate_prefix")
        observed[key] = row
    if set(observed) != set(expected):
        errors.append("prefix_inventory")
    for key in set(observed) & set(expected):
        row, oracle_row = observed[key], expected[key]
        for field in ("classification", "reachable_terminal_dispositions",
                      "legal_continuation_count", "terminal_prefix"):
            if row.get(field) != oracle_row[field]:
                errors.append("prefix_" + field)
                break
        if row.get("claim") != spec["claim"]:
            errors.append("claim_scope")
        if row.get("consumer_authority") is not False or row.get("consumer_side_effects") != 0:
            errors.append("authority_or_effect")
    counts = defaultdict(int)
    for row in observed.values():
        counts[row.get("classification")] += 1
    if raw.get("trace_count") != len(traces):
        errors.append("trace_count")
    if raw.get("unique_prefix_count") != len(expected):
        errors.append("prefix_count")
    if raw.get("classification_counts") != dict(sorted(counts.items())):
        errors.append("classification_counts")

    stable_fail = [key for key, item in expected.items()
                   if item["classification"] == "STABLE_FINAL"
                   and item["reachable_terminal_dispositions"] == ["FAIL"]
                   and not item["terminal_prefix"]]
    early_pass = [key for key, item in expected.items()
                  if item["classification"] == "STABLE_FINAL"
                  and item["reachable_terminal_dispositions"] == ["PASS"]
                  and not item["terminal_prefix"]]
    if not stable_fail:
        errors.append("missing_early_stable_fail")
    if early_pass:
        errors.append("early_pass_exists")
    for item in expected.values():
        if (item["classification"] == "STABLE_FINAL" and
                item["reachable_terminal_dispositions"] == ["PASS"]):
            state = {(event["source"], event["type"]): event["value"]
                     for event in json.loads(next(
                         key for key, val in expected.items() if val is item))}
            if not (state.get(("target", "result")) == "PASS" and
                    state.get(("effect", "result")) == "PASS" and
                    state.get(("generation", "status")) == "CURRENT" and
                    state.get(("optional", "frontier")) == "COMPLETE"):
                errors.append("pass_without_closed_valid_frontier")
                break

    expected_summaries = []
    deadline = spec["deadline_prefix_events"]
    for trace in traces:
        first_stable = next((i for i in range(len(trace) + 1)
                             if expected[dump(trace[:i])]["classification"] == "STABLE_FINAL"), None)
        expected_summaries.append({
            "trace": list(trace),
            "prefix_stability_final_at": first_stable,
            "wait_for_all_final_at": len(trace),
            "deadline_partial_at": deadline,
            "deadline_partial_disposition": outcome(trace[:deadline])
            if deadline >= len(trace) else "UNKNOWN",
        })
    if raw.get("trace_summaries") != expected_summaries:
        errors.append("trace_summaries")
    if raw.get("authority_grants") != 0 or raw.get("consumer_side_effects") != 0:
        errors.append("header_authority_or_effect")
    return errors


def mutate(raw, name):
    changed = copy.deepcopy(raw)
    if name == "drop_mandatory_check":
        row = next(r for r in changed["rows"] if any(
            e["source"] == "target" for e in r["prefix"]))
        row["prefix"] = [e for e in row["prefix"] if e["source"] != "target"]
    elif name == "forge_source_closed":
        row = next(r for r in changed["rows"] if any(
            e["source"] == "optional" and e["type"] == "frontier" and e["value"] == "TIMEOUT"
            for e in r["prefix"]))
        for event in row["prefix"]:
            if event["source"] == "optional" and event["type"] == "frontier":
                event["value"] = "COMPLETE"
                break
    elif name == "stale_as_current":
        row = next(r for r in changed["rows"] if any(
            e["source"] == "generation" and e["value"] == "INVALID"
            for e in r["prefix"]))
        for event in row["prefix"]:
            if event["source"] == "generation":
                event["value"] = "CURRENT"
                break
    elif name == "timeout_as_complete":
        row = next(r for r in changed["rows"] if any(
            e["source"] == "optional" and e["type"] == "frontier" and e["value"] == "TIMEOUT"
            for e in r["prefix"]))
        for event in row["prefix"]:
            if event["source"] == "optional" and event["type"] == "frontier":
                event["value"] = "COMPLETE"
                break
    return changed


def main():
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    raw_path = Path(sys.argv[2])
    raw = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines()]
    if not raw:
        raise SystemExit("empty raw JSONL")
    header, rows = raw[0], raw[1:]
    bundle = dict(header)
    bundle["rows"] = rows
    errors = validate(spec, bundle)
    controls = {}
    for name in ("drop_mandatory_check", "forge_source_closed",
                 "stale_as_current", "timeout_as_complete"):
        controls[name] = bool(validate(spec, mutate(bundle, name)))
    status = "PASS_METHOD_SCOPED" if not errors and all(controls.values()) else "FAIL_AUDIT"
    traces, oracle_rows = oracle(spec)
    report = {
        "schema": "prefix-stability-6689-audit-v1",
        "status": status,
        "errors": errors,
        "oracle_prefixes": len(oracle_rows),
        "oracle_traces": len(traces),
        "raw_prefixes": len(rows),
        "mutation_controls_rejected": controls,
        "scope": "finite authored evidence-prefix model only; not runtime freshness, authority, GUI, or performance",
    }
    Path(sys.argv[3]).write_text(dump(report) + "\n", encoding="utf-8")
    print(dump(report))
    raise SystemExit(0 if status == "PASS_METHOD_SCOPED" else 2)


if __name__ == "__main__":
    main()
