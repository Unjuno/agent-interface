#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,sys,time
from pathlib import Path
from Xlib import X,XK,display
from Xlib.ext import xtest
HERE=Path(__file__).resolve().parent
PORTABLE=Path(os.environ['AGENT_INTERFACE_PORTABLE_ORACLE']); sys.path.insert(0,str(PORTABLE))
from contract import OFFICE_FLOOR, admit_program, capability_manifest
from clipboard_lease import ClipboardLease
CORPUS=['café','βeta','東京','あいうえお','🙂','e\u0301','naïve','résumé','中文','한국']
WRITER_PAYLOAD='sentinel\n'+'\n'.join(CORPUS)
CALC_PAYLOAD='\n'.join(CORPUS)

def program(pid,seq,text):
    return {'schema':'agent-interface/program-v0','program_id':pid,'source':{'observation_seq':seq,'binding_revision':1},'authority':{'lease_id':'unicode-clipboard-v1','expires_at_ns':time.monotonic_ns()+60_000_000_000},'ops':[{'op':'focus','target':'office'},{'op':'text','text':text},{'op':'release_all'}],'terminal':{'release_all_required':True}}
def kcode(d,n):
    aliases={'CTRL':'Control_L','ENTER':'Return','HOME':'Home'}; sym=XK.string_to_keysym(aliases.get(n,n)); c=d.keysym_to_keycode(sym)
    if not c: raise RuntimeError(f'key {n}')
    return c
def chord(d,ns):
    cs=[kcode(d,n) for n in ns]
    for c in cs: xtest.fake_input(d,X.KeyPress,c)
    for c in reversed(cs): xtest.fake_input(d,X.KeyRelease,c)
    d.sync()
def click(d,w,x,y):
    t=w.translate_coords(d.screen().root,0,0); xtest.fake_input(d,X.MotionNotify,x=t.x+x,y=t.y+y); xtest.fake_input(d,X.ButtonPress,1); xtest.fake_input(d,X.ButtonRelease,1); d.sync()
def owner_id(d):
    o=d.get_selection_owner(d.intern_atom('CLIPBOARD')); return getattr(o,'id',None)
def owner_id_fresh(display_name):
    q=display.Display(display_name)
    try: return owner_id(q)
    finally: q.close()
def clip_read(display_name):
    c=ClipboardLease(display_name)
    try:return c.read_text()
    finally:c.close()
def map_snapshot(d):
    mn=d.display.info.min_keycode; mx=d.display.info.max_keycode
    return [tuple(x) for x in d.get_keyboard_mapping(mn,mx-mn+1)]
def physical_down(d):
    km=d.query_keymap(); out=[]
    for n in ['Control_L','v','s','Home','Return']:
        c=kcode(d,n)
        if km[c//8] & (1 << (c%8)): out.append(n)
    mask=d.screen().root.query_pointer().mask
    return {'keys':out,'buttons':[n for n,b in [('left',X.Button1Mask),('middle',X.Button2Mask),('right',X.Button3Mask)] if mask&b]}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--display',required=True); ap.add_argument('--window-id',type=int,required=True); ap.add_argument('--app',choices=['writer','calc'],required=True); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); a.out.mkdir(parents=True,exist_ok=False)
    d=display.Display(a.display); w=d.create_resource_object('window',a.window_id); mapping_before=map_snapshot(d)
    # Candidate has generic v0 text semantic but explicitly depends on clipboard capabilities out-of-band.
    man=capability_manifest('unicode-clipboard-lowering-v1','linux','x11',OFFICE_FLOOR|{'clipboard.read','clipboard.write'},frames=('screen_physical_px','window_client'))
    prev_owner=owner_id(d); prev_text=clip_read(a.display)
    payload = WRITER_PAYLOAD if a.app=='writer' else CALC_PAYLOAD
    stale=program('unicode-stale',4,payload); sa=admit_program(stale,man,now_ns=time.monotonic_ns(),current_observation_seq=5,current_binding_revision=1)
    stale_owner=owner_id(d); stale_text=clip_read(a.display)
    task=program('unicode-fresh',5,payload); adm=admit_program(task,man,now_ns=time.monotonic_ns(),current_observation_seq=5,current_binding_revision=1)
    if not adm.accepted: raise RuntimeError(adm)
    w.set_input_focus(X.RevertToParent,X.CurrentTime); d.sync(); time.sleep(.05)
    if a.app=='writer':
        click(d,w,300,250); time.sleep(.05); chord(d,['CTRL','a'])
    else:
        click(d,w,80,180); time.sleep(.05); chord(d,['CTRL','HOME'])
    lease=ClipboardLease(a.display); owner_during=None; owner_restored=None; restored_text=None
    try:
        lease.set_text(payload); owner_during=lease.owner_id(); chord(d,['CTRL','v'])
        if a.app=='calc':
            lease.pump(.40); chord(d,['ENTER']); lease.pump(.50)
        else:
            lease.pump(.55)
        lease.set_text(prev_text); restored_text=lease.read_text(); owner_restored=lease.owner_id()
        chord(d,['CTRL','s'])
        if a.app=='calc':
            lease.pump(.40); chord(d,['ENTER']); lease.pump(1.20)
        else:
            lease.pump(.80)
        # Capture state while lease is alive.
        mapping_after=map_snapshot(d); released=physical_down(d)
        # Destroy lease while previous owner process remains alive; previous owner cannot reclaim automatically.
        lease.close(); time.sleep(.05); owner_after_close=owner_id_fresh(a.display)
    finally:
        try: lease.close()
        except: pass
    out={'schema':'agent-interface/x11-unicode-clipboard-execution-v1','app':a.app,'corpus':CORPUS,'payload':payload,'stale':{'accepted':sa.accepted,'error':sa.error,'owner_before':prev_owner,'owner_after':stale_owner,'text_before':prev_text,'text_after':stale_text},'fresh_admission':{'accepted':adm.accepted,'error':adm.error},'clipboard':{'owner_before':prev_owner,'owner_during':owner_during,'owner_after_restore_alive':owner_restored,'owner_after_lease_close':owner_after_close,'previous_text':prev_text,'restored_text':restored_text,'utf8_text_restored_while_alive':restored_text==prev_text,'owner_identity_restored':owner_restored==prev_owner,'owner_reclaimed_after_close':owner_after_close==prev_owner},'keymap_unchanged':mapping_before==mapping_after,'release':released,'passed_transport':(not sa.accepted and sa.error=='STALE_OBSERVATION' and stale_owner==prev_owner and stale_text==prev_text and restored_text==prev_text and mapping_before==mapping_after and not released['keys'] and not released['buttons'])}
    (a.out/'execution.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,indent=2)); d.close(); return 0 if out['passed_transport'] else 1
if __name__=='__main__': raise SystemExit(main())
