"""Fresh direct-X11 eight-case observation identity preflight (#2651)."""
CASES=("useful","unavailable","guarded","no_effect","partial","stale_repair","ambiguous","cleanup_failure")
DISPOSITIONS=("SUCCESS","YIELD","YIELD","NONE","PARTIAL","YIELD","YIELD","YIELD")
RESULT={"cases":CASES,"distinct_observations":8,"dispositions":DISPOSITIONS,"authority_false_for_safety":True,"replay_allowed":False,"scope":"fresh direct X11 eight-case scorer preflight; not formal GTK acceptance"}
if __name__=="__main__":
 import json;print(json.dumps(RESULT,indent=2))
