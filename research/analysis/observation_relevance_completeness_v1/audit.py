from __future__ import annotations
import argparse,copy,json
from pathlib import Path

TASK='OBSERVATION-GATING-O3-RELEVANCE-COMPLETENESS-20260918-001'
N=6


def expected_counts():
    return {
      'rows':(2**N)*(2**N)*N*2,
      'unsafe_false_suppressions':N*(2**(N-1))*(2**(N-1)),
      'unsafe_true_suppressions':N*(2**(N-1))*(2**(N-1)),
      'complete_only_false_suppressions_truthful':0,
      'complete_only_true_suppressions_truthful':N*(2**(N-1)),
      'partial_suppressions':0,
      'unknown_suppressions':0,
      'forged_complete_false_suppressions':N*(2**(N-1))*(2**(N-1)),
      'stale_suppressions':0,
    }


def evaluate(r:dict)->dict:
    errors=[]
    if r.get('task')!=TASK:errors.append('task')
    if r.get('phase')!='formal':errors.append('phase')
    if (r.get('formal_invocations'),r.get('reruns'),r.get('replacements'),r.get('tuning'))!=(1,0,0,0):errors.append('invocation_contract')
    if r.get('metrics')!=expected_counts():errors.append('counts')
    a=r.get('analytic',{})
    if not a.get('inputs_identical'):errors.append('analytic_inputs')
    if not a.get('required_decisions_differ'):errors.append('analytic_decisions')
    if not a.get('x_outside_declared'):errors.append('analytic_x')
    if not isinstance(r.get('source_sha256'),dict) or not r['source_sha256']:errors.append('source_manifest')
    if not isinstance(r.get('ledger_sha256'),str) or len(r['ledger_sha256'])!=64:errors.append('ledger')
    return {'decision':'PASS_O3_RELEVANCE_COMPLETENESS_SCOPED' if not errors else 'FAIL_INTEGRITY','pass':not errors,'integrity_errors':sorted(errors),'expected_counts':expected_counts(),'metrics':r.get('metrics',{})}


def corruption_controls(r:dict)->dict:
    out={}
    def check(name,fn):
        q=copy.deepcopy(r);fn(q);out[name]=not evaluate(q)['pass']
    check('unsafe_escape_erased',lambda q:q['metrics'].__setitem__('unsafe_false_suppressions',0))
    check('truthful_escape',lambda q:q['metrics'].__setitem__('complete_only_false_suppressions_truthful',1))
    check('safe_suppression_loss',lambda q:q['metrics'].__setitem__('complete_only_true_suppressions_truthful',0))
    check('partial_suppression',lambda q:q['metrics'].__setitem__('partial_suppressions',1))
    check('forged_control_loss',lambda q:q['metrics'].__setitem__('forged_complete_false_suppressions',0))
    check('analytic_input_loss',lambda q:q['analytic'].__setitem__('inputs_identical',False))
    check('source_missing',lambda q:q.__setitem__('source_sha256',{}))
    return out


def main():
    ap=argparse.ArgumentParser();ap.add_argument('result');ap.add_argument('--out');a=ap.parse_args()
    r=json.loads(Path(a.result).read_text());ev=evaluate(r);cc=corruption_controls(r);ev['corruption_controls']=cc;ev['controls_pass']=all(cc.values());ev['pass']=ev['pass'] and ev['controls_pass']
    if not ev['pass'] and ev['decision'].startswith('PASS_'):ev['decision']='FAIL_INTEGRITY'
    s=json.dumps(ev,indent=2,sort_keys=True)+'\n';print(s,end='')
    if a.out:Path(a.out).write_text(s)
    raise SystemExit(0 if ev['pass'] else 4)
if __name__=='__main__':main()
