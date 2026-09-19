"""Finite independent effect-evidence verifier for Issue #2078."""
import hashlib,json
def verify(scorer,effect):
    if effect is None:return "UNKNOWN"
    if scorer["session"]!=effect["session"] or scorer["target"]!=effect["target"]:return "REJECTED"
    if scorer["ok"]!=effect["completed"]:return "CONFLICT"
    if scorer["effect_id"]!=effect["effect_id"]:return "REJECTED"
    return "ACCEPTED"
def run():
    scorer={"session":"s1","target":"A","ok":True,"effect_id":"e1"}
    cases=[("legit",scorer,dict(session="s1",target="A",completed=True,effect_id="e1"),"ACCEPTED"),
           ("forged",dict(scorer,effect_id="e2"),dict(session="s1",target="A",completed=True,effect_id="e1"),"REJECTED"),
           ("wrong_effect",scorer,dict(session="s1",target="A",completed=False,effect_id="e1"),"CONFLICT"),
           ("missing",scorer,None,"UNKNOWN"),
           ("wrong_target",scorer,dict(session="s1",target="B",completed=True,effect_id="e1"),"REJECTED")]
    rows=[{"case":n,"outcome":verify(a,b),"expected":e,"authority":False} for n,a,b,e in cases]
    assert all(r["outcome"]==r["expected"] and not r["authority"] for r in rows)
    return rows
if __name__=="__main__":
    rows=run(); print(json.dumps(rows,sort_keys=True))
    print(hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest())
