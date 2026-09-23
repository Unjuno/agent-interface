from __future__ import annotations
import json, os, pathlib, subprocess, sys, time
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import construction as fx
from Xlib import X

ALLOC='native-handle-destroy-generation-20260923-02'
KINDS=('STABLE_FRESH','REPLACED_STATIC_DIAGNOSTIC','REPLACED_DESTROY_GENERATION')

def point_for(bridge):
    g=bridge.backend.geometry('app')
    return [g['x']+20,g['y']+70]

def run_case(dpy,out,kind):
    app=fx.App(dpy); bridge=None
    xid1=app.create(); pix1=app.pixels()
    bridge=fx.NativeHandleBridge(dpy,{'app':xid1},'app',out/'bridge')
    obs=bridge.observe(); point=point_for(bridge); off=bridge.mint('old',obs['sequence'],point)
    emit0=bridge.backend.emissions; effect0=app.effect
    row={'kind':kind,'xid1':xid1,'pixels1':pix1,'point':point,'offset':off,
         'binding_revision_before':bridge.binding_revision,'scope_before':bridge.scope,
         'emissions_before':emit0,'effect_before':effect0}
    try:
        if kind=='STABLE_FRESH':
            result=bridge.click('old',off); effect=app.drain_effect()
            row.update(result=result,effect_delta=effect,
                       emission_delta=bridge.backend.emissions-emit0)
        else:
            destroyed,events=app.destroy_with_event(dpy)
            xid2=app.create(reuse=xid1); pix2=app.pixels()
            app.window.set_input_focus(X.RevertToParent,X.CurrentTime); app.d.sync()
            row.update(destroyed_xid=destroyed,destroy_events=events,xid2=xid2,pixels2=pix2,
                       same_xid=xid1==xid2,same_pixels=pix1==pix2)
            if kind=='REPLACED_STATIC_DIAGNOSTIC':
                current=bridge.observe(); image=bridge.history[current['sequence']][1]
                diagnostic=bridge.store.resolve_point('old',off,current,image,time.monotonic_ns(),
                                                       session_scope=bridge.scope)
                row.update(diagnostic=diagnostic,effect_delta=app.drain_effect(),
                           emission_delta=bridge.backend.emissions-emit0,
                           binding_revision_after=bridge.binding_revision,scope_after=bridge.scope)
            elif kind=='REPLACED_DESTROY_GENERATION':
                review=bridge.review_window(xid2)
                emit_after_review=bridge.backend.emissions
                old=bridge.click('old',off); old_effect=app.drain_effect()
                if review.get('status')!='reviewed':
                    raise RuntimeError(f'review failed: {review}')
                seq=review['observation']['sequence']; fresh_point=point_for(bridge)
                fresh_off=bridge.mint('fresh',seq,fresh_point)
                fresh=bridge.click('fresh',fresh_off); fresh_effect=app.drain_effect()
                row.update(review=review,old_result=old,old_effect_delta=old_effect,
                           old_emission_delta=bridge.backend.emissions-emit_after_review-3,
                           fresh_point=fresh_point,fresh_offset=fresh_off,fresh_result=fresh,
                           fresh_effect_delta=fresh_effect,total_emission_delta=bridge.backend.emissions-emit0,
                           binding_revision_after=bridge.binding_revision,scope_after=bridge.scope)
            else:
                raise AssertionError(kind)
        row['terminal_release']=bridge.backend.release_all()
    finally:
        if bridge is not None: bridge.close()
        app.close()
    return row

def main():
    out=pathlib.Path(sys.argv[1]).resolve(); out.mkdir(parents=True,exist_ok=False)
    expected=os.environ.get('EXPECTED_HEAD','')
    commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    if expected and commit!=expected: raise RuntimeError(f'head mismatch {commit} != {expected}')
    orders=[
      ['STABLE_FRESH','REPLACED_STATIC_DIAGNOSTIC','REPLACED_DESTROY_GENERATION'],
      ['REPLACED_STATIC_DIAGNOSTIC','REPLACED_DESTROY_GENERATION','STABLE_FRESH'],
      ['REPLACED_DESTROY_GENERATION','STABLE_FRESH','REPLACED_STATIC_DIAGNOSTIC'],
      ['STABLE_FRESH','REPLACED_DESTROY_GENERATION','REPLACED_STATIC_DIAGNOSTIC'],
    ]
    rows=[]; sessions=[]
    for session,order in enumerate(orders):
        td,d,env,xp,wm,sock=fx.start(); oldenv=os.environ.copy(); os.environ.update(env)
        s={'session':session,'display':d,'order':order}
        try:
            for kind in order:
                caseout=out/f'session-{session}-{kind.lower()}'; caseout.mkdir()
                rows.append({'session':session,**run_case(d,caseout,kind)})
        finally:
            wm.terminate()
            try: wmrc=wm.wait(timeout=3)
            except subprocess.TimeoutExpired: wm.kill(); wmrc=wm.wait()
            xp.terminate()
            try: xrc=xp.wait(timeout=3)
            except subprocess.TimeoutExpired: xp.kill(); xrc=xp.wait()
            for _ in range(50):
                if not sock.exists(): break
                time.sleep(.02)
            s.update(openbox_exit=wmrc,xvfb_exit=xrc,socket_absent=not sock.exists())
            os.environ.clear(); os.environ.update(oldenv)
        sessions.append(s)
    raw={'allocation':ALLOC,'source_commit':commit,'expected_head':expected,
         'formal_invocations':1,'formal_retries':0,'rows':rows,'sessions':sessions}
    (out/'RAW.json').write_text(json.dumps(raw,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'allocation':ALLOC,'rows':len(rows),'sessions':len(sessions),'source_commit':commit},sort_keys=True))
if __name__=='__main__': main()
