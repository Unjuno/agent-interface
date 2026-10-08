import json, sys
data=json.load(open(sys.argv[1],encoding="utf-8"))
rows=[]
for c in data["cases"]:
    missing=[x for x in c["mandatory"] if x not in c["observed"]]
    failed=any(v=="fail" for v in c["observed"].values())
    sealed="generation_sealed" in c["events"]
    if missing: disposition="pending"
    elif failed: disposition="final_negative"
    elif sealed: disposition="final_positive"
    else: disposition="pending"
    rows.append({"id":c["id"],"disposition":disposition,"pending_obligations":missing,"mandatory_count":len(c["mandatory"]),"observed_count":len(c["observed"]),"stability_metric":{"generation_sealed":sealed,"optional_open":c["optional_open"]}})
print(json.dumps({"schema":"candidate-prefix-v1","rows":rows},sort_keys=True))
