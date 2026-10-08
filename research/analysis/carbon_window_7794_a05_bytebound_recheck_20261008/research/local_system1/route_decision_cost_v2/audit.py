import hashlib,json,math,sys
from pathlib import Path
LABELS={'CTRL_WHEEL','NATIVE_SCALE','STALE_CAPABILITY','UNSUPPORTED'}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 r=json.loads(Path('FORMAL_RESULT.json').read_text()); errs=[]
 if r.get('formal_invocation')!=1 or r.get('reruns')!=0: errs.append('invocation')
 if set(r.get('labels',[]))!=LABELS: errs.append('labels')
 b=r['backends']; ex=r['extraction_only_us']; r95=b['RULE']['end_to_end_us']['p95']
 for n in ['RULE','LINEAR','TREE']:
  if b[n]['backend_errors']!=0 or b[n]['end_to_end_errors']!=0: errs.append('correctness_'+n)
  for phase in ['backend_only_us','end_to_end_us']:
   x=b[n][phase]
   if not (0<=x['p50']<=x['p95']<=x['p99']<=x['max']): errs.append('quantiles_'+n+'_'+phase)
  if b[n]['end_to_end_us']['p95']>=1000: errs.append('under1ms_'+n)
 if r95>=25: errs.append('rule25')
 ef=ex['p95']/r95; lr=b['LINEAR']['end_to_end_us']['p95']/r95; tr=b['TREE']['end_to_end_us']['p95']/r95
 if ef<0.5: errs.append('extract_fraction')
 if lr<3: errs.append('linear_ratio')
 if tr<3: errs.append('tree_ratio')
 if any(r.get(k)!=0 for k in ['network_calls','gradient_updates','task_input_calls','authority_grants']): errs.append('side_effect')
 expected='PASS_REAL_TYPED_DECISION_COST_SCOPED' if not errs else ('REJECT_LOCAL_DECISION_COST' if r95>=1000 else 'HOLD_WRAPPER_OVERHEAD_NOT_STABLE')
 if r.get('decision')!=expected: errs.append('decision')
 out={'audit':'PASS' if not errs else 'FAIL','errors':errs,'decision':r.get('decision'),'rule_p95_us':r95,'extraction_fraction':ef,'linear_ratio':lr,'tree_ratio':tr,'result_sha256':sha('FORMAL_RESULT.json')}
 print(json.dumps(out,sort_keys=True)); sys.exit(0 if not errs else 1)
if __name__=='__main__': main()
