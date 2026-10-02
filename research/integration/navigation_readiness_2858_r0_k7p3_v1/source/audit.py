import argparse,json,statistics
from pathlib import Path
POL=['NO_EXTRA_WAIT','FIXED_100MS','REOBSERVE_ACTIVE']; LOAD=['IDLE','CONTENDED']; PHASE=['FRESH','SEQUENTIAL']
def audit(root):
 root=Path(root); errors=[]; checks=0; cases=[]; launch=json.loads((root/'LAUNCHER.json').read_text()); checks+=1
 if len(launch)!=24: errors.append('launcher_count')
 for lr in launch:
  checks+=2
  if lr['returncode']!=0: errors.append('launcher_nonzero:'+lr['case_id'])
  p=root/lr['case_id']/'CASE.json'
  if not p.exists(): errors.append('missing_case:'+lr['case_id']); continue
  c=json.loads(p.read_text()); cases.append(c); checks+=3
  if c.get('status')!='complete_measurement': errors.append('case_status:'+lr['case_id'])
  if c['policy']!=lr['policy'] or c['load']!=lr['load'] or c['phase']!=lr['phase']: errors.append('identity:'+lr['case_id'])
  if c['phase']=='SEQUENTIAL':
   checks+=2
   if not c.get('setup',{}).get('ready'): errors.append('setup_not_ready:'+lr['case_id'])
   if c.get('setup',{}).get('policy')!='FIXED_100MS': errors.append('setup_policy:'+lr['case_id'])
  m=c.get('measurement'); checks+=4
  if not isinstance(m,dict): errors.append('missing_measurement:'+lr['case_id']); continue
  if m.get('policy')!=c['policy']: errors.append('measurement_policy:'+lr['case_id'])
  if m.get('ready'):
   if m.get('ready_ns') is None or m['ready_ns']<m['enter_done_ns']: errors.append('time_order:'+lr['case_id'])
   if m['elapsed_total_ms']<0 or m['enter_to_ready_ms']<0: errors.append('negative_time:'+lr['case_id'])
  else:
   if m.get('failure') is None: errors.append('untyped_failure:'+lr['case_id'])
  names={x['name'] for x in c.get('processes',[])}; checks+=1
  if not {'xvfb','openbox','chromium'}.issubset(names): errors.append('processes:'+lr['case_id'])
 by={}
 for ph in PHASE:
  for load in LOAD:
   for pol in POL:
    rows=[c['measurement'] for c in cases if c['phase']==ph and c['load']==load and c['policy']==pol]; key='|'.join([ph,load,pol]); checks+=1
    if len(rows)!=2: errors.append('cell_n:'+key)
    ready=sum(bool(x.get('ready')) for x in rows); vals=[x['elapsed_total_ms'] for x in rows if x.get('ready')]
    by[key]={'n':len(rows),'ready':ready,'median_total_ms':statistics.median(vals) if vals else None,'failures':[x.get('failure') for x in rows if not x.get('ready')]}
 discr=[]
 for ph in PHASE:
  for load in LOAD:
   z=by['|'.join([ph,load,'NO_EXTRA_WAIT'])]; f=by['|'.join([ph,load,'FIXED_100MS'])]
   if z['ready']==0 and f['ready']==2: discr.append(ph+'|'+load)
 if errors: decision='HOLD_INTEGRITY'
 elif discr: decision='PASS_FIXED_WAIT_DISCRIMINATES_SCOPED'
 else: decision='HOLD_WAIT_BENEFIT_NOT_ESTABLISHED'
 return {'checks':checks,'errors':errors,'cases':len(cases),'measurements':len(cases),'by_cell':by,'discriminating_strata':discr,'decision':decision}
if __name__=='__main__':
 ap=argparse.ArgumentParser(); ap.add_argument('root'); a=ap.parse_args(); print(json.dumps(audit(a.root),indent=2,sort_keys=True))
