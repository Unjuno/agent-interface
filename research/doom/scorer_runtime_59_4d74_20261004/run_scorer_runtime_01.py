from pathlib import Path
import subprocess,json,hashlib,time
root=Path(__file__).resolve().parent;out=root/'scorer-runtime-01';out.mkdir(exist_ok=False)
image=(root/'image-02/image.id').read_text().strip()
args=['C:/Program Files/WSL/wslc.exe','run','--name','scorer-runtime-59-4d74-01','--pull','never','--cpus','1','--memory','512M','--network','none','--user','65534','--env','HOME=/tmp','--env','PYTHONDONTWRITEBYTECODE=1','--env','SDL_VIDEODRIVER=dummy','--mount',f'type=bind,source={root},target=/study,readonly','--mount',f'type=bind,source={out},target=/out',image,'/usr/local/bin/python3','-B','/study/scorer_runtime_01.py']
(out/'FREEZE.json').write_text(json.dumps({'allocation':'SCORER-REFRESH-59-4D74-01','image':image,'argv':args,'source_sha256':hashlib.sha256((root/'scorer_runtime_01.py').read_bytes()).hexdigest(),'wad_sha256':hashlib.sha256((root/'fixture-input/freedoom2.wad').read_bytes()).hexdigest(),'retries':0,'scope':'Neutral headless CPU scorer construction, not matched live recovery lane; requested memory cap enforcement unproven.'},indent=2)+'\n')
start=time.monotonic()
with (out/'stdout.txt').open('wb')as so,(out/'stderr.txt').open('wb')as se:r=subprocess.run(args,stdout=so,stderr=se,timeout=45)
(out/'HOST.json').write_text(json.dumps({'exit':r.returncode,'elapsed_s':time.monotonic()-start},indent=2)+'\n');print((out/'stdout.txt').read_text());print((out/'stderr.txt').read_text())
