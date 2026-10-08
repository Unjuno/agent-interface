from __future__ import annotations
import json,select,subprocess,sys,threading,time
from pathlib import Path
from Xlib import X,XK,display
from Xlib.ext import record
def wait(fn,timeout=5):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        v=fn()
        if v:return v
        time.sleep(.01)
    raise TimeoutError('bounded no-input wait expired')
def main():
    out=Path(sys.argv[1]);appsrc=Path(sys.argv[2]);obssrc=Path(sys.argv[3])
    if out.exists() and any(out.iterdir()):raise SystemExit('STOP_OUTPUT_EXISTS')
    out.mkdir(parents=True,exist_ok=True);tk=out/'tk';obslog=out/'observer_events.jsonl';app=obs=None;owner=control=probe=None;ctx=None;blocks=[];rec_errors=[];started=threading.Event();error=None;ready=None
    def cb(reply):
        b={'category':int(reply.category),'data_hex':bytes(reply.data or b'').hex(),'client_swapped':bool(reply.client_swapped)};blocks.append(b)
        if b['category']==record.StartOfData:started.set()
    def rec_loop():
        try:owner.record_enable_context(ctx,cb)
        except Exception as e:rec_errors.append(repr(e))
    try:
        app=subprocess.Popen([sys.executable,str(appsrc),str(tk),str(out/'unused_actions.json')],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True);sf=tk/'state.json'
        wait(lambda:json.loads(sf.read_text()) if sf.exists() else None);state=wait(lambda:(s if (s:=(json.loads(sf.read_text()) if sf.exists() else {})).get('focus_widget') else None))
        obs=subprocess.Popen([sys.executable,str(obssrc),str(state['root_xid']),str(obslog)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
        ready=json.loads(wait(lambda:obs.stdout.readline().strip() if select.select([obs.stdout],[],[],0)[0] else None))
        probe=display.Display();kc_a=probe.keysym_to_keycode(XK.XK_a);kc_s=probe.keysym_to_keycode(XK.XK_Shift_L)
        def state_up(km,kc):return not bool(km[kc>>3]&(1<<(kc&7)))
        km0=bytes(probe.query_keymap());neutral0={'a':state_up(km0,kc_a),'Shift_L':state_up(km0,kc_s)}
        owner=display.Display();control=display.Display();ctx=owner.record_create_context(0,[record.AllClients],[dict(core_requests=(0,0),core_replies=(0,0),ext_requests=(0,0,0,0),ext_replies=(0,0,0,0),delivered_events=(X.KeyPress,X.KeyRelease),device_events=(0,0),errors=(0,0),client_started=False,client_died=False)])
        worker=threading.Thread(target=rec_loop,daemon=True);worker.start();wait(started.is_set,2);time.sleep(.5)
        km1=bytes(probe.query_keymap());neutral1={'a':state_up(km1,kc_a),'Shift_L':state_up(km1,kc_s)}
        raw={'schema':'blackstart-x11-noinput-baseline-t12-raw-v1','input_dispatched':False,'baseline_seconds':.5,'keycodes':{'a':kc_a,'Shift_L':kc_s},'initial_neutral':neutral0,'terminal_neutral':neutral1,'ready':ready,'observer_rows':[json.loads(x) for x in obslog.read_text().splitlines() if x] if obslog.exists() else [],'record_blocks':blocks,'record_errors':rec_errors,'error':None}
    except Exception as e:raw={'schema':'blackstart-x11-noinput-baseline-t12-raw-v1','input_dispatched':False,'error':{'type':type(e).__name__,'message':str(e)},'ready':ready,'record_blocks':blocks,'record_errors':rec_errors}
    finally:
        if ctx is not None and control is not None:
            try:control.record_disable_context(ctx)
            except Exception as e:rec_errors.append(repr(e))
        if 'worker' in locals():worker.join(2)
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
        for d in (control,owner,probe):
            if d is not None:
                try:d.close()
                except Exception:pass
        if 'raw' not in locals():raw={'schema':'blackstart-x11-noinput-baseline-t12-raw-v1','input_dispatched':False,'error':{'type':'incomplete','message':'runner stopped before raw outcome'}}
        raw['record_errors']=rec_errors;raw['app_returncode']=app.returncode if app else None
        (out/'record_blocks.jsonl').write_text(''.join(json.dumps(b,sort_keys=True)+'\n' for b in blocks),encoding='utf8')
        (out/'run.raw.json').write_text(json.dumps(raw,indent=2,sort_keys=True)+'\n')
    return 0 if raw.get('error') is None and raw.get('input_dispatched') is False else 2
if __name__=='__main__':raise SystemExit(main())
