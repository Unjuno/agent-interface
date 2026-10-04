import json,pathlib
from saved_oracle import score_done
R=pathlib.Path(__file__).resolve().parent;P=json.loads((R/'PLAN.json').read_text(encoding='utf-8'));rows=[];errors=[];groups={0:[],50:[]}
for spec in P['rows']:
 D=R/'runs'/('row'+str(spec['index']+1));bad=[]
 if not (D/'raw.json').exists():errors.append('missing row '+str(spec['index']));continue
 raw=json.loads((D/'raw.json').read_text(encoding='utf-8'));host=json.loads((D/'HOST_RECEIPT.json').read_text(encoding='utf-8'))
 if raw['errors'] or host['errors'] or host.get('exit_code')!=0:bad.append('native/host infrastructure')
 if raw['source_hashes']!=P['source_hashes'] or raw['spec']!=spec:bad.append('source/row identity')
 if [t['label'] for t in raw.get('tasks',[])]!=['prime','trial']:bad.append('exact2 native dispatch inventory')
 task_reports=[]
 for row in raw.get('tasks',[]):
  score=score_done(D,row);bad.extend(e for e in score['errors'] if e!='saved effect or collateral cell content')
  if row['label']=='prime' and not score['effect']['pass_effect']:bad.append('priming effect')
  if row['label']=='trial' and (row['a'],row['b'],row['x'],row['y'],row['click_wait_ms'])!=(73,79,82,168,spec['click_wait_ms']):bad.append('exact trial parameters')
  ops=row['program']['ops'];prefix=[dict(op='focus',target='owned'),dict(op='pointer_move',frame='screen_physical_px',x=row['x'],y=row['y']),dict(op='pointer_button',button='left',down=True),dict(op='pointer_button',button='left',down=False)]
  if ops[:4]!=prefix or (row['click_wait_ms'] and ops[4]!=dict(op='wait_update',timeout_ms=row['click_wait_ms'])) or (not row['click_wait_ms'] and ops[4]!=dict(op='text',text='7')):bad.append('exact click/wait/text boundary')
  execution=row['receipt']['execution'];releases=execution.get('releases',[])
  if not releases or not all(v.get('verified') is True and v.get('keys_down')==[] and v.get('buttons_down')==[] for v in releases):bad.append('public release')
  if execution['completed_ops']!=list(range(len(ops))):bad.append('complete operations')
  task_reports.append(dict(label=row['label'],effect=score['effect'],dispatch_ms=(row['end_ns']-row['start_ns'])/1e6))
 cleanup=raw.get('cleanup_physical')
 if not cleanup or cleanup['keys'] or cleanup['buttons']:bad.append('cleanup neutral unavailable/fail')
 if len(raw.get('terminal',[]))!=3 or any(x['exit_code'] not in (0,255) for x in raw.get('terminal',[])):bad.append('helper parent termination')
 trial=next((t for t in task_reports if t['label']=='trial'),None)
 if trial:groups[spec['click_wait_ms']].append(trial['effect']['pass_effect'])
 rows.append(dict(index=spec['index'],click_wait_ms=spec['click_wait_ms'],tasks=task_reports,errors=bad));errors.extend(bad)
complete=len(rows)==8 and not errors;zero=sum(groups[0]);fifty=sum(groups[50]);signal=complete and zero<4 and fifty==4
result=dict(allocation=P['allocation'],disposition='SCOPED_BOUNDARY_SIGNAL_MECHANISM_UNPROVEN' if signal else 'HOLD_INCOMPLETE_OR_NO_BOUNDARY_SIGNAL',errors=errors,rows=rows,success_counts={'0ms':zero,'50ms':fifty},model_calls=0,original_A01_replayed=False,limits=['fresh model-free diagnostic, not original formal regrade','Calc internal event routing/semantic readiness unobserved','no universal wait/default adoption or whole integration/token result','cell-content oracle excludes formatting/unobserved effects','parent terminal/neutral records not full descendant proof'])
p=R/'AUDIT.json'
if p.exists():raise RuntimeError('first audit path exists')
p.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result));raise SystemExit(bool(errors))
