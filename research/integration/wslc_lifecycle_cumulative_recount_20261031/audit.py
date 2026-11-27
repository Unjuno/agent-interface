"""Recount preflight and per-task totals from all four lifecycle packets."""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json,subprocess,sys
here=Path(__file__).resolve().parent;root=here.parent
blocks=[('forward','wslc_three_arm_lifecycle_20261031','3fbdb0b73a1e1bfd08aa0ce845a5667a9a1dd11e719a3d1044185c0d835179ae',['ar01','ar02','ar03']),('reverse','wslc_three_arm_lifecycle_reverse_20261031','e2ca439688f52b08c53b4477b49d2a7c5657ef44f3eed8e6b5843c5da1209cab',['as01','as02','as03']),('first-newseed','wslc_three_arm_lifecycle_first_newseed_20261031','933ecb915ed55bd8646457158f82fa87c2e6d4a1e8f3acf11f50f7f9a43da88b',['at01','at02','at03']),('resilient','wslc_three_arm_lifecycle_resilient_20261031','bb40b7be6374061ed4578d83af2a74abd04c253c9016408da92d5ea0e6778560',['aw01','aw02','aw03'])]
report=[]
for label,name,digest,ids in blocks:
 folder=root/name;packet=folder/'public.zip';assert hashlib.sha256(packet.read_bytes()).hexdigest()==digest
 audit=json.loads(subprocess.check_output([sys.executable,str(folder/'audit.py')],text=True));assert audit['status']=='audited'
 with ZipFile(packet) as z:
  j=lambda n:json.loads(z.read(n).decode('utf-8-sig'))
  arms={};seeds=set()
  for ident in ids:
   c=j(f'{ident}/conditions.json');arm=c['arm'];seeds.add(c['seed']);pre=j(f'{ident}/preflight-summary.json');assert len(pre)==1 and pre[0]['completed'] and pre[0]['usage'] is not None
   r=j(f'{ident}/out/result.json');rows=r['arms'][arm];l=j(f'{ident}/launcher-result.json');assert len(rows)==6
   inp=pre[0]['usage']['input_tokens'];out=pre[0]['usage']['output_tokens'];ns=pre[0]['total_ns'];known=True;points=[]
   for index,row in enumerate(rows,1):
    assert row['task_id']==f'task-{index}'
    for call in row['model_calls']:
     usage=call.get('usage');assert usage is not None;inp+=usage['input_tokens'];out+=usage['output_tokens']
    ns+=row['elapsed_ns']
    if row['typed_outcome']!='completed':known=False
    points.append({'task':index,'status':row['typed_outcome'],'route':row['route'],'cumulative_input_tokens':inp if known else None,'known_input_lower_bound':inp,'cumulative_output_tokens':out if known else None,'preflight_plus_task_seconds':ns/1e9,'usage_complete':known})
   arms[arm]={'points':points,'lifecycle_seconds':l.get('lifecycle_ns')/1e9 if l.get('lifecycle_ns') is not None else None,'preflight_input_tokens':pre[0]['usage']['input_tokens']}
  assert len(seeds)==1 and set(arms)=={'plain','persistent','ephemeral'}
  def first_less(field):
   for a,b in zip(arms['persistent']['points'],arms['plain']['points']):
    if a['status']=='completed' and b['status']=='completed' and a[field] is not None and b[field] is not None and a[field]<b[field]:return a['task']
   return None
  def sustained_less(field):
   pairs=list(zip(arms['persistent']['points'],arms['plain']['points']))
   for i in range(len(pairs)):
    if all(a['status']=='completed' and b['status']=='completed' and a[field] is not None and b[field] is not None and a[field]<b[field] for a,b in pairs[i:]):return i+1
   return None
  report.append({'block':label,'seed':next(iter(seeds)),'first_persistent_less_input_task':first_less('cumulative_input_tokens'),'sustained_persistent_less_input_task':sustained_less('cumulative_input_tokens'),'first_persistent_less_partial_time_task':first_less('preflight_plus_task_seconds'),'sustained_persistent_less_partial_time_task':sustained_less('preflight_plus_task_seconds'),'arms':arms})
assert all(b['first_persistent_less_input_task']==2 and b['sustained_persistent_less_input_task']==2 for b in report)
assert [b['first_persistent_less_partial_time_task'] for b in report]==[2,2,1,3]
assert [b['sustained_persistent_less_partial_time_task'] for b in report]==[2,2,1,5]
assert report[2]['arms']['ephemeral']['points'][-1]['cumulative_input_tokens'] is None
print(json.dumps({'status':'audited','time_scope':'preflight duration plus summed task intervals; excludes startup/idle/cleanup and is not end-to-end','blocks':report},indent=2))
