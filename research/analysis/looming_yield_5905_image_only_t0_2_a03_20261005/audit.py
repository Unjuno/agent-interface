import json,math,sys
from candidate import analyze,PIX,GROW,TTC

def audit(obs,truth,raw):
 errors=[]; seqs={s['sequence_id']:s for s in obs['sequences']}; got={r['sequence_id']:r for r in raw['sequences']}
 if len(seqs)!=13 or set(seqs)!=set(got): errors.append('sequence_set')
 for sid,s in seqs.items():
  try:
   independent=analyze(s); r=got[sid]
   for key in ('status','reason','gate','metrics','pixel_grid','growth_grid','ttc_grid'):
    if independent[key]!=r[key]: errors.append('reconstruct:'+sid+':'+key)
   if independent['features']!=r['features']: errors.append('features:'+sid)
   if len(s['frames'])!=5: errors.append('frame_count:'+sid)
  except Exception as e: errors.append('decode:'+sid+':'+type(e).__name__)
 pos=set(truth['contact_cases']); allneg=set(truth['control_labels']); twin={'animation-twin-1'}; controls=allneg-twin
 front={}
 for method in ('pixel','growth','ttc'):
  grid_key=method+'_grid'; thresholds=list(got['approach-1'][grid_key]); points=[]
  for th in thresholds:
   tp=sum(bool(got[x][grid_key][th]) for x in pos); fp=sum(bool(got[x][grid_key][th]) for x in controls)
   points.append({'threshold':th,'tp':tp,'fp':fp})
  front[method]={'points':points,'max_tp_at_fp_0':max([x['tp'] for x in points if x['fp']==0] or [0])}
 for sid in controls:
  r=got[sid]
  if r['status']!='UNKNOWN' or any(r[k+'_grid'][th] for k,ths in [('pixel',PIX),('growth',GROW),('ttc',TTC)] for th in map(str,ths)): errors.append('control_gate:'+sid)
 for sid in pos:
  r=got[sid]; end=r['features'][-1]['t_s']+r['yield_latency_s']; lead=truth['contact_cases'][sid]['contact_at_s']-end
  if r['status']!='TRACKABLE' or not any(r['ttc_grid'].values()) or lead<=0: errors.append('approach_release:'+sid)
 a=seqs['approach-1']; b=seqs['animation-twin-1']
 if [(x['t_s'],x['track_id'],x['pgm_b64']) for x in a['frames']] != [(x['t_s'],x['track_id'],x['pgm_b64']) for x in b['frames']]: errors.append('twin_input_not_identical')
 elif got['approach-1']!=got['animation-twin-1']: errors.append('twin_output_mismatch')
 if front['ttc']['max_tp_at_fp_0']<=max(front['pixel']['max_tp_at_fp_0'],front['growth']['max_tp_at_fp_0']): errors.append('no_increment_at_equal_false_yield')
 return {'audit':'PASS_RAW_RECONSTRUCTION' if not errors else 'FAIL_RAW_RECONSTRUCTION','errors':errors,'frontier':front,'identifiability_twin':'MATCHED_OUTPUTS' if got['approach-1']==got['animation-twin-1'] else 'MISMATCH','false_yield_allowance_identifiable_controls':0,'disposition':'PASS_METHOD_SCOPED_WITH_IDENTIFIABILITY_LIMIT' if not errors else 'FAIL_OR_STOP'}

if __name__=='__main__':
 obs=json.load(open(sys.argv[1],encoding='utf8')); truth=json.load(open(sys.argv[2],encoding='utf8')); raw=json.load(open(sys.argv[3],encoding='utf8')); result=audit(obs,truth,raw)
 with open(sys.argv[4],'w',encoding='utf8',newline='\n') as f: json.dump(result,f,sort_keys=True,indent=2); f.write('\n')
 print(json.dumps({'audit':result['audit'],'errors':result['errors'],'disposition':result['disposition']})); sys.exit(0 if not result['errors'] else 1)
