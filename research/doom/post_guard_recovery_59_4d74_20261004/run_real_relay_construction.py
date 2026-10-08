from pathlib import Path
import sys,subprocess,time,json,threading,queue,hashlib
root=Path(__file__).resolve().parent; out=root/'real-relay-construction-01';out.mkdir(exist_ok=False)
image=(root/'image-02/image.id').read_text().strip();wsl='C:/Program Files/WSL/wslc.exe'
names=['real_file_stdio_proxy.py','fake_pending_server.py','real_relay_container_check.py','run_real_relay_construction.py']
pins={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in names}
for p in (root/'planner-source-02').rglob('*.py'):
    pins[p.relative_to(root).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
name='post-guard-relay-59-4d74-real-construction01'
args=[wsl,'run','--name',name,'--pull','never','--cpus','1','--memory','512M','--network','none',
      '--user','65534','--env','HOME=/tmp','--env','PYTHONPATH=/source','--env','PYTHONDONTWRITEBYTECODE=1',
      '--mount',f'type=bind,source={root},target=/study,readonly',
      '--mount',f'type=bind,source={root / "planner-source-02"},target=/source,readonly',
      '--mount',f'type=bind,source={out},target=/out',image,'/usr/local/bin/python3','/study/real_relay_container_check.py']
cli=root.parent.parent.parent.parent.parent / 'unused'
cli=Path('C:/Users/junny/AppData/Local/OpenAI/Codex/bin/8aaf1547b825b104/codex.exe')
workspace=root/'real-empty-workspace';workspace.mkdir(exist_ok=False)
args[args.index('--mount'):args.index('--mount')]=['--env','HOST_WORKSPACE='+str(workspace)]
hostargs=[str(cli),'app-server','--stdio','--disable','plugins','--disable','remote_plugin','--disable','shell_tool','--disable','shell_snapshot','-c','project_doc_max_bytes=0']
pins['CLI_SHA256']=hashlib.sha256(cli.read_bytes()).hexdigest()
(out/'FREEZE.json').write_text(json.dumps({'files':pins,'host_argv':hostargs,'container_argv':args,
       'scope':'one actual provider transport construction, at most 2 requested turns, no game/input; interruption usage may remain unknown',
       'cases':['real pending interrupt','real fresh continuation'],
       'max_seconds':60,'retry':False},indent=2)+'\n')
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
        if time.monotonic()-start>60:raise TimeoutError('construction deadline')
        if host.poll() is not None:raise RuntimeError('fake host terminated early')
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
            json.loads(b);host.stdin.write(b);host.stdin.flush();req+=1
        try:
            b=q.get(timeout=.005);json.loads(b)
            p=out/f'response-{resp:06d}.jsonl';p.with_suffix('.tmp').write_bytes(b);p.with_suffix('.tmp').rename(p);resp+=1
        except queue.Empty:pass
    code=guest.wait(timeout=5)
except Exception as e:
    error=repr(e)
    import traceback
    (out/'exception.txt').write_text(traceback.format_exc())
    if guest is not None and guest.poll() is None:subprocess.run([wsl,'stop',name],capture_output=True,timeout=20)
    code=None if guest is None else guest.wait(timeout=20)
finally:
    host.stdin.close()
    try:host.wait(timeout=5)
    except subprocess.TimeoutExpired:host.terminate();host.wait(timeout=5)
    t.join(timeout=5);raw.close();err.close();cout.close();cerr.close()
r={'container_exit':code,'host_exit':host.returncode,'reader_alive':t.is_alive(),
   'requests_forwarded':req,'responses_forwarded':resp,'error':error,'elapsed_s':time.monotonic()-start,
   'provider_calls':'derive requested turn/start count from retained requests','game_sessions':0,'input_emissions':0,'sharing_waits':sharing_wait}
(out/'HOST.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)
raise SystemExit(0 if code==0 and error is None and not t.is_alive() else 1)

