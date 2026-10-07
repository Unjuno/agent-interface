from pathlib import Path
import subprocess,json,hashlib,time,shutil
root=Path(__file__).resolve().parent;source=root/'current-release-composition-source-01';source.mkdir(exist_ok=False)
for p in (root/'accepted-sink-source-01').glob('*.py'):shutil.copyfile(p,source/p.name)
for name,content in json.loads((root/'composition_source_payload_01.json').read_text()).items():(source/name).write_bytes(content.encode())
shutil.copyfile(root/'composition_trace_01.py',source/'composition_trace_01.py')
out=root/'current-release-composition-01';out.mkdir(exist_ok=False)
image=(root/'image-02/image.id').read_text().strip()
args=['C:/Program Files/WSL/wslc.exe','run','--name','current-release-composition-59-4d74-01','--pull','never','--cpus','1','--memory','512M','--network','none','--user','65534','--env','HOME=/tmp','--env','PYTHONDONTWRITEBYTECODE=1','--mount',f'type=bind,source={source},target=/source,readonly','--mount',f'type=bind,source={out},target=/out',image,'/usr/local/bin/python3','-B','/source/composition_trace_01.py']
freeze={'H':'Latest executor publication composes with additive cancellation owner without replacing existing V11.','T':'One unchanged owner/thread integration fixture with passive emit recorder, latest executor609dfb2 and owner12/transition4 from7440head99b7d130 plus earlier support.','D':'One fixture passes, verified cancelled empty release emitted before cancelled terminal; otherwise preserve FAIL/STOP.','C':'Supplied schedule/fake Xlib/minimal backend, not full session/per-key transition batch or physical release.','U':'No game/model/GPU/X server/input; no source adoption; requested caps enforcement unproven.','executor_head':'609dfb2f895ff31626e121dada0e36e9db956287','owner_head':'99b7d130742b4e884709a862bc074d15e6b42ac9','files':{p.name:{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}for p in source.glob('*.py')},'image':image,'argv':args,'retries':0}
(out/'FREEZE.json').write_text(json.dumps(freeze,indent=2)+'\n');start=time.monotonic()
with (out/'stdout.txt').open('wb')as so,(out/'stderr.txt').open('wb')as se:r=subprocess.run(args,stdout=so,stderr=se,timeout=45)
(out/'HOST.json').write_text(json.dumps({'exit':r.returncode,'elapsed_s':time.monotonic()-start,'retry':False},indent=2)+'\n')
print((out/'stdout.txt').read_text());print((out/'stderr.txt').read_text())
