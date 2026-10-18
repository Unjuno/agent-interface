#!/usr/bin/env python3
"""Independent audit applying the frozen A15 plan without extra thresholds."""
import hashlib, importlib.util, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent
M = json.loads((ROOT / "manifest.json").read_text())

def require(ok, why):
    if not ok: raise ValueError(why)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def point(p, b):
    return type(p) is list and len(p)==2 and all(type(x) is int for x in p) and b[0]<=p[0]<=b[2] and b[1]<=p[1]<=b[3]
def compiler():
    s=ROOT/"sources"; t=s/"tree"
    sys.path[:0]=[str(s/"r02"),str(t/"research/live_control"),str(t)]
    spec=importlib.util.spec_from_file_location("a15_candidate_v1",s/"candidate.py")
    c=importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
    import planner_contract_schema as b
    return c,b

def main():
    for name,digest in M["frozen_files"].items(): require(sha(ROOT/name)==digest,"frozen source changed: "+name)
    for name,row in M["sources"].items(): require(sha(ROOT/row["file"])==row["sha256"],"source hash mismatch: "+name)
    for name,row in M["inputs"].items(): require(sha(ROOT/row["file"])==row["sha256"],"input hash mismatch: "+name)
    cases={}; usage={"input_tokens":0,"cached_input_tokens":0,"cache_write_input_tokens":0,"output_tokens":0,"reasoning_output_tokens":0}
    for case in M["case_order"]:
        d=ROOT/"outputs"/case
        start=json.loads((d/"CALL_STARTED.json").read_text()); done=json.loads((d/"CALL_RESULT.json").read_text())
        require(start["attempt"]==1 and start["case"]==case,"attempt identity mismatch: "+case)
        require(done["returncode"]==0 and done["timed_out"] is False and done["answer_present"] is True,"call incomplete: "+case)
        raw=(d/"answer.json").read_bytes(); ans=json.loads(raw)
        require(hashlib.sha256(raw).hexdigest()==done["answer_sha256"],"answer hash mismatch: "+case)
        require(set(ans)=={"grounding_status","reason","field_point","submit_point","value_crop","contract"},"unexpected output fields: "+case)
        events=[json.loads(x) for x in (d/"stdout.jsonl").read_text().splitlines() if x.strip()]
        finished=[e for e in events if e.get("type")=="turn.completed"]
        require(len(finished)==1,"not exactly one completed model turn: "+case)
        items=[e.get("item",{}) for e in events if e.get("type")=="item.completed"]
        require(len(items)==1 and items[0].get("type")=="agent_message","non-message item/tool activity present: "+case)
        use=finished[0].get("usage",{})
        for k in usage:
            require(type(use.get(k)) is int,"usage missing or invalid: "+case+"/"+k)
            usage[k]+=use[k]
        if case=="transition_053":
            require(ans["grounding_status"]=="ABSTAIN" and ans["reason"]=="targets_not_visible","transition frame not safely refused")
            require(all(ans[k] is None for k in ("field_point","submit_point","value_crop","contract")),"abstention includes target data")
            cases[case]={"status":"ABSTAIN","reason":ans["reason"],"target_data_null":True,"usage":use}
        else:
            require(ans["grounding_status"]=="READY" and ans["reason"]=="none","ready frame was not admitted")
            r=M["positive_regions_xyxy"]
            require(point(ans["field_point"],r["field"]),"field point outside visible field")
            require(point(ans["submit_point"],r["submit"]),"submit point outside visible button")
            require(ans["field_point"][0]>120,"field point is not to the right of the visible caret")
            crop=ans["value_crop"]
            require(type(crop) is list and len(crop)==4 and all(type(x) is int for x in crop),"invalid value crop")
            require(r["text_interior"][0]<=crop[0]<crop[2]<=r["field"][2] and
                    r["field"][1]<=crop[1]<crop[3]<=r["text_interior"][3] and
                    crop[2]-crop[0]>=160 and crop[3]-crop[1]>=10,"crop outside or too small for editable field")
            c,b=compiler(); compiled=c.compile_contract_v2(ans["contract"],M["aliases"],"a15-task3",compile_contract=b.compile_contract)
            acts=compiled["actions"]; branches=[br for st in compiled["method"]["states"].values() for br in st["branches"]]
            action_br=[br for br in branches if br["outcome"]=="action"]
            require(len(action_br)==2 and all(br["when"].get("target_valid") is True for br in action_br),"fresh target guards missing")
            require(all("target_valid" not in act["expected_effect"] for act in acts.values()),"transient target postcondition")
            submit=[br for br in action_br if acts[br["action"]]["operation"]=="submit_form"]
            require(len(submit)==1 and submit[0]["when"].get("exact_token_visible") is True,"submit lacks exact-token precondition")
            require(any(br["outcome"]=="complete" and br["when"].get("exact_saved_title") is True for br in branches),"completion lacks exact saved-title evidence")
            cases[case]={"status":"READY","field_point":ans["field_point"],"submit_point":ans["submit_point"],"value_crop":crop,"compiler":"A12 lifecycle guard + frozen R02 compiler accepted","lifecycle_guards_valid":True,"usage":use}
    return {"schema":"a15_transition_abstention_audit_v2","disposition":"PASS_SELECTIVE_ABSTENTION_CONSTRUCTION_SCOPED","cases":cases,"usage_totals":usage,"raw_output_paths":{case:{"answer":f"outputs/{case}/answer.json","stdout_jsonl":f"outputs/{case}/stdout.jsonl","stderr":f"outputs/{case}/stderr.txt","argv":f"outputs/{case}/argv.json","call_started":f"outputs/{case}/CALL_STARTED.json","call_result":f"outputs/{case}/CALL_RESULT.json"} for case in M["case_order"]},"a14_visual_review_correction":{"source_path":"A14_TASK3_VISUAL_REVIEW.md","exact_image_sha256":M["inputs"]["ready_054"]["sha256"],"finding":"The exact pinned frame contains Value and Save controls; its recorded model points target them. The adjacent sequence 053 is the no-current-target transition frame."},"historical_result_changed":False,"formal_allocation_or_gui_input":False,"efficiency_or_transfer_claimed":False,"audit_note":"The first frozen audit helper rejected field x=130 using an extra x>=220 right-half predicate absent from PLAN.md and PROMPT.txt. This second audit applies the preregistered field-region and right-of-caret requirements; the original failure is preserved as AUDIT_INITIAL.json."}
if __name__=="__main__":
    try: print(json.dumps(main(),indent=2,sort_keys=True))
    except Exception as exc:
        print(json.dumps({"schema":"a15_transition_abstention_audit_v2","disposition":"FAIL_OR_INCOMPLETE","error":f"{type(exc).__name__}: {exc}"},indent=2),file=sys.stderr); raise SystemExit(1)
