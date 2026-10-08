"""Synthetic stdio endpoint. It is not the production Python/MCP relay or a backend."""
import base64, json, os, pathlib, sys, threading, time

ROOT = pathlib.Path(sys.argv[1]).resolve()
MODE = sys.argv[2]
def record(name,value):
    with (ROOT/name).open('x',encoding='utf-8',newline='\n') as f:
        json.dump(value,f,separators=(',',':'));f.write('\n')
def event(kind,**fields):
    with (ROOT/'peer-events.jsonl').open('a',encoding='utf-8',newline='\n') as f:
        json.dump(dict(kind=kind,**fields),f,separators=(',',':'));f.write('\n')
def deadman():
    time.sleep(8)
    event('self_deadline',code=73)
    os._exit(73)
threading.Thread(target=deadman,daemon=True).start()
record('peer-started.json',dict(pid=os.getpid(),parent_pid=os.getppid(),case=ROOT.name,synthetic=True))
event('started',pid=os.getpid())
line = sys.stdin.buffer.readline()
if not line:
    event('eof_before_request');sys.exit(0)
request = json.loads(line)
record('accepted.json',request)
event('accepted',id=request['id'],tool=request['tool'])
while not (ROOT/'permit-response').exists(): time.sleep(.005)
event('permit_observed')
record('synthetic-effect.json',dict(count=1,synthetic=True,request_id=request['id']))
event('synthetic_effect',count=1)
if MODE == 'exit17':
    event('intentional_exit',code=17);sys.exit(17)
meta = dict(status='completed',image_status='image',fixture='synthetic-only',
  execution=dict(releases=[dict(verified=True,keys_down=[],buttons_down=[])]))
png = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aCBkAAAAASUVORK5CYII='
reply = dict(id=request['id']+(1 if MODE=='wrong-id' else 0),tool=request['tool'],status='returned',next_id=request['id']+1,
  result=dict(content=[dict(type='text',text=json.dumps(meta,separators=(',',':'))),dict(type='image',mimeType='image/png',data=png)]))
record('response-intended.json',reply)
encoded = (json.dumps(reply,separators=(',',':'))+'\n').encode()
try:
    written = os.write(sys.stdout.fileno(),encoded)
    event('response_write',bytes=written,expected=len(encoded))
except OSError as error:
    event('response_write_error',error=str(error),winerror=getattr(error,'winerror',None))
extra = sys.stdin.buffer.readline()
if extra:
    event('unexpected_second_request',bytes=len(extra));sys.exit(74)
event('stdin_eof')
