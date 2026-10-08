from __future__ import annotations
import argparse,hashlib,json,os,re,secrets,subprocess,time
from pathlib import Path
from Xlib import display

def sha(b): return hashlib.sha256(b).hexdigest()
def cmd(args,env):
 p=subprocess.run(args,text=True,capture_output=True,env=env); return {'args':args,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
def parse_syms(text,name):
 m=re.search(r'key\s+<'+re.escape(name)+r'>\s*\{(.*?)\};',text,re.S)
 if not m:return []
 s=re.search(r'symbols\[Group1\]\s*=\s*\[(.*?)\]',m.group(1),re.S) or re.search(r'\[(.*?)\]',m.group(1),re.S)
 return [x.strip() for x in s.group(1).split(',')] if s else []
def live(env):
 d=display.Display(env['DISPLAY']); info=d.display.info; mapping=[list(r) for r in d.get_keyboard_mapping(info.min_keycode,info.max_keycode-info.min_keycode+1)]; mods=d.get_modifier_mapping()
 try: mm=[list(r) for r in mods]
 except TypeError:
  k=getattr(mods,'keycodes_per_modifier',0); f=list(getattr(mods,'keycodes',[])); mm=[f[i*k:(i+1)*k] for i in range(8)]
 o={'min_keycode':info.min_keycode,'max_keycode':info.max_keycode,'mapping':mapping,'modifier_mapping':mm}; raw=json.dumps(o,separators=(',',':'),sort_keys=True).encode();o['sha256']=sha(raw);d.close();return o
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--plan',type=Path,required=True);ap.add_argument('--index',type=int,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False);p=json.loads(a.plan.read_text())
 n=p['display_base']+a.index; disp=f':{n}'; auth=a.out/'Xauthority';auth.touch();cookie=secrets.token_hex(16); xa=subprocess.run(['xauth','-f',str(auth),'add',disp,'.',cookie],text=True,capture_output=True)
 env=os.environ.copy();env['DISPLAY']=disp;env['XAUTHORITY']=str(auth);log=(a.out/'xdummy.log').open('w');proc=subprocess.Popen(['Xdummy',disp,'-auth',str(auth),'-nolisten','tcp','-noreset'],stdout=log,stderr=subprocess.STDOUT,text=True)
 startup=False
 for _ in range(50):
  q=subprocess.run(['xdpyinfo'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  if q.returncode==0:startup=True;break
  if proc.poll() is not None:break
  time.sleep(.1)
 result={'schema':'agent-interface/xkb-xdummy-arm-v1','display':disp,'startup':startup,'xauth_returncode':xa.returncode,'input_operations':0}
 try:
  if not startup:
   result['decision']='SETUP_BLOCKED_XDUMMY'; return 0
  ext=cmd(['xdpyinfo','-queryExtensions'],env);result['xkeyboard_present']='XKEYBOARD' in ext['stdout'].upper()
  bq=cmd(['setxkbmap','-query'],env); b=live(env); bd=cmd(['xkbcomp','-xkb',disp,'-'],env);(a.out/'baseline.server.xkb').write_text(bd['stdout'])
  pr=cmd(['setxkbmap','-layout',p['layout'],'-print'],env);(a.out/'de.print.xkb').write_text(pr['stdout']);rr=cmd(['xkbcomp','-xkb','-w','0',str(a.out/'de.print.xkb'),str(a.out/'de.resolved.xkb')],env); rb=(a.out/'de.resolved.xkb').read_bytes(); rh=sha(rb)
  apply=cmd(['xkbcomp','-w','0',str(a.out/'de.resolved.xkb'),disp],env);aq=cmd(['setxkbmap','-query'],env);aft=live(env);ad=cmd(['xkbcomp','-xkb',disp,'-'],env);(a.out/'after.server.xkb').write_text(ad['stdout'])
  resolved=rb.decode(); after=ad['stdout']; rs=parse_syms(resolved,'AD01'); rralt=parse_syms(resolved,'RALT'); asy=parse_syms(after,'AD01'); ar=parse_syms(after,'RALT')
  server_changed=sha(bd['stdout'].encode())!=sha(ad['stdout'].encode()); live_changed=b['sha256']!=aft['sha256']; native= len(asy)>=3 and asy[2]=='at' and ar and ar[0]=='ISO_Level3_Shift'
  integrity=result['xkeyboard_present'] and rh==p['resolved_sha256'] and rr['returncode']==0 and rs[:4]==['q','Q','at','Greek_OMEGA'] and rralt and rralt[0]=='ISO_Level3_Shift'
  decision='PASS_XDUMMY_NATIVE_XKB_MAP_SCOPED' if integrity and apply['returncode']==0 and server_changed and live_changed and native else ('SETUP_BLOCKED_NATIVE_XKB_APPLY' if integrity and apply['returncode']==0 else 'FAIL_INTEGRITY')
  result.update(decision=decision,resolved_sha256=rh,apply=apply,baseline_query=bq['stdout'],after_query=aq['stdout'],baseline_server_sha256=sha(bd['stdout'].encode()),after_server_sha256=sha(ad['stdout'].encode()),baseline_live_sha256=b['sha256'],after_live_sha256=aft['sha256'],server_dump_changed=server_changed,live_core_map_changed=live_changed,after_ad01_symbols=asy,after_ralt_symbols=ar,native_ad01_level3_at=native,integrity=integrity,baseline_modifier_mapping=b['modifier_mapping'],after_modifier_mapping=aft['modifier_mapping'])
  return 0 if decision!='FAIL_INTEGRITY' else 2
 finally:
  if proc.poll() is None: proc.terminate()
  try: proc.wait(timeout=3)
  except subprocess.TimeoutExpired: proc.kill();proc.wait()
  log.close(); result['xdummy_returncode']=proc.returncode; (a.out/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps({'decision':result.get('decision'),'startup':startup,'xdummy_rc':proc.returncode}))
if __name__=='__main__':raise SystemExit(main())
