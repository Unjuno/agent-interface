from pathlib import Path
import subprocess,json,hashlib,time,sys,shutil
root=Path(__file__).resolve().parent;mode=sys.argv[1]
assert mode in ('02','03')
source=root/('integration-guard-source-'+mode)
shutil.copyfile(root/'integration_guard_probe_02.py',source/'probe.py')
out=root/('integration-guard-'+mode);out.mkdir(exist_ok=False)
image=(root/'image-02/image.id').read_text().strip()
args=['C:/Program Files/WSL/wslc.exe','run','--name','integration-guard-59-4d74-'+mode,'--pull','never','--network','none','--user','65534','--cpus','1','--memory','512M','--workdir','/out','--env','HOME=/tmp','--env','PYTHONDONTWRITEBYTECODE=1','--mount',f'type=bind,source={source},target=/source,readonly','--mount',f'type=bind,source={out},target=/out',image,'/usr/local/bin/python3','-B','/source/probe.py']
freeze={'mode':mode,'image':image,'argv':args,'source':{p.relative_to(source).as_posix():{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':len(p.read_bytes())}for p in source.rglob("*")if p.is_file()},'launcher_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'retries':0,'scope':'Construction fake proxy/Xlib with real ownerthread; no formal/native/game/model/input. Requestedcapsenforcementunproven.'}
(out/'FREEZE.json').write_text(json.dumps(freeze,indent=2)+'\n')
start=time.monotonic()
with(out/'stdout.txt').open('wb')as so,(out/'stderr.txt').open('wb')as se:r=subprocess.run(args,stdout=so,stderr=se,timeout=45)
(out/'HOST.json').write_text(json.dumps({'exit':r.returncode,'elapsed_s':time.monotonic()-start},indent=2)+'\n')
print(r.returncode);print((out/'stdout.txt').read_text());print((out/'stderr.txt').read_text())
