#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, socket, subprocess, sys, time
from pathlib import Path
from types import SimpleNamespace
from Xlib import X, display
from Xlib.ext import xtest
import preflight_dependency as dep
from routing import choose_payload_aware, CLIPBOARD_EFFECTS
from xkb_projection import resolve_xkb, project_group1_two_levels
HERE=Path(__file__).resolve().parent

def rpc(path,obj):
    s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM); end=time.monotonic()+3
    while True:
        try:s.connect(path);break
        except OSError:
            if time.monotonic()>=end: raise
            time.sleep(.005)
    s.sendall((json.dumps(obj)+'\n').encode()); data=b''
    while not data.endswith(b'\n'):
        z=s.recv(65536)
        if not z:break
        data+=z
    s.close(); return json.loads(data.decode())

def apply(d,layout,variant,outdir):
    outdir.mkdir(parents=True,exist_ok=True)
    first=d.display.info.min_keycode; cur=dep.keyboard_mapping(d)
    text=resolve_xkb(os.environ['DISPLAY'],os.environ['XAUTHORITY'],layout,variant,outdir)
    proj,matched=project_group1_two_levels(text,first,cur)
    d.change_keyboard_mapping(first,[tuple(r) for r in proj]); d.sync()
    live=dep.keyboard_mapping(d)
    return live,matched

def send_old_plan(d,plan):
    emissions=0
    for code,shift in plan.strokes:
        if shift:
            xtest.fake_input(d,X.KeyPress,plan.shift_code);d.sync();emissions+=1
        xtest.fake_input(d,X.KeyPress,code);d.sync();emissions+=1
        xtest.fake_input(d,X.KeyRelease,code);d.sync();emissions+=1
        if shift:
            xtest.fake_input(d,X.KeyRelease,plan.shift_code);d.sync();emissions+=1
        time.sleep(.001)
    return emissions

def find_control(live,first):
    from Xlib import XK
    sym=XK.string_to_keysym('Control_L')
    for i,row in enumerate(live):
        if sym in row:return first+i
    raise RuntimeError('Control_L absent')

def paste(d,live,first):
    ctrl=find_control(live,first); plan=dep.prepare('v',live,first); code,shift=plan.strokes[0]
    if shift: raise RuntimeError('v requires shift')
    for c,down in [(ctrl,True),(code,True),(code,False),(ctrl,False)]:
        xtest.fake_input(d,X.KeyPress if down else X.KeyRelease,c);d.sync()
    return 4

def physical_empty(d):
    s=dep.physical_state(d); return s, not s['keys'] and not s['mask']

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--target-layout',required=True);ap.add_argument('--target-variant',default='');ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=False)
    if not os.environ.get('DISPLAY') or not os.environ.get('XAUTHORITY'):raise RuntimeError('xvfb-run required')
    d=display.Display(); first=d.display.info.min_keycode
    us,_=apply(d,'us','',a.out/'us-map'); us_hash=dep.fingerprint(us); old_plan=dep.prepare('@',us,first)
    sock=str(a.out/'receiver.sock'); r=subprocess.Popen([sys.executable,str(HERE/'receiver.py'),sock],env=os.environ.copy(),text=True,stdout=subprocess.PIPE,stderr=(a.out/'receiver.stderr').open('w')); xid=int(json.loads(r.stdout.readline())['xid']); win=d.create_resource_object('window',xid);win.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync()
    svc_sock=str(a.out/'clipboard.sock');svc=subprocess.Popen([sys.executable,str(HERE/'clipboard_service.py'),svc_sock],env=os.environ.copy(),text=True,stdout=subprocess.PIPE,stderr=(a.out/'clipboard.stderr').open('w'));json.loads(svc.stdout.readline())
    try:
        live,matched=apply(d,a.target_layout,a.target_variant,a.out/'target-map'); target_hash=dep.fingerprint(live); changed=target_hash!=us_hash
        current_direct_ok=True; current_err=None
        try:dep.prepare('@',live,first)
        except dep.Rejected as e:current_direct_ok=False;current_err=str(e)
        # Unsafe control: stale US-compiled plan after map change.
        rpc(sock,{'op':'reset'});win.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync();unsafe_emissions=send_old_plan(d,old_plan);time.sleep(.015);unsafe_text=rpc(sock,{'op':'get'})['text'];unsafe_phys,unsafe_release=physical_empty(d)
        # Safe current executor must re-preflight current map.
        rpc(sock,{'op':'reset'});win.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync();b=SimpleNamespace(d=d,emissions=0);safe=dep.deliver(b,'@',target=xid,observation=1,current_observation=1,revision=1,current_revision=1,expires_ns=time.monotonic_ns()+2_000_000_000,pacing_s=.001);time.sleep(.015);safe_text=rpc(sock,{'op':'get'})['text']
        transparent=choose_payload_aware('@',live,first,frozenset()); clip=choose_payload_aware('@',live,first,CLIPBOARD_EFFECTS)
        # Actuate only the fresh clipboard route, if selected.
        rpc(sock,{'op':'reset'});before=rpc(svc_sock,{'op':'status'});fresh_clip_text='';fresh_paste=0
        if clip.selected=='clipboard_utf8':
            setr=rpc(svc_sock,{'op':'set','text':'@'});win.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync();fresh_paste=paste(d,live,first);time.sleep(.015);fresh_clip_text=rpc(sock,{'op':'get'})['text'];after=rpc(svc_sock,{'op':'status'})
        else:
            setr=None;after=rpc(svc_sock,{'op':'status'})
        final_phys,final_release=physical_empty(d); final_hash=dep.fingerprint(dep.keyboard_mapping(d))
        changed_case=a.target_layout!='us' or bool(a.target_variant)
        unsafe_gate=(unsafe_text!='@') if changed_case else (unsafe_text=='@')
        safe_gate=(not safe['accepted'] and safe['emissions']==0 and safe_text=='' and safe['preflight_rejected']) if changed_case else (safe['accepted'] and safe_text=='@' and safe['emissions']>0)
        decision_gate=(transparent.selected is None and clip.selected=='clipboard_utf8') if changed_case else (transparent.selected=='direct_keys' and clip.selected=='direct_keys')
        clipboard_gate=(fresh_clip_text=='@' and fresh_paste==4 and after['version']==before['version']+1) if changed_case else (fresh_paste==0 and after['version']==before['version'])
        map_gate=final_hash==target_hash
        passed=unsafe_gate and safe_gate and decision_gate and clipboard_gate and unsafe_release and final_release and map_gate and ((changed_case and changed) or (not changed_case and not changed))
        rep={'schema':'agent-interface/text-route-keymap-freshness-case-v1','target_layout':a.target_layout,'target_variant':a.target_variant,'matched_key_blocks':matched,'us_hash':us_hash,'target_hash':target_hash,'mapping_changed':changed,'current_direct_ok':current_direct_ok,'current_direct_error':current_err,'unsafe':{'emissions':unsafe_emissions,'actual':unsafe_text,'physical':unsafe_phys,'release_empty':unsafe_release},'safe':{'receipt':safe,'actual':safe_text},'fresh_transparent':transparent.__dict__,'fresh_clipboard':clip.__dict__,'fresh_clipboard_effect':{'paste_emissions':fresh_paste,'actual':fresh_clip_text,'version_before':before['version'],'version_after':after['version']},'final_map_hash':final_hash,'final_physical':final_phys,'gates':{'unsafe':unsafe_gate,'safe':safe_gate,'decision':decision_gate,'clipboard':clipboard_gate,'map':map_gate,'release':final_release},'passed':passed}
        (a.out/'report.json').write_text(json.dumps(rep,indent=2,ensure_ascii=False,default=lambda x:x.value if hasattr(x,'value') else list(x) if isinstance(x,frozenset) else str(x))+'\n');print(json.dumps({'layout':a.target_layout,'changed':changed,'unsafe_actual':unsafe_text,'safe_error':safe['error'],'transparent':transparent.selected,'clipboard':clip.selected,'clipboard_actual':fresh_clip_text,'passed':passed},ensure_ascii=False));return 0 if passed else 1
    finally:
        try:rpc(svc_sock,{'op':'quit'})
        except:pass
        try:svc.wait(timeout=.5)
        except:svc.kill()
        try:rpc(sock,{'op':'quit'})
        except:pass
        try:r.wait(timeout=.5)
        except:r.kill()
        d.close()
if __name__=='__main__':raise SystemExit(main())
