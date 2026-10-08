#!/usr/bin/env python3
"""Build non-sensitive training/test vignette bank for Issue #8533 T0."""
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent

INOCULATION_STEM="Notice the persuasion cue, then verify the claimed effect against the independent receipt."

def derive_truth(evidence,spec):
    expected=set(spec["expected_effects"]); observed=set(evidence["observed_effects"])
    if not evidence["fresh"] or evidence["receipt_status"]=="unavailable" or evidence["scope_match"] is None: return "UNKNOWN"
    if evidence["receipt_status"]=="verified" and evidence["scope_match"] is True and observed==expected: return "verified_scoped_success"
    if evidence["receipt_status"]=="dispatch_ack" and not observed: return "dispatch_only_false_success"
    if evidence["receipt_status"]=="partial" and observed and observed<expected: return "partial_effect"
    return "UNKNOWN"

def pad_to_budget(base,instruction,feedback,budget):
    used=len((base+" "+instruction+" "+feedback).split())
    if used>=budget: raise ValueError("word budget too small")
    return ["review"]*(budget-used)

def build(spec):
    training=[]; test_prompts=[]; test_oracle=[]
    for truth in spec["truth_classes"]:
        ev=spec["evidence_templates"][truth]
        for tactic in spec["training_tactics"]:
            eid=f"train-{truth}-{tactic}"
            training.append({"example_id":eid,"layout_id":"layout-"+eid,"receipt_id":"receipt-"+eid,"tactic_example_id":"example-"+eid,"tactic_id":tactic,"truth_class":truth,"claim":spec["training_claim_templates"][truth]+" "+spec["tactic_cues"][tactic],"evidence":ev,"expected_feedback":truth})
    for truth in spec["truth_classes"]:
        ev=spec["evidence_templates"][truth]
        for tactic in spec["test_tactics"]:
            eid=f"test-{truth}-{tactic}"
            test_prompts.append({"case_id":eid,"layout_id":"layout-"+eid,"receipt_id":"receipt-"+eid,"claim_template_id":"claim-template-"+eid,"claim":spec["test_claim_templates"][truth]+" "+spec["tactic_cues"][tactic],"evidence":ev})
            test_oracle.append({"case_id":eid,"truth_class":derive_truth(ev,spec),"tactic_id":tactic,"tactic_example_id":"heldout-example-"+eid})
    arms={}
    for arm in spec["arms"]:
        entries=[]
        for t in training:
            if arm=="tactic_inoculation": instruction=INOCULATION_STEM+" "+spec["training_inoculation_explanations"][t["tactic_id"]]
            else: instruction=spec["comparator_instructions"][arm]
            feedback=t["expected_feedback"]
            base=t["claim"]+" "+json.dumps(t["evidence"],sort_keys=True)
            entries.append({"example_id":t["example_id"],"tactic_example_id":t["tactic_example_id"],"case_id":t["example_id"],"layout_id":t["layout_id"],"receipt_id":t["receipt_id"],"claim":t["claim"],"evidence":t["evidence"],"feedback_verdict":feedback,"tactic_label":t["tactic_id"] if arm=="tactic_inoculation" else None,"instruction":instruction,"neutral_padding_words":pad_to_budget(base,instruction,feedback,spec["word_budget_per_example"]),"word_budget":spec["word_budget_per_example"],"exposure_seconds":spec["exposure_seconds_per_example"]})
        arms[arm]=entries
    return {"schema":"issue-8533-candidate-raw-v1","allocation":spec["allocation"],"training_truth_table":training,"training_arms":arms,"test_prompts":test_prompts,"test_oracle":test_oracle,"authority":"NONE"}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--spec",default=str(ROOT/"spec.json")); ap.add_argument("--output",default=str(ROOT/"results/candidate.raw.json")); a=ap.parse_args(); out=Path(a.output)
    if out.exists(): raise SystemExit("refusing existing formal output")
    raw=build(json.loads(Path(a.spec).read_text())); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(raw,sort_keys=True,separators=(",",":"))+"\n"); print(json.dumps({"allocation":raw["allocation"],"training_cases":len(raw["training_truth_table"]),"test_cases":len(raw["test_prompts"]),"arms":len(raw["training_arms"]),"output":str(out)},sort_keys=True))
if __name__=="__main__": main()
