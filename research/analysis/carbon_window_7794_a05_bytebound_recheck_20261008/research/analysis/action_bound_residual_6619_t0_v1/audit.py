"""Raw-only independent accounting auditor for Issue #6619 synthetic traces."""
import json
import sys
from pathlib import Path


def grid(w, h, val=0):
    return [[val] * w for _ in range(h)]


def place(img, x, y, val):
    if 0 <= y < len(img) and 0 <= x < len(img[0]):
        img[y][x] = val


def shift(frame, amount):
    out = grid(len(frame[0]), len(frame))
    for y, row in enumerate(frame):
        for x, val in enumerate(row):
            place(out, x + amount, y, val)
    return out


def expected_frames(case):
    w, h = 32, 24
    base = grid(w, h)
    for yy in range(h):
        for xx in range(w):
            if (xx + 3 * yy) % 11 == 0:
                base[yy][xx] = 20
    dx = {"exact":2,"under":1,"over":3,"delayed":0,"failed":0,"none":0}[case["delivery"]]
    moved = shift(base, dx)
    kind = case["event"]
    if kind in ("flash", "critical"):
        place(moved,16,12,255 if kind=="flash" else 240)
    elif kind == "external-scroll":
        place(moved,7,4,180)
    elif kind in ("object","parallax-critical","nonrigid"):
        px={"object":10,"parallax-critical":12,"nonrigid":20}[kind]
        value=250 if kind=="parallax-critical" else 90
        place(moved,px,8,value)
        if kind=="nonrigid": place(moved,px+1,8,value)
    return [base,moved]


def event_visible(case, frames):
    if case["event"] == "none" or case["event"] == "occluded-critical":
        return False, None
    if case["event"] in ("flash","critical"):
        p=(12,16)
    elif case["event"] == "external-scroll": p=(4,7)
    else:
        x={"object":10,"parallax-critical":12,"nonrigid":20}[case["event"]]
        p=(8,x)
    return frames[1][p[0]][p[1]] != frames[0][p[0]][p[1]], p


def selected(mask, y, x):
    return bool(mask[y][x])


def verify(fixture, raw):
    errs=[]; reconstructed=[]; metrics={}
    if raw.get("schema")!="action-bound-residual-raw-v1" or raw.get("fixture_schema")!=fixture.get("schema"):
        errs.append("schema")
    if len(raw.get("rows",[]))!=len(fixture["cases"]): errs.append("denominator")
    for case,row in zip(fixture["cases"],raw.get("rows",[])):
        frames=expected_frames(case)
        valid=case["generation"]==1 and case["delivery"] in ("exact","under","over")
        actual_dx={"exact":2,"under":1,"over":3,"delayed":0,"failed":0,"none":0}[case["delivery"]]
        receipt={"requested":"pan" if case["delivery"]!="none" else "none","delivery":case["delivery"],"actual_dx":actual_dx,
                 "source_generation":case["generation"],"captured_generation":1,"valid":valid}
        dx=actual_dx if valid else 0
        pred=shift(frames[0],dx)
        residual=[[int(a!=b) for a,b in zip(ar,br)] for ar,br in zip(pred,frames[1])]
        if row.get("id")!=case["id"]: errs.append(case["id"]+":identity")
        if row.get("frames")!=frames: errs.append(case["id"]+":frames")
        if row.get("receipt")!=receipt: errs.append(case["id"]+":receipt")
        if row.get("predicted_dx")!=dx or row.get("predicted_frame")!=pred: errs.append(case["id"]+":prediction")
        if row.get("residual_mask")!=residual: errs.append(case["id"]+":residual")
        detected,p=event_visible(case,frames)
        score={}
        for arm,mask in row.get("alarms",{}).items():
            count=sum(sum(int(v) for v in rr) for rr in mask) if isinstance(mask,list) else 10**9
            if count>fixture["alarm_budget_cells"]: errs.append(case["id"]+":"+arm+":budget")
            score[arm]=bool(detected and p and selected(mask,*p))
        if case["critical"] and detected and not all(score.get(a,False) for a in ("raw","agnostic","bound","sham")):
            # A missed visible mandatory cue invalidates the full-frame safety comparison as configured.
            errs.append(case["id"]+":critical-miss")
        reconstructed.append({"id":case["id"],"visible":detected,"deadline_frame":1 if detected else None,"detected":score,"critical":case["critical"]})
    byid={r["id"]:r for r in reconstructed}
    held=byid.get("heldout-bound-pan-flash",{})
    # In this fixed coordinate fixture raw/aligned alarms are bounded; report rather than tune to obtain a pass.
    metrics={"rows":len(reconstructed),"visible_events":sum(r["visible"] for r in reconstructed),
             "critical_visible":sum(r["critical"] and r["visible"] for r in reconstructed),
             "heldout_bound_detected":bool(held.get("detected",{}).get("bound")),
             "heldout_raw_detected":bool(held.get("detected",{}).get("raw")),
             "method_checks":len(fixture["cases"])*5+3}
    # Each mutation is passed through independent reconstruction; all must fail.
    mutations=[]
    m=json.loads(json.dumps(raw));m["rows"][0]["receipt"]["delivery"]="failed";mutations.append(m)
    m=json.loads(json.dumps(raw));m["rows"][0]["frames"][1][12][16]=0;mutations.append(m)
    m=json.loads(json.dumps(raw));m["rows"][1]["alarms"]["bound"]=[[0]*32 for _ in range(24)];mutations.append(m)
    m=json.loads(json.dumps(raw));m["rows"][10]["receipt"]["valid"]=True;mutations.append(m)
    m=json.loads(json.dumps(raw));m["rows"][0]["alarms"]["raw"]=[[1]*32 for _ in range(24)];mutations.append(m)
    rejected=0
    for mutant in mutations:
        merr,_,_=verify(fixture,mutant)
        rejected += bool(merr)
    metrics.update({"mutation_controls_rejected":rejected,"mutation_controls_total":len(mutations)})
    if rejected!=len(mutations): errs.append("mutation-controls")
    return errs,metrics,reconstructed


def verify_core(fixture, raw):
    """Independent accounting subset used to test mutation rejection."""
    errors=[]
    if raw.get("schema")!="action-bound-residual-raw-v1" or raw.get("fixture_schema")!=fixture.get("schema"):
        errors.append("schema")
    if len(raw.get("rows",[]))!=len(fixture["cases"]):
        errors.append("denominator")
    for case,row in zip(fixture["cases"],raw.get("rows",[])):
        frames=expected_frames(case)
        valid=case["generation"]==1 and case["delivery"] in ("exact","under","over")
        actual_dx={"exact":2,"under":1,"over":3,"delayed":0,"failed":0,"none":0}[case["delivery"]]
        receipt={"requested":"pan" if case["delivery"]!="none" else "none","delivery":case["delivery"],"actual_dx":actual_dx,
                 "source_generation":case["generation"],"captured_generation":1,"valid":valid}
        predicted_dx=actual_dx if valid else 0
        predicted=shift(frames[0],predicted_dx)
        residual=[[int(a!=b) for a,b in zip(ar,br)] for ar,br in zip(predicted,frames[1])]
        if row.get("id")!=case["id"] or row.get("frames")!=frames or row.get("receipt")!=receipt:
            errors.append(case["id"]+":source")
        if row.get("predicted_dx")!=predicted_dx or row.get("predicted_frame")!=predicted or row.get("residual_mask")!=residual:
            errors.append(case["id"]+":residual")
        for arm,mask in row.get("alarms",{}).items():
            if not isinstance(mask,list) or len(mask)!=24 or any(len(rr)!=32 for rr in mask):
                errors.append(case["id"]+":"+arm+":shape")
                continue
            if sum(sum(int(v) for v in rr) for rr in mask)>fixture["alarm_budget_cells"]:
                errors.append(case["id"]+":"+arm+":budget")
    return errors


def main(fpath,rpath,opath):
    fixture=json.loads(Path(fpath).read_text(encoding="utf-8"));raw=json.loads(Path(rpath).read_text(encoding="utf-8"))
    errs,metrics,rows=verify(fixture,raw)
    out={"schema":"action-bound-residual-audit-v1","disposition":"METHOD_PASS_SCOPED" if not errs else "FAIL_AUDIT",
         "errors":errs,"metrics":metrics,"reconstructed_rows":rows,
         "hypothesis_disposition":"HOLD_NO_INCREMENTAL_BENEFIT" if not metrics.get("heldout_bound_detected") or metrics.get("heldout_raw_detected") else "REQUIRES_CRITICAL_GATE_REVIEW",
         "scope":"synthetic raster method accounting only; no real-world visual-control or safety inference"}
    Path(opath).write_text(json.dumps(out,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")
    print(json.dumps(out,sort_keys=True))
    if errs: raise SystemExit(1)


if __name__=="__main__":
    if len(sys.argv)!=4: raise SystemExit("usage: audit.py CASES.json RAW.json AUDIT.json")
    main(*sys.argv[1:])
