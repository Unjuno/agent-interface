#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,os,socket,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace
from Xlib import X,XK,display
from Xlib.ext import xtest
import preflight_dependency as dep
from routing import choose_payload_aware,CLIPBOARD_EFFECTS
from xkb_projection import resolve_xkb,project_group1_two_levels
HERE=Path(__file__).resolve().parent
EXPECTED_DIRECT_BLOB='35c7375e50f3e0c58f57c8139a6dc8abeef87771'
EXPECTED_COARSE_BLOB='6ed3fccd7dd0acd7b6c4911a895ff3c96c8c31fd'
PAYLOADS=['office','#','@','[','\\',']','^','`','{','|','}','~','βeta']
BUDGETS=[('transparent',frozenset()),('clipboard',CLIPBOARD_EFFECTS)]
def git_blob(path):
 d=Path(path).read_bytes();return hashlib.sha1(b'blob '+str(len(d)).encode()+b'\0'+d).hexdigest()
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
def selection_owner(d):
 owner=d.get_selection_owner(d.intern_atom('CLIPBOARD'));return getattr(owner,'id',None)
def start_owner(text,ready,stderr):
 try:ready.unlink()
 except FileNotFoundError:pass
 p=subprocess.Popen([sys.executable,str(HERE/'clipboard_owner.py'),'--display',os.environ['DISPLAY'],'--text',text,'--ready',str(ready)],env=os.environ.copy(),stdout=subprocess.DEVNULL,stderr=stderr.open('w'))
 end=time.monotonic()+3
 while not ready.exists():
  if p.poll() is not None:raise RuntimeError('clipboard owner exited')
  if time.monotonic()>=end:raise RuntimeError('clipboard owner timeout')
  time.sleep(.005)
 return p,json.loads(ready.read_text())
def stop(p):
 if p and p.poll() is None:p.terminate()
 if p:
  try:p.wait(timeout=.5)
  except subprocess.TimeoutExpired:p.kill();p.wait()
def find_control(live,first):
 sym=XK.string_to_keysym('Control_L')
 for i,row in enumerate(live):
  if sym in row:return first+i
 raise RuntimeError('Control_L absent')
def send_paste(d,live,first):
 ctrl=find_control(live,first);plan=dep.prepare('v',live,first)
 if len(plan.strokes)!=1 or plan.strokes[0][1]:raise RuntimeError('paste v not simple unshifted')
 v=plan.strokes[0][0]
 for code,down in [(ctrl,True),(v,True),(v,False),(ctrl,False)]:
  xtest.fake_input(d,X.KeyPress if down else X.KeyRelease,code);d.sync()
 return 4
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--layout',required=True);ap.add_argument('--variant',default='');ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=False)
 if git_blob(HERE/'preflight_dependency.py')!=EXPECTED_DIRECT_BLOB:raise RuntimeError('direct dependency mismatch')
 if git_blob(HERE/'coarse_model_dependency.py')!=EXPECTED_COARSE_BLOB:raise RuntimeError('coarse dependency mismatch')
 if not os.environ.get('DISPLAY') or not os.environ.get('XAUTHORITY'):raise RuntimeError('private xvfb-run required')
 d=display.Display();first=d.display.info.min_keycode;baseline=dep.keyboard_mapping(d);base_hash=dep.fingerprint(baseline)
 xkb=resolve_xkb(os.environ['DISPLAY'],os.environ['XAUTHORITY'],a.layout,a.variant,a.out);projected,matched=project_group1_two_levels(xkb,first,baseline);d.change_keyboard_mapping(first,[tuple(r) for r in projected]);d.sync();live=dep.keyboard_mapping(d);applied=dep.fingerprint(live);mapping_changed=applied!=base_hash
 sock=str(a.out/'receiver.sock');receiver=subprocess.Popen([sys.executable,str(HERE/'receiver.py'),sock],env=os.environ.copy(),text=True,stdout=subprocess.PIPE,stderr=(a.out/'receiver.stderr').open('w'));xid=int(json.loads(receiver.stdout.readline())['xid']);win=d.create_resource_object('window',xid);win.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync();time.sleep(.03)
 prior,prior_meta=start_owner('PRIOR-αβ',a.out/'prior.ready',a.out/'prior.stderr');prior_owner=selection_owner(d)
 service_sock=str(a.out/'clipboard-service.sock');service=subprocess.Popen([sys.executable,str(HERE/'clipboard_service.py'),service_sock],env=os.environ.copy(),text=True,stdout=subprocess.PIPE,stderr=(a.out/'clipboard-service.stderr').open('w'));json.loads(service.stdout.readline());first_candidate_owner=None;rows=[]
 try:
  for payload in PAYLOADS:
   for budget_name,budget in BUDGETS:
    rpc(sock,{'op':'reset'});win.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync();before_text=rpc(sock,{'op':'get'})['text'];owner_before=selection_owner(d);svc_before=rpc(service_sock,{'op':'status'});route=choose_payload_aware(payload,live,first,budget);direct_emissions=0;paste_emissions=0;direct_receipt=None;svc_set=None
    if route.selected=='direct_keys':
     backend=SimpleNamespace(d=d,emissions=0);direct_receipt=dep.deliver(backend,payload,target=xid,observation=9,current_observation=9,revision=4,current_revision=4,expires_ns=time.monotonic_ns()+3_000_000_000,pacing_s=.001);direct_emissions=backend.emissions
    elif route.selected=='clipboard_utf8':
     svc_set=rpc(service_sock,{'op':'set','text':payload})
     if first_candidate_owner is None:first_candidate_owner=svc_set['owner_id']
     win.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync();paste_emissions=send_paste(d,live,first)
    time.sleep(.012);actual=rpc(sock,{'op':'get'})['text'];svc_after=rpc(service_sock,{'op':'status'});map_same=dep.fingerprint(dep.keyboard_mapping(d))==applied;physical=dep.physical_state(d);owner_after=selection_owner(d)
    if route.selected=='direct_keys':gate=bool(direct_receipt and direct_receipt['accepted'] and actual==payload and direct_emissions>0 and svc_after['version']==svc_before['version'] and owner_before==owner_after and map_same and not physical['keys'] and not physical['mask'])
    elif route.selected is None:gate=(actual==before_text=='' and direct_emissions==0 and paste_emissions==0 and svc_after['version']==svc_before['version'] and owner_before==owner_after and map_same and not physical['keys'] and not physical['mask'])
    else:gate=(actual==payload and direct_emissions==0 and paste_emissions==4 and svc_set is not None and svc_after['version']==svc_before['version']+1 and owner_after==svc_set['owner_id'] and map_same and not physical['keys'] and not physical['mask'])
    rows.append({'payload':payload,'budget':budget_name,'coverage':'ascii' if all(ord(c)<128 for c in payload) else 'unicode','coarse_selected':route.coarse_selected,'payload_selected':route.selected,'coarse_mismatch':route.coarse_selected!=route.selected,'direct_preflight_ok':route.direct_preflight_ok,'direct_preflight_error':route.direct_preflight_error,'direct_emissions':direct_emissions,'paste_emissions':paste_emissions,'actual':actual,'owner_before':owner_before,'owner_after':owner_after,'clipboard_version_before':svc_before['version'],'clipboard_version_after':svc_after['version'],'map_same':map_same,'physical_after':physical,'gate':gate})
 finally:
  try:rpc(service_sock,{'op':'quit'})
  except Exception:pass
  try:service.wait(timeout=1)
  except subprocess.TimeoutExpired:service.kill();service.wait()
  stop(prior)
  try:rpc(sock,{'op':'quit'})
  except Exception:pass
  try:receiver.wait(timeout=1)
  except subprocess.TimeoutExpired:receiver.kill();receiver.wait()
  final_map=dep.fingerprint(dep.keyboard_mapping(d));final_physical=dep.physical_state(d);d.close()
 counts={k:sum(r['payload_selected']==k for r in rows) for k in ['direct_keys','clipboard_utf8',None]};mismatches=sum(r['coarse_mismatch'] for r in rows);clipboard_owner_transition=(first_candidate_owner is not None and first_candidate_owner!=prior_owner);passed=all(r['gate'] for r in rows) and clipboard_owner_transition and final_map==applied and not final_physical['keys'] and not final_physical['mask'] and (a.layout=='us' or mapping_changed)
 report={'schema':'agent-interface/text-delivery-payload-routing-arm-v1','layout':a.layout,'variant':a.variant,'matched_key_blocks':matched,'mapping_changed':mapping_changed,'applied_map_hash':applied,'final_map_hash':final_map,'candidate_map_invariant':final_map==applied,'final_physical':final_physical,'trial_count':len(rows),'route_counts':{'direct_keys':counts['direct_keys'],'clipboard_utf8':counts['clipboard_utf8'],'none':counts[None]},'coarse_mismatch_count':mismatches,'prior_clipboard_owner':prior_owner,'candidate_clipboard_owner':first_candidate_owner,'clipboard_owner_transition':clipboard_owner_transition,'trials':rows,'passed':passed}
 (a.out/'report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n');print(json.dumps({k:report[k] for k in ['layout','variant','trial_count','route_counts','coarse_mismatch_count','clipboard_owner_transition','mapping_changed','candidate_map_invariant','passed']},indent=2));return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())
