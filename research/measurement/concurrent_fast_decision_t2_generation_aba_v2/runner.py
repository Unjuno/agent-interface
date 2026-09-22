import argparse, hashlib, json, random, time
from model import Candidate, StateOnlyComparator
from oracle import Oracle
SEED=145920260918012
N=200_000
SCOPES=["A","B","C","D"]

# 10 deterministic trace classes; first two are explicit ABA stale attempts = 40%.
CLASSES=["ABA_CLEAR","ABA_BOUNCE","FRESH_G2","WATCH","HARD","AUTH_FALSE","REPLAY","CROSS_SCOPE","FORGED_GEN","DUP_RETURN"]

def snap_candidate(c):
    return {
      "scope": {k:{"gen":v.generation,"open":v.open,"state":v.state,"returns":sorted(v.closed_events)} for k,v in sorted(c.scopes.items())},
      "prepared": {k:{"scope":v.scope,"gen":v.generation,"state":v.state,"used":v.consumed} for k,v in sorted(c.prepared.items())},
      "effects": list(c.effects),
    }

def call_pair(c,o,op,*args,**kwargs):
    if op=="req": cr=c.frontier_request(*args); oo=o.req(*args); ok=cr.get("ok") == oo[0]
    elif op=="obs": cr=c.observe(*args); oo=o.obs(*args); ok=cr.get("ok") == oo[0]
    elif op=="prep": cr=c.prepare(*args); oo=o.prep(*args); ok=cr.get("ok") == oo[0]
    elif op=="ret": cr=c.frontier_return(*args); oo=o.ret(*args); ok=cr.get("ok") == oo[0]
    elif op=="admit": cr=c.try_admit(*args,**kwargs); oo=o.admit(*args,**kwargs); ok=cr.get("admit") == oo
    else: raise AssertionError(op)
    return cr, ok and snap_candidate(c)==o.snapshot()

def trace(i, klass):
    scope=SCOPES[i%4]; other=SCOPES[(i+1)%4]
    c=Candidate(); o=Oracle(); comp=StateOnlyComparator()
    mismatch=0
    def both(op,*a,**kw):
      nonlocal mismatch
      r,ok=call_pair(c,o,op,*a,**kw)
      if not ok: mismatch+=1
      return r
    # g1 clear prepare
    both("req",scope); both("obs",scope,"CLEAR"); both("prep",scope,f"d1-{i}")
    # mirror setup in comparator
    comp.frontier_request(scope); comp.observe(scope,"CLEAR"); comp.prepare(scope,f"d1-{i}")
    both("ret",scope,f"ret1-{i}"); comp.frontier_return(scope,f"ret1-{i}")
    stale_attempt=False; stale_candidate=False; stale_comparator=False; fresh_effect=False
    if klass in ("ABA_CLEAR","ABA_BOUNCE","FRESH_G2","REPLAY","CROSS_SCOPE","FORGED_GEN"):
      both("req",scope); comp.frontier_request(scope)
    if klass=="ABA_CLEAR":
      both("obs",scope,"CLEAR"); comp.observe(scope,"CLEAR")
      stale_attempt=True; stale_candidate=both("admit",scope,f"d1-{i}",True)["admit"]; stale_comparator=comp.try_admit(scope,f"d1-{i}",True)["admit"]
    elif klass=="ABA_BOUNCE":
      both("obs",scope,"WATCH"); comp.observe(scope,"WATCH"); both("obs",scope,"CLEAR"); comp.observe(scope,"CLEAR")
      stale_attempt=True; stale_candidate=both("admit",scope,f"d1-{i}",True)["admit"]; stale_comparator=comp.try_admit(scope,f"d1-{i}",True)["admit"]
    elif klass=="FRESH_G2":
      both("obs",scope,"CLEAR"); comp.observe(scope,"CLEAR"); both("prep",scope,f"d2-{i}"); comp.prepare(scope,f"d2-{i}")
      fresh_effect=both("admit",scope,f"d2-{i}",True)["admit"]
    elif klass=="WATCH":
      both("req",scope); both("obs",scope,"WATCH"); both("prep",scope,f"w-{i}"); fresh_effect=both("admit",scope,f"w-{i}",True)["admit"]
    elif klass=="HARD":
      both("req",scope); both("obs",scope,"HARD"); both("prep",scope,f"h-{i}"); fresh_effect=both("admit",scope,f"h-{i}",True)["admit"]
    elif klass=="AUTH_FALSE":
      both("req",scope); both("obs",scope,"CLEAR"); both("prep",scope,f"a-{i}"); fresh_effect=both("admit",scope,f"a-{i}",False)["admit"]
    elif klass=="REPLAY":
      both("obs",scope,"CLEAR"); both("prep",scope,f"d2-{i}"); fresh_effect=both("admit",scope,f"d2-{i}",True)["admit"]; both("admit",scope,f"d2-{i}",True)
    elif klass=="CROSS_SCOPE":
      both("obs",scope,"CLEAR"); stale_attempt=True; stale_candidate=both("admit",other,f"d1-{i}",True)["admit"]
    elif klass=="FORGED_GEN":
      both("obs",scope,"CLEAR"); stale_attempt=True; stale_candidate=both("admit",scope,f"d1-{i}",True,claimed_generation=999999)["admit"]
    elif klass=="DUP_RETURN":
      # duplicate already-closed event must not advance/reclose
      r=both("ret",scope,f"ret1-{i}")
      if r.get("ok"): mismatch+=1
    return {"i":i,"class":klass,"mismatch":mismatch,"stale_attempt":stale_attempt,"stale_candidate":stale_candidate,"stale_comparator":stale_comparator,"fresh_effect":fresh_effect,"candidate_effects":len(c.effects)}

def main():
  ap=argparse.ArgumentParser(); ap.add_argument("--out",required=True); a=ap.parse_args()
  rng=random.Random(SEED); classes=[]
  # Exactly 40k explicit ABA: 20k each. Remaining classes uniformly 20k each.
  for k in CLASSES: classes.extend([k]*20_000)
  rng.shuffle(classes)
  t0=time.monotonic_ns(); rows=[]; counts={k:0 for k in CLASSES}
  for i,k in enumerate(classes):
    r=trace(i,k); rows.append(r); counts[k]+=1
  summary={
    "allocation":"issue1460-generation-aba-v2-20260922-01","seed":SEED,"traces":len(rows),"class_counts":counts,
    "mismatches":sum(r["mismatch"] for r in rows),
    "aba_stale_attempts":sum(r["stale_attempt"] and r["class"] in ("ABA_CLEAR","ABA_BOUNCE") for r in rows),
    "candidate_stale_effects":sum(r["stale_candidate"] for r in rows),
    "comparator_stale_effects":sum(r["stale_comparator"] for r in rows),
    "fresh_g2_effects":sum(r["fresh_effect"] and r["class"]=="FRESH_G2" for r in rows),
    "watch_hard_authfalse_effects":sum(r["fresh_effect"] and r["class"] in ("WATCH","HARD","AUTH_FALSE") for r in rows),
    "elapsed_ns":time.monotonic_ns()-t0,
  }
  summary["decision"]="PASS_T2_GENERATION_ABA_GUARD_SCOPED" if (
    summary["mismatches"]==0 and summary["aba_stale_attempts"]>=40_000 and summary["candidate_stale_effects"]==0 and
    summary["comparator_stale_effects"]>0 and summary["fresh_g2_effects"]>0 and summary["watch_hard_authfalse_effects"]==0
  ) else "FAIL_T2_GENERATION_ABA_GUARD"
  payload={"summary":summary,"rows":rows}
  raw=json.dumps(payload,sort_keys=True,separators=(",",":"))
  with open(a.out,"w",encoding="utf-8") as f: f.write(raw+"\n")
  print(json.dumps(summary,sort_keys=True))
if __name__=="__main__": main()
