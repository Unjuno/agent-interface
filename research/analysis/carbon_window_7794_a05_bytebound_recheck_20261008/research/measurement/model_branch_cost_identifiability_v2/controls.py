#!/usr/bin/env python3
import copy, json, tempfile
from pathlib import Path
from audit import audit

HERE=Path(__file__).parent
a=json.loads((HERE/"RESULT_A.json").read_text())
b=json.loads((HERE/"RESULT_B.json").read_text())
controls=[]

def run(name,ma=None,mb=None,source_mutation=None):
    aa=copy.deepcopy(a); bb=copy.deepcopy(b)
    if ma: ma(aa)
    if mb: mb(bb)
    if source_mutation is None:
        r=audit(aa,bb,HERE)
    else:
        with tempfile.TemporaryDirectory() as td:
            dst=Path(td)
            for p in HERE.iterdir():
                if p.is_file():
                    (dst/p.name).write_bytes(p.read_bytes())
            source_mutation(dst)
            r=audit(aa,bb,dst)
    controls.append({"name":name,"rejected":not r["audit_pass"],"decision":r["decision"],"errors":r["errors"]})

run("fake_A_admissible",ma=lambda x:x.__setitem__("admissible_pair_count",1))
run("A_B_pair_disagreement",mb=lambda x:x.__setitem__("admissible_pairs",[[0,0]]))
run("causal_cost_laundering",ma=lambda x:x.__setitem__("causal_per_branch_estimate",1.0))
def corrupt_source(root):
    p=root/"INPUT_LEDGER.json"
    p.write_bytes(p.read_bytes()+b" ")
run("source_byte_mutation",source_mutation=corrupt_source)

if not all(x["rejected"] for x in controls):
    raise SystemExit("corruption control escaped")
out={"controls":controls,"rejected":sum(x["rejected"] for x in controls),"total":len(controls)}
(HERE/"CORRUPTION.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps(out,indent=2,sort_keys=True))
