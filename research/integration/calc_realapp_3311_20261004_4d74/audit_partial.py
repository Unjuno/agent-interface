import hashlib,json,pathlib,sys
from saved_oracle import score_done
R=pathlib.Path(__file__).resolve().parent;P=json.loads((R/'PLAN.json').read_text(encoding='utf-8'));reports=[];errors=[];totals={m:{} for m in ('direct','persistent')};threads=[]
for index,mode in enumerate(P['sessions']):
 O=R/'runs'/('session'+str(index+1)+'-'+mode);bad=[];stages=[]
 if not (O/'SESSION.json').exists() or not (O/'raw.json').exists():errors.append('missing session '+str(index));continue
 host=json.loads((O/'SESSION.json').read_text(encoding='utf-8'));raw=json.loads((O/'raw.json').read_text(encoding='utf-8'))
 if host['errors'] or raw['errors'] or host.get('native_exit')!=0:bad.append('host/native error or nonzero exit')
 if raw['source_hashes']!=P['source_hashes']:bad.append('source pins')
 if len(raw.get('tasks',[]))!=6:bad.append('six saved tasks')
 expected_labels=['task'+str(i)+('-repair' if mode=='persistent' and i==3 else '') for i in range(6)]
 if [r['label'] for r in raw.get('tasks',[])]!=expected_labels:bad.append('exact task labels')
 for row in raw.get('tasks',[]):
  try:
   score=score_done(O,row);bad.extend(score['errors']);execution=row['receipt']['execution'];releases=execution.get('releases',[])
   if not releases or not all(x.get('verified') is True and x.get('keys_down')==[] and x.get('buttons_down')==[] for x in releases):bad.append('public verified release')
   if execution['completed_ops']!=list(range(len(row['program']['ops']))):bad.append('complete native program')
  except Exception as e:bad.append('saved row malformed '+repr(e))
 refused=[r for r in raw['guard_attempts'] if r['decision']!='ACCEPT']
 if mode=='persistent':
  if len(refused)!=1 or refused[0]['label']!='task3' or refused[0]['decision']!='STALE_GEOMETRY' or refused[0]['input_dispatches']!=0 or refused[0]['cached']==refused[0]['current']:bad.append('physical stale pre-input refusal')
 elif refused:bad.append('unexpected direct refusal')
 if 'cleanup_physical' not in raw:bad.append('UNKNOWN_PHYSICAL_CLEANUP_AFTER_EXTERNAL_STOP')
 elif raw['cleanup_physical']['keys'] or raw['cleanup_physical']['buttons']:bad.append('physical cleanup')
 for directory in sorted(O.glob('model-*')):
  path=directory/'HOST_RECORD.private.json'
  if not path.exists():bad.append('missing model record');continue
  record=json.loads(path.read_text(encoding='utf-8'))
  if record['errors'] or record.get('app_server_exit')!=0 or record.get('forced_terminate'):bad.append('model stage errors/termination')
  if record.get('dynamic_calls')!=1 or record.get('turn_start_requests')!=1 or record.get('turn_completed',{}).get('turn',{}).get('status')!='completed':bad.append('actual turn/tool count')
  identity=record.get('thread_start',{}).get('thread',{}).get('id');threads.append(identity)
  usage=record.get('usage');updates=[m['params']['tokenUsage'] for m in record['received'] if m.get('method')=='thread/tokenUsage/updated']
  if not usage or not updates or usage!=updates[-1]['total']:bad.append('actual cumulative usage custody')
  else:
   for key,value in usage.items():totals[mode][key]=totals[mode].get(key,0)+value
  tool=record.get('tool_request',{});v=tool.get('params',{});args=v.get('arguments',{});args=json.loads(args) if isinstance(args,str) else args;label=record['label'];base=label.split('-repair')[0];ready=json.loads((O/(base+('.REFUSED.json' if '-repair' in label else '.READY.json'))).read_text(encoding='utf-8'));proposal=json.loads((O/(label+'.proposal.json')).read_text(encoding='utf-8'))
  if proposal!={'x':args.get('x'),'y':args.get('y'),'binding':ready['geometry']}:bad.append('model coordinates/native proposal custody')
  if ready['image']['artifact']['sha256']!=record.get('model_input_png_sha256'):bad.append('input PNG custody')
  response=[m for m in record['sent'] if m.get('id')==tool.get('id') and 'result' in m]
  if len(response)!=1:bad.append('feedback response identity')
  else:
   import base64
   blocks=response[0]['result']['contentItems'];images=[x for x in blocks if x.get('type')=='inputImage']
   if len(images)!=1:bad.append('feedback PNG block count')
   else:
    blob=base64.b64decode(images[0]['imageUrl'].split(',',1)[1]);done=json.loads((O/(base+'.DONE.json')).read_text(encoding='utf-8'));digest=done['image']['image']['artifact']['sha256']
    if hashlib.sha256(blob).hexdigest()!=digest or digest!=record.get('model_feedback_png_sha256'):bad.append('feedback original PNG bytes')
  stages.append(dict(label=record['label'],thread_id=identity,usage=usage))
 expected_stages=['task'+str(i) for i in range(6)] if mode=='direct' else ['task0','task3-repair']
 if [s['label'] for s in stages]!=expected_stages:bad.append('exact grounding/repair stage inventory')
 reports.append(dict(index=index,mode=mode,saved_tasks=len(raw.get('tasks',[])),model_stages=stages,refusals=len(refused),errors=bad,wall_ns=host['ended_wall_ns']-host['started_wall_ns']));errors.extend(bad)
if len(threads)!=16 or len(set(threads))!=16 or None in threads:errors.append('16 distinct measured threads')
if len(reports)!=4:errors.append('complete ABBA session inventory')
a=totals['direct'].get('inputTokens',0);b=totals['persistent'].get('inputTokens',0);reduction=1-b/a if a and b and len(reports)==4 and not errors else None;scoped=not errors and reduction is not None and reduction>=.20
result=dict(allocation=P['allocation'],disposition='SCOPED_TOKEN_SIGNAL_FULL_INTEGRATION_HOLD' if scoped else 'HOLD_INCOMPLETE_OR_NO_SCOPED_SIGNAL',errors=errors,sessions=reports,usage_totals=totals,input_token_relative_reduction=reduction,full_issue_disposition='HOLD_BROADER_CONTROLS_AND_COMPOSED_CURRENT_BUNDLE_UNPROVEN',limits=['fresh low-effort gpt-5.6-luna contexts; provider snapshot unknown','shared fixed product-entry tool; direct has same capability but no cross-task cache; not optimal baseline','only caller-owned geometry cache over pinned public X11 path, not full guarded-X11 texture handle/compiled graph bundle','no proof of provider image attention/usefulness/billing/internal retry count','output/reasoning and input/cache subsets follow provider semantics; do not add overlapping categories','host wall spans descriptive, include process/setup/context differences; no causal speed claim','cell-content collateral oracle excludes formatting/all unobserved effects','same-author independent saved-byte reader, not external scientific committee vote'])
path=R/'AUDIT_PARTIAL.json'
if path.exists():raise RuntimeError('first auditor path exists; refusing overwrite')
path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result));sys.exit(bool(errors))
