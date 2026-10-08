"""Independent reference audit; no imports from candidate or runner."""
import copy
import itertools
import json
import sys
from pathlib import Path


EVENTS = ("INVALIDATE", "POLL", "OBS_MATCH", "OBS_UNLINKED", "OBS_REPLAY", "OBS_OLD_REQUEST", "ACT")


def reference(trace):
    generation, sequence, observed_generation, stale = 0, 0, 0, False
    pending, after, serial, old = None, None, 0, None
    requests, observations, actions = [], [], []
    for event in trace:
        if event == "INVALIDATE":
            generation += 1
            stale = True
            observed_generation = -1
            old = pending
            pending = after = None
        elif event == "POLL":
            if stale and pending is None:
                serial += 1
                pending = f"req-{serial}"
                after = sequence
                requests.append({"id": pending, "generation": generation, "after_seq": after})
        elif event in ("OBS_MATCH", "OBS_UNLINKED", "OBS_REPLAY", "OBS_OLD_REQUEST"):
            supplied_id, supplied_generation, supplied_seq = pending, generation, sequence + 1
            if event == "OBS_UNLINKED":
                supplied_id = None
            if event == "OBS_REPLAY":
                supplied_seq = sequence if after is None else after
            if event == "OBS_OLD_REQUEST":
                supplied_id = old if old is not None else "superseded-request"
            valid = bool(pending is not None and supplied_id == pending and supplied_generation == generation
                         and after is not None and supplied_seq > after)
            observations.append({"event": event, "request_id": supplied_id,
                                 "generation": supplied_generation, "seq": supplied_seq, "linked": valid})
            if valid:
                sequence, observed_generation, stale, pending, after = supplied_seq, supplied_generation, False, None, None
        elif event == "ACT":
            actions.append({"generation": generation,
                             "admitted": (not stale and observed_generation == generation)})
        else:
            raise ValueError("unknown reference event")
    return {"trace": list(trace), "requests": requests, "observations": observations,
            "actions": actions,
            "final": {"generation": generation, "observation_seq": sequence,
                      "observed_generation": observed_generation, "stale": stale,
                      "pending_id": pending, "request_counter": serial}}


def audit(raw, expected):
    errors = []
    if raw.get("source_main") != expected.get("source_main"):
        errors.append("source_main")
    if raw.get("alphabet") != expected.get("alphabet"):
        errors.append("alphabet")
    rows = raw.get("rows")
    if not isinstance(rows, list) or len(rows) != expected.get("trace_count") or raw.get("trace_count") != expected.get("trace_count"):
        return errors + ["trace_count"]
    cursor = 0
    for length in range(expected["max_trace_length"] + 1):
        for trace in itertools.product(EVENTS, repeat=length):
            if rows[cursor] != reference(trace):
                errors.append(f"trace:{cursor}:reference_mismatch")
            cursor += 1
    if cursor != len(rows):
        errors.append("enumeration_completeness")
    return errors


def corruptions(raw, expected):
    probes = {}
    x = copy.deepcopy(raw); x["rows"].pop(); probes["drop_trace"] = x
    x = copy.deepcopy(raw); x["rows"][1]["actions"].append({"generation": 1, "admitted": True}); probes["accept_stale_action"] = x
    x = copy.deepcopy(raw); x["rows"][1]["final"]["stale"] = False; probes["clear_on_unlinked"] = x
    x = copy.deepcopy(raw); x["rows"][8]["requests"].append({"id": "duplicate", "generation": 1, "after_seq": 0}); probes["duplicate_pending_request"] = x
    x = copy.deepcopy(raw); x["rows"][0]["trace"].append("ACT"); probes["change_trace_event"] = x
    return {name: bool(audit(value, expected)) for name, value in probes.items()}


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    raw = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    expected = json.loads((root / "expected.json").read_text(encoding="utf-8"))
    errors = audit(raw, expected)
    mutations = corruptions(raw, expected)
    missed = [name for name, rejected in mutations.items() if not rejected]
    result = {"passed": not errors and not missed, "errors": errors,
              "mutation_controls": {"rejected": len(mutations) - len(missed), "total": len(mutations),
                                    "results": mutations}, "missed_mutations": missed}
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["passed"] else 1)
