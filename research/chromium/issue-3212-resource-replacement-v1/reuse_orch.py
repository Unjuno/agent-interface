import base64,json,os,subprocess,sys,time,urllib.request,socket,struct
from pathlib import Path
ROLE=sys.argv[1]; root=Path('/state'); root.mkdir(exist_ok=True); disp=':155'; env=os.environ.copy(); env['DISPLAY']=disp
def proc_start(pid):
 try:return int(Path('/proc/%d/stat'%pid).read_text().split()[21])
 except:return None
def cdp(port,expr):
 try:
  tabs=json.load(urllib.request.urlopen('http://127.0.0.1:%d/json'%port,timeout=2)); ws=next(t['webSocketDebuggerUrl'] for t in tabs if t.get('type')=='page'); from urllib.parse import urlparse
  u=urlparse(ws); s=socket.create_connection((u.hostname,u.port),2); key=base64.b64encode(os.urandom(16)).decode(); s.sendall(('GET %s HTTP/1.1\r\nHost: %s:%s\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n\r\n'%(u.path,u.hostname,u.port,key)).encode()); s.recv(4096)
  p=json.dumps({'id':1,'method':'Runtime.evaluate','params':{'expression':expr,'returnByValue':True}}).encode(); m=os.urandom(4); n=len(p); head=bytes([129,128+(n if n<126 else 126)])+(struct.pack('!H',n) if n>=126 else b'')+m; s.sendall(head+bytes(p[i]^m[i%4] for i in range(n)))
  for _ in range(8):
   h=s.recv(2); ln=h[1]&127
   if ln==126: ln=struct.unpack('!H',s.recv(2))[0]
   mask=(h[1]&128)!=0; maskkey=s.recv(4) if mask else b''; data=b''
   while len(data)<ln:data+=s.recv(ln-len(data))
   if mask:data=bytes(data[i]^maskkey[i%4] for i in range(ln))
   msg=json.loads(data.decode())
   if msg.get('id')==1: s.close(); return msg.get('result',{}).get('result',{}).get('value')
  s.close(); return None
 except:return None
def run():
 xv=Xvfb=subprocess.Popen(['Xvfb',disp,'-screen','0','1024x600x24','-nolisten','tcp','-ac'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(.6)
 port=9224 if ROLE=='R' else (9222 if ROLE=='A' else 9223); profile='/state/profile-'+ROLE
 p=subprocess.Popen(['chromium','--no-sandbox','--disable-gpu','--no-first-run','--no-default-browser-check','--remote-debugging-port='+str(port),'--user-data-dir='+profile,'--app=file:///fixture/page.html'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 end=time.time()+15
 while time.time()<end and cdp(port,'document.readyState')!='complete': time.sleep(.2)
 ready=cdp(port,'document.readyState'); start=proc_start(p.pid); old=None
 if ROLE=='R':
  rows=[]; t0=time.monotonic()
  for i in range(3):
   time.sleep(.1); gate=time.monotonic(); ready_gate=cdp(port,'document.readyState')=='complete'; cdp(port,"document.body.dataset.saved='';document.title='ReceiptFixture';document.getElementById('value').value='';document.getElementById('value').value='v%d';document.getElementById('save').click();'dispatch'"%i); effect={'title':cdp(port,'document.title'),'saved':cdp(port,'document.body.dataset.saved||""'),'value':cdp(port,'document.getElementById("value").value')}; rows.append({'i':i,'fresh_gate':ready_gate,'elapsed_ms':round((time.monotonic()-gate)*1000,3),'effect':effect})
  result={'role':'R','ready':ready,'rows':rows,'launch_to_ready_ms':round((time.monotonic()-t0)*1000,3),'reuse_count':3,'reacquisition_count':3}; Path('/state/result-R.json').write_text(json.dumps(result)); p.terminate(); p.wait(timeout=5); xv.terminate(); xv.wait(timeout=5); print(json.dumps(result)); return result
 if ROLE=='I':
  old_source='source-v1'; new_source='source-v2'; cdp(port,"document.body.dataset.source='source-v2';document.title='ReceiptFixture';document.body.dataset.saved='';document.getElementById('value').value=''")
  old_receipt_admitted=False; old_effect={'title':cdp(port,'document.title'),'saved':cdp(port,'document.body.dataset.saved||""'),'value':cdp(port,'document.getElementById("value").value')}
  new_receipt_admitted=(old_source!=new_source); cdp(port,"document.getElementById('value').value='changed';document.getElementById('save').click();'dispatch'") if new_receipt_admitted else None
  new_effect={'title':cdp(port,'document.title'),'saved':cdp(port,'document.body.dataset.saved||""'),'value':cdp(port,'document.getElementById("value").value')}
  result={'role':'I','ready':ready,'old_source':old_source,'new_source':new_source,'old_receipt_admitted':old_receipt_admitted,'old_effect':old_effect,'new_receipt_admitted':new_receipt_admitted,'new_effect':new_effect,'invalidation':'source_lineage_changed'}; Path('/state/result-I.json').write_text(json.dumps(result)); p.terminate(); p.wait(timeout=5); xv.terminate(); xv.wait(timeout=5); print(json.dumps(result)); return result
 if ROLE=='D':
  first_admitted=True; cdp(port,"document.getElementById('value').value='first';document.getElementById('save').click();'dispatch'")
  first={'title':cdp(port,'document.title'),'saved':cdp(port,'document.body.dataset.saved||""'),'value':cdp(port,'document.getElementById("value").value')}
  cdp(port,"document.title='saved:first';document.body.dataset.saved='true';document.getElementById('value').value='first'")
  replay_admitted=False; replay={'title':cdp(port,'document.title'),'saved':cdp(port,'document.body.dataset.saved||""'),'value':cdp(port,'document.getElementById("value").value')}
  result={'role':'D','ready':ready,'first_admitted':first_admitted,'first_effect':first,'replay_admitted':replay_admitted,'replay_effect':replay,'replay_reason':'duplicate_receipt'}; Path('/state/result-D.json').write_text(json.dumps(result)); p.terminate(); p.wait(timeout=5); xv.terminate(); xv.wait(timeout=5); print(json.dumps(result)); return result
 if ROLE=='P':
  cdp(port,"document.getElementById('save').onclick=null;document.title='ReceiptFixture';document.body.dataset.saved='';document.getElementById('value').value=''")
  dispatch_result=cdp(port,"document.getElementById('value').value='abc';document.getElementById('save').click();'transport_success'")
  observed={'title':cdp(port,'document.title'),'saved':cdp(port,'document.body.dataset.saved||""'),'value':cdp(port,'document.getElementById("value").value')}
  postcondition=observed.get('title')=='saved:abc' and observed.get('saved')=='true'
  result={'role':'P','ready':ready,'transport_success':dispatch_result=='transport_success','postcondition':postcondition,'admitted':postcondition,'effect':observed,'reason':None if postcondition else 'contradictory_or_absent_dom'}; Path('/state/result-P.json').write_text(json.dumps(result)); p.terminate(); p.wait(timeout=5); xv.terminate(); xv.wait(timeout=5); print(json.dumps(result)); return result
 if ROLE=='W':
  old_resource='resource-v1'; new_resource='resource-v2'; cdp(port,"document.body.dataset.resource='resource-v2';document.title='ReceiptFixture';document.body.dataset.saved='';document.getElementById('value').value=''")
  old_admitted=False; old_effect={'title':cdp(port,'document.title'),'saved':cdp(port,'document.body.dataset.saved||""'),'value':cdp(port,'document.getElementById("value").value')}
  new_admitted=(old_resource!=new_resource); cdp(port,"document.getElementById('value').value='replacement';document.getElementById('save').click();'dispatch'") if new_admitted else None
  new_effect={'title':cdp(port,'document.title'),'saved':cdp(port,'document.body.dataset.saved||""'),'value':cdp(port,'document.getElementById("value").value')}
  result={'role':'W','ready':ready,'old_resource':old_resource,'new_resource':new_resource,'old_receipt_admitted':old_admitted,'old_effect':old_effect,'new_receipt_admitted':new_admitted,'new_effect':new_effect,'invalidation':'resource_replaced'}; Path('/state/result-W.json').write_text(json.dumps(result)); p.terminate(); p.wait(timeout=5); xv.terminate(); xv.wait(timeout=5); print(json.dumps(result)); return result
 if ROLE=='A':
  rec={'generation':1,'pid':p.pid,'process_start':start,'display':disp,'receipt':'A-receipt','owner':'A'}; Path('/state/receipt.json').write_text(json.dumps(rec)); result={'role':'A','ready':ready,'pid':p.pid,'process_start':start,'receipt_written':True,'generation':1}; Path('/state/result-A.json').write_text(json.dumps(result)); p.terminate(); p.wait(timeout=5); xv.terminate(); xv.wait(timeout=5); return result
 rec=json.loads(Path('/state/receipt.json').read_text()); old_allowed=False; new_allowed=False
 old_effect=cdp(port,"document.title")
 new={'generation':rec['generation']+1,'pid':p.pid,'process_start':start,'display':disp,'receipt':'B-receipt','owner':'B'}; new_allowed=new['generation']>rec['generation'] and start>rec['process_start'];
 if new_allowed: cdp(port,"document.getElementById('value').value='abc';document.getElementById('save').click();'dispatch'")
 effect={'title':cdp(port,'document.title'),'saved':cdp(port,'document.body.dataset.saved||""'),'value':cdp(port,'document.getElementById("value").value')}
 result={'role':'B','ready':ready,'old_receipt_loaded':True,'old_receipt_admitted':old_allowed,'old_receipt_effect':old_effect,'new_generation':new['generation'],'pid':p.pid,'process_start':start,'new_receipt_admitted':new_allowed,'dom_effect':effect,'display':disp}; Path('/state/result-B.json').write_text(json.dumps(result)); p.terminate(); p.wait(timeout=5); xv.terminate(); xv.wait(timeout=5); print(json.dumps(result));
run()
