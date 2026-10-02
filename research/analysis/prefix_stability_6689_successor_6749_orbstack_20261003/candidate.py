"""Finite prefix-stability candidate for successor Issue #6749."""
import hashlib
import itertools
import json
import sys
from collections import defaultdict, Counter
from pathlib import Path


def canonical(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def merges(streams, prefix=()):
    if not any(streams):
        yield list(prefix)
        return
    for i, stream in enumerate(streams):
        if stream:
            rest = list(streams)
            rest[i] = stream[1:]
            yield from merges(rest, prefix + (stream[0],))


def all_traces(spec):
    for target, effect, generation, optional in itertools.product(
            spec["mandatory_values"], spec["mandatory_values"],
            spec["generation_values"], spec["optional_streams"]):
        streams = [
            [{"source":"target","type":"result","value":target,"generation":spec["generation"]}],
            [{"source":"effect","type":"result","value":effect,"generation":spec["generation"]}],
            [{"source":"generation","type":"status","value":generation,"generation":spec["generation"]}],
            optional]
        yield from merges(streams)


def terminal(trace):
    values = {(e["source"], e["type"]): e["value"] for e in trace}
    if values.get(("generation", "status")) != "CURRENT":
        return "UNKNOWN"
    if any(values.get((s, "result")) == "FAIL" for s in ("target", "effect")):
        return "FAIL"
    if any(values.get((s, "result")) != "PASS" for s in ("target", "effect")):
        return "UNKNOWN"
    optional = [e for e in trace if e["source"] == "optional"]
    if any(e["type"] == "note" and e["value"] == "CONFLICT" for e in optional):
        return "FAIL"
    if any(e["type"] == "frontier" and e["value"] == "COMPLETE" for e in optional):
        return "PASS"
    return "UNKNOWN"


def obligations(prefix):
    seen = {(e["source"], e["type"]): e["value"] for e in prefix}
    pending = ["mandatory:" + source for source in ("target", "effect")
               if (source, "result") not in seen]
    if ("generation", "status") not in seen:
        pending.append("generation_status")
    if seen.get(("optional", "frontier")) != "COMPLETE":
        pending.append("optional_frontier_completion")
    return sorted(pending)


def classify(prefix, outcomes):
    if len(outcomes) == 1:
        return {"PASS":"STABLE_PASS", "FAIL":"STABLE_FAIL", "UNKNOWN":"STABLE_UNKNOWN"}[outcomes[0]]
    seen = {(e["source"], e["type"]): e["value"] for e in prefix}
    if (seen.get(("target", "result")) == "PASS" and
        seen.get(("effect", "result")) == "PASS" and
        seen.get(("generation", "status")) == "CURRENT" and
        ("optional", "frontier") not in seen):
        return "CLOSED_FRONTIER_REQUIRED"
    return "PROVISIONAL"


def build(spec, spec_path):
    traces = list(all_traces(spec))
    continuations = defaultdict(list)
    for trace in traces:
        for n in range(len(trace) + 1):
            continuations[canonical(trace[:n])].append(trace)
    rows = []
    for key, futures in continuations.items():
        prefix = json.loads(key)
        outcomes = sorted({terminal(t) for t in futures})
        label = classify(prefix, outcomes)
        rows.append({"prefix":prefix, "classification":label,
                     "reachable_terminal_dispositions":outcomes,
                     "legal_continuation_count":len(futures),
                     "terminal_prefix":all(len(prefix) == len(t) for t in futures),
                     "pending_obligations":obligations(prefix),
                     "claim":spec["claim"], "consumer_authority":False,
                     "consumer_side_effects":0})
    rows.sort(key=lambda r:(len(r["prefix"]), canonical(r["prefix"])))
    disposition_counts = dict(sorted(Counter(r["classification"] for r in rows).items()))
    early_counts = dict(sorted(Counter(
        "EARLY_" + r["reachable_terminal_dispositions"][0]
        for r in rows if not r["terminal_prefix"] and r["classification"].startswith("STABLE_")
    ).items()))
    raw = {"schema":"prefix-stability-successor-6749-raw-v1",
           "fixture_sha256":digest(spec_path), "world_count":32,
           "trace_count":len(traces), "unique_prefix_count":len(rows),
           "disposition_counts":disposition_counts,
           "early_finalization_metrics":early_counts,
           "authority_grants":0,"consumer_side_effects":0,"rows":rows}
    return raw


def main():
    spec_path, out_path = map(Path, sys.argv[1:3])
    raw = build(json.loads(spec_path.read_text()), spec_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(raw, sort_keys=True, separators=(",",":"))+"\n")
    print(json.dumps({k:raw[k] for k in ("world_count","trace_count","unique_prefix_count","disposition_counts","early_finalization_metrics")}))


if __name__ == "__main__":
    main()
