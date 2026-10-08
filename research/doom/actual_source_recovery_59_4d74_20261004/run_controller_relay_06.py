from pathlib import Path
import sys,subprocess,time,json,threading,queue,hashlib
from host_image_custody import verify_local_images
from controller_process_cleanup import retire_process
root=Path(__file__).resolve().parent
config=json.loads(Path(sys.argv[1]).read_text())
max_seconds=config['max_seconds']
if not isinstance(max_seconds,int) or not 30<=max_seconds<=180:raise ValueError('bounded lifetime required')
out=root/config['output_directory']
if out.resolve().parent!=root.resolve():raise ValueError('owned direct-child output required')
if not config.get('allocation_id'):raise ValueError('frozen allocation identifier required')
image=(root/'image-02/image.id').read_text().strip();wsl='C:/Program Files/WSL/wslc.exe'
name=config['container_name']
workspace=root/config['host_workspace'];workspace.mkdir(exist_ok=False)
out.mkdir(exist_ok=False)
cli=Path('C:/Users/junny/AppData/Local/OpenAI/Codex/bin/8aaf1547b825b104/codex.exe')
hostargs=[str(cli),'app-server','--stdio','--disable','plugins','--disable','remote_plugin','--disable','shell_tool','--disable','shell_snapshot','-c','project_doc_max_bytes=0']
env={'HOME':'/tmp','PYTHONDONTWRITEBYTECODE':'1','GAME_SOURCE':'/study/current-controller-source-10','HOST_EMPTY_CWD':str(workspace),'GUEST_OUTPUT_ROOT':'/out','HOST_OUTPUT_ROOT':str(out),'RELAY_COMMAND_JSON':json.dumps(['/usr/local/bin/python3','/study/controller_file_stdio_proxy.py','/out']),'RELAY_MAX_SECONDS':str(max_seconds),'QUALIFIED_WAD_PATH':'/study/fixture-input/freedoom2.wad','QUALIFIED_CONTROLLER_ASSETS':'/study/current-controller-source-10/research/doom'}
args=[wsl,'run','--workdir','/out','--name',name,'--pull','never','--cpus','1','--memory','1G','--network','none','--user','65534']
for key,value in env.items():args+=['--env',key+'='+value]
args+=['--mount',f'type=bind,source={root},target=/study,readonly','--mount',f'type=bind,source={out},target=/out',image,'/usr/local/bin/python3','/study/portable_controller_entry_06.py','--out','/out/episode','--iterations',str(config['iterations']),'--seed',str(config['seed']),'--session-span',str(config['session_span']),'--model',config['model'],'--effort',config['effort'],'--load-fixture-manifest','/study/fixture-input/fixture.json']
pins={}
for folder in ['current-controller-source-10','fixture-input']:
 for p in (root/folder).rglob('*'):
  if p.is_file():pins[p.relative_to(root).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
for f in ['portable_controller_entry_03.py','portable_controller_entry_06.py','controller_file_stdio_proxy.py','host_image_custody.py','controller_process_cleanup.py','run_controller_relay_06.py']:pins[f]=hashlib.sha256((root/f).read_bytes()).hexdigest()
(out/'FREEZE.json').write_text(json.dumps({'config':config,'files':pins,'cli_sha256':hashlib.sha256(cli.read_bytes()).hexdigest(),'host_argv':hostargs,'container_argv':args,'retry':False},indent=2)+'\n')
raw=(out/'host.stdout.jsonl').open('wb');err=(out/'host.stderr.txt').open('wb')
cout=(out/'container.stdout.txt').open('wb');cerr=(out/'container.stderr.txt').open('wb')
host=subprocess.Popen(hostargs,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,cwd=root)
q=queue.Queue()
def reader():
    for line in host.stdout:
        raw.write(line);raw.flush();q.put(line)
t=threading.Thread(target=reader,daemon=True);t.start();guest=None;error=None;req=0;resp=0;start=time.monotonic(); sharing_wait=[];blocked_since=None
try:
    guest=subprocess.Popen(args,stdout=cout,stderr=cerr)
    while guest.poll() is None:
        if time.monotonic()-start>max_seconds:raise TimeoutError('construction deadline')
        if host.poll() is not None:raise RuntimeError('host app-server terminated early')
        p=out/f'request-{req:06d}.jsonl'
        if p.exists():
            try:
                b=p.read_bytes()
            except PermissionError as problem:
                now=time.monotonic()
                if blocked_since is None:blocked_since=now
                sharing_wait.append({'request_index':req,'observed_s':now-start,'error':repr(problem)})
                if now-blocked_since>2:raise TimeoutError('request sharing unavailable >2s') from problem
                time.sleep(.01);continue
            blocked_since=None
            message=json.loads(b)
            receipts=verify_local_images(message,out)
            if receipts:
                with (out/'host-image-receipts.jsonl').open('a') as receipt_log:
                    receipt_log.write(json.dumps({'request_index':req,'images':receipts})+'\n')
            host.stdin.write(b);host.stdin.flush();req+=1
        try:
            b=q.get(timeout=.005);json.loads(b)
            p=out/f'response-{resp:06d}.jsonl';p.with_suffix('.tmp').write_bytes(b);p.with_suffix('.tmp').rename(p);resp+=1
        except queue.Empty:pass
    code=guest.wait(timeout=5)
except Exception as e:
    error=repr(e)
    import traceback
    (out/'exception.txt').write_text(traceback.format_exc())
    if guest is not None and guest.poll() is None:
        try:
            stopped=subprocess.run([wsl,'stop',name],capture_output=True,timeout=20)
            (out/'container-stop.json').write_text(json.dumps({'exit':stopped.returncode,'stdout':stopped.stdout.decode(errors='replace'),'stderr':stopped.stderr.decode(errors='replace')},indent=2))
        except Exception as stop_error:
            (out/'container-stop-error.txt').write_text(repr(stop_error))
        guest_retirement=retire_process(guest)
        (out/'guest-client-retirement.json').write_text(json.dumps(guest_retirement,indent=2))
    code=None if guest is None else guest.poll()
finally:
    host_retirement=retire_process(host)
    (out/'host-retirement.json').write_text(json.dumps(host_retirement,indent=2))
    t.join(timeout=5);raw.close();err.close();cout.close();cerr.close()
r={'container_exit':code,'host_exit':host.returncode,'reader_alive':t.is_alive(),
   'requests_forwarded':req,'responses_forwarded':resp,'error':error,'elapsed_s':time.monotonic()-start,
   'provider_calls':'derive requested turn/start count from retained requests','game_sessions':'derive from runtime events','input_emissions':'derive from owner raw evidence','sharing_waits':sharing_wait}
(out/'HOST.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)
raise SystemExit(0 if code==0 and error is None and not t.is_alive() else 1)

