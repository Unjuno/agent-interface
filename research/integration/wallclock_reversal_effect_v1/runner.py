#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, pathlib, subprocess, time
from Xlib import X, XK, display
from Xlib.ext import xtest
from candidate import decide, admit

SCENARIOS=['RIGHT_RECENT_REVERSAL','LEFT_RECENT_REVERSAL','RIGHT_AGE200','LEFT_AGE200','DUPLICATE_SOURCE','CROSS_EPOCH_OR_STALE']
FORMAL_BATCHES={1:[(s,0) for s in SCENARIOS],2:[(s,1) for s in SCENARIOS]}


def read_json_line(pipe, noise):
    while True:
        line=pipe.readline()
        if not line: raise RuntimeError('EOF_BEFORE_JSON')
        try: return json.loads(line)
        except json.JSONDecodeError: noise.append(line.rstrip())


def wait_display(env,xv):
    end=time.monotonic()+3
    while time.monotonic()<end:
        if xv.poll() is not None: raise RuntimeError(f'XVFB_EXIT:{xv.returncode}')
        try:
            d=display.Display(env['DISPLAY']); d.close(); return
        except Exception: time.sleep(.02)
    raise RuntimeError('XVFB_NOT_READY')


def keymap_down(d,keycode):
    keys=d.query_keymap()
    idx=keycode//8; bit=1<<(keycode%8)
    return bool(keys[idx]&bit)


def fixture(scenario,rep,base_ns):
    epoch='epoch-A'; session=f'session-{scenario.lower()}-r{rep}'
    if scenario in ('RIGHT_RECENT_REVERSAL','LEFT_RECENT_REVERSAL'):
        post=1 if scenario.startswith('RIGHT') else -1
        # reversal at -75 ms; newest/middle straddle symmetrically, preceding interval is full old direction
        rel=[-25_000_000,-125_000_000,-225_000_000]
        r=-75_000_000
    elif scenario in ('RIGHT_AGE200','LEFT_AGE200'):
        post=1 if scenario.startswith('RIGHT') else -1
        rel=[0,-100_000_000,-200_000_000]; r=-200_000_000
    elif scenario=='DUPLICATE_SOURCE':
        post=1; rel=[0,0,-100_000_000]; r=-75_000_000
    else:
        post=1; rel=[-25_000_000,-125_000_000,-225_000_000]; r=-75_000_000
    rec=[]
    for i,t in enumerate(rel):
        pre=-post
        dt=(t-r)/1e9
        x=(pre if t<=r else post)*73.0*dt
        ep=epoch
        if scenario=='CROSS_EPOCH_OR_STALE' and rep==0 and i==2: ep='epoch-B'
        rec.append({'source_ns':base_ns+t,'x':x,'epoch':ep,'sequence':3-i})
    return session,epoch,post,rec


def run_case(root,scenario,rep,display_no,phase):
    case_id=f'{phase}-{scenario.lower()}-r{rep}'; cdir=root/case_id; cdir.mkdir(parents=True)
    sock=pathlib.Path(f'/tmp/.X11-unix/X{display_no}'); lock=pathlib.Path(f'/tmp/.X{display_no}-lock')
    if sock.exists() or lock.exists(): raise RuntimeError('PREEXISTING_DISPLAY')
    xauth=cdir/'Xauthority'; xauth.write_bytes(b'')
    env=dict(os.environ,DISPLAY=f':{display_no}',XAUTHORITY=str(xauth),PYTHONDONTWRITEBYTECODE='1')
    os.environ['DISPLAY']=env['DISPLAY']; os.environ['XAUTHORITY']=env['XAUTHORITY']
    xv=subprocess.Popen(['Xvfb',f':{display_no}','-screen','0','360x180x24','-nolisten','tcp','-ac'],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    app=None; d=None
    try:
        wait_display(env,xv)
        app=subprocess.Popen(['python','-B',str(pathlib.Path(__file__).with_name('app.py'))],env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
        noise=[]; ready=read_json_line(app.stdout,noise)
        if ready.get('event')!='ready': raise RuntimeError(f'APP_NOT_READY:{ready}')
        d=display.Display(env['DISPLAY']); winid=int(ready['window_id'])
        focus=int(d.get_input_focus().focus.id)
        if focus!=winid: raise RuntimeError(f'FOCUS_MISMATCH:{focus}:{winid}')
        left=d.keysym_to_keycode(XK.string_to_keysym('Left')); right=d.keysym_to_keycode(XK.string_to_keysym('Right'))
        if not left or not right: raise RuntimeError('KEYCODE_MISSING')
        before={'left':keymap_down(d,left),'right':keymap_down(d,right)}
        if any(before.values()): raise RuntimeError('KEY_NOT_NEUTRAL_BEFORE')
        base=time.perf_counter_ns(); session,epoch,post,records=fixture(scenario,rep,base)
        decision=decide(records,session_id=session,window_id=winid); created=time.perf_counter_ns()
        # Pure binding probe must fail closed and never dispatch input.
        foreign=admit(decision,now_ns=created,decision_created_ns=created,session_id=session+'-foreign',epoch=epoch,window_id=winid+1)
        if foreign.get('admitted'): raise RuntimeError('FOREIGN_BINDING_ADMITTED')
        if scenario=='CROSS_EPOCH_OR_STALE' and rep==1:
            time.sleep(.170)
        now=time.perf_counter_ns(); admission=admit(decision,now_ns=now,decision_created_ns=created,session_id=session,epoch=epoch,window_id=winid)
        input_events=[]
        if admission.get('admitted'):
            keycode=right if admission['direction']==1 else left
            name='Right' if admission['direction']==1 else 'Left'
            t0=time.perf_counter_ns(); xtest.fake_input(d,X.KeyPress,keycode); d.sync(); t1=time.perf_counter_ns()
            xtest.fake_input(d,X.KeyRelease,keycode); d.sync(); t2=time.perf_counter_ns()
            input_events=[{'kind':'press','key':name,'keycode':keycode,'request_ns':t0,'sync_ns':t1},{'kind':'release','key':name,'keycode':keycode,'request_ns':t1,'sync_ns':t2}]
        time.sleep(.04)
        app.stdin.write(json.dumps({'op':'snapshot'})+'\n'); app.stdin.flush(); snap=read_json_line(app.stdout,noise)
        after={'left':keymap_down(d,left),'right':keymap_down(d,right)}
        expected_effect=post if scenario in ('RIGHT_RECENT_REVERSAL','LEFT_RECENT_REVERSAL') else 0
        result={'schema':'agent-interface/wallclock-reversal-effect-case-v1','case_id':case_id,'phase':phase,'scenario':scenario,'rep':rep,
                'session_id':session,'epoch':epoch,'window_id':winid,'source_records':records,'oracle_post_dir':post,
                'decision':decision,'decision_created_ns':created,'admission_checked_ns':now,'admission':admission,'foreign_binding_probe':foreign,
                'input_events':input_events,'app_snapshot':snap,'keymap_before':before,'keymap_after':after,'expected_effect':expected_effect,
                'app_startup_noise':noise,'authority':'none'}
        return result,cdir,xv,app,d
    except Exception:
        raise


def cleanup(xv,app,d):
    if d is not None:
        try: d.close()
        except Exception: pass
    app_rc=None; app_err=''
    if app is not None:
        try:
            if app.poll() is None:
                app.stdin.write(json.dumps({'op':'close'})+'\n'); app.stdin.flush();
                read_json_line(app.stdout,[])
            app_rc=app.wait(timeout=2)
        except Exception:
            app.kill(); app_rc=app.wait(timeout=2)
        app_err=app.stderr.read()
    try: xv.terminate(); xv_rc=xv.wait(timeout=2)
    except Exception: xv.kill(); xv_rc=xv.wait(timeout=2)
    return {'app_exit':app_rc,'xvfb_exit':xv_rc,'app_stderr':app_err,'xvfb_stderr':xv.stderr.read()}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--mode',choices=['construction','formal'],required=True); ap.add_argument('--batch',type=int); ap.add_argument('--out',required=True)
    a=ap.parse_args(); root=pathlib.Path(a.out); root.mkdir(parents=True,exist_ok=False)
    sched=[(s,0) for s in SCENARIOS] if a.mode=='construction' else FORMAL_BATCHES.get(a.batch)
    if sched is None: raise SystemExit('invalid batch')
    rows=[]; raw=root/'RAW.jsonl'
    for j,(scenario,rep) in enumerate(sched):
        xv=app=d=None
        try:
            r,cdir,xv,app,d=run_case(root,scenario,rep,450+(a.batch or 0)*20+j,a.mode)
            r['cleanup']=cleanup(xv,app,d); xv=app=d=None
            (cdir/'RESULT.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
            rows.append(r)
            with raw.open('a') as f: f.write(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n')
        except Exception as e:
            if xv is not None:
                try: cleanup(xv,app,d)
                except Exception: pass
            (root/'STOP.json').write_text(json.dumps({'scenario':scenario,'rep':rep,'error':repr(e)},indent=2)+'\n')
            raise
    summary={'mode':a.mode,'batch':a.batch,'cases':len(rows),'effects':[r['app_snapshot']['effect'] for r in rows],
             'admitted':sum(bool(r['admission'].get('admitted')) for r in rows),'neutral':sum(not any(r['keymap_after'].values()) for r in rows),
             'wrong_effects':sum(r['app_snapshot']['effect']!=r['expected_effect'] for r in rows)}
    (root/'SUMMARY.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n'); print(json.dumps(summary,sort_keys=True))
if __name__=='__main__': main()
