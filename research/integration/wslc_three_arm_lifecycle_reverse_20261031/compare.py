from pathlib import Path
from zipfile import ZipFile
import hashlib,json,statistics,subprocess,sys
here=Path(__file__).resolve().parent;previous=here.parent/'wslc_three_arm_lifecycle_20261031';runs=[];conditions=[]
for label,folder in [('forward',previous),('reverse',here)]:
 audited=json.loads(subprocess.check_output([sys.executable,str(folder/'audit.py')],text=True));assert audited['status']=='audited'
 with ZipFile(folder/'public.zip') as z:
  read=lambda n:json.loads(z.read(n).decode('utf-8-sig'))
  allocations=['ar01','ar02','ar03'] if label=='forward' else ['as01','as02','as03'];cs=[read(a+'/conditions.json') for a in allocations];conditions.append(cs)
  assert len({c['input_manifest_sha256'] for c in cs})==1
  runs.append({'order':label,'arms':{x['arm']:x for x in audited['runs']}})
fields=('input_manifest_sha256','container_image','model','seed','cpu','memory','network','endpoint','codex_sha256','host_python_sha256','launcher_python','jsonschema_version','host_path_converter')
base=conditions[0][0]
for cset in conditions:
 for c in cset:
  for f in fields:assert c[f]==base[f],(f,c[f],base[f])
print(json.dumps({'status':'audited','forward_plain_seconds':runs[0]['arms']['plain']['lifecycle_seconds'],'forward_persistent_seconds':runs[0]['arms']['persistent']['lifecycle_seconds'],'reverse_plain_seconds':runs[1]['arms']['plain']['lifecycle_seconds'],'reverse_persistent_seconds':runs[1]['arms']['persistent']['lifecycle_seconds'],'per_pair_persistent_reduction_percent':[(1-r['arms']['persistent']['lifecycle_seconds']/r['arms']['plain']['lifecycle_seconds'])*100 for r in runs],'median_plain_seconds':statistics.median(r['arms']['plain']['lifecycle_seconds'] for r in runs),'median_persistent_seconds':statistics.median(r['arms']['persistent']['lifecycle_seconds'] for r in runs),'runs':runs},indent=2))
