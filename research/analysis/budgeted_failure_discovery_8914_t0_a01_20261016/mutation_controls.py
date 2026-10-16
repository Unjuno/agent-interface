#!/usr/bin/env python3
"""Run negative mutations against copied raw only; never reruns candidate."""
import copy, json, shutil, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
RAW=ROOT/"raw"
def load(name): return json.loads((RAW/name).read_text())
def save(path, value): path.write_text(json.dumps(value,sort_keys=True,separators=(",",":"))+"\n")
base_shallow, base_bundle=load("shallow-input.json"),load("candidate-output.json")
mutations={}
# A concealed deep outcome in the candidate input must violate the frozen schema.
s=copy.deepcopy(base_shallow); s["worlds"]["signal"]["eligible"][0]["deep_failure"]=True
b=copy.deepcopy(base_bundle)
mutations["deep_outcome_leak"]=(s,b,True)
# A duplicated repeat identity must fail the denominator or uniqueness audit.
s=copy.deepcopy(base_shallow); b=copy.deepcopy(base_bundle); b["attempts"].append(copy.deepcopy(b["attempts"][0]))
mutations["duplicate_repeat"]=(s,b,False)
# Reset custody mismatch is not an eligible sample.
s=copy.deepcopy(base_shallow); b=copy.deepcopy(base_bundle); b["attempts"][0]["reset_hash"]="0"*64
mutations["reset_mismatch"]=(s,b,False)
# Same cell/repeat reused under another attempt identity is a repeat-dependence fault.
s=copy.deepcopy(base_shallow); b=copy.deepcopy(base_bundle); b["attempts"][1]["sample_key"]=b["attempts"][0]["sample_key"]
mutations["repeat_dependence"]=(s,b,False)
# Scores must be exactly reconstructible from training shallow outcomes.
s=copy.deepcopy(base_shallow); b=copy.deepcopy(base_bundle); b["scores"]["signal"]["scores"][next(iter(b["scores"]["signal"]["scores"]))]["feature"] += .01
mutations["score_leakage"]=(s,b,False)
results={}
for name,(shallow,bundle,repair_hash) in mutations.items():
    with tempfile.TemporaryDirectory(prefix="8914-audit-mutation-") as td:
        d=Path(td)
        shutil.copy2(RAW/"shallow-input.json",d/"shallow-input.json")
        save(d/"shallow-input.json",shallow)
        if repair_hash:
            bundle["shallow_input_sha256"]=__import__("hashlib").sha256((d/"shallow-input.json").read_bytes()).hexdigest()
        save(d/"candidate-output.json",bundle)
        p=subprocess.run([sys.executable,str(ROOT/"audit_raw.py"),str(d)],capture_output=True,text=True)
        results[name]={"rejected":p.returncode!=0,"exit":p.returncode,"output":p.stdout.strip()[:300]}
if not all(v["rejected"] for v in results.values()):
    print(json.dumps({"status":"FAIL_MUTATION_CONTROLS","results":results},sort_keys=True)); raise SystemExit(1)
print(json.dumps({"status":"PASS_MUTATION_CONTROLS_SCOPED","count":len(results),"results":results},sort_keys=True))
