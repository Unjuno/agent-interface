"""Read-only semantic selection identity fixture for Issue #2018."""
import hashlib,json
VIS="same-pixels"
def visual_only(expected,obs): return obs["visual"]==expected["visual"]
def semantic(expected,obs):
    return obs.get("available",False) and obs.get("app")==expected["app"] and obs.get("window")==expected["window"] and obs.get("object")==expected["object"] and obs.get("generation")==expected["generation"]
def combined(expected,obs): return visual_only(expected,obs) and semantic(expected,obs)
def run():
    expected={"visual":VIS,"app":"calc","window":"w1","object":"cell-A","generation":4}
    cases=[("stable",dict(expected,available=True)),
      ("replacement",dict(expected,object="cell-B",generation=5,available=True)),
      ("focus_transfer",dict(expected,window="w2",available=True)),
      ("unavailable",dict(expected,available=False)),
      ("stale",dict(expected,generation=3,available=True)),
      ("conflict",dict(expected,visual="different",available=True))]
    rows=[]
    for name,obs in cases:
        rows.append({"case":name,"visual":visual_only(expected,obs),
                     "semantic":semantic(expected,obs),
                     "combined":combined(expected,obs),"authority_events":0})
    assert rows[0]["combined"] and not rows[1]["combined"] and not rows[2]["combined"]
    assert all(not r["combined"] for r in rows[1:])
    assert all(r["authority_events"]==0 for r in rows)
    return rows
if __name__=="__main__":
    rows=run(); print(json.dumps(rows,sort_keys=True))
    print("digest",hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest())
