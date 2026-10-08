"""Image-only horizontal tracking; oracle is opened only after input has stopped."""
import argparse,contextlib,hashlib,json,shutil,sys,time
from pathlib import Path
import numpy as np
from PIL import ImageGrab

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'observation_gating'))
import gui_suite as suite


def locate(im):
    p=np.asarray(im)
    red=(p[:,:,0]>220)&(p[:,:,1]<60)&(p[:,:,2]<60)
    green=(p[:,:,1]>220)&(p[:,:,0]<60)&(p[:,:,2]<60)
    if red.sum()<100 or green.sum()<100:raise RuntimeError('visible target or player lost')
    return float(np.where(red)[1].mean()),float(np.where(green)[1].mean())


def run(out,seed,mode,delay_ms,seconds):
    out.mkdir(parents=True,exist_ok=False);session=None;rows=[];held=None
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (HERE/'arena.py',HERE/'live.py')}
    (out/'sources.json').write_text(json.dumps(hashes,indent=2))
    try:
        with (out/'setup.txt').open('w') as log,contextlib.redirect_stdout(log):session=suite.Session()
        # Observe WM readiness before mapping a client; fixed constructor sleep
        # alone did not prevent an initial window-discovery timeout.
        atom=session.d.intern_atom('_NET_SUPPORTING_WM_CHECK')
        session._wait(lambda:session.d.screen().root.get_full_property(atom,0) is not None,4,'window manager')
        oracle=session.tmp/'score.json'
        with (out/'app-output.txt').open('w') as app_log:
            session.spawn(['python3',str(HERE/'arena.py'),'--seed',str(seed),'--seconds',str(seconds),'--out',str(oracle)],stdout=app_log,stderr=app_log)
            session.wait_window('AI TRACK READY');session.focus('AI TRACK READY')
            def raw(key,down):
                code=session.d.keysym_to_keycode(suite.base.XK.string_to_keysym(key))
                suite.base.xtest.fake_input(session.d,suite.base.X.KeyPress if down else suite.base.X.KeyRelease,code)
                session.d.sync()
            initial=ImageGrab.grab(xdisplay=session.name).convert('RGB');locate(initial);initial.save(out/'initial.png')
            print(json.dumps(dict(event='ready',image=str(out/'initial.png'),task='Use green player to track red target',methods=['local','delayed'])),flush=True)
            command=json.loads(input())
            if command.get('method') not in ('local','delayed'):raise ValueError('explicit tracking method required')
            mode=command['method']
            (out/'agent-command.json').write_text(json.dumps(command))
            raw('Return',True);raw('Return',False)
            start=time.perf_counter();next_decision=start;next_image=start;last_image=None
            while time.perf_counter()-start<seconds+.15:
                tick=time.perf_counter();im=ImageGrab.grab(xdisplay=session.name).convert('RGB')
                capture=time.perf_counter();target,player=locate(im)
                decision=mode=='local' or tick>=next_decision
                if decision:
                    desired='Right' if target-player>18 else 'Left' if target-player < -18 else None
                    if desired!=held:
                        if held is not None:raw(held,False)
                        if desired is not None:raw(desired,True)
                        held=desired
                    next_decision=tick+delay_ms/1000
                ready=time.perf_counter()
                rows.append(dict(t=tick-start,target=target,player=player,decision=decision,held=held,
                                 capture_ms=(capture-tick)*1000,feedback_to_input_ms=(ready-capture)*1000))
                if tick>=next_image:
                    im.save(out/f'frame-{len(rows):04d}.png');next_image=tick+1
                last_image=im
                time.sleep(max(0,.05-(time.perf_counter()-tick)))
            if held is not None:raw(held,False);held=None
            bitmap=session.d.query_keymap()
            for key in ('Left','Right'):
                code=session.d.keysym_to_keycode(suite.base.XK.string_to_keysym(key))
                assert not bitmap[code//8]&(1<<(code%8))
            stopped=time.perf_counter();last_image.save(out/'final.png')
            # Independent scoring starts only here, after all task input.
            session._wait(oracle.exists,2,'score output')
            truth=json.loads(oracle.read_text());shutil.copy2(oracle,out/'oracle.json')
            errors=np.array([r['error'] for r in truth]);times=np.array([r['t'] for r in truth])
            weights=np.diff(times,prepend=0)
            report=dict(seed=seed,mode=mode,delay_ms=delay_ms,seconds=seconds,release_verified=True,
                mean_error_px=float(np.average(errors,weights=weights)),
                fraction_within_30px=float(np.average(errors<=30,weights=weights)),
                capture_count=len(rows),decision_count=sum(r['decision'] for r in rows),
                local_loop_p95_ms=float(np.percentile(np.diff([r['t'] for r in rows])*1000,95)),
                control_wall_seconds=stopped-start,scope='synthetic GUI; simulated decision cadence, no LLM calls')
            (out/'report.json').write_text(json.dumps(report,indent=2));return report
    finally:
        (out/'control.json').write_text(json.dumps(rows))
        if session is not None:
            # The private X server is closed even if capture/input raises.
            session.close();shutil.rmtree(session.tmp)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--seed',type=int,required=True);ap.add_argument('--mode',choices=['local','delayed'],required=True)
    ap.add_argument('--delay-ms',type=float,default=1000);ap.add_argument('--seconds',type=float,default=6)
    a=ap.parse_args();print(json.dumps(run(a.out,a.seed,a.mode,a.delay_ms,a.seconds),indent=2))
