#!/usr/bin/env python3
"""Apply preregistered Issue #5322 decision gates to an independently audited summary."""
import argparse, json
from pathlib import Path

def evaluate(summary, audit):
    if audit.get("status") != "PASS" or audit.get("errors"):
        return {"status":"STOP_AUDIT_INTEGRITY","violations":["independent raw audit did not pass"]}
    controls=audit.get("corruption_controls_rejected",{})
    expected={"drop_row","flip_truth","alter_probability","forge_source","forge_audit"}
    if set(controls)!=expected or not all(controls.values()):
        return {"status":"STOP_AUDIT_CONTROLS","violations":["frozen corruption controls incomplete or accepted"]}
    arms=summary["arms"]
    meta=arms["metadata_only"]; proper=arms["proper_score_random_audit"]; adversarial=arms["adversarial_audit"]
    gates={
      "overclaim_reduction": meta["responsive_overclaim_rate"]-proper["responsive_overclaim_rate"] >= .15-1e-12,
      "responsive_brier_not_worse": proper["responsive_brier"] <= meta["responsive_brier"]+1e-12,
      "false_pass_increase_bounded": proper["false_pass_rate"] <= meta["false_pass_rate"]+.01+1e-12,
      "valid_unknown_decrease_bounded": proper["valid_unknown_rate"] >= meta["valid_unknown_rate"]-.02-1e-12,
      "random_audit_cost_bounded": proper["mean_audits_per_agent"] <= .25+1e-12,
      "false_independence_detection": adversarial["false_independence_detection_rate"] >= .30-1e-12,
    }
    return {"status":"PASS" if all(gates.values()) else "FAIL","gates":gates,
      "observed":{
       "overclaim_reduction":meta["responsive_overclaim_rate"]-proper["responsive_overclaim_rate"],
       "responsive_brier_delta":proper["responsive_brier"]-meta["responsive_brier"],
       "false_pass_delta":proper["false_pass_rate"]-meta["false_pass_rate"],
       "valid_unknown_delta":proper["valid_unknown_rate"]-meta["valid_unknown_rate"],
       "mean_audits_per_agent":proper["mean_audits_per_agent"],
       "false_independence_detection_rate":adversarial["false_independence_detection_rate"]},
      "scope":"synthetic one-shot simulator only; advisory mechanism signals, no model/runtime/authority claim"}

def main():
    p=argparse.ArgumentParser(); p.add_argument("summary",type=Path); p.add_argument("audit",type=Path); p.add_argument("--output",type=Path,required=True); a=p.parse_args()
    s=json.loads(a.summary.read_text(encoding="utf-8")); au=json.loads(a.audit.read_text(encoding="utf-8"))
    r=evaluate(s,au); a.output.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n",encoding="utf-8"); print(json.dumps(r,sort_keys=True))
if __name__=="__main__": main()
