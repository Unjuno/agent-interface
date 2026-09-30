import hashlib, json, shutil, subprocess, time
from pathlib import Path
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
REL=HERE.relative_to(REPO).as_posix()
BASE='python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9'
OUT=HERE/'construction'; OUT.mkdir(exist_ok=True)
for name in ('arena.py','engine.py'):
    src=REPO/'research/procedural_control_arena_v0'/name
    dst=HERE/'images/evaluator'/name
    shutil.copyfile(src,dst)
    if hashlib.sha256(src.read_bytes()).digest()!=hashlib.sha256(dst.read_bytes()).digest(): raise SystemExit(f'copy mismatch: {name}')
images=[]
for name in ('evaluator','controller'):
    tag=f'agent-arena-isolation-{name}-v2:20260927'
    cmd=['docker','build','--pull','--platform','linux/amd64','--tag',tag,str(HERE/'images'/name)]
    p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    (OUT/f'{name}-build.log').write_text(p.stdout,encoding='utf-8')
    if p.returncode: raise SystemExit(f'build failure: {name}')
    raw=subprocess.run(['docker','image','inspect',tag],check=True,capture_output=True,text=True).stdout
    (OUT/f'{name}-image-inspect.json').write_text(raw,encoding='utf-8')
    obj=json.loads(raw)[0]
    public_cmd=['docker','build','--pull','--platform','linux/amd64','--tag',tag,f'{REL}/images/{name}']
    images.append({'name':name,'tag':tag,'id':obj['Id'],'base':BASE,'log_sha256':hashlib.sha256(p.stdout.encode()).hexdigest(),'command':public_cmd})
record={'built_unix':time.time(),'arena_source_sha256':{n:hashlib.sha256((REPO/'research/procedural_control_arena_v0'/n).read_bytes()).hexdigest() for n in ('arena.py','engine.py')},'images':images}
(OUT/'BUILD_RECORD.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps(record,indent=2))
