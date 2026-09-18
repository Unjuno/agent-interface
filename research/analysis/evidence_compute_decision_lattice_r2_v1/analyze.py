from fractions import Fraction as F
from itertools import product
import argparse,hashlib,json
from pathlib import Path
KINDS=('CACHED_COMPLETE','ACTIVE_JOB')
TIME=tuple(F(i,2) for i in range(5)) # 0..2 by .5
P=tuple(F(i,4) for i in range(5)) # 0..1
COST=tuple(F(i,1) for i in range(3)) # 0,1,2
OUT=('REUSE','DROP_EXPIRED','REBUILD_REQUIRED','CANCEL_STALE','CANCEL_TARDY','RUN','WAIT','TIE')

def economic(p,g,w):
    r=p*w;q=(1-p)*g
    return 'RUN' if r<q else ('WAIT' if r>q else 'TIE')

def lattice(kind,match,t,c,d,p,g,w):
    if kind=='CACHED_COMPLETE':
        if not match:return 'REBUILD_REQUIRED'
        if t>d:return 'DROP_EXPIRED'
        return 'REUSE'
    if kind!='ACTIVE_JOB':raise ValueError('kind')
    if not match:return 'CANCEL_STALE'
    if t+c>d:return 'CANCEL_TARDY'
    return economic(p,g,w)

def oracle(kind,match,t,c,d,p,g,w):
    if kind=='CACHED_COMPLETE':
        return 'REBUILD_REQUIRED' if not match else ('DROP_EXPIRED' if t>d else 'REUSE')
    if not match:return 'CANCEL_STALE'
    if t+c>d:return 'CANCEL_TARDY'
    rc=p*w;wc=(1-p)*g
    if rc<wc:return 'RUN'
    if rc>wc:return 'WAIT'
    return 'TIE'

def directed():
    return {
      'cached_exact_deadline':lattice('CACHED_COMPLETE',True,F(1),F(0),F(1),F(1),F(9),F(0))=='REUSE',
      'cached_expired':lattice('CACHED_COMPLETE',True,F(2),F(0),F(1),F(0),F(9),F(0))=='DROP_EXPIRED',
      'cached_mismatch':lattice('CACHED_COMPLETE',False,F(0),F(0),F(2),F(0),F(99),F(0))=='REBUILD_REQUIRED',
      'active_stale':lattice('ACTIVE_JOB',False,F(0),F(1),F(2),F(0),F(99),F(0))=='CANCEL_STALE',
      'active_tardy':lattice('ACTIVE_JOB',True,F(1),F(2),F(2),F(0),F(99),F(0))=='CANCEL_TARDY',
      'active_tie_deadline':lattice('ACTIVE_JOB',True,F(1),F(1),F(2),F(1,2),F(1),F(1))=='TIE',
      'zero_zero':lattice('ACTIVE_JOB',True,F(0),F(1),F(2),F(3,4),F(0),F(0))=='TIE',
    }

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--construction',action='store_true');ap.add_argument('--output',required=True);a=ap.parse_args();o=Path(a.output);assert not o.exists()
    tv=TIME[:3] if a.construction else TIME;pv=P[:3] if a.construction else P;cv=COST[:2] if a.construction else COST
    rows=0;mis=0;counts={k:0 for k in OUT};invalid_reuse=0;invalid_rebuild=0;hard_override=0;selector_mis=0;rebuild_bypass=0;unknown=0
    for kind,match,t,c,d,p,g,w in product(KINDS,(False,True),tv,tv,tv,pv,cv,cv):
        x=lattice(kind,match,t,c,d,p,g,w);y=oracle(kind,match,t,c,d,p,g,w);rows+=1;mis+=int(x!=y);unknown+=int(x not in OUT);counts[x]+=1
        invalid_reuse+=int(x=='REUSE' and not (kind=='CACHED_COMPLETE' and match and t<=d))
        invalid_rebuild+=int(x=='REBUILD_REQUIRED' and not (kind=='CACHED_COMPLETE' and not match))
        rebuild_bypass+=int(kind=='CACHED_COMPLETE' and not match and x in ('RUN','WAIT','TIE'))
        if kind=='ACTIVE_JOB' and ((not match) or t+c>d):hard_override+=int(x in ('RUN','WAIT','TIE'))
        if kind=='ACTIVE_JOB' and match and t+c<=d:selector_mis+=int(x!=economic(p,g,w))
    dc=directed()
    corruptions={
      'expired_reuse_rejected':lattice('CACHED_COMPLETE',True,F(2),F(0),F(1),F(0),F(10),F(0))!='REUSE',
      'mismatched_reuse_rejected':lattice('CACHED_COMPLETE',False,F(0),F(0),F(2),F(0),F(10),F(0))=='REBUILD_REQUIRED',
      'stale_utility_override_rejected':lattice('ACTIVE_JOB',False,F(0),F(1),F(2),F(0),F(10),F(0))=='CANCEL_STALE',
      'tardy_utility_override_rejected':lattice('ACTIVE_JOB',True,F(1),F(2),F(2),F(0),F(10),F(0))=='CANCEL_TARDY',
      'rebuild_run_bypass_rejected':lattice('CACHED_COMPLETE',False,F(0),F(0),F(2),F(0),F(10),F(0)) not in ('RUN','WAIT','TIE'),
    }
    good=(mis==0 and invalid_reuse==0 and invalid_rebuild==0 and hard_override==0 and selector_mis==0 and rebuild_bypass==0 and unknown==0 and all(dc.values()) and all(corruptions.values()))
    r={'construction':a.construction,'rows':rows,'decision_counts':counts,'candidate_oracle_mismatch':mis,'invalid_reuse':invalid_reuse,'invalid_rebuild_required':invalid_rebuild,'hard_gate_override':hard_override,'active_selector_mismatch':selector_mis,'rebuild_direct_run_wait_bypass':rebuild_bypass,'unknown_dispositions':unknown,'directed_controls':dc,'corruption_controls':corruptions,'formal_invocations':0 if a.construction else 1,'reruns':0,'replacements':0,'tuning':0,'decision':('CONSTRUCTION_PASS' if a.construction and good else ('PASS_EVIDENCE_COMPUTE_DECISION_LATTICE_SCOPED' if good else 'FAIL_INTEGRITY'))}
    raw=json.dumps(r,sort_keys=True,separators=(',',':')).encode();r['digest']=hashlib.sha256(raw).hexdigest();o.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,indent=2,sort_keys=True))
if __name__=='__main__':main()
