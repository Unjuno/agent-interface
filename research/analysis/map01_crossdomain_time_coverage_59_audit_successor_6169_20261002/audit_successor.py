"""Independent raw-only audit of the immutable #6164 candidate result."""
import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
INPUTS = HERE / "_run" / "inputs"
RAW_NAMES = (
    "doom-v38-events.jsonl", "doom-v39-events.jsonl", "doom-analysis.json",
    "openttd-events.jsonl", "openttd-observer.txt", "openttd-audit.json",
)


def jsonl(text):
    rows = [json.loads(line) for line in text.splitlines() if line.strip()]
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError("JSONL rows must be objects")
    return rows


def observer_rows(text):
    rows = []
    for line in text.splitlines():
        marker = line.find("AIT {")
        if marker < 0:
            continue
        row = json.loads(line[marker + 4:])
        if isinstance(row, dict) and isinstance(row.get("tiles"), list):
            rows.append(row)
    return rows


def observer_states(rows):
    return [tuple((tile.get("id"), tile.get("road"), tile.get("owner"))
                  for tile in row["tiles"]) for row in rows]


def event_counts(rows):
    counts = {}
    for row in rows:
        event = row.get("event")
        if not isinstance(event, str):
            raise ValueError("raw event missing event name")
        counts[event] = counts.get(event, 0) + 1
    return counts


def neutral_terminal_joins(pointer_downs, events):
    terminals = {row.get("id"): row for row in events if row.get("event") == "terminal"}
    return sum(
        row.get("id") in terminals
        and terminals[row["id"]].get("release", {}).get("verified") is True
        and terminals[row["id"]]["release"].get("buttons_down") == []
        and terminals[row["id"]]["release"].get("keys_down") == []
        for row in pointer_downs
    )


def audit(freeze, contents, candidate):
    errors = []

    def expect(condition, label):
        if not condition:
            errors.append(label)

    for name in RAW_NAMES:
        expected = freeze["inputs"].get(name)
        observed = hashlib.sha256(contents[name].encode("utf-8")).hexdigest()
        expect(observed == expected, f"raw hash mismatch: {name}")
    expect(candidate.get("source_sha256") == freeze["inputs"],
           "candidate source hash map differs from freeze")
    expect(candidate.get("candidate_invocations") == 1
           and candidate.get("retries") == 0,
           "predecessor candidate invocation accounting differs")
    expect(candidate.get("status") == "HOLD_CROSSDOMAIN_TIME_COVERAGE_UNIDENTIFIED"
           and candidate.get("cross_domain_time_coverage_identified") is False
           and candidate.get("shared_time_denominator_identified") is False,
           "candidate does not preserve scoped HOLD")

    v38, v39, analysis, openttd, observer_text, task_audit = (
        jsonl(contents[RAW_NAMES[0]]), jsonl(contents[RAW_NAMES[1]]),
        json.loads(contents[RAW_NAMES[2]]), jsonl(contents[RAW_NAMES[3]]),
        contents[RAW_NAMES[4]], json.loads(contents[RAW_NAMES[5]]),
    )
    domains = {row.get("domain"): row for row in candidate.get("domains", [])}
    for version, rows, name in (("v38", v38, "doom_v38"),
                                 ("v39", v39, "doom_v39")):
        result = domains.get(name, {})
        counts = event_counts(rows)
        expect(result.get("event_counts") == counts,
               f"{name} candidate/raw event counts differ")
        admissions = [r for r in rows if r.get("event") == "input_admission"]
        held = [r for r in rows if r.get("event") == "keys_held"]
        released = [r for r in rows if r.get("event") == "input_released"]
        scores = [r for r in rows if r.get("event") == "post_control_score"]
        expect(result.get("admitted_actuations") == len(admissions),
               f"{name} admitted-actuation count differs")
        expect(result.get("input_released_program_records") == len(released),
               f"{name} release-record count differs")
        expect(result.get("first_useful_feedback_verified") is False,
               f"{name} overstates useful feedback")
        expect(result.get("per_actuation_occupancy_identified") is False
               and result.get("time_coverage_identified") is False,
               f"{name} overstates occupancy/time coverage")
        expect(len(admissions) == (11 if version == "v38" else 39)
               and len(held) == (11 if version == "v38" else 28)
               and len(released) == (0 if version == "v38" else 1)
               and len(scores) == 1,
               f"{name} raw event counts differ from independently fixed fixture")
        expect(bool(scores) and result.get("post_control_scores") == scores,
               f"{name} post-control score rows differ from raw")
        expect(all(r.get("map_exit") is False for r in scores),
               f"{name} raw outcome unexpectedly reports map exit")
        expect(not any(r.get("event") in {"physical_up", "key_up_admission"}
                       or (r.get("event") == "input_released" and r.get("key") is not None)
                       for r in rows),
               f"{name} has an unexpected per-press-up witness")

    observer = observer_rows(observer_text)
    states = observer_states(observer)
    transitions = [i for i in range(1, len(states)) if states[i] != states[i - 1]]
    unique_states = len(set(states))
    button_downs = [r for r in openttd if r.get("event") == "pointer_admission"
                    and r.get("operation") == "button_down"]
    button_ups = [r for r in openttd if r.get("event") == "pointer_admission"
                  and r.get("operation") == "button_up"]
    neutral_joins = neutral_terminal_joins(button_downs, openttd)
    od = domains.get("openttd", {})
    oc = event_counts(openttd)
    expect(od.get("event_counts") == oc, "OpenTTD candidate/raw event counts differ")
    expect(od.get("admitted_actuations") == 9,
           "OpenTTD admitted actuation count differs")
    expect((len(button_downs), len(button_ups), neutral_joins) == (7, 0, 7),
           "OpenTTD pointer/neutral raw counts differ from frozen fixture")
    expect(od.get("pointer_button_down_admissions") == len(button_downs)
           and od.get("per_button_up_admissions") == len(button_ups)
           and od.get("same_program_verified_neutral_terminal_joins") == neutral_joins,
           "OpenTTD candidate pointer counts differ from raw")
    expect((len(observer), unique_states, transitions) == (263, 2, [91]),
           "OpenTTD observer raw reconstruction differs")
    # These fields intentionally describe different levels of evidence.
    expect(od.get("observer_records") == len(transitions),
           "OpenTTD scoreable transition-witness count differs")
    expect(od.get("observer_record_count") == len(observer),
           "OpenTTD total parsed observer-record count differs")
    expect(od.get("observer_transition_indices") == transitions
           and od.get("observer_unique_states") == unique_states,
           "OpenTTD observer transition summary differs")
    expect(od.get("effect_clock_join_identified") is False
           and od.get("time_coverage_identified") is False,
           "OpenTTD promotes unjoined observer transition")
    top_level_link_fields = {key for row in observer for key in row
                             if key.endswith("_ns") or "clock" in key
                             or "sequence" in key or key in {"actuation_id", "action_id"}}
    expect(not top_level_link_fields, "observer has unexpected host/action join fields")
    outcome = task_audit["continuous_independent_observer_outcome"]
    expect(outcome.get("status") == "partial_A_to_B_only"
           and task_audit.get("hard_success") is False,
           "OpenTTD independent task outcome differs")

    return {
        "schema": "map01-crossdomain-time-coverage-audit-successor-v1",
        "allocation_id": freeze["allocation_id"],
        "status": "PASS_AUDIT_SUCCESSOR_SCOPED" if not errors else "FAIL_AUDIT_SUCCESSOR",
        "errors": errors,
        "reconstructed": {
            "doom_v38": {"input_admissions": 11, "keys_held": 11,
                          "input_released": 0, "post_control_score": 1,
                          "per_press_up": False},
            "doom_v39": {"input_admissions": 39, "keys_held": 28,
                          "input_released": 1, "post_control_score": 1,
                          "per_press_up": False},
            "openttd": {"button_down_admissions": len(button_downs),
                        "button_up_admissions": len(button_ups),
                        "neutral_terminal_joins": neutral_joins,
                        "observer_transition_witnesses": len(transitions),
                        "observer_record_count": len(observer),
                        "transition_indices": transitions,
                        "unique_states": unique_states},
        },
        "limitations": ["raw-only audit of retained evidence",
                        "no per-actuation physical occupancy or common time denominator",
                        "no new candidate, model, game, GUI, input, or task-effect run"],
    }


def load_inputs():
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    # Decode the exact bytes without universal-newline translation so hashes
    # remain bound to the retained source blobs on Windows as well as POSIX.
    contents = {name: (INPUTS / name).read_bytes().decode("utf-8") for name in RAW_NAMES}
    candidate = json.loads((INPUTS / "candidate_result.json").read_text(encoding="utf-8"))
    return freeze, contents, candidate


def main():
    freeze, contents, candidate = load_inputs()
    result = audit(freeze, contents, candidate)
    out = HERE / "audit_result.json"
    out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS_AUDIT_SUCCESSOR_SCOPED" else 1)


if __name__ == "__main__":
    main()
