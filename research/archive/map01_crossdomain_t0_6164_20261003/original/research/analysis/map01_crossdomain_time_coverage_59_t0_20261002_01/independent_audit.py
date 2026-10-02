"""Independent raw-only reconstruction; deliberately imports no candidate code."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
INPUTS = HERE / "inputs"
FREEZE = HERE / "FREEZE.json"
RAW_NAMES = (
    "doom-v38-events.jsonl", "doom-v39-events.jsonl", "doom-analysis.json",
    "openttd-events.jsonl", "openttd-observer.txt", "openttd-audit.json",
)


def jsonl_rows(text):
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def ait_rows(text):
    out = []
    for line in text.splitlines():
        marker = line.find("AIT {")
        if marker >= 0:
            row = json.loads(line[marker + 4:])
            if isinstance(row, dict) and isinstance(row.get("tiles"), list):
                out.append(row)
    return out


def ait_transitions(rows):
    states = [tuple((tile.get("id"), tile.get("road"), tile.get("owner"))
                    for tile in row["tiles"]) for row in rows]
    transitions = [i for i in range(1, len(states)) if states[i] != states[i - 1]]
    return transitions, len(set(states))


def candidate_claims_hold(candidate):
    return (candidate.get("status") == "HOLD_CROSSDOMAIN_TIME_COVERAGE_UNIDENTIFIED"
            and candidate.get("cross_domain_time_coverage_identified") is False
            and all(row.get("time_coverage_identified") is False
                    for row in candidate.get("domains", [])))


def raw_audit(freeze, contents, candidate):
    errors = []
    if not candidate_claims_hold(candidate):
        errors.append("candidate must preserve per-domain and cross-domain HOLD")
    if candidate.get("candidate_invocations") != 1 or candidate.get("retries") != 0:
        errors.append("candidate invocation accounting mismatch")

    v38, v39, analysis, openttd, observer_text, openttd_audit = (
        jsonl_rows(contents[RAW_NAMES[0]]), jsonl_rows(contents[RAW_NAMES[1]]),
        json.loads(contents[RAW_NAMES[2]]), jsonl_rows(contents[RAW_NAMES[3]]),
        contents[RAW_NAMES[4]], json.loads(contents[RAW_NAMES[5]]),
    )
    doom_expectations = (
        ("doom_v38", v38, 11, 11, 0, 0),
        ("doom_v39", v39, 39, 28, 1, 1),
    )
    domain_results = {row.get("domain"): row for row in candidate.get("domains", [])}
    for name, rows, admissions_n, held_n, released_n, score_n in doom_expectations:
        admissions = [r for r in rows if r.get("event") == "input_admission"]
        held = [r for r in rows if r.get("event") == "keys_held"]
        released = [r for r in rows if r.get("event") == "input_released"]
        scores = [r for r in rows if r.get("event") == "post_control_score"]
        no_per_press_up = not any(
            r.get("event") in {"physical_up", "key_up_admission"}
            or (r.get("event") == "input_released" and r.get("key") is not None)
            for r in rows)
        result = domain_results.get(name, {})
        if (len(admissions), len(held), len(released), len(scores)) != (
                admissions_n, held_n, released_n, score_n):
            errors.append(f"{name} source counts differ")
        if not all(type(r.get("admitted_ns")) is int
                   and type(r.get("input_ack_ns")) is int for r in admissions):
            errors.append(f"{name} admission bracket missing")
        if not no_per_press_up:
            errors.append(f"{name} unexpectedly contains a per-press up witness")
        if result.get("per_actuation_occupancy_identified") is not False:
            errors.append(f"{name} candidate overstates physical occupancy")
        if result.get("first_useful_feedback_verified") is not False:
            errors.append(f"{name} promotes unverified plan frames to useful feedback")
        if released and any(r.get("owner_release", {}).get("verified") is not True
                            for r in released):
            errors.append(f"{name} terminal empty-input witness malformed")
        if not scores or any(r.get("map_exit") is not False for r in scores):
            errors.append(f"{name} post-control outcome inconsistent")

    analysis_runs = {r["run"]: r for r in analysis["runs"]}
    for version in ("v38", "v39"):
        name = f"map01-{version}-" + (
            "integrated-threat-live-01" if version == "v38"
            else "coast-liveness-live-01")
        if name not in analysis_runs:
            errors.append(f"missing {version} program-envelope summary")

    button_downs = [r for r in openttd if r.get("event") == "pointer_admission"
                    and r.get("operation") == "button_down"]
    button_ups = [r for r in openttd if r.get("event") == "pointer_admission"
                  and r.get("operation") == "button_up"]
    terminals = {r.get("id"): r for r in openttd if r.get("event") == "terminal"}
    neutral_join_count = sum(
        r.get("id") in terminals
        and terminals[r["id"]].get("release", {}).get("verified") is True
        and terminals[r["id"]]["release"].get("buttons_down") == []
        and terminals[r["id"]]["release"].get("keys_down") == []
        for r in button_downs)
    observer = ait_rows(observer_text)
    transitions, unique_states = ait_transitions(observer)
    top_level_link_fields = {key for row in observer for key in row
                             if key.endswith("_ns") or "clock" in key
                             or "sequence" in key or key in {"actuation_id", "action_id"}}
    openttd_result = domain_results.get("openttd", {})
    if (len(button_downs), len(button_ups), neutral_join_count) != (7, 0, 7):
        errors.append("OpenTTD button-down/up/neutral-terminal counts differ")
    if (len(observer), unique_states, transitions) != (263, 2, [91]):
        errors.append("independent OpenTTD observer transition differs")
    if top_level_link_fields:
        errors.append("OpenTTD observer unexpectedly has shared host/action identity fields")
    if openttd_result.get("effect_clock_join_identified") is not False:
        errors.append("candidate joins observer index to host actuation time")
    if openttd_result.get("observer_transition_indices") != [91]:
        errors.append("candidate observer transition index differs")
    task_outcome = openttd_audit["continuous_independent_observer_outcome"]
    if (task_outcome.get("status") != "partial_A_to_B_only"
            or openttd_audit.get("hard_success") is not False):
        errors.append("OpenTTD task outcome source mismatch")

    return {
        "schema": "map01-crossdomain-time-coverage-independent-audit-v1",
        "status": ("PASS_AUDIT_CROSSDOMAIN_HOLD_REPRODUCED" if not errors
                   else "FAIL_AUDIT"),
        "errors": errors,
        "checks": {
            "doom_raw_counts_and_missing_per_press_up": not any(
                "doom_" in error for error in errors),
            "openttd_observer_transition_and_no_clock_join": not any(
                "OpenTTD" in error or "observer" in error for error in errors),
            "candidate_keeps_time_coverage_unknown": candidate.get(
                "cross_domain_time_coverage_identified") is False,
            "source_hashes_match_freeze": all(
                hashlib.sha256(contents[name].encode("utf-8")).hexdigest()
                == freeze["inputs"][name]["sha256"] for name in RAW_NAMES),
        },
        "independently_reconstructed": {
            "doom_v38": {"input_admissions": 11, "keys_held": 11,
                          "input_released": 0, "per_press_up": False},
            "doom_v39": {"input_admissions": 39, "keys_held": 28,
                          "input_released": 1, "per_press_up": False},
            "openttd": {"button_down_admissions": 7, "button_up_admissions": 0,
                        "same_program_verified_neutral_terminals": 7,
                        "observer_records": len(observer),
                        "unique_states": unique_states,
                        "transition_indices": transitions,
                        "shared_host_or_actuation_fields": sorted(top_level_link_fields)},
        },
        "candidate_and_auditor_separate": True,
        "auditor_invocations": 1,
        "retries": 0,
    }


def run():
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    contents = {}
    for name, item in freeze["inputs"].items():
        data = (INPUTS / name).read_bytes()
        if hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise SystemExit(f"STOP_INPUT_HASH_MISMATCH:{name}")
        contents[name] = data.decode("utf-8")
    candidate = json.loads((HERE / "candidate_result.json").read_text(encoding="utf-8"))
    result = raw_audit(freeze, contents, candidate)
    result["allocation_id"] = freeze["allocation_id"]
    (HERE / "audit_result.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS_AUDIT_CROSSDOMAIN_HOLD_REPRODUCED" else 1)


if __name__ == "__main__":
    run()
