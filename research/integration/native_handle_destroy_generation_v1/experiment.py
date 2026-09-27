from __future__ import annotations
import json, os, pathlib, subprocess, tempfile, time, hashlib
from Xlib import X, display

ROOT = pathlib.Path(__file__).resolve().parents[3]
import sys
sys.path.insert(0, str(ROOT / 'research/live_control'))
sys.path.insert(0, str(ROOT))
from native_handle_bridge_v1 import NativeHandleBridge

ALLOC='native-handle-destroy-generation-20260923-01'
POINT=[90,100]
OFFSET=[12,19]
GEOM=[50,50,220,140]

class App:
    def __init__(self, dpy):
        self.d=display.Display(dpy); self.root=self.d.screen().root
        self.window=None; self.xid=None; self.effect=0
    def _draw(self,w):
        gc=w.create_gc(foreground=self.d.screen().black_pixel, background=self.d.screen().white_pixel)
        w.fill_rectangle(gc,0,0,220,140)
        gc.change(foreground=self.d.screen().white_pixel)
        for i in range(0,220,20): w.fill_rectangle(gc,i,0,10,140)
        gc.change(foreground=self.d.screen().black_pixel)
        w.fill_rectangle(gc,70,40,80,60)
        self.d.sync()
    def create(self, reuse=None):
        if reuse is not None:
            base=self.d.display.info.resource_id_base; mask=self.d.display.info.resource_id_mask
            self.d.display.free_resource_id(reuse)
            self.d.display.last_resource_id = reuse & mask
        w=self.root.create_window(*GEOM,0,self.d.screen().root_depth,X.InputOutput,X.CopyFromParent,
            background_pixel=self.d.screen().white_pixel,
            event_mask=X.ExposureMask|X.ButtonPressMask|X.ButtonReleaseMask|X.StructureNotifyMask)
        w.map(); self.d.sync(); time.sleep(.03); self._draw(w)
        w.set_input_focus(X.RevertToParent,X.CurrentTime); self.d.sync()
        self.window=w; self.xid=w.id; return w.id
    def destroy(self):
        xid=self.xid; self.window.destroy(); self.d.sync(); time.sleep(.03); self.window=None
        return xid
    def drain_effect(self):
        count=0
        self.d.sync(); time.sleep(.03)
        while self.d.pending_events():
            e=self.d.next_event()
            if e.type==X.ButtonPress: count+=1
        self.effect += count
        return count
    def pixels(self):
        im=self.window.get_image(0,0,GEOM[2],GEOM[3],X.ZPixmap,0xffffffff)
        raw=bytes(im.data); return {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
    def close(self):
        try:
            if self.window is not None: self.window.destroy(); self.d.sync()
        except Exception: pass
        self.d.close()

def observe_destroy(dpy,xid, destroy_fn):
    od=display.Display(dpy); ow=od.create_resource_object('window',xid)
    ow.change_attributes(event_mask=X.StructureNotifyMask); od.sync()
    destroy_fn(); deadline=time.monotonic()+1.0; rows=[]
    while time.monotonic()<deadline:
        od.sync()
        while od.pending_events():
            e=od.next_event(); rows.append({'type':e.type,'window':getattr(getattr(e,'window',None),'id',None)})
            if e.type==X.DestroyNotify and rows[-1]['window']==xid:
                od.close(); return rows
        time.sleep(.01)
    od.close(); return rows

def one_case(dpy,out,kind):
    app=App(dpy); xid1=app.create(); pix1=app.pixels()
    bridge=NativeHandleBridge(dpy,{'app':xid1},'app',out/'bridge')
    source=bridge.observe(); off=bridge.mint('target',source['sequence'],POINT)
    before_emit=bridge.backend.emissions; before_effect=app.effect
    row={'kind':kind,'xid1':xid1,'pixels1':pix1,'binding_revision_before':bridge.binding_revision,
         'scope_before':bridge.scope,'mint_offset':off,'emissions_before':before_emit,'effect_before':before_effect}
    try:
        if kind=='STABLE_FRESH':
            res=bridge.click('target',off); eff=app.drain_effect()
            row.update(result=res,effect_delta=eff,emission_delta=bridge.backend.emissions-before_emit)
        else:
            events=observe_destroy(dpy,xid1,app.destroy)
            xid2=app.create(reuse=xid1); pix2=app.pixels(); app.window.set_input_focus(X.RevertToParent,X.CurrentTime); app.d.sync()
            row.update(destroy_events=events,xid2=xid2,pixels2=pix2,same_xid=xid1==xid2,same_pixels=pix1==pix2)
            if kind=='REPLACED_STATIC_DIAGNOSTIC':
                obs=bridge.observe(); image=bridge.history[bridge.sequence][1]
                diag=bridge.store.resolve_point('target',off,obs,image,time.monotonic_ns(),session_scope=bridge.scope)
                row.update(diagnostic=diag,effect_delta=app.drain_effect(),emission_delta=bridge.backend.emissions-before_emit)
            elif kind=='REPLACED_DESTROY_GENERATION':
                review=bridge.review_window(xid2)
                after_review_emit=bridge.backend.emissions
                old=bridge.click('target',off); old_eff=app.drain_effect()
                seq=review['observation']['sequence']
                fresh_off=bridge.mint('fresh',seq,POINT)
                fresh=bridge.click('fresh',fresh_off); fresh_eff=app.drain_effect()
                row.update(review=review,old_result=old,fresh_result=fresh,old_effect_delta=old_eff,
                           fresh_effect_delta=fresh_eff,old_emission_delta=after_review_emit-before_emit,
                           total_emission_delta=bridge.backend.emissions-before_emit,
                           binding_revision_after=bridge.binding_revision,scope_after=bridge.scope)
            else: raise AssertionError(kind)
        release=bridge.backend.release_all()
        row['terminal_release']=release
    finally:
        bridge.close(); app.close()
    return row

def start_xvfb(display_no,tmp):
    d=f':{display_no}'; auth=tmp/'Xauthority'; auth.write_bytes(b'')
    runtime=tmp/'runtime'; runtime.mkdir(mode=0o700)
    home=tmp/'home'; home.mkdir()
    env=os.environ.copy(); env.update(DISPLAY=d,XAUTHORITY=str(auth),XDG_RUNTIME_DIR=str(runtime),HOME=str(home))
    p=subprocess.Popen(['Xvfb',d,'-screen','0','800x600x24','-nolisten','tcp','-ac'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env)
    sock=pathlib.Path(f'/tmp/.X11-unix/X{display_no}')
    for _ in range(100):
        if sock.exists(): break
        if p.poll() is not None: raise RuntimeError('Xvfb exited')
        time.sleep(.02)
    wm=subprocess.Popen(['openbox','--sm-disable'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env)
    time.sleep(.15)
    if wm.poll() is not None: raise RuntimeError('openbox exited')
    return p,wm,env,sock

def main():
    out=pathlib.Path(sys.argv[1]).resolve(); out.mkdir(parents=True,exist_ok=False)
    rows=[]; sessions=[]
    orders=[['STABLE_FRESH','REPLACED_STATIC_DIAGNOSTIC','REPLACED_DESTROY_GENERATION'],
            ['REPLACED_STATIC_DIAGNOSTIC','REPLACED_DESTROY_GENERATION','STABLE_FRESH'],
            ['REPLACED_DESTROY_GENERATION','STABLE_FRESH','REPLACED_STATIC_DIAGNOSTIC'],
            ['STABLE_FRESH','REPLACED_DESTROY_GENERATION','REPLACED_STATIC_DIAGNOSTIC']]
    for s,order in enumerate(orders):
        td=pathlib.Path(tempfile.mkdtemp(prefix=f'i4242-{s}-'))
        xp,wm,env,sock=start_xvfb(180+s,td); oldenv=os.environ.copy(); os.environ.update(env)
        session_row={'session':s,'xvfb_running':xp.poll() is None}; sessions.append(session_row)
        try:
            for k in order:
                caseout=out/f'session-{s}-{k.lower()}'; caseout.mkdir()
                rows.append({'session':s,**one_case(env['DISPLAY'],caseout,k)})
        finally:
            wm.terminate()
            try: wmrc=wm.wait(timeout=3)
            except subprocess.TimeoutExpired: wm.kill(); wmrc=wm.wait()
            xp.terminate()
            try: rc=xp.wait(timeout=3)
            except subprocess.TimeoutExpired: xp.kill(); rc=xp.wait()
            session_row['xvfb_exit']=rc
            for _ in range(50):
                if not sock.exists(): break
                time.sleep(.02)
            session_row['openbox_exit']=wmrc
            session_row['socket_absent']=not sock.exists()
            os.environ.clear(); os.environ.update(oldenv)
    raw={'allocation':ALLOC,'rows':rows,'sessions':sessions,'formal_invocations':1,'formal_retries':0}
    (out/'RAW.json').write_text(json.dumps(raw,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'allocation':ALLOC,'rows':len(rows),'sessions':len(sessions)}))
if __name__=='__main__': main()
