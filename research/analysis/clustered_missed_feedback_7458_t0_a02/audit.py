import itertools,json,math,pathlib,sys
ROOT=pathlib.Path(__file__).parent
f=json.loads((ROOT/"FREEZE.json").read_text(encoding="utf-8-sig")); r=json.loads((ROOT/"raw.json").read_text(encoding="utf-8"))
errors=[]; expected=[]
for idx,gaps in enumerate(sorted(set(itertools.permutations(f["circular_gap_multiset"])) )):
    miss=set(); p=0
    for gap in gaps:
        p=(p+gap)%f["period"]; miss.add(p); p=(p+1)%f["period"]
    x=0.; peak=0.; unsafe_ticks=0
    for t in range(f["horizon"]):
        d=.22*math.sin(2*math.pi*t/12)+.18*math.sin(2*math.pi*t/7)
        x=(1.2*x if t%f["period"] in miss else .45*x)+d
        peak=max(peak,abs(x)); unsafe_ticks += abs(x)>1.
    win=max(sum((s+j)%f["period"] in miss for j in range(4)) for s in range(f["period"]))
    expected.append({"id":idx,"gaps":list(gaps),"miss_ticks":sorted(miss),"total_misses":len(miss)*(f["horizon"]//f["period"]),"total_delay_units":len(miss)*(f["horizon"]//f["period"]),"age_histogram":sorted(gaps),"max_misses_4_window":win,"peak_abs_x":round(peak,12),"unsafe_ticks":unsafe_ticks,"unsafe":unsafe_ticks>0,"split":"train" if idx<16 else "heldout"})
if r["counts"]!={"schedules":24,"train":16,"heldout":8}: errors.append("counts mismatch")
if len(r["rows"])!=24: errors.append("row count")
for e,a in zip(expected,r["rows"]):
    for k,v in e.items():
        if a.get(k)!=v: errors.append(f"row {e['id']} field {k}: {a.get(k)} != {v}")
valid=[t for t in range(1,5) if sum(e["unsafe"] and e["max_misses_4_window"]<t for e in expected[:16])==0]
th=max(valid) if valid else None
if r["threshold"]!=th: errors.append("threshold mismatch")
for a in r["rows"]:
    exp=None if th is None else a["max_misses_4_window"]>=th
    if a.get("predict_unsafe")!=exp: errors.append(f"prediction mismatch {a['id']}")
status="PASS_AUDIT" if not errors else "FAIL_AUDIT"
out={"status":status,"errors":errors,"independently_recomputed_rows":len(expected),"threshold":th,"note":"audit independently recomputes the declared simulator and labels; it does not validate transfer to GUI or controller behavior"}
(ROOT/"audit.json").write_text(json.dumps(out,sort_keys=True,indent=2)+"\n",encoding="utf-8",newline="\n")
print(json.dumps(out,sort_keys=True)); sys.exit(bool(errors))
