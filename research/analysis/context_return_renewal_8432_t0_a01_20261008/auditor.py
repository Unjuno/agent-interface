"""Independent verifier and frozen mutation controls for the T0 package."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def canon(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def reconstruct(protocol):
    f = protocol["factors"]
    rows = []
    for phase, context, map_id in (("acquire_A", "A", "A"), ("correct_B", "B", "B")):
        for ordinal, action in zip(range(1, 5), f["demonstration_action_order"]):
            rows.append({"event_id": phase + "-" + str(ordinal), "phase": phase,
                         "context_marker": context, "mapping_id": map_id,
                         "cue_id": f["cue_id"], "action": action,
                         "observed_outcome": f["mapping_" + map_id][action],
                         "source_kind": "fixed_outcome_example"})
    episodes = []
    for treatment in ("chronological", "context_tagged", "none"):
        for route in protocol["tracks"]:
            records = rows if treatment != "none" else []
            view = {"treatment": treatment, "records": records}
            if treatment == "context_tagged":
                view["applicability"] = {"A": "context-A-only", "B": "context-B-only"}
            phase_tests = []
            for phase in route["phases"]:
                if phase["kind"] == "demonstration":
                    continue
                trials = []
                for ordinal in (1, 2, 3, 4):
                    trials.append({"trial_id": phase["phase"] + "-" + str(ordinal),
                                   "context_marker": phase["context_marker"],
                                   "cue_id": f["cue_id"], "mapping_id": phase["mapping_id"],
                                   "action_support": list(f["actions"]),
                                   "outcome_oracle": dict(protocol["scorer"]["outcomes"])})
                phase_tests.append({"phase": phase["phase"],
                                    "context_marker": phase["context_marker"],
                                    "mapping_id": phase["mapping_id"], "trials": trials})
            episodes.append({"track_id": route["id"], "history_treatment": treatment,
                             "environment_phase_order": [x["phase"] for x in route["phases"]],
                             "history": view, "test_phases": phase_tests})
    return {"format": "context-return-renewal-t0-raw-v1",
            "allocation_id": protocol["allocation_id"], "candidate_invocations": 1,
            "model_calls": 0, "gui_calls": 0, "external_network_calls": 0,
            "cue_support": [f["cue_id"]], "action_support": list(f["actions"]),
            "episodes": episodes,
            "diagnostic_proposal_traces": protocol["diagnostic_proposal_traces"],
            "diagnostic_trace_label": "deterministic scorer controls only; not model observations",
            "current_mapping_id": protocol["scorer"]["current_mapping_id"],
            "executed_effects": False}


def validate(raw, protocol):
    if canon(raw) != canon(reconstruct(protocol)):
        raise ValueError("raw differs from independent frozen reconstruction")
    if raw["candidate_invocations"] != 1 or any(raw[k] != 0 for k in (
            "model_calls", "gui_calls", "external_network_calls")):
        raise ValueError("invocation/scope mismatch")
    matched = [e for e in raw["episodes"] if e["history_treatment"] != "none"]
    if len(matched) != 12:
        raise ValueError("expected 12 matched episodes")
    for episode in matched:
        if len(episode["history"]["records"]) != 8:
            raise ValueError("matched history count mismatch")
        if len(episode["test_phases"]) != 2 or any(len(p["trials"]) != 4 for p in episode["test_phases"]):
            raise ValueError("test sample count mismatch")
        if [p["mapping_id"] for p in episode["test_phases"]] != ["B", "B"]:
            raise ValueError("current mapping must remain B")
        if any(r["phase"] not in ("acquire_A", "correct_B") for r in episode["history"]["records"]):
            raise ValueError("test mapping leaked into history")
        counts = {}
        for r in episode["history"]["records"]:
            key = (r["phase"], r["action"], r["observed_outcome"])
            counts[key] = counts.get(key, 0) + 1
        if counts != {("acquire_A", "old_choice", 1): 2,
                      ("acquire_A", "corrected_choice", 0): 2,
                      ("correct_B", "old_choice", 0): 2,
                      ("correct_B", "corrected_choice", 1): 2}:
            raise ValueError("cue/action/outcome support mismatch")
    return True


def score(trace, outcomes):
    n = len(trace)
    if n != 4:
        raise ValueError("diagnostic trace size mismatch")
    return {"trials": n,
            "old_choice_recurrence_count": sum(x == "old_choice" for x in trace),
            "regret": sum(max(outcomes.values()) - outcomes[x] for x in trace)}


def controls(protocol):
    cases = protocol["diagnostic_proposal_traces"]
    no_signal = {k: score(v, protocol["scorer"]["outcomes"]) for k, v in cases["no_signal"].items()}
    if len({(x["old_choice_recurrence_count"], x["regret"]) for x in no_signal.values()}) != 1:
        raise ValueError("no-signal control disagrees across contexts")
    seeded = {k: score(v, protocol["scorer"]["outcomes"]) for k, v in cases["seeded_return_signal"].items()}
    a, b, c = seeded["context_return"], seeded["continued_B"], seeded["novel_C"]
    if not (a["old_choice_recurrence_count"] > b["old_choice_recurrence_count"] and
            a["old_choice_recurrence_count"] > c["old_choice_recurrence_count"] and
            a["regret"] > b["regret"] and a["regret"] > c["regret"]):
        raise ValueError("seeded return signal not distinguished")
    return {"no_signal": no_signal, "seeded_return_signal": seeded}


def mutations(raw, protocol):
    cases = {}
    bad = copy.deepcopy(raw)
    bad["episodes"][0]["history"]["records"].append({"phase": "return_A", "mapping_id": "B"})
    cases["leak_test_mapping_into_history"] = bad
    bad = copy.deepcopy(raw)
    bad["episodes"][0]["environment_phase_order"].remove("correct_B")
    cases["erase_phase_boundary"] = bad
    bad = copy.deepcopy(raw)
    bad["episodes"][0]["test_phases"][1]["context_marker"] = "B"
    cases["relabel_return_context"] = bad
    bad = copy.deepcopy(raw)
    bad["episodes"][0]["test_phases"][1]["mapping_id"] = "A"
    cases["change_current_mapping"] = bad
    result = {}
    for name, altered in cases.items():
        try:
            validate(altered, protocol)
        except (KeyError, TypeError, ValueError):
            result[name] = True
        else:
            result[name] = False
    if not all(result.values()):
        raise ValueError("a frozen mutation was accepted: " + repr(result))
    return result


def main():
    freeze = read("FREEZE.json")
    protocol = read("PROTOCOL.json")
    for filename, field in (("PROTOCOL.json", "protocol_sha256"),
                            ("candidate.py", "candidate_sha256"),
                            ("auditor.py", "auditor_sha256")):
        if hashlib.sha256((ROOT / filename).read_bytes()).hexdigest() != freeze[field]:
            raise ValueError("frozen identity mismatch: " + filename)
    raw_path = ROOT / "RAW.json"
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    validate(raw, protocol)
    audit = {"format": "context-return-renewal-t0-audit-v1",
             "status": "PASS_METHOD_SCOPED", "allocation_id": protocol["allocation_id"],
             "source_commit": freeze["main_sha"],
             "protocol_sha256": freeze["protocol_sha256"],
             "candidate_sha256": freeze["candidate_sha256"],
             "auditor_sha256": freeze["auditor_sha256"],
             "raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
             "episodes_independently_reconstructed": len(raw["episodes"]),
             "matched_treatment_track_episodes": 12,
             "source_examples_per_matched_episode": 8,
             "test_trials_per_test_phase": 4,
             "diagnostic_scorer_controls": controls(protocol),
             "mutation_controls_rejected": mutations(raw, protocol),
             "model_calls": 0, "gui_calls": 0, "external_network_calls": 0,
             "scope": "Finite deterministic method construction only; no model-choice, learning, or GUI-behavior evidence."}
    out = ROOT / "AUDIT.json"
    with out.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(audit, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(json.dumps(audit, sort_keys=True, separators=(",", ":"), ensure_ascii=False))


if __name__ == "__main__":
    main()
