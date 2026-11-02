"""Stage a declared subset of Git blobs; not an assertion of import completeness."""
import hashlib, io, json, subprocess, sys, tarfile
from pathlib import Path
repo=Path(sys.argv[1]).resolve(); out=Path(sys.argv[2]).resolve(); commit=sys.argv[3]
if len(commit)!=40 or any(c not in '0123456789abcdef' for c in commit):raise ValueError('full lowercase commit required')
resolved=subprocess.check_output(['git','rev-parse',commit+'^{commit}'],cwd=repo,text=True).strip()
if resolved!=commit:raise ValueError('commit mismatch')
paths=subprocess.check_output(['git','ls-tree','-r','--name-only',commit,'runtime'],cwd=repo,text=True).splitlines()
selected=[p for p in paths if p.endswith(('.py','.json','.txt')) and '/results/' not in p and '/test_' not in p]
extra=['research/live_control/integrated_efficiency_app_server_model_v1.py','research/live_control/codex_app_server_client_v2.py','research/live_control/codex_app_server_command_v1.py','research/live_control/compiled_form_grounding_v1.py','research/live_control/plain_form_points_v1.py','research/live_control/persistent_planner_adapter_v2.py','research/live_control/plain_form_points_schema_v1.json','research/live_control/plain_form_points_responder_v1.txt','research/live_control/compiled_form_grounding_schema_v1.json','research/live_control/compiled_form_grounding_responder_v1.txt']
selected=sorted(set(selected+extra))
if not selected:raise ValueError('empty selection')
archive=subprocess.check_output(['git','-c','core.autocrlf=false','archive','--format=tar',commit,'--',*selected],cwd=repo)
out.mkdir(parents=False,exist_ok=False);records=[]
with tarfile.open(fileobj=io.BytesIO(archive),mode='r:') as tar:
 members=tar.getmembers()
 files=[m for m in members if m.isfile()]
 if set(m.name for m in files)!=set(selected) or any(not (m.isfile() or m.isdir()) for m in members):raise ValueError('unexpected archive entries')
 for member in files:
  target=(out/member.name).resolve()
  if not target.is_relative_to(out):raise ValueError('archive traversal')
  data=tar.extractfile(member).read();target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
  records.append({'path':member.name,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
manifest={'source_commit':commit,'scope':'selected source files; completeness unverified','files':records}
(out.parent/(out.name+'-manifest.json')).write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'files':len(records),'bytes':sum(x['bytes'] for x in records),'commit':commit}))
