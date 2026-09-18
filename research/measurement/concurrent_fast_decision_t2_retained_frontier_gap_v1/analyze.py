import base64, hashlib, json, math
from fractions import Fraction
from pathlib import Path

ROOT=Path(__file__).resolve().parent
DEADLINE_NS=12_000_000
T1_MAX_NS=2_692_318
EXPECTED_MODEL="gpt-6-astra"
EXPECTED_EFFORT="medium"

def git_blob_sha1(raw: bytes) -> str:
    return hashlib.sha1(f"blob {len(raw)}\0".encode("ascii")+raw).hexdigest()

def type7(values, p: Fraction) -> Fraction:
    xs=sorted(values)
    if not xs:
        raise ValueError("empty sample")
    h=Fraction(len(xs)-1)*p
    lo=h.numerator//h.denominator
    hi=math.ceil(h)
    if lo==hi:
        return Fraction(xs[lo])
    w=h-lo
    return Fraction(xs[lo])*(1-w)+Fraction(xs[hi])*w

def summary(values):
    xs=sorted(values)
    return {
        "min_ns":{"num":xs[0],"den":1},
        "median_ns":frac_json(type7(xs,Fraction(1,2))),
        "p95_ns":frac_json(type7(xs,Fraction(95,100))),
        "max_ns":{"num":xs[-1],"den":1},
    }

def frac_json(x: Fraction):
    return {"num":x.numerator,"den":x.denominator}

def ratio_summary(s):
    return {k.replace("_ns","_over_t1_max"):frac_json(Fraction(v["num"],v["den"])/T1_MAX_NS) for k,v in s.items()}

frozen=json.loads((ROOT/"FROZEN_RECORDS.json").read_text(encoding="utf-8"))
rows=[]
errors=[]
for item in frozen["records"]:
    try:
        raw=base64.b64decode(item["raw_content_b64"],validate=True)
        actual_sha=git_blob_sha1(raw)
        if actual_sha!=item["blob_sha1"]:
            errors.append(f"blob_sha_mismatch:{item['run']}:{actual_sha}")
        record=json.loads(raw)
        started=int(record["started_ns"]); closed=int(record["stdin_closed_ns"]); exited=int(record["exited_ns"])
        row={
            "run":item["run"],"path":item["path"],"blob_sha1":item["blob_sha1"],
            "exit_code":record.get("exit_code"),"requested_model":record.get("requested_model"),
            "requested_effort":record.get("requested_effort"),"observed_model_identity":record.get("observed_model_identity"),
            "cost":record.get("cost"),"started_ns":started,"stdin_closed_ns":closed,"exited_ns":exited,
            "started_to_exit_ns":exited-started,"stdin_closed_to_exit_ns":exited-closed,
        }
        rows.append(row)
    except Exception as exc:
        errors.append(f"parse:{item.get('run')}:{type(exc).__name__}:{exc}")

start_vals=[r["started_to_exit_ns"] for r in rows]
strict_vals=[r["stdin_closed_to_exit_ns"] for r in rows]
start_summary=summary(start_vals) if rows else None
strict_summary=summary(strict_vals) if rows else None
checks={
    "records_10_of_10":len(rows)==10 and len(errors)==0,
    "exit_code_zero_10_of_10":len(rows)==10 and all(r["exit_code"]==0 for r in rows),
    "requested_model_exact_10_of_10":len(rows)==10 and all(r["requested_model"]==EXPECTED_MODEL for r in rows),
    "requested_effort_exact_10_of_10":len(rows)==10 and all(r["requested_effort"]==EXPECTED_EFFORT for r in rows),
    "all_strict_intervals_gt_12ms":len(rows)==10 and all(r["stdin_closed_to_exit_ns"]>DEADLINE_NS for r in rows),
    "t1_max_effect_lt_12ms":T1_MAX_NS<DEADLINE_NS,
    "observed_identity_null_10_of_10":len(rows)==10 and all(r["observed_model_identity"] is None for r in rows),
}
if errors:
    disposition="FAIL_INTEGRITY"
elif not checks["all_strict_intervals_gt_12ms"]:
    disposition="HOLD_RETAINED_SAMPLE_HAS_NO_GAP"
elif all(checks.values()):
    disposition="PASS_RETAINED_FRONTIER_GAP_ELIGIBLE_SCOPED"
else:
    disposition="FAIL_INTEGRITY"
result={
    "format":"retained-frontier-gap-analysis-v1","issue":1451,"base_ref":frozen["git_ref"],
    "deadline_ns":DEADLINE_NS,"t1_max_effect_ns":T1_MAX_NS,"rows":rows,"errors":errors,
    "started_to_exit":start_summary,"stdin_closed_to_exit":strict_summary,
    "started_to_exit_ratios":ratio_summary(start_summary) if start_summary else None,
    "stdin_closed_to_exit_ratios":ratio_summary(strict_summary) if strict_summary else None,
    "checks":checks,"disposition":disposition,
    "scope_note":"Requested Astra route / real model subprocess interval only; observed_model_identity is null and served-model identity is not independently verified.",
}
(ROOT/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(disposition)
