"""Recount source-capture to server-submission from retained WSLc packets."""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json,statistics
root=Path(__file__).resolve().parent.parent
sources=[('a03','wslc_model_three_arm_preflight_20261031_a03','65d0663af5aa8f963673bcc403b91119f7f4832eb75f31c3e0b30dcf38943a8e'),('a04','wslc_model_three_arm_preflight_reverse_20261031_a04','0dfa31344facac348c6b66be5117968819039df22c70179e0310c3fe0315fd49')]
reports=[]
for label,directory,digest in sources:
 p=root/directory/'raw.zip';assert hashlib.sha256(p.read_bytes()).hexdigest()==digest
 with ZipFile(p) as z:
  j=lambda n:json.loads(z.read(n).decode('utf-8-sig'))
  record=j('out/result.json');pre=j('preflight-summary.json');schema=j('schema-audit.json');assert record['passed'] and record['calls']==14
  assert len(pre)==len(schema)==3 and {x['arm'] for x in pre}=={'plain','ephemeral','persistent'} and all(x['attempted'] and x['completed'] and x['usage'] is not None for x in pre) and all(x['valid'] and not x['errors'] for x in schema)
  arms={};taskmaps={}
  for arm in ('plain','ephemeral','persistent'):
   rows=record['arms'][arm];details=j(f'out/arms/{arm}/task-details.json');history=[json.loads(x) for x in z.read(f'out/arms/{arm}/runtime/submission-history.jsonl').splitlines() if x.strip()];oracle=record['independent'][arm]
   assert len(rows)==len(details)==len(history)==6 and oracle['success'] and oracle['record_count']==6 and not oracle['unexpected'] and not oracle['duplicates'] and not oracle['missing']
   values=[];seen=set()
   for row,detail in zip(rows,details):
    ident=row['task_id'];matches=[h for h in history if h['task_id']==ident];assert ident not in seen and len(matches)==1;seen.add(ident);actual=matches[0];assert actual['exact'] is True and detail['submission_records']==matches and row['exact_submission'] and row['submission_count']==1 and row['typed_outcome']=='completed' and row['releases_verified']
    start=detail['source']['capture_ns'];end=actual['received_ns'];assert type(start) is int and type(end) is int and 0<=end-start<=row['elapsed_ns'] and row['source_to_completion_ns']==end-start
    assert detail['trace']==row
    values.append({'task':ident,'layout':row['layout'],'route':row['route'],'capture_to_submission_seconds':(end-start)/1e9,'task_elapsed_seconds':row['elapsed_ns']/1e9,'model_calls':len(row['model_calls'])})
   assert {v['task'] for v in values}=={f'task-{i}' for i in range(1,7)};arms[arm]=values;taskmaps[arm]={v['task']:v for v in values}
  for i in range(1,7):assert len({taskmaps[a][f'task-{i}']['layout'] for a in taskmaps})==1
  assert [v['route'] for v in arms['persistent']]==['cold','reuse','reuse','repair','reuse','reuse'] and [v['model_calls'] for v in arms['persistent']]==[1,0,0,1,0,0]
  deltas=[{'task':f'task-{i}','persistent_route':taskmaps['persistent'][f'task-{i}']['route'],'plain_minus_persistent_seconds':taskmaps['plain'][f'task-{i}']['capture_to_submission_seconds']-taskmaps['persistent'][f'task-{i}']['capture_to_submission_seconds']} for i in range(1,7)]
  reports.append({'run':label,'raw_scope_text':record['scope'],'preflight_completed':True,'capture_to_submission_median_seconds':{a:statistics.median(x['capture_to_submission_seconds'] for x in rows) for a,rows in arms.items()},'paired_deltas':deltas,'arms':arms})
print(json.dumps({'status':'audited','metric':'same-container source capture to fixture server submission receipt; excludes independent verification and setup','runs':reports},indent=2))
