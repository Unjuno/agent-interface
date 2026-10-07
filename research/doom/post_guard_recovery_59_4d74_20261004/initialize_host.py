from pathlib import Path
import subprocess,json,time,threading,queue,hashlib
root=Path(__file__).resolve().parent;out=root/'initialize-01';out.mkdir(exist_ok=False)
cli=Path('C:/Users/junny/AppData/Local/OpenAI/Codex/bin/8aaf1547b825b104/codex.exe');image=(root/'image-02/image.id').read_text().strip();wsl='C:/Program Files/WSL/wslc.exe'
cliargs=[str(cli),'app-server','--stdio'];name='post-guard-host-init-59-4d74-01'
args=[wsl,'run','--name',name,'--pull','never','--cpus','1','--memory','512M','--network','none','--user','65534','--env','HOME=/tmp','--mount',f'type=bind,source={root},target=/study,readonly','--mount',f'type=bind,source={out},target=/out',image,'/usr/local/bin/python3','/study/initialize_container.py']
(out/'argv.json').write_text(json.dumps({'cli':cliargs,'cli_sha256':hashlib.sha256(cli.read_bytes()).hexdigest(),'container':args},indent=2))
raw=(out/'host.stdout.jsonl').open('wb');err=(out/'host.stderr.txt').open('wb');cout=(out/'container.stdout.txt').open('wb');cerr=(out/'container.stderr.txt').open('wb');q=queue.Queue();host=subprocess.Popen(cliargs,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,cwd=root);sent=False;notified=False;error=None;guest=None;start=time.monotonic()
def reader():
 for line in host.stdout:
  raw.write(line);raw.flush();q.put(line)
t=threading.Thread(target=reader,daemon=True);t.start()
try:
 guest=subprocess.Popen(args,stdout=cout,stderr=cerr)
 while guest.poll() is None:
  if time.monotonic()-start>35:raise TimeoutError('preflight deadline')
  if host.poll() is not None:raise RuntimeError('host app-server exited')
  req=out/'initialize.request.json'
  if req.exists() and not sent:
   host.stdin.write(req.read_bytes());host.stdin.flush();sent=True
  try:
   line=q.get(timeout=.01);msg=json.loads(line)
   if msg.get('id')==1:
    (out/'initialize.response.tmp').write_bytes(line);(out/'initialize.response.tmp').rename(out/'initialize.response.json')
  except queue.Empty:pass
  if (out/'initialized.request.json').exists() and not notified:
   host.stdin.write((out/'initialized.request.json').read_bytes());host.stdin.flush();notified=True;(out/'initialized.forwarded').write_text('forwarded\n')
 code=guest.wait(timeout=5)
except Exception as exc:
 error=repr(exc)
 if guest is not None and guest.poll() is None:subprocess.run([wsl,'stop',name],capture_output=True,timeout=20)
 code=None if guest is None else guest.wait(timeout=20)
finally:
 host.stdin.close()
 try:host.wait(timeout=5)
 except subprocess.TimeoutExpired:host.terminate();host.wait(timeout=5)
 t.join(timeout=5);raw.close();err.close();cout.close();cerr.close()
r={'scope':'setup transport handshake only; not model cancellation/persistent turn qualification','container_exit':code,'host_exit':host.returncode,'host_reader_alive':t.is_alive(),'initialize_sent':sent,'initialized_sent':notified,'error':error,'elapsed_s':time.monotonic()-start,'model_turns':0};(out/'HOST.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r));raise SystemExit(0 if code==0 and error is None and not t.is_alive() else 1)
