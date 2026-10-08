"""Eight-case scorer contract preflight for #2642/#2606."""
CASES=("useful","unavailable","guarded","no_effect","partial","stale_repair","ambiguous","cleanup_failure")
EXPECTED=("SUCCESS","YIELD","YIELD","NONE","PARTIAL","YIELD","YIELD","YIELD")
if __name__=="__main__":
 import json; print(json.dumps({"cases":CASES,"expected":EXPECTED,"scope":"Docker contract/scorer preflight; not live GTK acceptance"},indent=2))
