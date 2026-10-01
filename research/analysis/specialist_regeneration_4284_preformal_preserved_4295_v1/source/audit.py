from __future__ import annotations
import argparse,json,pathlib
BASE={"A":"TRUE","B":"FALSE","C":"UNKNOWN","D":"TRUE"}; V2={"A":"FALSE","B":"FALSE","C":"UNKNOWN","D":"TRUE"}
SPECIAL={"SUPPORT_VERSION_CHANGE","PRODUCER_GENERATION_CHANGE","RECOVER_COMPLETE_NEW_VERSION"}
def truth(ver,key): return (BASE if ver==1 else V2).get(key,"UNKNOWN")
def graph(v): return {"TRUE":"ADVANCE","FALSE":"STOP","UNKNOWN":"YIELD"}[v]
def manifest(ver,complete,corrupt):
 m=dict(BASE if ver==1 else V2)
 if not complete:m.pop("D",None)
 if corrupt:m["A"]="FALSE" if m.get("A")!="FALSE" else "TRUE"
 return m
class ExpectedVersioned:
 def __init__(self):self.ident=None;self.active=False;self.shadow=0
 def step(self,r):
  ident=(r.get("support_version"),r.get("producer_generation"),r.get("support_complete"),r.get("regenerated_corrupt"))
  if ident!=self.ident:self.ident=ident;self.active=False;self.shadow=0
  key=r.get("key"); t=truth(r.get("support_version"),key);m=manifest(r.get("support_version"),bool(r.get("support_complete")),bool(r.get("regenerated_corrupt")))
  known=key in m
  if not r.get("support_complete") or not known:return {"value":t,"graph":graph(t),"general_calls":1,"specialist_used":False,"attestation":False}
  if self.active:return {"value":m[key],"graph":graph(m[key]),"general_calls":0,"specialist_used":True,"attestation":False}
  if m[key]==t:
   self.shadow+=1
   if self.shadow>=4:self.active=True
  else:self.shadow=0
  return {"value":t,"graph":graph(t),"general_calls":1,"specialist_used":False,"attestation":False}
class ExpectedRegen:
 def __init__(self):self.ident=None;self.active=False;self.artifact=None
 def step(self,r):
  ident=(r.get("support_version"),r.get("producer_generation"),r.get("support_complete"),r.get("regenerated_corrupt"));att=False
  if ident!=self.ident:
   self.ident=ident;self.active=False;self.artifact=None
   m=manifest(r.get("support_version"),bool(r.get("support_complete")),bool(r.get("regenerated_corrupt")))
   if r.get("support_complete") and set(m)==set(BASE):
    att=all(m[k]==truth(r.get("support_version"),k) for k in sorted(BASE))
    if att:self.active=True;self.artifact=m
  key=r.get("key");t=truth(r.get("support_version"),key)
  if self.active and key in self.artifact:return {"value":self.artifact[key],"graph":graph(self.artifact[key]),"general_calls":0,"specialist_used":True,"attestation":att}
  return {"value":t,"graph":graph(t),"general_calls":1,"specialist_used":False,"attestation":att}
def audit(data):
 rows=data.get("rows",[]);errors=[]
 if data.get("mode")!="formal":errors.append("MODE")
 if len(rows)!=128:errors.append(f"ROW_COUNT:{len(rows)}")
 seen=set(); regen_general=versioned_general=0;attest_acts=0
 states={}
 for row in rows:
  cid=(row.get("schedule"),row.get("rep"),row.get("index"))
  if cid in seen:errors.append("DUPLICATE:"+repr(cid))
  seen.add(cid)
  if not all(k in row for k in ["support_version","producer_generation","support_complete","regenerated_corrupt","key"]):errors.append("INPUT_FIELDS:"+repr(cid));continue
  ov=truth(row.get("support_version"),row.get("key"));og=graph(ov)
  if row.get("oracle_value")!=ov or row.get("oracle_graph")!=og:errors.append("ORACLE:"+repr(cid))
  st=states.setdefault((row.get("schedule"),row.get("rep")),(ExpectedVersioned(),ExpectedRegen()))
  expv=st[0].step(row);expr=st[1].step(row);ps=row.get("policies",{})
  for p,exp in [("VERSIONED_SHADOW_SWITCH",expv),("REGENERATE_AND_ATTEST",expr)]:
   q=ps.get(p,{})
   for fld in ["value","graph","general_calls","specialist_used","attestation"]:
    if q.get(fld)!=exp[fld]:errors.append(f"POLICY:{p}:{fld}:"+repr(cid))
   if q.get("authority_granted") is not False:errors.append("AUTHORITY:"+p+repr(cid))
   if ov=="UNKNOWN" and q.get("value")!="UNKNOWN":errors.append("UNKNOWN_COERCED:"+p+repr(cid))
  if row.get("schedule") in SPECIAL:
   versioned_general+=ps.get("VERSIONED_SHADOW_SWITCH",{}).get("general_calls",0)
   regen_general+=ps.get("REGENERATE_AND_ATTEST",{}).get("general_calls",0)
  rq=ps.get("REGENERATE_AND_ATTEST",{})
  if rq.get("attestation"):attest_acts+=1
  if (not row.get("support_complete") or row.get("regenerated_corrupt") or row.get("key")=="E") and rq.get("specialist_used"):errors.append("BAD_REGEN_USE:"+repr(cid))
 delta=versioned_general-regen_general
 if delta<8:errors.append(f"GENERAL_DELTA:{delta}")
 if attest_acts<1:errors.append("NO_ATTESTATION")
 return {"decision":"PASS_REGENERATE_TRIVIAL_SPECIALIST_SCOPED" if not errors else "FAIL_OR_HOLD","errors":errors,"rows":len(rows),"versioned_general_special_schedules":versioned_general,"regen_general_special_schedules":regen_general,"general_call_reduction":delta,"attestation_events":attest_acts}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("raw");ap.add_argument("out");a=ap.parse_args();d=json.loads(pathlib.Path(a.raw).read_text());r=audit(d);pathlib.Path(a.out).write_text(json.dumps(r,sort_keys=True,indent=2)+"\n");print(json.dumps(r,sort_keys=True));raise SystemExit(0 if not r["errors"] else 1)
if __name__=="__main__":main()
