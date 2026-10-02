"""Candidate prefix-stability classifier for Issue #6689's finite model."""

import hashlib
import itertools
import json
import sys
from collections import defaultdict
from pathlib import Path


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def interleavings(streams, prefix=()):
    if not any(streams):
        yield list(prefix)
        return
    for i, stream in enumerate(streams):
        if not stream:
            continue
        rest = list(streams)
        rest[i] = stream[1:]
        yield from interleavings(rest, prefix + (stream[0],))


def worlds(spec):
    for target, effect, generation, optional in itertools.product(
            spec["mandatory_values"], spec["mandatory_values"],
            spec["generation_values"], spec["optional_streams"]):
        streams = [
            [{"source": "target", "type": "result", "value": target,
              "generation": spec["generation"]}],
            [{"source": "effect", "type": "result", "value": effect,
              "generation": spec["generation"]}],
            [{"source": "generation", "type": "status", "value": generation,
              "generation": spec["generation"]}],
            optional,
        ]
        for trace in interleavings(streams):
            yield trace


def terminal_disposition(trace):
    observed = {(e["source"], e["type"]): e["value"] for e in trace}
    if observed.get(("generation", "status")) != "CURRENT":
        return "UNKNOWN"
    if any(observed.get((source, "result")) == "FAIL"
           for source in ("target", "effect")):
        return "FAIL"
    if any(observed.get((source, "result")) != "PASS"
           for source in ("target", "effect")):
        return "UNKNOWN"
    optional_rows = [e for e in trace if e["source"] == "optional"]
    if any(e.get("value") == "CONFLICT" for e in optional_rows):
        return "FAIL"
    frontier = next((e.get("value") for e in optional_rows
                     if e["type"] == "frontier"), None)
    if frontier == "COMPLETE":
        return "PASS"
    return "UNKNOWN"


def prefix_key(prefix):
    return canonical(prefix)


def classify(prefix, continuations):
    if not continuations:
        return "UNKNOWN", []
    outcomes = sorted({terminal_disposition(trace) for trace in continuations})
    if len(outcomes) == 1:
        return "STABLE_FINAL", outcomes
    values = {(event["source"], event["type"]): event["value"]
              for event in prefix}
    mandatory_pass = all(values.get((source, "result")) == "PASS"
                         for source in ("target", "effect"))
    current = values.get(("generation", "status")) == "CURRENT"
    frontier_seen = ("optional", "frontier") in values
    if mandatory_pass and current and not frontier_seen:
        return "CLOSED_FRONTIER_REQUIRED", outcomes
    return "PROVISIONAL", outcomes


def build(spec, spec_path):
    traces = list(worlds(spec))
    by_prefix = defaultdict(list)
    for trace in traces:
        for end in range(len(trace) + 1):
            by_prefix[prefix_key(trace[:end])].append(trace)
    rows = []
    prefix_map = {}
    for key, extensions in by_prefix.items():
        prefix = json.loads(key)
        classification, outcomes = classify(prefix, extensions)
        terminal = all(len(prefix) == len(trace) for trace in extensions)
        row = {
            "prefix": prefix,
            "prefix_events": len(prefix),
            "classification": classification,
            "reachable_terminal_dispositions": outcomes,
            "legal_continuation_count": len(extensions),
            "terminal_prefix": terminal,
            "claim": spec["claim"],
            "consumer_authority": False,
            "consumer_side_effects": 0,
        }
        rows.append(row)
        prefix_map[key] = row
    rows.sort(key=lambda row: (row["prefix_events"], canonical(row["prefix"])))

    traces_summary = []
    deadline = spec["deadline_prefix_events"]
    for trace in traces:
        early = next((i for i in range(len(trace) + 1)
                      if prefix_map[prefix_key(trace[:i])]["classification"] == "STABLE_FINAL"),
                     None)
        traces_summary.append({
            "trace": trace,
            "prefix_stability_final_at": early,
            "wait_for_all_final_at": len(trace),
            "deadline_partial_at": deadline,
            "deadline_partial_disposition": (
                terminal_disposition(trace[:deadline])
                if deadline >= len(trace) else "UNKNOWN"),
        })

    counts = defaultdict(int)
    for row in rows:
        counts[row["classification"]] += 1
        if not row["terminal_prefix"] and row["classification"] == "STABLE_FINAL":
            counts["EARLY_STABLE_" + row["reachable_terminal_dispositions"][0]] += 1
        if row["classification"] == "STABLE_FINAL" and row["reachable_terminal_dispositions"] == ["PASS"] and not row["terminal_prefix"]:
            counts["EARLY_PASS"] += 1
    header = {
        "schema": "prefix-stability-6689-raw-v1",
        "spec_sha256": sha(spec_path),
        "world_count": 40,
        "trace_count": len(traces),
        "unique_prefix_count": len(rows),
        "classification_counts": dict(sorted(counts.items())),
        "trace_summaries": traces_summary,
        "authority_grants": 0,
        "consumer_side_effects": 0,
    }
    return header, rows


def main():
    spec_path, output_path = Path(sys.argv[1]), Path(sys.argv[2])
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    header, rows = build(spec, spec_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as stream:
        stream.write(canonical(header) + "\n")
        for row in rows:
            stream.write(canonical(row) + "\n")
    print(json.dumps({"rows": header["unique_prefix_count"],
                      "traces": header["trace_count"],
                      "sha256": sha(output_path)}, sort_keys=True))


if __name__ == "__main__":
    main()
