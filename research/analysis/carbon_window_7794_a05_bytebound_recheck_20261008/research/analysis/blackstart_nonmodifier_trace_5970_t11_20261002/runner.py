from __future__ import annotations
import json,select,subprocess,sys,threading,time,uuid
from pathlib import Path
from Xlib import X,XK,display
from Xlib.ext import record,xtest
def wait(fn,timeout=5):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        v=fn()
        if v:return v
        time.sleep(.01)
    raise TimeoutError('bounded wait expired')
def rows(p):return [json.loads(x) for x in p.read_text().splitlines() if x] if p.exists() else []
def main():
    out=Path(sys.argv[1]);appsrc=Path(sys.argv[2]);obssrc=Path(sys.argv[3])
    if out.exists() and any(out.iterdir()):raise SystemExit('STOP_OUTPUT_EXISTS')
    out.mkdir(parents=True,exist_ok=True);tk=out/'tk';applog=tk/'app_events.jsonl';obslog=out/'observer_events.jsonl';acts=out/'actions.json';driver=out/'driver.jsonl'
    epoch='t11-'+uuid.uuid4().hex;ids={k:f'{epoch}:{k.lower()}' for k in ('KeyPress','KeyRelease')};acts.write_text(json.dumps({'by_kind':{k:{'seq':i,'actuation_id':v} for i,(k,v) in enumerate(ids.items(),1)}}))
    app=obs=owner=control=inject=None;ctx=None;keycode=0;released=False;initial_neutral=None;terminal_neutral=None;error=None;ready=None;blocks=[];rec_errors=[];started=threading.Event()
    def log(phase,**kw):
        with driver.open('a',encoding='utf8') as f:f.write(json.dumps({'phase':phase,'mono_ns':time.monotonic_ns(),**kw},sort_keys=True)+'\n')
    def callback(reply):
        b={'category':int(reply.category),'data_hex':bytes(reply.data or b'').hex(),'client_swapped':bool(reply.client_swapped)};blocks.append(b)
        if b['category']==record.StartOfData:started.set()
    def rec_loop():
        try:owner.record_enable_context(ctx,callback)
        except Exception as e:rec_errors.append(repr(e))
    try:
        app=subprocess.Popen([sys.executable,str(appsrc),str(tk),str(acts)],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True);sf=tk/'state.json'
        wait(lambda:json.loads(sf.read_text()) if sf.exists() else None);state=wait(lambda:(s if (s:=(json.loads(sf.read_text()) if sf.exists() else {})).get('focus_widget') else None))
        obs=subprocess.Popen([sys.executable,str(obssrc),str(state['root_xid']),str(obslog)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
        ready=json.loads(wait(lambda:obs.stdout.readline().strip() if select.select([obs.stdout],[],[],0)[0] else None))
        if not ready.get('ready'):raise RuntimeError('OBSERVER_NOT_READY')
        owner=display.Display();control=display.Display();inject=display.Display();keycode=inject.keysym_to_keycode(XK.XK_a)
        if not keycode:raise RuntimeError('A_KEYCODE_MISSING')
        km=bytes(inject.query_keymap());initial_neutral=not bool(km[keycode>>3]&(1<<(keycode&7)))
        if not initial_neutral:raise RuntimeError('A_KEY_NOT_NEUTRAL_BEFORE_TRIAL')
        ctx=owner.record_create_context(0,[record.AllClients],[dict(core_requests=(0,0),core_replies=(0,0),ext_requests=(0,0,0,0),ext_replies=(0,0,0,0),delivered_events=(X.KeyPress,X.KeyRelease),device_events=(0,0),errors=(0,0),client_started=False,client_died=False)])
        worker=threading.Thread(target=rec_loop,daemon=True);worker.start();wait(started.is_set,2)
        log('record_started',context_id=ctx,keycode=keycode,initial_neutral=initial_neutral,selected_xids=ready['selected_xids'],parent_xid=ready['parent_xid'])
        log('press_dispatch',keycode=keycode,actuation_id=ids['KeyPress']);xtest.fake_input(inject,X.KeyPress,detail=keycode);inject.sync();wait(lambda:any(r.get('actuation_id')==ids['KeyPress'] for r in rows(applog)))
    except Exception as e:error={'type':type(e).__name__,'message':str(e)};log('candidate_error',error=error)
    finally:
        if inject is not None and keycode:
            try:
                log('release_dispatch_cleanup',keycode=keycode,actuation_id=ids['KeyRelease']);xtest.fake_input(inject,X.KeyRelease,detail=keycode);inject.sync();released=True
                try:wait(lambda:any(r.get('actuation_id')==ids['KeyRelease'] for r in rows(applog)),2)
                except Exception:log('release_app_row_missing')
                try:wait(lambda:len(rows(obslog))>=2,1.5)
                except Exception:log('observer_pair_wait_expired',observer_rows=rows(obslog))
            except Exception as e:log('cleanup_error',message=repr(e))
        if ctx is not None and control is not None:
            try:control.record_disable_context(ctx)
            except Exception as e:rec_errors.append(repr(e))
        if 'worker' in locals():worker.join(2)
        if inject is not None and keycode:
            try:km=bytes(inject.query_keymap());terminal_neutral=not bool(km[keycode>>3]&(1<<(keycode&7)));log('terminal_keymap',neutral=terminal_neutral,keymap_hex=km.hex())
            except Exception as e:log('keymap_error',message=repr(e))
        if obs is not None and obs.poll() is None:
            try:obs.stdin.write('stop\n');obs.stdin.flush();obs.wait(timeout=2)
            except Exception:obs.terminate();obs.wait(timeout=2)
        if app is not None and app.poll() is None:
            app.terminate()
            try:app.wait(timeout=2)
            except subprocess.TimeoutExpired:app.kill();app.wait(timeout=2)
        if ctx is not None and owner is not None:
            try:owner.record_free_context(ctx)
            except Exception as e:rec_errors.append(repr(e))
        for d in (control,inject,owner):
            if d is not None:
                try:d.close()
                except Exception:pass
        (out/'record_blocks.jsonl').write_text(''.join(json.dumps(b,sort_keys=True)+'\n' for b in blocks),encoding='utf8')
    result={'schema':'blackstart-nonmodifier-trace-t11-raw-v1','epoch':epoch,'keysym':'a','keycode':keycode,'ready':ready,'initial_neutral':initial_neutral,'app_rows':rows(applog),'observer_rows':rows(obslog),'record_blocks':blocks,'record_errors':rec_errors,'release_attempted':released,'terminal_neutral':terminal_neutral,'error':error}
    (out/'run.raw.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');return 0 if released and initial_neutral is True and terminal_neutral is True else 2
if __name__=='__main__':raise SystemExit(main())
