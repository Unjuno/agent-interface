"""Separate raw-only replay; imports no candidate implementation."""
from __future__ import annotations
import copy, hashlib, json
from pathlib import Path

def replay(stream: dict, raw: bytes) -> dict:
    intake_ids=[]; screen_counts={}; started=[]; eligible=[]; checks=[]
    for entry in stream["rows"]:
        category=entry["kind"]
        if category=="intake":
            intake_ids.append(entry["id"]); label=entry["screen"]; screen_counts[label]=screen_counts.get(label,0)+1
        elif category=="test" and entry.get("test_started") is True:
            record={"id":entry["id"],"claim_id":entry["claim_id"],"outcome":entry["outcome"],"abandoned_after_interim":entry["abandoned_after_interim"],"statistical_eligible":entry["statistical_eligible"]}
            started.append(record)
            if entry.get("statistical_eligible") is True:
                eligible.append({"id":entry["id"],"claim_id":entry["claim_id"],"p_value":entry["p_value"]})
        elif category=="deterministic":
            checks.append({"id":entry["id"],"outcome":entry["outcome"],"hard_safety":entry["hard_safety"]})
        else: raise ValueError("unrecognized record or unstarted test")
    return {"schema":"portfolio-intake-ledger-v1","fixture_id":stream["fixture_id"],"input_sha256":hashlib.sha256(raw).hexdigest(),"intake":{"count":len(intake_ids),"screen_counts":dict(sorted(screen_counts.items())),"ids":intake_ids},"started_opportunities":started,"statistical_family":eligible,"deterministic":checks,"counts":{"all_rows":len(stream["rows"]),"screened_out_not_tested":len(intake_ids),"started_test_opportunities":len(started),"statistical_family_size":len(eligible),"deterministic_rows":len(checks),"started_negative_abandoned":sum(1 for x in started if x["outcome"]=="TEST_STARTED_FAIL" and x["abandoned_after_interim"] is True)}}

def mutations_rejected(gold: dict) -> dict[str,bool]:
    bad={}
    x=copy.deepcopy(gold); x["intake"]["ids"].pop(); bad["omit_intake_row"]=x
    x=copy.deepcopy(gold); x["started_opportunities"]=[r for r in x["started_opportunities"] if r["id"]!="claim-neg-abandoned"]; x["counts"]["started_test_opportunities"]-=1; x["counts"]["started_negative_abandoned"]-=1; bad["reclassify_started_negative_as_untested"]=x
    x=copy.deepcopy(gold); x["started_opportunities"]=[r for r in x["started_opportunities"] if r["outcome"]!="TEST_STARTED_STOP"]; x["counts"]["started_test_opportunities"]-=1; bad["omit_started_stop"]=x
    x=copy.deepcopy(gold); x["deterministic"][0]["invented_p_value"]=0.000001; bad["invent_method_p_value"]=x
    x=copy.deepcopy(gold); x["deterministic"]=[r for r in x["deterministic"] if r["outcome"]!="HARD_SAFETY_FAIL"]; x["counts"]["deterministic_rows"]-=1; bad["remove_hard_safety_failure"]=x
    return {name: corrupted!=gold for name,corrupted in bad.items()}

def main() -> None:
    root=Path(__file__).resolve().parent; raw=(root/"formal_input.json").read_bytes(); stream=json.loads(raw)
    candidate_raw=(root/"candidate_raw.json").read_bytes(); got=json.loads(candidate_raw); expected=replay(stream,raw); controls=mutations_rejected(expected); exact=got==expected
    result={"schema":"portfolio-intake-independent-audit-v1","fixture_id":stream["fixture_id"],"input_sha256":hashlib.sha256(raw).hexdigest(),"candidate_sha256":hashlib.sha256(candidate_raw).hexdigest(),"rows_reconstructed":expected["counts"]["all_rows"],"exact_replay":exact,"reconstructed_counts":expected["counts"],"corruption_controls_rejected":controls,"corruptions_rejected":sum(controls.values()),"disposition":"PASS_METHOD_SCOPED" if exact and all(controls.values()) else "FAIL_AUDIT","limits":["one authored synthetic stream","no FDR/error-rate guarantee","no GUI/model/product claim"]}
    (root/"audit.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"exact_replay":exact,"corruptions_rejected":result["corruptions_rejected"],"disposition":result["disposition"]},sort_keys=True))

if __name__=="__main__": main()
