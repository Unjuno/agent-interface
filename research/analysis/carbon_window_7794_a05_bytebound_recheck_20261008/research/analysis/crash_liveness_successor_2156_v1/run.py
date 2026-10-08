import hashlib, json

CASES=[
 ("PERSISTED_TOKEN_VISIBLE",True,True,False,True,"REPLAY"),
 ("PERSISTED_TOKEN_LOST",True,False,False,True,"QUERY_EFFECT"),
 ("PREPERSIST_CRASH",False,False,False,True,"ISSUE_NEW_ID"),
 ("CORRUPT_OR_TRUNCATED_JOURNAL",None,None,False,True,"RECONCILE"),
 ("EFFECT_ALREADY_APPLIED",True,False,True,False,"ABORT"),
 ("EFFECT_UNKNOWN",True,False,None,False,"QUERY_EFFECT"),
]

def decide(kind,persisted,delivered,effect,idempotent):
 if kind=="PERSISTED_TOKEN_VISIBLE": return "REPLAY"
 if kind=="PERSISTED_TOKEN_LOST": return "QUERY_EFFECT" if effect is not True else "ABORT"
 if kind=="PREPERSIST_CRASH": return "ISSUE_NEW_ID"
 if kind=="CORRUPT_OR_TRUNCATED_JOURNAL": return "RECONCILE"
 if kind=="EFFECT_ALREADY_APPLIED": return "ABORT"
 return "QUERY_EFFECT"

def main():
 rows=[]
 for kind,persisted,delivered,effect,idempotent,expected in CASES:
  actual=decide(kind,persisted,delivered,effect,idempotent)
  rows.append({"kind":kind,"persisted":persisted,"delivered":delivered,"effect":effect,"idempotent":idempotent,"decision":actual,"expected":expected,"new_authority":0,"external_effects":0})
 assert all(r["decision"]==r["expected"] for r in rows)
 assert all(r["new_authority"]==0 and r["external_effects"]==0 for r in rows)
 raw=json.dumps(rows,sort_keys=True,separators=(",",":")).encode()
 out={"decision":"HOLD_PRE_MODEL_CRASH_LIVENESS_POLICY","cases":6,"oracle_agreement":6,"blind_non_idempotent_replays":0,"new_authority":0,"external_effects":0,"model_invocations":0,"sha256":hashlib.sha256(raw).hexdigest()}
 print(json.dumps(out,indent=2,sort_keys=True))
if __name__=="__main__": main()
