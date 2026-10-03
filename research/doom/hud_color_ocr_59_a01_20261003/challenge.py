"""Saved-only eight effective evidence mutations; no producer/engine replay."""
import argparse
import copy
import json
from pathlib import Path
from auditor import audit

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT.parents[2]/"research/doom/results/map01-v39-coast-liveness-live-01/runtime"
parser=argparse.ArgumentParser(); parser.add_argument("phase",choices=["pilot","evaluation"]); args=parser.parse_args()
raw=json.loads((ROOT/f"runs/{args.phase}_candidate/raw.json").read_text())
truth=json.loads((ROOT/"TRUTH.json").read_text())
original=audit(raw,truth,args.phase,ROOT/f"input/{args.phase}",SOURCE)
cases=[]
for name in ("duplicate_id","normalized_digits","reference_health","crop_hash","negative_duration","missing_prediction","memory_bound","missing_source_row"):
    candidate=copy.deepcopy(raw); labels=copy.deepcopy(truth)
    row=candidate["rows"][0]; method=candidate["transforms"][0]
    if name=="duplicate_id": candidate["rows"][1]["id"]=row["id"]
    elif name=="normalized_digits": row["predictions"][method]["digits"]+="0"
    elif name=="reference_health": labels["phases"][args.phase][0]["reference_health"]+=1
    elif name=="crop_hash": row["crop_sha256"]="0"*64
    elif name=="negative_duration": row["predictions"][method]["elapsed_ns"]=-1
    elif name=="missing_prediction": del row["predictions"][method]
    elif name=="memory_bound": candidate["cgroup"]["memory.max"]="max"
    else: labels["phases"][args.phase].pop()
    try: audit(candidate,labels,args.phase,ROOT/f"input/{args.phase}",SOURCE)
    except ValueError as error: cases.append({"case":name,"rejected":True,"reason":str(error)})
    else: cases.append({"case":name,"rejected":False})
result={"status":"PASS_8_SAVED_MUTATIONS" if all(row["rejected"] for row in cases) else "FAIL_MUTATION_ACCEPTED","original":original,"cases":cases}
with (ROOT/f"CHALLENGE_{args.phase}.json").open("x") as output: json.dump(result,output,indent=2); output.write("\n")
print(json.dumps(result))
if result["status"].startswith("FAIL"): raise SystemExit(1)
