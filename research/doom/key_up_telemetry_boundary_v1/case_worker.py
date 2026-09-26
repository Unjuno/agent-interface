#!/usr/bin/env python3
import argparse, json, os, subprocess, sys, time
from pathlib import Path

SCHEDULES = {
    'ORDINARY_SINGLE': ['a'],
    'ORDINARY_MULTI': ['a', 'd'],
    'CANCEL_AFTER_HELD': ['a', 'd'],
    'CANCEL_DURING_ADMISSION': ['a', 'd'],
}

def now(): return time.perf_counter_ns()
def emit(rows, **kw):
    kw.setdefault('emit_ns', now()); rows.append(kw)

def key_is_down(bitmap, keycode):
    b = bitmap[keycode // 8]
    return bool(b & (1 << (keycode % 8)))

def drain_events(win):
    out=[]
    while win.display.pending_events():
        e=win.display.next_event()
        if e.type in (2,3):
            out.append({'type':'press' if e.type==2 else 'release','detail':int(e.detail),'observed_ns':now()})
    return out

def run(args):
    outdir=Path(args.out); outdir.mkdir(parents=True, exist_ok=False)
    display_num=300 + args.index
    xvfb=subprocess.Popen(['Xvfb',f':{display_num}','-screen','0','320x200x24','-nolisten','tcp','-ac'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    sock=Path(f'/tmp/.X11-unix/X{display_num}')
    deadline=time.time()+3
    while time.time()<deadline and not sock.exists():
        if xvfb.poll() is not None: break
        time.sleep(.02)
    if not sock.exists():
        so,se=xvfb.communicate(timeout=1)
        raise RuntimeError(f'Xvfb failed rc={xvfb.returncode} stdout={so!r} stderr={se!r}')
    os.environ['DISPLAY']=f':{display_num}'
    os.environ['XAUTHORITY']='/dev/null'
    from Xlib import X, display, XK
    from Xlib.ext import xtest
    d=display.Display()
    root=d.screen().root
    win=root.create_window(0,0,200,100,0,d.screen().root_depth,X.InputOutput,X.CopyFromParent,
                           background_pixel=d.screen().white_pixel,event_mask=X.KeyPressMask|X.KeyReleaseMask)
    win.map(); d.sync(); d.set_input_focus(win,X.RevertToParent,X.CurrentTime); d.sync()
    rows=[]
    keys=SCHEDULES[args.schedule]
    keycodes=[]
    for k in keys:
        kc=d.keysym_to_keycode(XK.string_to_keysym(k)); assert kc
        keycodes.append((k,kc))
    before=bytes(d.query_keymap())
    emit(rows,event='case_start',policy=args.policy,schedule=args.schedule,requested_keys=keys,before_keymap_hex=before.hex())
    admitted=[]
    for pos,(k,kc) in enumerate(keycodes):
        if args.schedule=='CANCEL_DURING_ADMISSION' and pos==1:
            emit(rows,event='cancel_requested',reason='directed_after_first_admission')
            break
        call_ns=now(); xtest.fake_input(d,X.KeyPress,kc); d.sync(); ack_ns=now()
        admitted.append((k,kc,ack_ns))
        emit(rows,event='input_admission',id='p',step=0,key=k,call_ns=call_ns,input_ack_ns=ack_ns)
    full=len(admitted)==len(keycodes)
    if full:
        emit(rows,event='keys_held',id='p',step=0,keys=[k for k,_,_ in admitted],input_ack_ns=now())
    if args.schedule in ('ORDINARY_SINGLE','ORDINARY_MULTI'):
        time.sleep(.220)
    elif args.schedule=='CANCEL_AFTER_HELD':
        time.sleep(.035); emit(rows,event='cancel_requested',reason='after_keys_held')
    release_receipts=[]
    for k,kc,_down_ack in reversed(admitted):
        call_ns=now(); xtest.fake_input(d,X.KeyRelease,kc); d.sync(); ack_ns=now()
        if args.policy=='KEY_UP_RECEIPT':
            rec={'event':'key_released','id':'p','step':0,'key':k,'call_ns':call_ns,'input_ack_ns':ack_ns}
            rows.append({**rec,'emit_ns':now()}); release_receipts.append(rec)
    final=bytes(d.query_keymap()); verified_ns=now()
    neutral=all(not key_is_down(final,kc) for _,kc in keycodes)
    emit(rows,event='owner_release',id='p',reason=('completed' if args.schedule.startswith('ORDINARY') else 'cancelled'),verified=neutral,verified_ns=verified_ns,keys_down=[k for k,kc in keycodes if key_is_down(final,kc)])
    xevents=drain_events(win)
    terminal=bytes(d.query_keymap()); terminal_neutral=all(not key_is_down(terminal,kc) for _,kc in keycodes)
    emit(rows,event='terminal',id='p',status=('completed' if args.schedule.startswith('ORDINARY') else 'cancelled'),full_keyset_established=full,admitted_keys=[k for k,_,_ in admitted],release_receipt_keys=[r['key'] for r in release_receipts],verified_empty=terminal_neutral,authority='none')
    (outdir/'events.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows),encoding='utf-8')
    (outdir/'xevents.json').write_text(json.dumps(xevents,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    result={'policy':args.policy,'schedule':args.schedule,'requested_keys':keys,'admitted_keys':[k for k,_,_ in admitted],
            'full_keyset_established':full,'release_receipt_keys':[r['key'] for r in release_receipts],
            'terminal_neutral':terminal_neutral,'xevents':xevents,'worker_pid':os.getpid()}
    (outdir/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    win.destroy(); d.sync(); d.close()
    xvfb.terminate()
    try: xvfb.wait(timeout=2)
    except subprocess.TimeoutExpired:
        xvfb.kill(); xvfb.wait(timeout=2)
    (outdir/'xvfb_exit.json').write_text(json.dumps({'returncode':xvfb.returncode})+'\n')
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--policy',choices=['BASELINE','KEY_UP_RECEIPT'],required=True); ap.add_argument('--schedule',choices=list(SCHEDULES),required=True); ap.add_argument('--index',type=int,required=True); ap.add_argument('--out',required=True)
    run(ap.parse_args())
