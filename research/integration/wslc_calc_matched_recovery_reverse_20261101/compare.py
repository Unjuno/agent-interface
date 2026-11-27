"""Recount both retained matched-recovery blocks; do not run with -O."""
from pathlib import Path
from zipfile import ZipFile
import json,statistics,subprocess,sys
here=Path(__file__).resolve().parent
previous=here.parent/'wslc_calc_matched_recovery_20261031'
records=[]
for folder in (previous,here):
 proc=subprocess.run([sys.executable,str(folder/'audit.py')],capture_output=True,text=True,check=True)
 result=json.loads(proc.stdout);assert result['status']=='audited';records.extend(result['results'])
with ZipFile(previous/'public.zip') as a,ZipFile(here/'public.zip') as b:
 old=json.loads(a.read('i01/conditions.json'));new=json.loads(b.read('j01/conditions.json'))
 assert old['candidate']==new['candidate'] and old['image']==new['image'] and old['source_manifest_sha256']==new['source_manifest_sha256'] and old['host_python']==new['host_python']
 sessions=[]
 for z,tag in [(a,'i01'),(a,'i02'),(b,'j01'),(b,'j02')]:sessions.append(json.loads(z.read(tag+'/model-call-1/result.json'))['thread_id'])
 assert len(set(sessions))==4
byroute={x:[r for r in records if r['route']==x] for x in ('fresh','compiled')}
result={'scope':'two ordered pairs, fixed task, no population inference','records':records,'medians':{route:{'task_seconds':statistics.median(x['task_seconds'] for x in rows),'input_tokens':statistics.median(x['usage']['input_tokens'] for x in rows),'output_tokens':statistics.median(x['usage']['output_tokens'] for x in rows)} for route,rows in byroute.items()}}
print(json.dumps(result,indent=2))
