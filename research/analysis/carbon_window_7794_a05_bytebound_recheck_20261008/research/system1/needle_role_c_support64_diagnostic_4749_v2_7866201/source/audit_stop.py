"""Independent verification that failed one-shot produced no raw outputs."""
import json,os,sys
p=sys.argv[1]
items=sorted(os.listdir(p))
if items:
    print(json.dumps({"disposition":"HOLD_UNEXPECTED_PARTIAL_OUTPUT","entries":items},sort_keys=True)); raise SystemExit(1)
print(json.dumps({"disposition":"STOP_NO_RAW_OUTPUT","entries":[],"optimizer_updates":0,"seed_reusable":False},sort_keys=True))

