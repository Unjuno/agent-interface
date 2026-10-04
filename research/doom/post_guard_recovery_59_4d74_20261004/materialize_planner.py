from pathlib import Path
import subprocess,json,hashlib
r=Path(__file__).resolve().parent;out=r/'planner-source';out.mkdir(exist_ok=False);repo='C:/Users/junny/Documents/Codex/2026-09-19/new-chat/work/calc-construction-publication-4d74';git='C:/Program Files/Git/cmd/git.exe';base='a2f6b60ac84300d45beb82c7cf5a6e06cfc7c456';pins={}
for name in ['codex_app_server_client_v2.py','persistent_planner_adapter_v2.py','test_codex_app_server_client_v2.py','test_persistent_planner_adapter_v2.py']:
 path='research/live_control/'+name;data=subprocess.run([git,'show',base+':'+path],cwd=repo,capture_output=True,check=True).stdout;target=out/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data);pins[path]=hashlib.sha256(data).hexdigest()
(r/'planner-source.json').write_text(json.dumps({'base':base,'members':pins},indent=2)+'\n');print(json.dumps(pins))
