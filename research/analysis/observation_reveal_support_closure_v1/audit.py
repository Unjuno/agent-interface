from __future__ import annotations
import argparse,copy,json
from pathlib import Path
TASK='OBSERVATION-GATING-O3-REVEAL-SUPPORT-CLOSURE-20260919-001'
N=10

def expected():
    configs=3**N; safe=2**N
    return {
      'rows':configs*4,
      'baseline_false_suppressions':configs-safe,
      'baseline_safe_reuses':safe,
      'candidate_false_suppressions':0,
      'candidate_safe_reuses':safe,
      'candidate_ambiguity_raw_fallbacks':configs-safe,
      'candidate_critical_forwards_current':configs,
      'candidate_stale_source_fallbacks':configs*2,
    }

def evaluate(r):
    e=[]
    if r.get('task')!=TASK:e.append('task')
    if r.get('phase')=='construction':
      if not r.get('pass'):e.append('construction')
      if len(r.get('rows',[]))!=7:e.append('construction_rows')
      if any(not x.get('rejected') for x in r.get('malformed',[])):e.append('malformed')
      a=r.get('analytic',{})
      if not a.get('crop_visible_evidence_identical') or not a.get('required_decisions_differ'):e.append('analytic')
      return {'decision':'PASS_CONSTRUCTION_ELIGIBLE' if not e else 'FAIL_CONSTRUCTION','pass':not e,'integrity_errors':e}
    if r.get('phase')!='formal':e.append('phase')
    if (r.get('formal_invocations'),r.get('reruns'),r.get('replacements'),r.get('tuning'))!=(1,0,0,0):e.append('invocation')
    if r.get('metrics')!=expected():e.append('counts')
    a=r.get('analytic',{})
    if not a.get('crop_visible_evidence_identical'):e.append('analytic_inputs')
    if not a.get('required_decisions_differ'):e.append('analytic_decisions')
    if not isinstance(r.get('source_sha256'),dict) or not r['source_sha256']:e.append('source')
    if not isinstance(r.get('ledger_sha256'),str) or len(r['ledger_sha256'])!=64:e.append('ledger')
    return {'decision':'PASS_O3_REVEAL_SUPPORT_CLOSURE_SCOPED' if not e else 'FAIL_INTEGRITY','pass':not e,'integrity_errors':sorted(e),'expected':expected(),'metrics':r.get('metrics',{})}

def controls(r):
    out={}
    def chk(n,fn):
      q=copy.deepcopy(r);fn(q);out[n]=not evaluate(q)['pass']
    chk('baseline_discriminator',lambda q:q['metrics'].__setitem__('baseline_false_suppressions',0))
    chk('candidate_escape',lambda q:q['metrics'].__setitem__('candidate_false_suppressions',1))
    chk('safe_reuse_loss',lambda q:q['metrics'].__setitem__('candidate_safe_reuses',0))
    chk('ambiguity_loss',lambda q:q['metrics'].__setitem__('candidate_ambiguity_raw_fallbacks',0))
    chk('critical_loss',lambda q:q['metrics'].__setitem__('candidate_critical_forwards_current',0))
    chk('analytic_loss',lambda q:q['analytic'].__setitem__('crop_visible_evidence_identical',False))
    chk('source_missing',lambda q:q.__setitem__('source_sha256',{}))
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('result');ap.add_argument('--out');a=ap.parse_args()
    r=json.loads(Path(a.result).read_text());ev=evaluate(r)
    if r.get('phase')=='formal':
      cc=controls(r);ev['corruption_controls']=cc;ev['controls_pass']=all(cc.values());ev['pass']=ev['pass'] and ev['controls_pass']
      if not ev['pass'] and ev['decision'].startswith('PASS_'):ev['decision']='FAIL_INTEGRITY'
    s=json.dumps(ev,indent=2,sort_keys=True)+'\n';print(s,end='')
    if a.out:Path(a.out).write_text(s)
    raise SystemExit(0 if ev['pass'] else 4)
if __name__=='__main__':main()
