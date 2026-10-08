from pathlib import Path
import json,time,hashlib
out=Path('/out'); request={'id':1,'method':'initialize','params':{'clientInfo':{'name':'agent-interface-recovery-preflight','title':'Agent Interface dependency preflight','version':'1'},'capabilities':{'experimentalApi':False,'requestAttestation':False}}}
b=json.dumps(request,separators=(',',':')).encode()+b'\n'; (out/'initialize.request.tmp').write_bytes(b);(out/'initialize.request.tmp').rename(out/'initialize.request.json')
end=time.monotonic()+25
while not (out/'initialize.response.json').exists():
 if time.monotonic()>end: raise TimeoutError('host initialize response missing')
 time.sleep(.01)
rbytes=(out/'initialize.response.json').read_bytes();r=json.loads(rbytes);assert type(r.get('id')) is int and r['id']==1 and 'result' in r and 'error' not in r
(out/'initialized.request.json').write_text('{"method":"initialized"}\n')
end=time.monotonic()+5
while not (out/'initialized.forwarded').exists():
 if time.monotonic()>end:raise TimeoutError('initialized forwarding not acknowledged')
 time.sleep(.01)
result={'scope':'real Windows CLI app-server initialize via private WSLc file mount; no thread/turn/model/GUI/input','request_sha256':hashlib.sha256(b).hexdigest(),'response_sha256':hashlib.sha256(rbytes).hexdigest(),'response_id':r['id'],'result_keys':sorted(r['result']),'initialized_forwarded':True}
(out/'container-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
