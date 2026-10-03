"""Saved-only separate scorer: no action, model, or producer imports."""
import hashlib,json,pathlib,sys
R=pathlib.Path('/src');P=json.loads((R/'PLAN.json').read_text());errors=[];rows=[];total={};execution=json.loads((R/'MODEL_EXECUTION.json').read_text())
def need(v,m):
 if not v:errors.append(m)
for p,h in P['source_hashes'].items():need(hashlib.sha256((R/p).read_bytes()).hexdigest()==h,'source drift '+p)
for host in execution['rows']:
 i=host['index'];O=R/'runs'/('row'+str(i+1).zfill(2));spec=P['rows'][i];raw=json.loads((O/'raw.json').read_text()) if (O/'raw.json').exists() else None
 events=[json.loads(l) for l in (O/'model.response.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()] if (O/'model.response.jsonl').exists() else [];done=[e for e in events if e.get('type')=='turn.completed'];items=[e['item'] for e in events if e.get('type')=='item.completed'];msg=[e for e in items if e.get('type')=='agent_message'];broker=json.loads((O/'model.broker.json').read_text()) if (O/'model.broker.json').exists() else {}
 row=dict(index=i,variant=spec['variant'],target=spec['target'],host_errors=host['errors'],broker_exit=broker.get('returncode'),thread_count=sum(e.get('type')=='thread.started' for e in events),turn_count=len(done),message_count=len(msg),other_items=[e.get('type') for e in items if e.get('type') not in ('agent_message','reasoning')],usage=done[0]['usage'] if len(done)==1 else None,exact=False)
 if row['usage']:
  for k,v in row['usage'].items():
   if type(v) is int:total[k]=total.get(k,0)+v
 if raw:
  need(raw['spec']==spec,'spec drift '+str(i));need(raw['source_hashes']==P['source_hashes'],'raw source drift '+str(i));row['raw_errors']=raw['errors'];row['status']=raw.get('receipt',{}).get('status');row['history']=raw.get('effect',{}).get('history',[]);row['released']=raw.get('cleanup_release',{}).get('verified') is True and raw.get('physical_button_mask')==0 and not any(raw.get('physical_keys',[1]))
  for label in ('initial','final'):
   if label in raw:
    ar=raw[label]['artifact'];image=O/'images'/pathlib.Path(ar['path']).name;need(hashlib.sha256(image.read_bytes()).hexdigest()==ar['sha256'],'PNG identity '+str(i)+label)
  row['image_sha256']=raw['initial']['artifact']['sha256'];h=row['history'];row['exact']=not raw['errors'] and row['status']=='completed' and len(h)==1 and h[0]['label']==spec['target'] and h[0]['matching_press'] and h[0]['button']==1 and raw['effect']['press'] is None and row['released'];row['proposal']=raw.get('proposal')
  if msg:need(json.loads(msg[0]['text'])==raw.get('proposal'),'proposal custody '+str(i))
 rows.append(row)
need(len({r.get('image_sha256') for r in rows if r.get('image_sha256')})<=1,'initial observations differ')
out=dict(status='PASS_SAVED_EVIDENCE' if not errors else 'FAIL_AUDIT',errors=errors,rows=rows,total_usage=total,planned_calls=8,attempted_calls=len(rows),exact=sum(r['exact'] for r in rows),application_retries=0,provider_retries='unknown',hypothesis='UNCERTAIN_EXPLORATORY_ONLY',scope='Native custom X11 fixture; response schema rename. Not registered function-tool order, broad model invariance, application-suite benefit or statistical causal ranking. Underlying provider snapshot unknown.')
print(json.dumps(out,indent=2,sort_keys=True));sys.exit(bool(errors))
