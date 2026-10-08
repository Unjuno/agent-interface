from __future__ import annotations

import json, os, select, subprocess, sys, threading, time, uuid
from pathlib import Path
from Xlib import X, XK, display
from Xlib.ext import record, xtest

def wait_for(fn, timeout=4):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        v=fn()
        if v: return v
        time.sleep(.01)
    raise TimeoutError("bounded wait expired")

def read_rows(p):
    return [json.loads(x) for x in p.read_text().splitlines() if x] if p.exists() else []

def main():
    out=Path(sys.argv[1]); app_script=Path(sys.argv[2]); obs_script=Path(sys.argv[3])
    if out.exists() and any(out.iterdir()): raise SystemExit("STOP_OUTPUT_ALREADY_EXISTS")
    out.mkdir(parents=True,exist_ok=True); tk=out/'tk'; app_log=tk/'app_events.jsonl'; obs_log=out/'observer_events.jsonl'
    raw_blocks=out/'record_blocks.jsonl'; actions=out/'actions.json'; driver=out/'driver.jsonl'
    epoch='t4-'+uuid.uuid4().hex; ids={k:f'{epoch}:{k.lower()}' for k in ('KeyPress','KeyRelease')}
    actions.write_text(json.dumps({'by_kind':{k:{'seq':i,'actuation_id':v} for i,(k,v) in enumerate(ids.items(),1)}}))
    owner=control=inject=app=observer=None; ctx=None; keycode=0; release_attempted=False; neutral=None; error=None
    lock=threading.Lock(); recording=threading.Event(); blocks=[]; rec_error=[]
    def log(phase,**kw):
        with driver.open('a',encoding='utf8') as f: f.write(json.dumps({'phase':phase,'mono_ns':time.monotonic_ns(),**kw},sort_keys=True)+'\n')
    def on_reply(reply):
        item={'category':int(reply.category),'data_hex':bytes(reply.data or b'').hex(),'element_header_hex':bytes(reply.element_header or b'').hex(),'client_swapped':bool(reply.client_swapped)}
        with lock: blocks.append(item)
        if int(reply.category)==record.StartOfData: recording.set()
    try:
        app=subprocess.Popen([sys.executable,str(app_script),str(tk),str(actions)],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
        state=wait_for(lambda: json.loads((tk/'state.json').read_text()) if (tk/'state.json').exists() else None)
        state=wait_for(lambda: (s if (s:=(json.loads((tk/'state.json').read_text()) if (tk/'state.json').exists() else {})).get('focus_widget') else None))
        observer=subprocess.Popen([sys.executable,str(obs_script),str(state['entry_xid']),epoch,str(obs_log),str(actions)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
        ready=json.loads(wait_for(lambda: observer.stdout.readline().strip() if select.select([observer.stdout],[],[],0)[0] else None))
        if ready.get('ready') is not True: raise RuntimeError('OBSERVER_NOT_READY')
        owner=display.Display(); control=display.Display(); inject=display.Display()
        if not owner.has_extension('RECORD') or not inject.has_extension('XTEST'): raise RuntimeError('REQUIRED_EXTENSION_MISSING')
        keycode=inject.keysym_to_keycode(XK.XK_Shift_L)
        if not keycode: raise RuntimeError('SHIFT_KEYCODE_MISSING')
        ctx=owner.record_create_context(0,[record.AllClients],[dict(core_requests=(0,0),core_replies=(0,0),ext_requests=(0,0,0,0),ext_replies=(0,0,0,0),delivered_events=(X.KeyPress,X.KeyRelease),device_events=(0,0),errors=(0,0),client_started=False,client_died=False)])
        worker=threading.Thread(target=lambda: _record_enable(owner,ctx,on_reply,rec_error),daemon=True); worker.start()
        wait_for(recording.is_set,2)
        log('record_started',context_id=ctx,keycode=keycode)
        log('press_dispatch',keycode=keycode,actuation_id=ids['KeyPress'])
        xtest.fake_input(inject,X.KeyPress,detail=keycode); inject.sync()
        wait_for(lambda: next((r for r in read_rows(app_log) if r.get('actuation_id')==ids['KeyPress']),None))
        log('press_app_seen')
    except Exception as e:
        error={'type':type(e).__name__,'message':str(e)}; log('candidate_error',error=error)
    finally:
        if inject is not None and keycode:
            try:
                log('release_dispatch_cleanup',keycode=keycode,actuation_id=ids['KeyRelease'])
                xtest.fake_input(inject,X.KeyRelease,detail=keycode); inject.sync(); release_attempted=True
                try: wait_for(lambda: next((r for r in read_rows(app_log) if r.get('actuation_id')==ids['KeyRelease']),None),2)
                except Exception: log('release_app_row_missing')
            except Exception as e: log('cleanup_error',message=repr(e))
        if ctx is not None and control is not None:
            try: control.record_disable_context(ctx)
            except Exception as e: rec_error.append(repr(e))
        if 'worker' in locals(): worker.join(2)
        if inject is not None and keycode:
            try:
                km=bytes(inject.query_keymap()); neutral=not bool(km[keycode>>3]&(1<<(keycode&7))); log('terminal_keymap',neutral=neutral,keymap_hex=km.hex())
            except Exception as e: log('keymap_error',message=repr(e))
        if observer is not None and observer.poll() is None:
            try: observer.stdin.write('stop\n'); observer.stdin.flush(); observer.wait(timeout=2)
            except Exception: observer.terminate(); observer.wait(timeout=2)
        if app is not None and app.poll() is None:
            app.terminate()
            try: app.wait(timeout=2)
            except subprocess.TimeoutExpired: app.kill(); app.wait(timeout=2)
        if ctx is not None and owner is not None:
            try: owner.record_free_context(ctx)
            except Exception as e: rec_error.append(repr(e))
        for d in (control,inject,owner):
            if d is not None:
                try: d.close()
                except Exception: pass
        with raw_blocks.open('w',encoding='utf8') as f:
            for b in blocks: f.write(json.dumps(b,sort_keys=True)+'\n')
    result={'schema':'blackstart-xrecord-t4-run-v1','epoch':epoch,'keycode':keycode,'app_rows':read_rows(app_log),'observer_rows':read_rows(obs_log),'record_blocks':blocks,'record_errors':rec_error,'release_attempted':release_attempted,'terminal_neutral':neutral,'error':error,'ready':ready if 'ready' in locals() else None}
    (out/'run.raw.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    return 0 if release_attempted and neutral is True and error is None else 2

def _record_enable(owner,ctx,callback,errors):
    try: owner.record_enable_context(ctx,callback)
    except Exception as e: errors.append(repr(e))

if __name__=='__main__': raise SystemExit(main())
