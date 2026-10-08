from __future__ import annotations
import argparse,json
from pathlib import Path

CONDS=["BASELINE","INBOUND_QUEUE_80MS","PROCESSING_80MS","OUTBOUND_QUEUE_80MS","STALE_300MS"]
ARMS=["TRANSLATED_LOWER","RECEIVER_ACTIVATION_TOKEN"]
SRC={"server.py":"0a8d3440ce621debe6ddbdc9f9f96383123de827f78b8335dbb357212a40b9ad","run_case.py":"f7525b1a14a8ae1cd28f7d894c595280bf32bd0ffbb94e816cd694e3753cb721","lease.py":"e71f9850d3999a31fcb86c00f9ef7a8ba19bae8d3a8bdc11bf7bd620817a535f"}

def audit(root:Path):
 e=[]; n=0
 def q(ok,msg):
  nonlocal n; n+=1
  if not ok:e.append(msg)
 rows=[json.loads(p.read_text()) for p in sorted(root.glob("*/record.json"))]
 ids=[r.get("case_id") for r in rows]
 expected={f"{a}-{c}-r{k}" for k in range(2) for c in CONDS for a in ARMS}
 q(len(rows)==20,f"ROW_COUNT:{len(rows)}"); q(len(ids)==len(set(ids)),"DUPLICATE_ID"); q(set(ids)==expected,"MATRIX_MISMATCH")
 lp=root/"launcher.json"; q(lp.exists(),"LAUNCHER_MISSING")
 if lp.exists():
  l=json.loads(lp.read_text()); cases=l.get("cases",[]); q(l.get("count")==20,f"LAUNCHER_COUNT:{l.get('count')}");q(len(cases)==20,f"LAUNCHER_ROWS:{len(cases)}")
  for x in cases:
   q(x.get("exit")==0,f"LAUNCHER_EXIT:{x.get('case_id')}");q(x.get("case_id") in expected,f"LAUNCHER_ID:{x.get('case_id')}");q(type(x.get("start_ns")) is int and type(x.get("end_ns")) is int and x["end_ns"]>=x["start_ns"],f"LAUNCHER_TIME:{x.get('case_id')}")
 for r in rows:
  cid=r.get("case_id"); arm=r.get("arm"); cond=r.get("condition")
  q(arm in ARMS and cond in CONDS,f"ARM_COND:{cid}");q(r.get("server_exit")==0,f"EXIT:{cid}")
  q((r.get("ttl_ns"),r.get("activation_window_ns"),r.get("offset_ns"))==(160_000_000,250_000_000,5_000_000_000),f"PARAM:{cid}")
  q(r.get("source_sha256")==SRC,f"SOURCE:{cid}")
  j=r.get("journal",[]);q(type(j) is list and len(j)>=2,f"JOURNAL:{cid}");q(r.get("shutdown_reply",{}).get("cmd")=="shutdown_reply",f"SHUTDOWN:{cid}")
  for x in j:
   q(type(x.get("sent_ns")) is int and type(x.get("recv_ns")) is int and x["recv_ns"]>=x["sent_ns"],f"JOURNAL_TIME:{cid}")
   q(x.get("request_wire")==json.dumps(x.get("request"),sort_keys=True,separators=(",",":")),f"REQUEST_WIRE:{cid}")
   q(x.get("reply_wire")==json.dumps(x.get("reply"),sort_keys=True,separators=(",",":")),f"REPLY_WIRE:{cid}")
   q(x.get("reply",{}).get("request_id") in {None,x.get("request",{}).get("request_id")},f"WIRE_ID:{cid}")
  if arm==ARMS[0]:
   lo=r["c3_ns"]-r["h4_ns"]; hi=r["c2_ns"]-r["h1_ns"]
   q((lo,hi)==(r["lower_ns"],r["upper_ns"]) and lo<=hi,f"CAL:{cid}");q(r["runtime_deadline_ns"]==r["host_deadline_ns"]+lo,f"TRANSLATE:{cid}")
   ext=r["runtime_deadline_ns"]-(r["host_deadline_ns"]+r["offset_ns"]);q(ext==r["deadline_extension_ns"] and ext<=0,f"EXTEND:{cid}")
   live=r["true_host_check_ns"]<r["host_deadline_ns"];q(live==r["actually_live"],f"LIVE_LABEL:{cid}")
   want="EXPIRED" if cond in {CONDS[3],CONDS[4]} else "LIVE";q(r["check_reply"]["status"]==want,f"STATUS:{cid}")
   if cond==CONDS[3]:q(live,f"NO_EARLY_REFUSAL:{cid}")
   if cond==CONDS[4]:q(not live,f"STALE_NOT_STALE:{cid}")
   q(r["check_reply"].get("task_input_authority") is False and r["check_reply"].get("task_success") is None,f"AUTH:{cid}")
  else:
   t=r["token_reply"];a=r["activation_reply"]
   q(t.get("lease_activated") is False and t.get("task_input_authority") is False and t.get("semantic_authority") is False and t.get("task_success") is None,f"TOKEN_AUTH:{cid}")
   if cond==CONDS[4]: q(a.get("status")=="REJECTED" and a.get("reason")=="STALE_TOKEN" and a.get("lease_activated") is False,f"STALE_TOKEN:{cid}")
   else:
    q(a.get("status")=="ACTIVATED" and a.get("lease_activated") is True,f"ACTIVATE:{cid}")
    if a.get("status")=="ACTIVATED":
     q(a["deadline_ns"]-a["activation_check_ns"]==r["ttl_ns"],f"TTL:{cid}");q(a["token_age_ns"]<=r["activation_window_ns"],f"TOKEN_AGE:{cid}")
     q(a.get("task_input_authority") is False and a.get("semantic_authority") is False and a.get("task_success") is None,f"ACT_AUTH:{cid}");q(a.get("issued_ns")==t.get("issued_ns"),f"ISSUE_BIND:{cid}")
 return {"decision":"PASS_RECEIVER_ACTIVATION_LEASE_BOUNDARY_SCOPED" if not e else "FAIL_AUDIT","rows":len(rows),"checks":n,"errors":e,"expected_source_sha256":SRC}

def main():
 p=argparse.ArgumentParser();p.add_argument("root");a=p.parse_args();o=audit(Path(a.root));print(json.dumps(o,sort_keys=True,indent=2));return 0 if not o["errors"] else 1
if __name__=="__main__":raise SystemExit(main())
