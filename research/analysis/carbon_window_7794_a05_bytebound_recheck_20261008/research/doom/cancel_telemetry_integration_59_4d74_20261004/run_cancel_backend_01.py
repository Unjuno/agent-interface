from pathlib import Path
import subprocess,json,hashlib,time,shutil
root=Path(__file__).resolve().parent;source=root/'cancel-backend-source-01';shutil.copytree(root/'current-game-source-08',source)
live=source/'research/live_control';doom=source/'research/doom';repo=Path('C:/Users/junny/Documents/Codex/2026-09-19/new-chat/work/calc-construction-publication-4d74')
shutil.copyfile(repo/'research/live_control/input_owner_cancel_telemetry_v1.py',live/'input_owner_cancel_telemetry_v1.py')
shutil.copyfile(root/'cancel-telemetry-source-01/research/live_control/input_owner_v11.py',live/'input_owner_v11.py')
for name in ['doom_cancel_telemetry_backend_v1.py','test_doom_cancel_telemetry_backend_v1.py']:shutil.copyfile(repo/'research/doom'/name,doom/name)
for name,content in json.loads((root/'cancel_backend_base_payload_01.json').read_text()).items():(doom/name).write_bytes(content.encode())
out=root/'cancel-backend-01';out.mkdir(exist_ok=False);image=(root/'image-02/image.id').read_text().strip()
args=['C:/Program Files/WSL/wslc.exe','run','--name','cancel-backend-59-4d74-01','--pull','never','--cpus','1','--memory','512M','--network','none','--user','65534','--env','HOME=/tmp','--env','PYTHONDONTWRITEBYTECODE=1','--env','PYTHONPATH=/source:/source/research/doom:/source/research/live_control:/source/research','--mount',f'type=bind,source={source},target=/source,readonly','--mount',f'type=bind,source={out},target=/out',image,'/usr/local/bin/python3','-B','/source/research/doom/test_doom_cancel_telemetry_backend_v1.py']
(out/'FREEZE.json').write_text(json.dumps({'H':'New opt-in backend explicitly selects additive owner and keeps inherited receipt provenance.','T':'Two existing constructor/receipt contracts adapted only importname, patched owner/base setup; frozen earlier support plus exact mainc9a V1/V2.','D':'Bothpass; elsepreserveFAIL/STOP.','C':'Mocked backend contracts, not full running backend/session/physicalinput.','U':'No game/Xserver/model/GPU or source takeover; requested caps unproven.','files':{p.relative_to(source).as_posix():{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}for p in source.rglob('*')if p.is_file()},'image':image,'argv':args,'retries':0},indent=2)+'\n');start=time.monotonic()
with (out/'stdout.txt').open('wb')as so,(out/'stderr.txt').open('wb')as se:r=subprocess.run(args,stdout=so,stderr=se,timeout=45)
(out/'HOST.json').write_text(json.dumps({'exit':r.returncode,'elapsed_s':time.monotonic()-start},indent=2)+'\n');print((out/'stdout.txt').read_text());print((out/'stderr.txt').read_text())
