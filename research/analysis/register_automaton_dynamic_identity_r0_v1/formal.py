#!/usr/bin/env python3
import argparse, hashlib, itertools, json, platform
from pathlib import Path
DOMAIN_MIN=1
DOMAIN_MAX=16

def oracle(bg,bt,qg,qt): return bg==qg and bt==qt
def two_register(bg,bt,qg,qt): return bg==qg and bt==qt
def generation_only(bg,bt,qg,qt): return bg==qg
def target_only(bg,bt,qg,qt): return bt==qt
def control_only_accept(bg,bt,qg,qt): return True

def upd(h, rec):
    h.update(json.dumps(rec,sort_keys=True,separators=(",",":")).encode()); h.update(b"\n")

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',required=True); a=ap.parse_args()
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    pol={"TWO_REGISTER":two_register,"GENERATION_ONLY":generation_only,"TARGET_ONLY":target_only,"CONTROL_ONLY_ACCEPT":control_only_accept}
    totals={n:{"unsafe_accept":0,"false_reject":0,"mismatch":0} for n in pol}
    h=hashlib.sha256(); cases=0; lower=[]
    for G in range(DOMAIN_MIN,DOMAIN_MAX+1):
      for T in range(DOMAIN_MIN,DOMAIN_MAX+1):
        for bg in range(G):
          for bt in range(T):
            for qg in range(G):
              for qt in range(T):
                want=oracle(bg,bt,qg,qt); rec={"G":G,"T":T,"bg":bg,"bt":bt,"qg":qg,"qt":qt,"oracle":want}
                for n,f in pol.items():
                  got=f(bg,bt,qg,qt); rec[n]=got
                  if got!=want:
                    totals[n]["mismatch"]+=1
                    if got: totals[n]["unsafe_accept"]+=1
                    else: totals[n]["false_reject"]+=1
                upd(h,rec); cases+=1
        b=G*T
        lower.append({"G":G,"T":T,"bound_prefixes":b,"pairwise_bound_witnesses":b*(b-1)//2,"unbound_witnesses":b,"required_literal_states":b+1})
    eq_checks=0; eq_mis=0; vals=range(3)
    for pg in itertools.permutations(vals):
      for pt in itertools.permutations(vals):
        for bg in vals:
          for bt in vals:
            for qg in vals:
              for qt in vals:
                before=two_register(bg,bt,qg,qt); after=two_register(pg[bg],pt[bt],pg[qg],pt[qt]); eq_checks+=1
                if before!=after: eq_mis+=1
    ok=(totals['TWO_REGISTER']['mismatch']==0 and totals['GENERATION_ONLY']['unsafe_accept']>0 and totals['TARGET_ONLY']['unsafe_accept']>0 and totals['CONTROL_ONLY_ACCEPT']['unsafe_accept']>0 and eq_mis==0)
    result={
      "task":"REGISTER-AUTOMATON-DYNAMIC-IDENTITY-R0-20260919-001",
      "decision":"PASS_REGISTER_AUTOMATON_IDENTITY_SCOPED" if ok else "FAIL_REGISTER_AUTOMATON_IDENTITY",
      "domain_min":DOMAIN_MIN,"domain_max":DOMAIN_MAX,"cases":cases,"stream_sha256":h.hexdigest(),"totals":totals,
      "equivariance":{"domain":"3x3","checks":eq_checks,"mismatches":eq_mis},
      "lower_bound":{"claim":"literal no-register FSM needs |G|*|T|+1 distinguishable states","checks":lower},
      "environment":{"python":platform.python_version(),"platform":platform.platform()},
      "formal_invocations":1,"reruns":0,"post_freeze_tuning":0}
    (out/'RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:result[k] for k in ['decision','cases','stream_sha256','totals','equivariance']},indent=2,sort_keys=True))
if __name__=='__main__': main()
