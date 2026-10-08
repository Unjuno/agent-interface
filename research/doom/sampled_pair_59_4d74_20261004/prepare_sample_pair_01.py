from pathlib import Path
import subprocess,json,hashlib
root=Path(__file__).resolve().parent
repo=root.parent/'calc-construction-publication-4d74'
commit=subprocess.check_output(['git','rev-parse','origin/main'],cwd=repo).decode().strip()
dest=root/'sample-pair-source-01';dest.mkdir(exist_ok=False)
paths=subprocess.check_output(['git','ls-tree','-r','--name-only',commit,'research/doom','research/live_control','research/real_apps_v1','research/observation_tiles','research/observation_gating'],cwd=repo).decode().splitlines()
paths=[p for p in paths if (p.endswith('.py') and len(p.split('/'))==3) or p in ['research/doom/map01_cover_policy_schema_v6.json','research/doom/map01_motor_responder_v10.txt']]
proc=subprocess.Popen(['git','cat-file','--batch'],cwd=repo,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
members={}
for p in paths:
    proc.stdin.write((commit+':'+p+'\n').encode());proc.stdin.flush()
    h=proc.stdout.readline().decode().split();data=proc.stdout.read(int(h[2]));assert proc.stdout.read(1)==b'\n'
    target=dest/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    members[p]={'sha256':hashlib.sha256(data).hexdigest(),'git_blob':h[0]}
proc.stdin.close();assert proc.wait()==0
entry=(root/'game_action_measurement_entry_01.py').read_text().replace('current-controller-source-11','sample-pair-source-01').replace("import sys,json,time","import sys,json,time,os").replace("Path('/out/scorer-last-action.jsonl')","Path(os.environ['ACTION_SAMPLE_PATH'])")
(root/'sample_pair_entry_01.py').write_text(entry)
(root/'SAMPLE_PAIR_SOURCE_01.json').write_text(json.dumps({'commit':commit,'members':members},indent=2))
print(commit,len(members))
