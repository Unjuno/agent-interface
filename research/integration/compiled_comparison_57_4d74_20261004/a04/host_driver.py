from pathlib import Path
import json,hashlib,subprocess,time,traceback
from model_bridge import serve_request
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'formal-output';P=json.loads((ROOT/'PROTOCOL.json').read_text());F=json.loads((ROOT/'FREEZE.json').read_text())
for name,digest in F['files'].items():
 if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:raise RuntimeError('changed frozen input '+name)
for name,digest in json.loads((ROOT/'SOURCE.json').read_text())['members'].items():
 if hashlib.sha256((ROOT/'source'/name).read_bytes()).hexdigest()!=digest:raise RuntimeError('changed source '+name)
if hashlib.sha256(Path(P['cli']).read_bytes()).hexdigest()!=P['cli_sha256']:raise RuntimeError('CLI changed')
OUT.mkdir(exist_ok=False);workspace=ROOT/'empty-workspace';workspace.mkdir(exist_ok=False)
name='compiled-comparison-57-4d74-20261004-a04'
args=[r'C:/Program Files/WSL/wslc.exe','run','--name',name,'--pull','never','--cpus','1','--memory','1G','--network','none','--user','65534','--env','HOME=/tmp','--env','PYTHONPATH=/source:/source/research/live_control','--mount',f'type=bind,source={ROOT / "source"},target=/source,readonly','--mount',f'type=bind,source={ROOT},target=/study,readonly','--mount',f'type=bind,source={OUT},target=/out',P['image'],'/usr/local/bin/python3','/study/comparison_runner.py']
(OUT/'container.argv.json').write_text(json.dumps(args,indent=2));stdout=(OUT/'container.stdout.txt').open('wb');stderr=(OUT/'container.stderr.txt').open('wb');started=time.perf_counter_ns();proc=subprocess.Popen(args,stdout=stdout,stderr=stderr);processed=set();calls=[];stop=None
try:
 while proc.poll() is None:
  for request in sorted((OUT/'requests').glob('*.request.json')):
   if request.name in processed:continue
   processed.add(request.name)
   result=serve_request(request,P['cli'],P['model'],P['effort'],workspace,OUT/'model-calls');calls.append(result)
   (OUT/'HOST_MODELS.json').write_text(json.dumps(calls,indent=2))
   print(json.dumps({'request':request.name,'transport_ok':result['transport_ok'],'usage':result['usage'],'wait_ns':result['wait_ns']}),flush=True)
  if (time.perf_counter_ns()-started)/1e9>P['max_elapsed_seconds']:stop='host_deadline';break
  time.sleep(.2)
except Exception as error:
 stop={'type':type(error).__name__,'detail':str(error)};traceback.print_exc()
finally:
 if stop and proc.poll() is None:
  subprocess.run([r'C:/Program Files/WSL/wslc.exe','stop',name],capture_output=True,timeout=30)
 code=proc.wait(timeout=30);stdout.close();stderr.close()
 (OUT/'HOST.json').write_text(json.dumps({'container_exit':code,'stop':stop,'model_calls':len(calls),'elapsed_ns':time.perf_counter_ns()-started,'formal_started':True},indent=2))
 print(json.dumps({'container_exit':code,'stop':stop,'model_calls':len(calls)}),flush=True)
raise SystemExit(0 if code==0 and stop is None else 1)
