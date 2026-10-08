import json,sys
fixture=json.load(open(sys.argv[1],encoding="utf-8"))
candidate=json.load(open(sys.argv[2],encoding="utf-8"))
expected={c["id"]:c["expect"] for c in fixture["cases"]}
errors=[]
if len(candidate.get("rows",[]))!=len(expected): errors.append("row_count")
for r in candidate.get("rows",[]):
    if r["id"] not in expected: errors.append("unknown_row:"+r["id"]); continue
    c=next(x for x in fixture["cases"] if x["id"]==r["id"])
    missing=[x for x in c["mandatory"] if x not in c["observed"]]
    failed=any(v=="fail" for v in c["observed"].values())
    sealed="generation_sealed" in c["events"]
    correct=("pending" if missing or (not failed and not sealed) else "final_negative" if failed else "final_positive")
    if r.get("disposition")!=correct: errors.append("disposition:"+r["id"])
    if r.get("pending_obligations")!=missing: errors.append("obligations:"+r["id"])
    if r.get("mandatory_count")!=len(c["mandatory"]) or r.get("observed_count")!=len(c["observed"]): errors.append("counts:"+r["id"])
    if r.get("stability_metric")!={"generation_sealed":sealed,"optional_open":c["optional_open"]}: errors.append("metrics:"+r["id"])
result={"verdict":"PASS" if not errors else "FAIL_AUDIT","rows_checked":len(candidate.get("rows",[])),"errors":errors,"mutation_controls":"not run"}
print(json.dumps(result,sort_keys=True))
sys.exit(0 if not errors else 1)
