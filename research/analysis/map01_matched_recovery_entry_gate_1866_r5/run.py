#!/usr/bin/env python3
import itertools, json, pathlib, sys

FIELDS=("physical_task_effect_endpoint","task_effect_contract","matched_arm","arm_bound_audit","terminal_integrity")

def decide(row):
    return "AUTHORIZE" if all(row[k] is True for k in FIELDS) else "HOLD"

def main(out):
    here=pathlib.Path(__file__).resolve().parent
    snap=json.loads((here/"SNAPSHOT.json").read_text())
    current={k:snap["gates"][k]["ready"] for k in FIELDS}
    vectors=[]
    for bits in itertools.product((False,True), repeat=len(FIELDS)):
        row=dict(zip(FIELDS,bits)); row["decision"]=decide(row); vectors.append(row)
    controls=[
        {"name":"missing_receipt",**current,"terminal_integrity":False},
        {"name":"stale_binding",**current,"matched_arm":False},
        {"name":"unknown_endpoint",**current,"physical_task_effect_endpoint":False},
        {"name":"corrupt_recomputation",**current,"arm_bound_audit":False},
        {"name":"task_effect_contract_missing",**current,"task_effect_contract":False},
    ]
    for row in controls: row["decision"]=decide(row)
    raw={"schema":"map01-recovery-entry-gate-1866-r5","snapshot":snap,"fields":list(FIELDS),
         "current":{**current,"decision":decide(current)},"vectors":vectors,"controls":controls}
    p=pathlib.Path(out); p.mkdir(parents=True,exist_ok=False)
    (p/"raw.json").write_text(json.dumps(raw,indent=2,sort_keys=True)+"\n")
    print(f"CURRENT {raw['current']['decision']} vectors={len(vectors)} authorize={sum(v['decision']=='AUTHORIZE' for v in vectors)} controls={len(controls)}")

if __name__=="__main__": main(sys.argv[1])
