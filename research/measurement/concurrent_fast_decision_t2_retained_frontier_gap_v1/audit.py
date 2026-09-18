import base64, hashlib, json, math
from fractions import Fraction
from pathlib import Path

ROOT=Path(__file__).resolve().parent
DEADLINE_NS=12_000_000
T1_MAX_NS=2_692_318

def blob(raw):
    return hashlib.sha1(f"blob {len(raw)}\0".encode()+raw).hexdigest()

def q7(xs,p):
    xs=sorted(xs); h=Fraction(len(xs)-1)*p; lo=h.numerator//h.denominator; hi=math.ceil(h)
    if lo==hi: return Fraction(xs[lo])
    return Fraction(xs[lo])*(1-(h-lo))+Fraction(xs[hi])*(h-lo)

def fj(x): return {"num":x.numerator,"den":x.denominator}
def sm(xs):
    xs=sorted(xs)
    return {"min_ns":fj(Fraction(xs[0])),"median_ns":fj(q7(xs,Fraction(1,2))),"p95_ns":fj(q7(xs,Fraction(95,100))),"max_ns":fj(Fraction(xs[-1]))}
def ratios(s): return {k.replace("_ns","_over_t1_max"):fj(Fraction(v["num"],v["den"])/T1_MAX_NS) for k,v in s.items()}

f=json.loads((ROOT/"FROZEN_RECORDS.json").read_text())
r=json.loads((ROOT/"RESULT.json").read_text())
fail=[]; rows=[]
for item in f["records"]:
    raw=base64.b64decode(item["raw_content_b64"],validate=True)
    if blob(raw)!=item["blob_sha1"]: fail.append(f"blob:{item['run']}")
    d=json.loads(raw)
    rows.append({"run":item["run"],"d":d,"a":d["exited_ns"]-d["started_ns"],"s":d["exited_ns"]-d["stdin_closed_ns"]})
if len(rows)!=10: fail.append("row_count")
if not all(x["d"]["exit_code"]==0 for x in rows): fail.append("exit")
if not all(x["d"].get("requested_model")=="gpt-6-astra" for x in rows): fail.append("model")
if not all(x["d"].get("requested_effort")=="medium" for x in rows): fail.append("effort")
if not all(x["d"].get("observed_model_identity") is None for x in rows): fail.append("identity")
if not all(x["s"]>DEADLINE_NS for x in rows): fail.append("deadline")
A=sm([x["a"] for x in rows]); S=sm([x["s"] for x in rows])
if A!=r["started_to_exit"]: fail.append("started_summary")
if S!=r["stdin_closed_to_exit"]: fail.append("strict_summary")
if ratios(A)!=r["started_to_exit_ratios"]: fail.append("started_ratios")
if ratios(S)!=r["stdin_closed_to_exit_ratios"]: fail.append("strict_ratios")
for x, rr in zip(rows,r["rows"]):
    if x["run"]!=rr["run"] or x["a"]!=rr["started_to_exit_ns"] or x["s"]!=rr["stdin_closed_to_exit_ns"]: fail.append(f"row:{x['run']}")
expected="PASS_RETAINED_FRONTIER_GAP_ELIGIBLE_SCOPED" if not fail else "FAIL_INTEGRITY"
if r["disposition"]!=expected: fail.append("disposition")
a={"format":"retained-frontier-gap-audit-v1","pass":not fail,"failures":fail,"recomputed_disposition":expected,"started_to_exit":A,"stdin_closed_to_exit":S,"source_integrity":not any(x.startswith("blob:") for x in fail)}
(ROOT/"AUDIT.json").write_text(json.dumps(a,indent=2,sort_keys=True)+"\n")
print("AUDIT_PASS" if not fail else "AUDIT_FAIL")
