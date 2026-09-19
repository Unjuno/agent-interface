import json,hashlib,argparse
from pathlib import Path

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--result',required=True); ap.add_argument('--freeze',required=True); ap.add_argument('--output',required=True); a=ap.parse_args()
    r=json.loads(Path(a.result).read_text()); f=json.loads(Path(a.freeze).read_text())
    specific=('TIMING','EVENT_SHAPE','FOCUS','EFFECT_SHAPE','COMPOSITE')
    checks={
      'decision':r['decision']=='PASS_PROVENANCE_FREE_ACTOR_INDISTINGUISHABILITY_SCOPED',
      'cardinality':r['pairs']==384 and r['histories']==768,
      'identical':r['identical_observable_pairs']==384,
      'forced_error':all(r['heuristics'][n]['errors']>=384 for n in specific),
      'unattributed_safe':r['heuristics']['UNATTRIBUTED']['false_specific_claims']==0,
      'witness':r['trusted_witness_pairs_separated']==384 and r['trusted_witness_errors']==0,
      'authority':r['authority_promotions']==0 and r['task_success_promotions']==0,
      'formal':r['formal_invocations']==1 and r['reruns']==0,
      'formal_source':sha('formal.py')==f['sha256']['formal.py'],
      'proof_source':sha('PROOF.md')==f['sha256']['PROOF.md'],
      'plan_source':sha('PLAN.md')==f['sha256']['PLAN.md'],
      'audit_source':sha('audit.py')==f['sha256']['audit.py'],
    }
    out={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'result_sha256':sha(a.result),'freeze_sha256':sha(a.freeze)}
    Path(a.output).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True))
    raise SystemExit(0 if out['status']=='PASS' else 1)
if __name__=='__main__': main()
