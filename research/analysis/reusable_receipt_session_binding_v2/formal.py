import json
from bridge import ReusableReceiptStore,FOCUS_BLOB,REUSABLE,FRESH

SESSIONS=("A","B")
RESOURCES=("focus:surface1","focus:surface2")

def receipt(session,resource,current):
    return {
      "role":REUSABLE,"storage":"PERSIST_DEPENDENCY",
      "scope":"FOCUS_OBSERVATION_CURRENTNESS","source_blob":FOCUS_BLOB,
      "session_id":session,"canonical_resource":resource,
      "current":current,"lineage":session+":"+resource,
      "prepared_version":"g0","current_version":"g0" if current else "g1",
      "identity_relation":"SAME"
    }

rows=[]
for ss in SESSIONS:
  for sr in RESOURCES:
    for current in (True,False):
      for qs in SESSIONS:
        for qr in RESOURCES:
          store=ReusableReceiptStore()
          accepted=store.store(receipt(ss,sr,current))
          out=store.revalidate(qs,qr,{"payload_session":qs,"payload_resource":qr})
          expected=(ss==qs and sr==qr and current)
          rows.append({
            "stored_session":ss,"stored_resource":sr,"current":current,
            "request_session":qs,"request_resource":qr,
            "store_accepted":accepted,"result":out["status"],
            "expected_revalidated":expected
          })

controls=[]
base=receipt("A","focus:surface1",True)
for name,mut in [
  ("missing_session",{"session_id":None}),
  ("missing_resource",{"canonical_resource":None}),
  ("commit_role",{"role":FRESH,"storage":"EPHEMERAL_ONLY"}),
  ("wrong_source",{"source_blob":"wrong"}),
  ("unknown_role",{"role":"UNKNOWN"})
]:
  x=dict(base); x.update(mut); s=ReusableReceiptStore()
  controls.append({"name":name,"accepted":s.store(x),"rejections":list(s.rejections)})

revalidated=sum(x["result"]=="revalidated" for x in rows)
false_accept=sum((x["result"]=="revalidated") != x["expected_revalidated"] for x in rows)
cross_session_accept=sum(x["result"]=="revalidated" and x["stored_session"]!=x["request_session"] for x in rows)
cross_resource_accept=sum(x["result"]=="revalidated" and x["stored_session"]==x["request_session"] and x["stored_resource"]!=x["request_resource"] for x in rows)
stale_current_accept=sum(x["result"]=="revalidated" and not x["current"] for x in rows)
control_accept=sum(x["accepted"] for x in controls)
commit_store=ReusableReceiptStore(); commit_store.store({**base,"role":FRESH,"storage":"EPHEMERAL_ONLY"})
result={
 "rows":len(rows),"revalidated":revalidated,"stale":len(rows)-revalidated,
 "classification_mismatches":false_accept,
 "cross_session_accepts":cross_session_accept,
 "cross_resource_accepts":cross_resource_accept,
 "stale_current_accepts":stale_current_accept,
 "controls":controls,"control_accepts":control_accept,
 "persistent_commit_receipts":commit_store.persistent_commit_count(),
 "formal_invocations":1,"reruns":0,"replacements":0,"tuning":0,
 "decision":None
}
pass_gate=(len(rows)==32 and revalidated==4 and false_accept==0 and
 cross_session_accept==0 and cross_resource_accept==0 and stale_current_accept==0 and
 control_accept==0 and result["persistent_commit_receipts"]==0)
result["decision"]="PASS_REUSABLE_RECEIPT_SESSION_RESOURCE_BINDING_SCOPED" if pass_gate else "FAIL_REUSABLE_RECEIPT_SESSION_RESOURCE_BINDING"
print(json.dumps(result,indent=2,sort_keys=True))
