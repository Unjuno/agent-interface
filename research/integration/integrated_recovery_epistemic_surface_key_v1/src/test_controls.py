from validator import *

def receipt(identity):
    return {"identity": identity, "authority":"none", "task_input_granted":False, "action_admission_eligible":False}

def I(client, trans, backend="x11"):
    return {"backend":known(backend), "top_level_client_id":known(client), "transient_for":trans}

# Exact observed null.
assert classify(receipt(I(2, known(None))), I(2, known(None)))["classification"] == EXACT_MATCH
# Exact observed relation.
assert classify(receipt(I(2, known(1))), I(2, known(1)))["classification"] == EXACT_MATCH
# Missing is not null and cannot become exact.
assert classify(receipt(I(2, {"state":UNKNOWN})), I(2, known(None)))["classification"] == CORE_MATCH_REFINEMENT_UNKNOWN
# Known refinement mismatch must reject even with equal core.
assert classify(receipt(I(2, known(1))), I(2, known(3)))["classification"] == MISMATCH
# Core mismatches reject before refinement uncertainty matters.
assert classify(receipt(I(2, {"state":UNKNOWN})), I(4, {"state":UNKNOWN}))["classification"] == MISMATCH
assert classify(receipt(I(2, known(None), "x11")), I(2, known(None), "wayland"))["classification"] == MISMATCH
# Missing mandatory evidence is invalid.
bad = I(2, known(None)); bad["top_level_client_id"]={"state":UNKNOWN}
assert classify(receipt(bad), I(2, known(None)))["classification"] == INVALID
# Malformed state/value is invalid.
bad = I(2, known(None)); bad["transient_for"]={"state":UNKNOWN,"value":None}
assert classify(receipt(bad), I(2, known(None)))["classification"] == INVALID
# Observation-only invariant is enforced.
r=receipt(I(2,known(None))); r["task_input_granted"]=True
assert classify(r,I(2,known(None)))["classification"] == INVALID
print("construction_controls=PASS count=9")
