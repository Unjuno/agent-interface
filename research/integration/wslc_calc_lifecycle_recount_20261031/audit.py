"""Recount existing Calc launcher durations; the sibling audit verifies effects."""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json,subprocess,sys
root=Path(__file__).resolve().parent.parent/'wslc_calc_varied_pair_329_517_20261031'
p=root/'public.zip';assert hashlib.sha256(p.read_bytes()).hexdigest()=='99ff8ee1e8940e3c88142c54638dbf94334dea132390bbc88d91fa2dd4f5a134'
checked=subprocess.run([sys.executable,str(root/'audit.py')],check=True,capture_output=True,text=True)
old=json.loads(checked.stdout);assert old['status']=='audited'
with ZipFile(p) as z:
 j=lambda n:json.loads(z.read(n).decode('utf-8-sig'))
 ref=j('d01/out/launcher.json'); a=j('d02/launcher-result.json'); b=j('d03/launcher-result.json')
 assert ref['exit_code']==0 and not ref['timeout']
 assert all(x['host_exit']==x['container_exit']==0 and not x['timeout'] for x in [a,b])
 assert a['container_name']=='calc-varied-d02-20261031' and b['container_name']=='calc-varied-d03-20261031'
 fresh=a['elapsed_seconds'];compiled=b['elapsed_seconds'];assert fresh>0 and compiled>0
 records={r['route']:r for r in old['results']};assert records['fresh']['task_seconds']<=fresh and records['compiled']['task_seconds']<=compiled
 report={'reference_launcher_seconds':ref['elapsed_seconds'],'fresh_launcher_seconds':fresh,'compiled_launcher_seconds':compiled,'compiled_vs_fresh_launcher_reduction_percent':round((fresh-compiled)/fresh*100,2),'fresh_task_seconds':records['fresh']['task_seconds'],'compiled_task_seconds':records['compiled']['task_seconds'],'fresh_input_tokens':records['fresh']['input_tokens'],'compiled_input_tokens':records['compiled']['input_tokens'],'shared_reference_cost_attribution':'unknown; manual preparation not timed'}
 print(json.dumps(report,indent=2))
