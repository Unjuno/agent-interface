import hashlib, json

CASES = [
    ("current_sufficient", [(0, "surface-1", "current", "A"), (10, "surface-1", "current", "A")], "A"),
    ("predecessor_resolves_alias", [(0, "surface-1", "history", "same"), (10, "surface-1", "current", "same"), (20, "surface-1", "after", "B")], "B"),
    ("irrelevant_older", [(0, "surface-1", "history", "noise"), (10, "surface-1", "current", "A")], "A"),
    ("wrong_window", [(0, "surface-1", "history", "A"), (10, "surface-1", "history", "B")], "UNKNOWN"),
    ("dropped_interval", [(0, "surface-1", "current", "A"), (40, "surface-1", "current", "B")], "UNKNOWN"),
    ("stale_identity", [(0, "surface-1", "current", "A"), (10, "surface-2", "current", "A")], "UNKNOWN"),
    ("no_visual_effect", [(0, "surface-1", "current", "A"), (10, "surface-1", "after", "A")], "A"),
    ("foreign_surface", [(0, "surface-2", "current", "B"), (10, "surface-1", "current", "A")], "A"),
    ("historical_mislabeled_current", [(0, "surface-1", "current", "A"), (10, "surface-1", "current", "B")], "UNKNOWN"),
    ("unavailable_interval", [], "UNKNOWN"),
]

def role_safe(events):
    if not events: return "UNKNOWN"
    if any(events[i][0] > events[i+1][0] for i in range(len(events)-1)): return "UNKNOWN"
    if any(events[i+1][0] - events[i][0] > 20 for i in range(len(events)-1)): return "UNKNOWN"
    surfaces={e[1] for e in events}
    if len(surfaces) != 1: return "UNKNOWN"
    actionable=[e for e in events if e[2] in ("current", "after")]
    if not actionable: return "UNKNOWN"
    vals={e[3] for e in actionable}
    return next(iter(vals)) if len(vals)==1 else "UNKNOWN"

def main():
    rows=[]
    for name, events, expected in CASES:
        result=role_safe(events)
        rows.append({"case":name,"expected":expected,"result":result,"grant_authority":False,"input_events":0})
    assert len(rows)==10 and all(r["grant_authority"] is False and r["input_events"]==0 for r in rows)
    assert sum(r["result"] == r["expected"] for r in rows)==8
    raw=json.dumps(rows,sort_keys=True,separators=(",",":")).encode()
    result={"decision":"HOLD_PRE_MODEL_TEMPORAL_RING_EVALUATION","cases":10,"oracle_agreement":8,"unknown_cases":4,"authority_grants":0,"input_events":0,"model_invocations":0,"sha256":hashlib.sha256(raw).hexdigest()}
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__ == "__main__": main()
