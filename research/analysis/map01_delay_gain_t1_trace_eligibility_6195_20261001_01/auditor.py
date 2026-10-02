#!/usr/bin/env python3
"""Independent raw-only T1 checker; does not import candidate.py."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

EXPECTED = {
    "v38": ("02d65d49b61feadbdec2e051bd23d1ca845d5df1", "research/doom/results/map01-v38-integrated-threat-live-01/runtime/events.jsonl"),
    "v39": ("cbaeed9c7ba27b53cef9d10730ae33313371ad9a", "research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl"),
}
CONSUMER_TAGS = {"consumed_sequence", "consumed_generation", "source_generation", "source_observation_id", "consumed_observation_id"}
DECISION_KINDS = {"decision", "model_response", "plan", "plan_received", "policy_output", "action_selection"}
EFFECT_KINDS = {"task_effect", "effect_scored", "independent_effect", "objective_effect"}
EFFECT_TAGS = {"independent_effect_id", "task_effect_score", "independent_scorer", "effect_oracle_id"}
RELEASE_KINDS = {"input_released", "keys_released", "release_verified"}


def blob_id(data: bytes) -> str:
    header = ("blob %d\0" % len(data)).encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def keys(obj) -> set[str]:
    result: set[str] = set()
    if isinstance(obj, dict):
        for name, value in obj.items():
            result.add(str(name))
            result |= keys(value)
    elif isinstance(obj, list):
        for value in obj:
            result |= keys(value)
    return result


def is_verified_up(record: dict) -> bool:
    return record.get("event") in RELEASE_KINDS and any(record.get(k) is True for k in ("verified_empty", "empty_input_verified", "terminal_input_empty")) and any(type(v) is int and key.endswith("_ns") for key, v in record.items())


def domain_if_clocked(record: dict) -> str | None:
    domain = record.get("clock_domain", record.get("monotonic_clock_id"))
    stamped = any(type(v) is int and k.endswith("_ns") for k, v in record.items())
    return str(domain) if domain is not None and stamped else None


def consumed_values(record) -> list[str]:
    values: list[str] = []
    if isinstance(record, dict):
        for name, value in record.items():
            if name in CONSUMER_TAGS and value is not None and value != "":
                values.append(json.dumps(value, sort_keys=True))
            values.extend(consumed_values(value))
    elif isinstance(record, list):
        for value in record:
            values.extend(consumed_values(value))
    return values


def same_release(press: dict, release: dict) -> bool:
    if not is_verified_up(release) or not press.get("id") or press.get("id") != release.get("id"):
        return False
    if "step" in press and press.get("step") != release.get("step"):
        return False
    return not ("keys" in press and "keys" in release and press.get("keys") != release.get("keys"))


def summarize(name: str, location: str) -> dict:
    data = Path(location).read_bytes()
    expected_blob, repo_path = EXPECTED[name]
    actual_blob = blob_id(data)
    if actual_blob != expected_blob:
        raise ValueError(f"wrong pinned Git blob: {name} {actual_blob}")
    events = [json.loads(line) for line in data.splitlines() if line.strip()]
    kinds = Counter(event.get("event", "<missing>") for event in events)
    capture = [e for e in events if e.get("event") in ("observation", "typed_observation") and type(e.get("capture_ns")) is int and type(e.get("sequence")) is int]
    bound = [e for e in events if e.get("event") in DECISION_KINDS and consumed_values(e)]
    down = [e for e in events if e.get("event") == "keys_held"]
    up = [e for e in events if e.get("event") in RELEASE_KINDS]
    verified_up = [e for e in up if is_verified_up(e)]
    unused_up = list(verified_up)
    matched_up = 0
    for press in down:
        position = next((i for i, release in enumerate(unused_up) if same_release(press, release)), None)
        if position is not None:
            matched_up += 1
            unused_up.pop(position)
    generations = sorted({value for decision in bound for value in consumed_values(decision)})
    effect = [e for e in events if e.get("event") in EFFECT_KINDS or bool(keys(e) & EFFECT_TAGS)]
    all_keys = set().union(*(keys(e) for e in events)) if events else set()
    domains = {domain_if_clocked(e) for group in (bound, down, effect) for e in group}
    checks = {
        "source_capture_with_sequence": len(capture) > 0,
        "decision_bound_to_consumed_generation": len(bound) > 0,
        "held_input_with_identity_bound_release": len(down) > 0 and matched_up == len(down),
        "same_trace_monotonic_clock_bridges_decision_action_effect": len(bound) > 0 and len(down) > 0 and len(effect) > 0 and None not in domains and len(domains) == 1,
        "independently_task_relevant_effect": len(effect) > 0,
        "repeated_correction_opportunity": len(generations) >= 2 and len(down) > 0,
    }
    return {
        "label": name,
        "source": {"git_blob": expected_blob, "repo_path": repo_path},
        "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "git_blob_sha": actual_blob,
        "events": len(events), "event_counts": dict(sorted(kinds.items())),
        "capture_rows": len(capture), "generation_bound_decision_rows": len(bound), "distinct_consumed_generation_values": len(generations),
        "keys_held_rows": len(down), "release_rows": len(up), "verified_empty_release_rows": len(verified_up), "identity_matched_release_rows": matched_up, "effect_rows": len(effect),
        "relevant_field_names": sorted(k for k in all_keys if any(term in k.lower() for term in ("sequence", "generation", "capture", "effect", "score", "release", "decision", "source", "clock"))),
        "gates": checks, "eligible": all(checks.values()),
    }


def valid(document: dict, paths: dict[str, str]) -> bool:
    expected_rows = [summarize(label, paths[label]) for label in ("v38", "v39")]
    disposition = "T1_ELIGIBLE_TRACE_FOUND" if any(row["eligible"] for row in expected_rows) else "HOLD_NO_CLOSED_LOOP_TRACE"
    return (
        document.get("schema") == "agent-interface/6195-t1-trace-eligibility-v1"
        and document.get("allocation_id") == "MAP01-DELAY-GAIN-TRACE-ELIGIBILITY-6195-T1-20261001-01"
        and document.get("main_sha") == "14b81dd1f6853623a694266b98538f812847257a"
        and document.get("traces") == expected_rows
        and document.get("disposition") == disposition
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--v38", required=True)
    ap.add_argument("--v39", required=True)
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    locations = {"v38": args.v38, "v39": args.v39}
    raw = Path(args.input).read_bytes()
    candidate = json.loads(raw)
    matches = valid(candidate, locations)
    probes = []
    edits = [
        lambda d: d["traces"][0].__setitem__("bytes", -1),
        lambda d: d["traces"][1]["gates"].__setitem__("independently_task_relevant_effect", True),
        lambda d: d.__setitem__("disposition", "T1_ELIGIBLE_TRACE_FOUND"),
        lambda d: d["traces"].pop(),
        lambda d: d.__setitem__("main_sha", "0" * 40),
    ]
    for n, edit in enumerate(edits, 1):
        mutated = json.loads(json.dumps(candidate))
        edit(mutated)
        probes.append({"mutation": n, "rejected": not valid(mutated, locations)})
    errors = []
    if not matches:
        errors.append("candidate disagrees with independent raw reconstruction")
    if any(not x["rejected"] for x in probes):
        errors.append("one or more mutation probes were accepted")
    output = {
        "schema": "agent-interface/6195-t1-trace-eligibility-audit-v1",
        "allocation_id": "MAP01-DELAY-GAIN-TRACE-ELIGIBILITY-6195-T1-20261001-01",
        "candidate_sha256": hashlib.sha256(raw).hexdigest(),
        "independent_match": matches,
        "traces_reconstructed": 2 if matches else 0,
        "mutations": probes,
        "errors": errors,
        "disposition": "PASS_AUDIT_RECONSTRUCTION" if not errors else "FAIL_AUDIT",
    }
    Path(args.output).write_text(json.dumps(output, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"disposition": output["disposition"], "traces": output["traces_reconstructed"], "mutations_rejected": sum(x["rejected"] for x in probes), "errors": errors}))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
