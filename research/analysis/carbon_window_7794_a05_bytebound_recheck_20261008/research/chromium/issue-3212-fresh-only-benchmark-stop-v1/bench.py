import base64,json,os,subprocess,sys,time,urllib.request,socket,struct
from pathlib import Path
env=os.environ.copy();env['DISPLAY']=':155'; state=Path('/state'); state.mkdir(exist_ok=True)
def ev(port,expr):
 try:
  t=json.load(urllib.request.urlopen('http://127.0.0.1:%d/json'%port,2)); ws=next(x['webSocketDebuggerUrl'] for x in t if x.get('type')=='page'); from urllib.parse import urlparse
  u=urlparse(ws); s=socket.create_connection((u.hostname,u.port),2); key=base64.b64encode(os.urandom(16)).decode(); s.sendall(('GET %s HTTP/1.1\r\nHost: %s:%s\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n\r\n'%(u.path,u.hostname,u.port,key)).encode()); s.recv(4096)
  p=json.dumps({'id':1,'method':'Runtime.evaluate','params':{'expression':expr,'returnByValue':True}}).encode(); m=os.urandom(4); n=len(p); h=bytes([129,128+(n if n<126 else 126)])+(struct.pack('!H',n) if n>=126 else b'')+m; s.sendall(h+bytes(p[i]^m[i%4] for i in range(n)))
  for _ in range(8):
   h=s.recv(2); ln=h[1]&127
   if ln==126:ln=struct.unpack('!H',s.recv(2))[0]
   mk=s.recv(4) if h[1]&128 else b''; d=b''
   while len(d)<ln:d+=s.recv(ln-len(d))
   if mk:d=bytes(d[i]^mk[i%4] for i in range(ln))
   m=json.loads(d.decode())
   if m.get('id')==1:s.close();return m.get('result',{}).get('result',{}).get('value')
 except:pass
 return None
def browser(profile,port):
 p=subprocess.Popen(['chromium','--no-sandbox','--disable-gpu','--no-first-run','--no-default-browser-check','--remote-debugging-port='+str(port),'--user-data-dir='+str(profile),'--app=file:///fixture/page.html'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); end=time.monotonic()+15
 while time.monotonic()<end and ev(port,'document.readyState')!='complete':time.sleep(.02)
 return p
def action(port,i):
 if ev(port,"document.body.dataset.saved='';document.title='ReceiptFixture';document.getElementById('value').value=''") is None:return None
 return ev(port,"document.getElementById('value').value='v%d';document.getElementById('save').click();({title:document.title,saved:document.body.dataset.saved,value:document.getElementById('value').value})"%i)
xv=subprocess.Popen(['Xvfb',':155','-screen','0','1024x600x24','-nolisten','tcp','-ac'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.5)
fresh=[]; t0=time.monotonic()
for i in range(3):
 time.sleep(.1); a=time.monotonic(); p=browser('/state/fresh-%d'%i,9222+i); ready=time.monotonic(); e=action(9222+i,i); done=time.monotonic(); fresh.append({'i':i,'launch_ready_ms':round((ready-a)*1000,3),'total_ms':round((done-a)*1000,3),'effect':e});p.terminate();p.wait(timeout=5)
reuse=[]; a=time.monotonic(); p=browser('/state/reuse',9225); launch_ready=time.monotonic()
for i in range(3):
 time.sleep(.1); gate=time.monotonic(); ready=ev(9225,'document.readyState')=='complete'; e=action(9225,i); done=time.monotonic(); reuse.append({'i':i,'fresh_gate_ms':round((time.monotonic()-gate)*1000,3),'total_ms':round((done-gate)*1000,3),'fresh_gate':ready,'effect':e})
p.terminate();p.wait(timeout=5);xv.terminate();xv.wait(timeout=5)
out={'fresh_only':fresh,'reusable_plus_fresh_gate':reuse,'fresh_total_ms':round(sum(x['total_ms'] for x in fresh),3),'reuse_total_ms':round((time.monotonic()-a)*1000,3),'model_wait_ms_each':100,'reuse_count':3,'reacquisition_count':3};Path('/state/result.json').write_text(json.dumps(out));print(json.dumps(out))
