#!/usr/bin/env python3
"""Independent truth, parity, and holdout auditor for Issue #8533 T0."""
import argparse,copy,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def oracle(e,spec):
    expected=set(spec["expected_effects"]); observed=set(e["observed_effects"])
    if e.get("fresh") is not True or e.get("receipt_status")=="unavailable" or e.get("scope_match") is None: return "UNKNOWN"
    if e.get("receipt_status")=="verified" and e.get("scope_match") is True and observed==expected: return "verified_scoped_success"
    if e.get("receipt_status")=="dispatch_ack" and len(observed)==0: return "dispatch_only_false_success"
    if e.get("receipt_status")=="partial" and len(observed)>0 and observed<expected: return "partial_effect"
    return "UNKNOWN"

def check(raw,spec):
    if raw.get("schema")!="issue-8533-candidate-raw-v1" or raw.get("authority")!="NONE": raise ValueError("schema/authority")
    training=raw.get("training_truth_table",[]); prompts=raw.get("test_prompts",[]); truths=raw.get("test_oracle",[]); arms=raw.get("training_arms",{})
    if len(training)!=spec["training_example_count"] or len(prompts)!=spec["test_example_count"] or len(truths)!=len(prompts): raise ValueError("assigned bank denominator")
    if set(arms)!=set(spec["arms"]): raise ValueError("training arms")
    truthset=set(spec["truth_classes"]); train_ids={r["example_id"] for r in training}; test_ids={r["case_id"] for r in prompts}
    for key,field in (("case ids","example_id"),("layout ids","layout_id"),("receipt ids","receipt_id"),("tactic examples","tactic_example_id")):
        tr={r[field] for r in training}; te={r[field] if field in r else r.get("tactic_example_id") for r in prompts}
        if key=="tactic examples": te={r["tactic_example_id"] for r in truths}
        if tr & te: raise ValueError("training/test reused "+key)
    for r in training:
        if r["truth_class"] not in truthset or r["expected_feedback"]!=oracle(r["evidence"],spec): raise ValueError("training oracle truth")
        if r["evidence"]!=spec["evidence_templates"][r["truth_class"]]: raise ValueError("training evidence does not match independent oracle template")
        if r["claim"]!=spec["training_claim_templates"][r["truth_class"]]+" "+spec["tactic_cues"][r["tactic_id"]]: raise ValueError("training claim/tactic taxonomy")
    for r in truths:
        if r["truth_class"] not in truthset: raise ValueError("unknown test class")
    truth_by_id={r["case_id"]:r for r in truths}
    prompt_by_id={r["case_id"]:r for r in prompts}
    if set(truth_by_id)!=set(prompt_by_id): raise ValueError("oracle join")
    for r in prompts:
        if any(k in r for k in ("truth_class","oracle_label","expected_feedback","tactic_id","tactic_example_id")): raise ValueError("test label leakage")
        tr=truth_by_id[r["case_id"]]
        if oracle(r["evidence"],spec)!=tr["truth_class"]: raise ValueError("test truth table mismatch")
        if r["evidence"]!=spec["evidence_templates"][tr["truth_class"]]: raise ValueError("test evidence does not match independent oracle template")
        if r["claim"]!=spec["test_claim_templates"][tr["truth_class"]]+" "+spec["tactic_cues"][tr["tactic_id"]]: raise ValueError("heldout claim/tactic taxonomy")
    expected_test={f"test-{truth}-{tactic}" for truth in spec["truth_classes"] for tactic in spec["test_tactics"]}
    if test_ids!=expected_test: raise ValueError("test factorial balance")
    if {r["tactic_id"] for r in truths}!=set(spec["test_tactics"]): raise ValueError("test tactic coverage")
    if not set(spec["test_tactics"])-set(spec["training_tactics"]): raise ValueError("no unseen tactic")
    train_by={r["example_id"]:r for r in training}
    for arm,entries in arms.items():
        if len(entries)!=len(training): raise ValueError("arm exposure count")
        ids={r["example_id"] for r in entries}
        if ids!=train_ids: raise ValueError("arm missing/duplicate example")
        for r in entries:
            base=train_by[r["example_id"]]
            for field in ("case_id","layout_id","receipt_id","claim","evidence","feedback_verdict"):
                expected=base["expected_feedback"] if field=="feedback_verdict" else base["example_id"] if field=="case_id" else base[field]
                if r[field]!=expected: raise ValueError("factual access parity")
            if r["word_budget"]!=spec["word_budget_per_example"] or r["exposure_seconds"]!=spec["exposure_seconds_per_example"]: raise ValueError("time/content parity metadata")
            shared=(r["claim"]+" "+json.dumps(r["evidence"],sort_keys=True)+" "+r["instruction"]+" "+r["feedback_verdict"]).split()
            if len(shared)+len(r["neutral_padding_words"])!=r["word_budget"]: raise ValueError("word budget mismatch")
            if arm=="tactic_inoculation":
                if r["tactic_label"]!=base["tactic_id"] or r["instruction"]!="Notice the persuasion cue, then verify the claimed effect against the independent receipt. "+spec["training_inoculation_explanations"][base["tactic_id"]]: raise ValueError("inoculation treatment content")
            elif r["tactic_label"] is not None or r["instruction"]!=spec["comparator_instructions"][arm]: raise ValueError("comparator treatment content")
    # Both accurate high-salience success claims and misleading high-salience claims must be present.
    truth_ids={r["case_id"]:r["truth_class"] for r in truths}
    if not any(t=="verified_scoped_success" for t in truth_ids.values()): raise ValueError("legitimate success control absent")
    if not all(any(truth_ids[r["case_id"]]==t for r in prompts) for t in ("dispatch_only_false_success","partial_effect","UNKNOWN")): raise ValueError("misleading/uncertain controls absent")
    return {"training_examples":len(training),"test_examples":len(prompts),"training_arms":len(arms),"truth_classes":len(truthset),"unseen_tactics":sorted(set(spec["test_tactics"])-set(spec["training_tactics"])),"checks":len(training)+len(prompts)+len(truths)+sum(map(len,arms.values()))+14,"errors":0}

def mutation_rejected(raw,spec,kind):
    x=copy.deepcopy(raw)
    if kind=="swap_test_truth": x["test_oracle"][0]["truth_class"]="UNKNOWN" if x["test_oracle"][0]["truth_class"]!="UNKNOWN" else "verified_scoped_success"
    elif kind=="hide_evidence": x["training_arms"]["evidence_first"][0]["evidence"]["observed_effects"]=[]
    elif kind=="leak_layout": x["test_prompts"][0]["layout_id"]=x["training_truth_table"][0]["layout_id"]
    elif kind=="unknown_as_success":
        r=next(r for r in x["test_oracle"] if r["truth_class"]=="UNKNOWN"); r["truth_class"]="verified_scoped_success"
    elif kind=="unequal_exposure": x["training_arms"]["neutral_control"][0]["exposure_seconds"]+=1
    elif kind=="oracle_leak": x["test_prompts"][0]["truth_class"]=x["test_oracle"][0]["truth_class"]
    elif kind=="authority": x["authority"]="APPROVED_HUMAN_TRAINING"
    else: raise ValueError("unknown mutation")
    try: check(x,spec)
    except (ValueError,KeyError,TypeError): return True
    return False

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--spec",default=str(ROOT/"spec.json")); ap.add_argument("--raw",default=str(ROOT/"results/candidate.raw.json")); ap.add_argument("--output",default=str(ROOT/"results/audit.raw.json")); a=ap.parse_args(); out=Path(a.output)
    if out.exists(): raise SystemExit("refusing existing formal output")
    spec=json.loads(Path(a.spec).read_text()); raw_bytes=Path(a.raw).read_bytes(); raw=json.loads(raw_bytes); summary=check(raw,spec)
    controls={m:mutation_rejected(raw,spec,m) for m in ("swap_test_truth","hide_evidence","leak_layout","unknown_as_success","unequal_exposure","oracle_leak","authority")}
    if not all(controls.values()): raise ValueError("mutation control accepted")
    summary.update({"allocation":spec["allocation"],"disposition":"METHOD_PASS_SCOPED","mutation_controls":controls,"mutation_rejections":f"{sum(controls.values())}/{len(controls)}","candidate_raw_sha256":hashlib.sha256(raw_bytes).hexdigest(),"authority":"NONE"})
    out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(summary,sort_keys=True,separators=(",",":"))+"\n"); print(json.dumps(summary,sort_keys=True))
if __name__=="__main__": main()
