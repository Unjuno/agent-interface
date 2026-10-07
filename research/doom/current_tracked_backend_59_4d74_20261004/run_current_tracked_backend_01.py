from pathlib import Path
import subprocess,json,hashlib,time
root=Path(__file__).resolve().parent
source=root/'current-tracked-backend-source-01'
assert (source/'SOURCE.json').is_file()
out=root/'current-tracked-backend-01';out.mkdir(exist_ok=False)
image=(root/'image-02/image.id').read_text().strip()
payload="import sys,runpy;sys.path[:0]=['/source/research/live_control','/source/research/doom','/source'];runpy.run_path('/source/research/doom/test_doom_cancel_telemetry_backend_v1.py',run_name='__main__')"
args=['C:/Program Files/WSL/wslc.exe','run','--name','current-tracked-backend-59-4d74-01','--pull','never','--network','none','--user','65534','--cpus','1','--memory','512M','--workdir','/out','--env','HOME=/tmp','--env','PYTHONDONTWRITEBYTECODE=1','--mount',f'type=bind,source={source},target=/source,readonly','--mount',f'type=bind,source={out},target=/out',image,'/usr/local/bin/python3','-B','-c',payload]
freeze={'source_manifest_sha256':hashlib.sha256((source/'SOURCE.json').read_bytes()).hexdigest(),'head':'31018e40b3032d02c34ddd83f49e9bd282ebd590','image':image,'argv':args,'gate':'Import current tracked dependencies and pass two mocked backend tests. No historical support substitution.','scope':'Construction only, no GUI/game/model/native input/full session; caps enforcement unproven.','retries':0}
(out/'FREEZE.json').write_text(json.dumps(freeze,indent=2)+'\n')
start=time.monotonic()
try:
 with (out/'stdout.txt').open('wb')as so,(out/'stderr.txt').open('wb')as se:r=subprocess.run(args,stdout=so,stderr=se,timeout=45)
 record={'exit':r.returncode,'elapsed_s':time.monotonic()-start}
except subprocess.TimeoutExpired:
 record={'exit':None,'status':'HOST_TIMEOUT_OBSERVATION','elapsed_s':time.monotonic()-start}
(out/'HOST.json').write_text(json.dumps(record,indent=2)+'\n')
print(record);print((out/'stderr.txt').read_text())
