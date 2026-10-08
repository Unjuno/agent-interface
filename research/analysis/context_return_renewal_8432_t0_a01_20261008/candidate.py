"""One-shot deterministic T0 materializer; no model, GUI, or network calls."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def materialize(protocol):
    f = protocol["factors"]
    rows = []
    for phase, context, map_id in (("acquire_A", "A", "A"), ("correct_B", "B", "B")):
        for ordinal, action in enumerate(f["demonstration_action_order"], 1):
            rows.append({
                "event_id": f"{phase}-{ordinal}", "phase": phase,
                "context_marker": context, "mapping_id": map_id,
                "cue_id": f["cue_id"], "action": action,
                "observed_outcome": f["mapping_" + map_id][action],
                "source_kind": "fixed_outcome_example",
            })
    episodes = []
    for treatment in protocol["history_treatments"]:
        for track in protocol["tracks"]:
            tests = []
            for phase in track["phases"]:
                if phase["kind"] != "test":
                    continue
                trials = [{
                    "trial_id": f"{phase['phase']}-{i}",
                    "context_marker": phase["context_marker"],
                    "cue_id": f["cue_id"], "mapping_id": phase["mapping_id"],
                    "action_support": f["actions"],
                    "outcome_oracle": protocol["scorer"]["outcomes"],
                } for i in range(1, f["n_trials_per_test_phase"] + 1)]
                tests.append({"phase": phase["phase"],
                              "context_marker": phase["context_marker"],
                              "mapping_id": phase["mapping_id"], "trials": trials})
            if treatment == "chronological":
                history = {"treatment": treatment, "records": rows}
            elif treatment == "context_tagged":
                history = {"treatment": treatment,
                           "applicability": {"A": "context-A-only", "B": "context-B-only"},
                           "records": rows}
            elif treatment == "none":
                history = {"treatment": treatment, "records": []}
            else:
                raise ValueError("unknown history treatment")
            episodes.append({"track_id": track["id"], "history_treatment": treatment,
                             "environment_phase_order": [p["phase"] for p in track["phases"]],
                             "history": history, "test_phases": tests})
    return {
        "format": "context-return-renewal-t0-raw-v1",
        "allocation_id": protocol["allocation_id"], "candidate_invocations": 1,
        "model_calls": 0, "gui_calls": 0, "external_network_calls": 0,
        "cue_support": [f["cue_id"]], "action_support": f["actions"],
        "episodes": episodes, "diagnostic_proposal_traces": protocol["diagnostic_proposal_traces"],
        "diagnostic_trace_label": "deterministic scorer controls only; not model observations",
        "current_mapping_id": protocol["scorer"]["current_mapping_id"],
        "executed_effects": False,
    }


def main():
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    protocol_path = ROOT / "PROTOCOL.json"
    protocol_bytes = protocol_path.read_bytes()
    protocol_hash = hashlib.sha256(protocol_bytes).hexdigest()
    if protocol_hash != freeze["protocol_sha256"]:
        raise ValueError("protocol identity mismatch")
    if hashlib.sha256((ROOT / "candidate.py").read_bytes()).hexdigest() != freeze["candidate_sha256"]:
        raise ValueError("candidate source identity mismatch")
    raw_path = ROOT / "RAW.json"
    with raw_path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(materialize(json.loads(protocol_bytes)), handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(json.dumps({"status": "MATERIALIZED_ONCE",
                      "raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
                      "episodes": 18, "model_calls": 0, "gui_calls": 0,
                      "external_network_calls": 0}, sort_keys=True))


if __name__ == "__main__":
    main()

