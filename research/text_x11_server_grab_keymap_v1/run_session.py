#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,socket,subprocess,sys,time
from pathlib import Path
from Xlib import X,display
from Xlib.ext import xtest
import preflight_dependency as dep
from xkb_projection import resolve_xkb,project_group1_two_levels
HERE=Path(__file__).resolve().parent

def rpc(path,obj):
 s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);end=time.monotonic()+3
 while True:
  try:s.connect(path);break
  except OSError:
   if time.monotonic()>=end:raise
   time.sleep(.005)
 s.sendall((json.dumps(obj)+'\n').encode());data=b''
 while not data.endswith(b'\n'):
  z=s.recv(65536)
  if not z:break
  data+=z
 s.close();return json.loads(data.decode())

def apply_rows(d,first,rows): d.change_keyboard_mapping(first,[tuple(r) for r in rows]);d.sync()
def resolved_rows(d,layout,outdir):
 outdir.mkdir(parents=True,exist_ok=True);first=d.display.info.min_keycode;cur=dep.keyboard_mapping(d)
 text=resolve_xkb(os.environ['DISPLAY'],os.environ['XAUTHORITY'],layout,'',outdir);return project_group1_two_levels(text,first,cur)[0]
def send_plan(d,plan):
 first_ns=time.monotonic_ns();n=0
 for code,shift in plan.strokes:
  if shift:xtest.fake_input(d,X.KeyPress,plan.shift_code);d.sync();n+=1
  xtest.fake_input(d,X.KeyPress,code);d.sync();n+=1
  xtest.fake_input(d,X.KeyRelease,code);d.sync();n+=1
  if shift:xtest.fake_input(d,X.KeyRelease,plan.shift_code);d.sync();n+=1
 return n,first_ns,time.monotonic_ns()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--layout',choices=['us','de','fr'],required=True);ap.add_argument('--session-id',required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
 d=display.Display();first=d.display.info.min_keycode;us=resolved_rows(d,'us',out/'us-map');apply_rows(d,first,us);live=dep.keyboard_mapping(d);us_hash=dep.fingerprint(live);plan=dep.prepare('@',live,first)
 target=resolved_rows(d,a.layout,out/'target-map');changed=a.layout!='us';rowsfile=out/'target-rows.json';rowsfile.write_text(json.dumps(target))
 sock=str(out/'receiver.sock');receiver=subprocess.Popen([sys.executable,str(HERE/'receiver.py'),sock],env=os.environ.copy(),text=True,stdout=subprocess.PIPE,stderr=(out/'receiver.stderr').open('w'));xid=int(json.loads(receiver.stdout.readline())['xid']);win=d.create_resource_object('window',xid);win.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync();time.sleep(.02)
 mut=None;request_start=request_done=applied_hash=None;grab_start=grab_acquired=ungrab_ns=None
 try:
  if changed:
   mut=subprocess.Popen([sys.executable,str(HERE/'mutator.py'),'--rows',str(rowsfile),'--first',str(first)],env=os.environ.copy(),text=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=(out/'mutator.stderr').open('w'));json.loads(mut.stdout.readline())
  rpc(sock,{'op':'reset'});win.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync()
  grab_start=time.monotonic_ns();d.grab_server();d.sync();grab_acquired=time.monotonic_ns();final_check_ns=time.monotonic_ns();final_check_hash=dep.fingerprint(dep.keyboard_mapping(d))
  if changed:
   mut.stdin.write('go\n');mut.stdin.flush();request_start=json.loads(mut.stdout.readline())['request_start_ns']
  emissions,first_input,last_input=send_plan(d,plan);time.sleep(.010);pre=rpc(sock,{'op':'peek_shadow'});ungrab_ns=time.monotonic_ns();d.ungrab_server();d.sync()
  if changed:
   done=json.loads(mut.stdout.readline());request_done=done['request_done_ns'];applied_hash=done['applied_hash'];mut.wait(timeout=2)
  time.sleep(.020);got=rpc(sock,{'op':'get'});final_hash=dep.fingerprint(dep.keyboard_mapping(d));physical=dep.physical_state(d)
  mechanics=(final_check_hash==us_hash and first_input<=last_input<=pre['reply_ns']<ungrab_ns and pre['shadow']=='' and pre['events']==[] and not physical['keys'] and not physical['mask'])
  if changed: mechanics=mechanics and final_check_ns<request_start<first_input and ungrab_ns<=request_done and applied_hash==final_hash and final_hash!=us_hash
  else: mechanics=mechanics and final_hash==us_hash
  control_ok=(got['text']=='@') if not changed else True
  passed=mechanics and control_ok
  rep={'schema':'agent-interface/text-x11-server-grab-keymap-session-v1','session_id':a.session_id,'layout':a.layout,'changed':changed,'us_hash':us_hash,'final_check_ns':final_check_ns,'final_check_hash':final_check_hash,'request_start_ns':request_start,'request_done_ns':request_done,'mutator_applied_hash':applied_hash,'grab_start_ns':grab_start,'grab_acquired_ns':grab_acquired,'first_input_ns':first_input,'last_input_ns':last_input,'pre_ungrab':pre,'ungrab_ns':ungrab_ns,'emissions':emissions,'final_text':got['text'],'receiver_events':got.get('events',[]),'final_map_hash':final_hash,'physical_after':physical,'mechanics_pass':mechanics,'control_pass':control_ok,'passed':passed}
  (out/'report.json').write_text(json.dumps(rep,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'session_id':a.session_id,'layout':a.layout,'pre_shadow':pre['shadow'],'final_text':got['text'],'mechanics_pass':mechanics,'passed':passed},ensure_ascii=False));return 0 if passed else 1
 finally:
  try:d.ungrab_server();d.sync()
  except:pass
  if mut and mut.poll() is None:mut.kill()
  try:rpc(sock,{'op':'quit'})
  except:pass
  try:receiver.wait(timeout=.5)
  except:receiver.kill()
  d.close()
if __name__=='__main__':raise SystemExit(main())
