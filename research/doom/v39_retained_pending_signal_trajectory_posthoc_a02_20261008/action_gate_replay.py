"""Re-evaluate retained V39 action gates with the exact current-main function."""
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]
FREEZE=json.loads((ROOT/"GUARD_FREEZE.json").read_text(encoding="utf-8"))


def load_evaluator():
    identity=FREEZE["action_gate_source"]
    source=ROOT/identity["snapshot"]
    if hashlib.sha256(source.read_bytes()).hexdigest()!=identity["sha256"]:
        raise ValueError("frozen action gate source hash mismatch")
    actual=subprocess.check_output(["git","-C",str(REPO),"rev-parse",
        f"{FREEZE['current_main_commit']}:{identity['path']}"],text=True).strip()
    if actual!=identity["git_blob"]:
        raise ValueError("frozen main action gate blob mismatch")
    spec=importlib.util.spec_from_file_location("frozen_action_validity",source)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.evaluate_action_validity,module.action_fingerprint


def compute():
    evaluate,fingerprint=load_evaluator()
    for name,digest in FREEZE["prior_a01_inputs"].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:
            raise ValueError(f"frozen A01 input hash mismatch: {name}")
    report=json.loads((ROOT/"report.json").read_text(encoding="utf-8"))
    decisions=[]
    for d in report["decisions"]:
        final=d.get("final_action_admission") or {}
        validity=final.get("action_validity")
        if validity is None:
            continue
        commands=(d.get("action") or {}).get("commands")
        if commands is None or fingerprint(commands)!=validity["contract"]["action_fingerprint"]:
            raise ValueError(f"action command fingerprint mismatch at decision {d['iteration']}")
        result=evaluate(commands,validity["contract"],validity["snapshot"],validity["controller_decided_ns"])
        if result!=validity:
            raise ValueError(f"current-main reevaluation differs at decision {d['iteration']}")
        contract=validity["contract"]
        source=contract["source"]["signals"]["health"]["value"]
        current=validity["snapshot"]["signals"]["health"]["value"]
        max_loss=next(p["value"] for p in contract["predicates"]
                      if p["signal_id"]=="health" and p["operator"]=="max_decrease_from_source")
        cover=d.get("cover_validity_admission") or {}
        effective=cover.get("effective") or {}
        decisions.append({
            "decision":d["iteration"],
            "source_health":source,
            "current_health":current,
            "observed_loss":source-current,
            "action_max_health_loss":max_loss,
            "action_minimum_health":source-max_loss,
            "cover_monitor_mode":cover.get("monitor_mode"),
            "cover_source_iteration":d.get("cover_policy_source_iteration"),
            "cover_hard_minimum":effective.get("hard_minimum"),
            "admission":final.get("status"),
            "reason":final.get("reason"),
            "reevaluation_matches_report":True,
            "executor_admission":final.get("executor_admission"),
            "effect_receipts":len(d.get("effect_receipts") or []),
            "prior_soft_event_summary":d.get("prior_soft_event_summary"),
        })
    rejected=[d for d in decisions if d["admission"]=="REJECTED_ACTION_NOT_CURRENT"]
    return {
        "schema":"v39-retained-action-gate-replay-v1",
        "classification":"POSTHOC_REPLAY_NOT_NEW_LIVE_ALLOCATION",
        "current_main_commit":FREEZE["current_main_commit"],
        "action_gate_git_blob":FREEZE["action_gate_source"]["git_blob"],
        "report_sha256":FREEZE["prior_a01_inputs"]["report.json"],
        "decisions_replayed":len(decisions),
        "decisions":decisions,
        "rejected_current_actions":len(rejected),
        "limitations":[
            "This re-evaluates recorded action contracts and snapshots; it does not infer that rejected plans were semantically wrong.",
            "A rejected action receives no executor admission or task effect in this record.",
            "Historical HUD signals are template-derived; no fresh controller, game, model, GUI, or OS input was run.",
        ],
    }
