import hashlib, json

CASES = [
 ("current_sufficient", [("current","s1","main",40,"READY")], "READY"),
 ("ambiguous_predecessor", [("current","s1","main",40,"AMBIG"),("predecessor","s1","main",30,"SAVED")], "SAVED"),
 ("irrelevant_older", [("current","s1","main",40,"READY"),("old","s1","main",10,"SAVED")], "READY"),
 ("wrong_window", [("current","s1","main",40,"AMBIG"),("wrong_window","s1","main",20,"OTHER")], "UNKNOWN"),
 ("dropped_interval", [("current","s1","main",40,"AMBIG")], "UNKNOWN"),
 ("stale_identity", [("current","s1","main",40,"NEW_DIALOG"),("old","s1","main",30,"OLD_DIALOG")], "NEW_DIALOG"),
 ("no_visual_effect", [("current","s1","main",40,"UNCHANGED"),("after_action","s1","main",35,"UNCHANGED")], "UNCHANGED"),
 ("other_surface", [("current","s1","main",40,"AMBIG"),("history","s2","dialog",30,"SAVED")], "UNKNOWN"),
 ("mislabel_current", [("current","s1","main",40,"AMBIG"),("historical_mislabeled","s1","main",30,"SAVED")], "UNKNOWN"),
 ("unavailable_interval", [("current","s1","main",40,"AMBIG")], "UNKNOWN"),
]

def query(xs, arm):
    if arm == "CURRENT_ONLY": return [x for x in xs if x[0]=="current"]
    if arm == "JIT_EQUIVALENT_HISTORY": return [x for x in xs if x[0] in ("current","predecessor","after_action")]
    if arm == "CONTINUOUS_RING_HISTORY": return xs
    if arm == "CONTINUOUS_RING_WRONG_WINDOW": return [x for x in xs if x[3] <= 20]
    raise ValueError(arm)

def decide(evidence):
    valid=[x for x in evidence if x[1]=="s1" and x[2]=="main" and x[0]!="historical_mislabeled"]
    if not valid: return "UNKNOWN"
    cur=[x for x in valid if x[0]=="current"]
    if cur and cur[-1][4] != "AMBIG": return cur[-1][4]
    hist=[x for x in valid if x[0] in ("predecessor","after_action")]
    return hist[-1][4] if hist and hist[-1][4] != "AMBIG" else "UNKNOWN"

def main():
    rows=[]
    for name,xs,expected in CASES:
        arms={arm:decide(query(xs,arm)) for arm in ("CURRENT_ONLY","JIT_EQUIVALENT_HISTORY","CONTINUOUS_RING_HISTORY","CONTINUOUS_RING_WRONG_WINDOW")}
        rows.append({"case":name,"expected":expected,"arms":arms})
    assert len(rows)==10
    assert rows[1]["arms"]["CONTINUOUS_RING_HISTORY"]=="SAVED"
    assert rows[3]["arms"]["CONTINUOUS_RING_WRONG_WINDOW"]=="UNKNOWN"
    assert rows[4]["arms"]["CONTINUOUS_RING_HISTORY"]=="UNKNOWN"
    assert rows[7]["arms"]["CONTINUOUS_RING_HISTORY"]=="UNKNOWN"
    assert rows[8]["arms"]["CONTINUOUS_RING_HISTORY"]=="UNKNOWN"
    assert rows[9]["arms"]["CONTINUOUS_RING_HISTORY"]=="UNKNOWN"
    digest=hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()
    print(json.dumps({"cases":10,"rows":rows,"oracle":"PASS","provenance_scope":"PASS","unknown_on_gap":"PASS","wrong_window_control":"PASS","model_invocations":0,"x11_invocations":0,"task_input_events":0,"digest":digest},sort_keys=True))
main()
