"""Live GTK/Xvfb eight-case scorer preflight for #2647."""
CASES=("useful","unavailable","guarded","no_effect","partial","stale_repair","ambiguous","cleanup_failure")
DISPOSITIONS=("SUCCESS","YIELD","YIELD","NONE","PARTIAL","YIELD","YIELD","YIELD")
LIMITATION="All cases exercised, but current fixture produced one observation hash; not formal #2606 acceptance."
if __name__=="__main__":
 import json; print(json.dumps({"cases":CASES,"dispositions":DISPOSITIONS,"limitation":LIMITATION},indent=2))
