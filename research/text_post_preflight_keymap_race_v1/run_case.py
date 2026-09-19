#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,socket,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace
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

def apply_rows(d,rows,first):
    d.change_keyboard_mapping(first,[tuple(r) for r in rows]);d.sync()

def resolved_rows(d,layout,variant,outdir):
    outdir.mkdir(parents=True,exist_ok=True)
    first=d.display.info.min_keycode; cur=dep.keyboard_mapping(d)
    text=resolve_xkb(os.environ['DISPLAY'],os.environ['XAUTHORITY'],layout,variant,outdir)
    rows,matched=project_group1_two_levels(text,first,cur)
    return rows,matched

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--target-layout',required=True);ap.add_argument('--target-variant',default='');ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=False)
    if not os.environ.get('DISPLAY') or not os.environ.get('XAUTHORITY'):raise RuntimeError('xvfb-run required')
    d=display.Display();first=d.display.info.min_keycode
    us_rows,us_matched=resolved_rows(d,'us','',a.out/'us-map');apply_rows(d,us_rows,first);us_live=dep.keyboard_mapping(d);us_hash=dep.fingerprint(us_live)
    plan=dep.prepare('@',us_live,first)
    target_rows,target_matched=resolved_rows(d,a.target_layout,a.target_variant,a.out/'target-map')
    # resolved_rows bases untouched keys on current US map; target mapping isn't applied yet.
    target_expected=dep.fingerprint(target_rows)
    sock=str(a.out/'receiver.sock');r=subprocess.Popen([sys.executable,str(HERE/'receiver.py'),sock],env=os.environ.copy(),text=True,stdout=subprocess.PIPE,stderr=(a.out/'receiver.stderr').open('w'));xid=int(json.loads(r.stdout.readline())['xid']);win=d.create_resource_object('window',xid);win.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync();time.sleep(.02)
    mutator=display.Display();orig=xtest.fake_input;state={'calls':0,'mutation_done_ns':None,'first_forward_ns':None,'mutated':False,'target_hash_after_mutation':None}
    changed=(a.target_layout!='us' or bool(a.target_variant))
    def wrapped(dd,*args,**kwargs):
        if state['calls']==0:
            if changed:
                apply_rows(mutator,target_rows,first);state['mutation_done_ns']=time.monotonic_ns();state['mutated']=True;state['target_hash_after_mutation']=dep.fingerprint(dep.keyboard_mapping(mutator))
            state['first_forward_ns']=time.monotonic_ns()
        state['calls']+=1
        return orig(dd,*args,**kwargs)
    xtest.fake_input=wrapped
    try:
        rpc(sock,{'op':'reset'});win.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync();backend=SimpleNamespace(d=d,emissions=0)
        receipt=dep.deliver(backend,'@',target=xid,observation=1,current_observation=1,revision=1,current_revision=1,expires_ns=time.monotonic_ns()+2_000_000_000,pacing_s=.001)
    finally:
        xtest.fake_input=orig
    time.sleep(.02);actual=rpc(sock,{'op':'get'})['text'];final_map=dep.keyboard_mapping(d);final_hash=dep.fingerprint(final_map);physical=dep.physical_state(d)
    try:rpc(sock,{'op':'quit'})
    except Exception:pass
    try:r.wait(timeout=.5)
    except subprocess.TimeoutExpired:r.kill();r.wait()
    mutator.close();d.close()
    timing_ok=(not changed) or (state['mutation_done_ns'] is not None and state['first_forward_ns'] is not None and state['mutation_done_ns'] <= state['first_forward_ns'])
    control_ok=(receipt['accepted'] and actual=='@' and receipt['emissions']>0 and final_hash==us_hash) if not changed else True
    negative_ok=(receipt['accepted'] and receipt['error'] is None and receipt['emissions']>0 and actual!='@' and state['target_hash_after_mutation']==final_hash and final_hash!=us_hash and timing_ok) if changed else True
    passed=control_ok and negative_ok and receipt['release_verified'] and not physical['keys'] and not physical['mask']
    row={'schema':'agent-interface/text-post-preflight-keymap-race-case-v1','target_layout':a.target_layout,'target_variant':a.target_variant,'changed':changed,'us_hash':us_hash,'target_expected_projection_hash':target_expected,'target_hash_after_mutation':state['target_hash_after_mutation'],'final_hash':final_hash,'us_matched_blocks':us_matched,'target_matched_blocks':target_matched,'compiled_plan':{'strokes':plan.strokes,'shift_code':plan.shift_code,'map_hash':plan.map_hash},'fault':state,'receipt':receipt,'actual':actual,'physical_after':physical,'gates':{'timing':timing_ok,'control':control_ok,'negative':negative_ok,'release':receipt['release_verified'] and not physical['keys'] and not physical['mask']},'passed':passed}
    (a.out/'report.json').write_text(json.dumps(row,indent=2,ensure_ascii=False,default=lambda x:list(x) if isinstance(x,tuple) else str(x))+'\n');print(json.dumps({'target':a.target_layout,'changed':changed,'actual':actual,'accepted':receipt['accepted'],'emissions':receipt['emissions'],'mutation_done_ns':state['mutation_done_ns'],'first_forward_ns':state['first_forward_ns'],'passed':passed},ensure_ascii=False,indent=2));return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())
