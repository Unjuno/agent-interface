import itertools, json, math, pathlib
ROOT = pathlib.Path(__file__).parent
freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8-sig"))
period, horizon = freeze["period"], freeze["horizon"]
perms = sorted(set(itertools.permutations(freeze["circular_gap_multiset"])))
rows=[]
for idx,gaps in enumerate(perms):
    misses=set(); pos=0
    for gap in gaps:
        pos=(pos+gap) % period
        misses.add(pos)
        pos=(pos+1) % period
    # Mapping gaps to locations can collide if offsets are incorrectly interpreted; assert contract.
    assert len(misses)==freeze["miss_count"], (gaps, misses)
    trace=[]; x=0.0; peak=0.0; unsafe_ticks=0
    for t in range(horizon):
        miss=(t % period) in misses
        d=0.22*math.sin(2*math.pi*t/12)+0.18*math.sin(2*math.pi*t/7)
        x=(1.2*x if miss else 0.45*x)+d
        peak=max(peak,abs(x)); unsafe_ticks += abs(x)>1.0
        trace.append({"t":t,"miss":miss,"x":round(x,12),"d":round(d,12)})
    window_max=max(sum(((start+j)%period) in misses for j in range(4)) for start in range(period))
    age_hist=sorted(gaps)
    rows.append({"id":idx,"gaps":list(gaps),"miss_ticks":sorted(misses),"total_misses":len(misses)*(horizon//period),"total_delay_units":len(misses)*(horizon//period),"age_histogram":age_hist,"max_misses_4_window":window_max,"peak_abs_x":round(peak,12),"unsafe_ticks":unsafe_ticks,"unsafe":unsafe_ticks>0,"trace":trace})
train,heldout=rows[:16],rows[16:]
valid=[]
for th in range(1,5):
    fs=sum((r["max_misses_4_window"]<th) and r["unsafe"] for r in train)
    if fs==0: valid.append(th)
threshold=max(valid) if valid else None
for r in rows:
    r["split"]="train" if r["id"]<16 else "heldout"
    r["predict_unsafe"]=None if threshold is None else r["max_misses_4_window"]>=threshold
    del r["trace"]
result={"study":"7458-t0-a02","status":"RAW_COMPLETE","threshold":threshold,"rows":rows,"counts":{"schedules":len(rows),"train":len(train),"heldout":len(heldout)},"metrics":{"heldout_false_safe":sum(r["unsafe"] and not r["predict_unsafe"] for r in heldout) if threshold else None,"heldout_false_alarm":sum((not r["unsafe"]) and r["predict_unsafe"] for r in heldout) if threshold else None,"heldout_safe":sum(not r["unsafe"] for r in heldout),"heldout_unsafe":sum(r["unsafe"] for r in heldout)}}
(ROOT/"raw.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8",newline="\n")
print(json.dumps({"status":result["status"],"count":len(rows),"threshold":threshold,"metrics":result["metrics"]},sort_keys=True))
