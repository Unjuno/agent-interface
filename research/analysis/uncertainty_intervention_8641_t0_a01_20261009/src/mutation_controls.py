#!/usr/bin/env python3
"""Construction-only rejection checks against retained candidate rows."""
import copy, json, pathlib, subprocess, sys, tempfile
Q,F,O,R=map(lambda x:json.loads(pathlib.Path(x).read_text()),sys.argv[1:5])
mutations={}
for name in ("label","dependence","epoch","cost"):
    bad=copy.deepcopy(R)
    if name=="label":
        case=next(x for x in F["cases"] if x["case_id"]=="ontology_uncertainty")
        case["source_cues"]["EPISTEMIC"]=0.05;case["source_cues"]["ALEATORIC"]=0.95
    elif name=="dependence":
        case=next(x for x in F["cases"] if x["case_id"]=="correlated_duplicate")
        case["dependency_warning"]=False
    elif name=="epoch":
        case=next(x for x in F["cases"] if x["case_id"]=="stale_epoch")
        case["source_cues"]["DYNAMIC"]=0.04;case["source_cues"]["ALEATORIC"]=0.96
    else:
        row=bad["rows"][0];row["reported_cost"]+=0.01
    with tempfile.TemporaryDirectory(prefix="8641-mutation-") as d:
        raw=pathlib.Path(d)/"mutated.json";out=pathlib.Path(d)/"audit.json"
        raw.write_text(json.dumps(bad))
        changed_fixture=pathlib.Path(d)/"fixture.json";changed_fixture.write_text(json.dumps(F))
        proc=subprocess.run([sys.executable,"src/auditor.py",sys.argv[1],str(changed_fixture),sys.argv[3],str(raw),str(out)],capture_output=True,text=True)
        mutations[name]={"rejected":proc.returncode!=0,"exit_code":proc.returncode}
summary={"controls":mutations,"detected":sum(x["rejected"] for x in mutations.values()),"total":len(mutations)}
print(json.dumps(summary,sort_keys=True))
if summary["detected"]!=summary["total"]:raise SystemExit(1)
