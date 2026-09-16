from __future__ import annotations
import argparse,hashlib,json,os,secrets,socket,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace
from Xlib import X,display
import candidate
HERE=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def rpc(path,obj):
 s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);end=time.monotonic()+3
 while True:
  try:s.connect(path);break
  except OSError:
   if time.monotonic()>=end:raise
   time.sleep(.01)
 s.sendall((json.dumps(obj)+'\n').encode());data=b''
 while not data.endswith(b'\n'):data+=s.recv(65536)
 s.close();return json.loads(data.decode())
def cmd(args,env):
 p=subprocess.run(args,text=True,capture_output=True,env=env);return {'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'args':args}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--rep',type=int,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False);s=json.loads((HERE/'schedule.json').read_text());disp=f":{s['display_base']+a.rep}";auth=a.out/'Xauthority';auth.touch();cookie=secrets.token_hex(16);xa=subprocess.run(['xauth','-f',str(auth),'add',disp,'.',cookie],text=True,capture_output=True);env=os.environ.copy();env.update(DISPLAY=disp,XAUTHORITY=str(auth));os.environ.update(DISPLAY=disp,XAUTHORITY=str(auth));log=(a.out/'xdummy.log').open('w');xp=subprocess.Popen(['Xdummy',disp,'-auth',str(auth),'-nolisten','tcp','-noreset'],stdout=log,stderr=subprocess.STDOUT,text=True);result={'schema':'xkb-xdummy-native-altgr-arm-v1','rep':a.rep,'display':disp,'input_operations':0,'xauth_returncode':xa.returncode};rc=0
 try:
  startup=False
  for _ in range(50):
   if subprocess.run(['xdpyinfo'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:startup=True;break
   if xp.poll() is not None:break
   time.sleep(.1)
  result['startup']=startup
  if not startup:result['decision']='SETUP_BLOCKED_XDUMMY';return 0
  pr=cmd(['setxkbmap','-layout',s['layout'],'-print'],env);(a.out/'de.print.xkb').write_text(pr['stdout']);rr=cmd(['xkbcomp','-xkb','-w','0',str(a.out/'de.print.xkb'),str(a.out/'de.resolved.xkb')],env);resolved=(a.out/'de.resolved.xkb').read_bytes();result['resolved_sha256']=sha(resolved)
  apy=cmd(['xkbcomp','-w','0',str(a.out/'de.resolved.xkb'),disp],env);live=cmd(['xkbcomp','-xkb',disp,'-'],env);(a.out/'live.server.xkb').write_text(live['stdout']);xkb_text=live['stdout'];result['live_xkb_sha256']=sha(xkb_text.encode());result['apply']=apy
  if result['resolved_sha256']!=s['resolved_sha256'] or apy['returncode']!=0:result['decision']='FAIL_INTEGRITY';return 2
  d=display.Display(disp);core=candidate.core_hash(d);mod=candidate.modifier_hash(d);modmap=candidate.modifier_mapping(d);sock=str(a.out/'receiver.sock');rp=subprocess.Popen([sys.executable,str(HERE/'receiver.py'),sock],env=env,text=True,stdout=subprocess.PIPE,stderr=(a.out/'receiver.stderr').open('w'));xid=int(json.loads(rp.stdout.readline())['xid']);win=d.create_resource_object('window',xid);win.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync();time.sleep(.05);rows=[]
  try:
   for seq,idx in enumerate(s['orders'][a.rep]):
    text=s['payloads'][idx];rpc(sock,{'op':'reset'});win.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync();backend=SimpleNamespace(d=d,emissions=0)
    try:plan=candidate.prepare(text,xkb_text);expected=True;levels=[st.level for st in plan.strokes]
    except candidate.Rejected as exc:plan=None;expected=False;levels=[];pre_error=str(exc)
    if plan is None:rec={'accepted':False,'error':pre_error,'emissions':0,'preflight_rejected':True,'release_verified':True,'physical_after':candidate.physical_state(d)}
    else:
     cur=cmd(['xkbcomp','-xkb',disp,'-'],env)['stdout'];rec=candidate.deliver(backend,plan,target=xid,current_xkb_text=cur,expected_core_hash=core,expected_modifier_hash=mod,expires_ns=time.monotonic_ns()+3_000_000_000)
    time.sleep(.025);actual=rpc(sock,{'op':'get'}).get('text','');curx=cmd(['xkbcomp','-xkb',disp,'-'],env)['stdout'];ch=sha(curx.encode());c2=candidate.core_hash(d);m2=candidate.modifier_hash(d);phys=candidate.physical_state(d);gate=(rec['accepted']==expected and rec.get('release_verified') is True and not phys['keys'] and phys['mask']==0 and ch==result['live_xkb_sha256'] and c2==core and m2==mod and ((expected and actual==text) or ((not expected) and actual=='' and rec['emissions']==0)))
    rows.append({'sequence':seq,'payload_index':idx,'payload':text,'expected_accept':expected,'expected_levels':levels,'candidate':rec,'actual':actual,'xkb_after_sha256':ch,'core_after_sha256':c2,'modifier_after_sha256':m2,'physical_after':phys,'gate':gate})
  finally:
   try:rpc(sock,{'op':'quit'})
   except Exception:pass
   try:rp.wait(timeout=2)
   except subprocess.TimeoutExpired:rp.kill();rp.wait()
   finalx=cmd(['xkbcomp','-xkb',disp,'-'],env)['stdout'];final={'xkb':sha(finalx.encode()),'core':candidate.core_hash(d),'modifier':candidate.modifier_hash(d),'physical':candidate.physical_state(d)};d.close()
  passed=all(r['gate'] for r in rows) and final['xkb']==result['live_xkb_sha256'] and final['core']==core and final['modifier']==mod and not final['physical']['keys'] and final['physical']['mask']==0
  result.update(decision='PASS_XDUMMY_NATIVE_ALTGR_DELIVERY_SCOPED' if passed else 'FAIL_DELIVERY',trials=rows,initial_core_sha256=core,initial_modifier_sha256=mod,initial_modifier_mapping=modmap,final=final,passed=passed,input_operations=sum(int(r['candidate'].get('emissions',0)) for r in rows));return 0 if passed else 2
 except Exception as exc:result['decision']='HARNESS_FAIL';result['error']=repr(exc);rc=2;return rc
 finally:
  if xp.poll() is None:xp.terminate()
  try:xp.wait(timeout=3)
  except subprocess.TimeoutExpired:xp.kill();xp.wait()
  log.close();result['xdummy_returncode']=xp.returncode;(a.out/'report.json').write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+'\n');print(json.dumps({'rep':a.rep,'decision':result.get('decision'),'input_operations':result.get('input_operations')}))
if __name__=='__main__':raise SystemExit(main())
