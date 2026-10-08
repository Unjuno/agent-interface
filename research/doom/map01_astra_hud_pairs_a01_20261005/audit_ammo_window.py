"""Independent raw reconstruction of the retained adjacent ammo windows."""
import hashlib
import json
from pathlib import Path, PurePosixPath

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
DATA = REPO / "research/doom/results/map01-astra-attempt-v1"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    pins = json.loads((HERE / "AMMO_WINDOW_INPUTS.json").read_text())
    mismatches = []
    for relative, expected in pins["inputs"].items():
        if digest(REPO / relative) != expected:
            mismatches.append({"kind": "input-hash", "path": relative})
    report = json.loads((DATA / "report.json").read_text())
    events = [json.loads(line) for line in (DATA / "events.jsonl").read_text().splitlines()]
    failure = json.loads((DATA / "failure-analysis-v1.json").read_text())
    local = json.loads((DATA / "local-exact-frame-manifest.json").read_text())
    observed = {row["sequence"]: row for row in events if row.get("event") == "observation" and row.get("sequence") in {117, 148, 211}}
    if set(observed) != {117, 148, 211}:
        mismatches.append({"kind": "endpoint-sequences"})
    decisions = report["decisions"][3:6]
    manual_ammo = failure["visual_transcription"]["ammo"]
    independently_built = []
    for offset, (from_i, to_i, a, b) in enumerate(((3,4,117,148),(4,5,148,211))):
        left, right = report["decisions"][from_i], report["decisions"][to_i]
        if PurePosixPath(left["source_image"]).name != PurePosixPath(observed[a]["image"]).name:
            mismatches.append({"kind":"left-source-link","decision":from_i})
        if PurePosixPath(right["source_image"]).name != PurePosixPath(observed[b]["image"]).name:
            mismatches.append({"kind":"right-source-link","decision":to_i})
        plan = left["execution_trace"][0]["id"]
        keys = [key for event in events if event.get("event")=="keys_held" and event.get("id")==plan for key in event.get("keys",[])]
        terminals = [event for event in events if event.get("event")=="terminal" and event.get("id")==plan]
        release = terminals[0].get("release") if len(terminals)==1 else None
        if not isinstance(release,dict) or release.get("event")!="owner_release" or release.get("verified") is not True or release.get("buttons_down")!=[] or release.get("keys_down")!=[]:
            mismatches.append({"kind":"owner-release-receipt","plan_id":plan})
        independently_built.append({
            "from_decision":from_i,
            "to_decision":to_i,
            "sequences":[a,b],
            "capture_delta_ns":observed[b]["capture_ns"]-observed[a]["capture_ns"],
            "ammo":[manual_ammo[from_i],manual_ammo[to_i]],
            "ammo_delta":manual_ammo[to_i]-manual_ammo[from_i],
            "commands":left["action"].get("commands",[]),
            "held_keys":keys,
            "owner_release": {
                "event":release.get("event") if release else None,
                "reason":release.get("reason") if release else None,
                "verified":release.get("verified") if release else None,
                "buttons_down":release.get("buttons_down") if release else None,
                "keys_down":release.get("keys_down") if release else None,
                "verified_ns":release.get("verified_ns") if release else None,
                "terminal_ns":terminals[0].get("terminal_ns") if len(terminals)==1 else None,
                "capture_to_verified_release_ms":(release["verified_ns"]-observed[b]["capture_ns"])/1e6 if release and "verified_ns" in release else None,
            },
            "plan_id":plan,
        })
    release_types=sorted({str(row.get("event")) for row in events if any(term in str(row.get("event","")).lower() for term in ("release","keyup","key_up"))})
    recorded=json.loads((HERE/"AMMO_WINDOW_RESULT.json").read_text())
    if recorded["windows"] != [
        {
            "from_decision":row["from_decision"],
            "to_decision":row["to_decision"],
            "source_sequences":row["sequences"],
            "source_capture_ns":[observed[row["sequences"][0]]["capture_ns"],observed[row["sequences"][1]]["capture_ns"]],
            "source_capture_interval_ms":row["capture_delta_ns"]/1e6,
            "ammo_manual":row["ammo"],
            "ammo_delta":row["ammo_delta"],
            "planner_commands":row["commands"],
            "compiled_commands":report["decisions"][row["from_decision"]]["compiled_commands"],
            "plan_id":row["plan_id"],
            "event_held_keys":row["held_keys"],
            "owner_release":row["owner_release"],
            "controller_model_interval_ms":(report["decisions"][row["from_decision"]]["controller_model_ended_ns"]-report["decisions"][row["from_decision"]]["controller_model_started_ns"])/1e6,
            "controller_model_start_ns":report["decisions"][row["from_decision"]]["controller_model_started_ns"],
            "controller_model_end_ns":report["decisions"][row["from_decision"]]["controller_model_ended_ns"],
            "selected_frame_sha256":{str(row["from_decision"]):json.loads((DATA/"frame-manifest.json").read_text())[row["from_decision"]]["sha256"],str(row["to_decision"]):json.loads((DATA/"frame-manifest.json").read_text())[row["to_decision"]]["sha256"]},
        } for row in independently_built
    ]:
        mismatches.append({"kind":"candidate-window-mismatch"})
    if recorded.get("standalone_release_event_type_count") != sum(1 for row in events if row.get("event")=="owner_release"):
        mismatches.append({"kind":"standalone-release-count"})
    audit={
        "schema":"map01-astra-ammo-window-audit-v1",
        "disposition":"PASS_AUDITED_POSTHOC_JOIN_HOLD_CAUSAL_ATTRIBUTION" if not mismatches else "FAIL_AMMO_WINDOW_AUDIT",
        "ammo_windows_recomputed":independently_built,
        "nested_owner_release_receipts_recomputed":[row["owner_release"] for row in independently_built],
        "standalone_release_event_type_count_recomputed":sum(1 for row in events if row.get("event")=="owner_release"),
        "mismatch_count":len(mismatches),
        "mismatches":mismatches,
        "scope":"independent report/event arithmetic and action-key joins only; HUD values and scene semantics remain manual",
    }
    (HERE/"AMMO_WINDOW_AUDIT.json").write_text(json.dumps(audit,indent=2)+"\n")
    print(json.dumps({"disposition":audit["disposition"],"mismatch_count":len(mismatches),"ammo_deltas":[row["ammo_delta"] for row in independently_built]},separators=(",",":")))
    if mismatches: raise SystemExit(1)


if __name__=="__main__":main()
