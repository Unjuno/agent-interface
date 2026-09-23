from __future__ import annotations
import hashlib, json, os, pathlib, subprocess, tempfile, time, sys
from Xlib import X, display

ROOT=pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'research/live_control'))
sys.path.insert(0,str(ROOT))
from native_handle_bridge_v1 import NativeHandleBridge

GEOM=[50,50,220,140]

def wait_viewable(w,d,timeout=3.0):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        d.sync()
        if w.get_attributes().map_state==X.IsViewable:
            return
        time.sleep(.02)
    raise RuntimeError('window never became IsViewable')

class App:
    def __init__(self,dpy):
        self.d=display.Display(dpy); self.root=self.d.screen().root; self.window=None
    def create(self,reuse=None):
        if reuse is not None:
            mask=self.d.display.info.resource_id_mask
            self.d.display.free_resource_id(reuse)
            self.d.display.last_resource_id=reuse & mask
        w=self.root.create_window(*GEOM,0,self.d.screen().root_depth,X.InputOutput,X.CopyFromParent,
            background_pixel=self.d.screen().white_pixel,
            event_mask=X.ExposureMask|X.StructureNotifyMask|X.ButtonPressMask)
        w.set_wm_name('issue4242-construction')
        w.set_wm_class('issue4242','Issue4242')
        w.map(); self.d.sync(); wait_viewable(w,self.d)
        gc=w.create_gc(foreground=self.d.screen().black_pixel,background=self.d.screen().white_pixel)
        w.fill_rectangle(gc,0,0,220,140)
        gc.change(foreground=self.d.screen().white_pixel)
        for i in range(0,220,20): w.fill_rectangle(gc,i,0,10,140)
        gc.change(foreground=self.d.screen().black_pixel); w.fill_rectangle(gc,70,40,80,60)
        self.d.sync()
        w.set_input_focus(X.RevertToParent,X.CurrentTime); self.d.sync()
        self.window=w
        return w.id
    def pixels(self):
        g=self.window.get_geometry()
        im=self.window.get_image(0,0,g.width,g.height,X.ZPixmap,0xffffffff)
        raw=bytes(im.data)
        return {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
    def destroy_with_event(self,dpy):
        xid=self.window.id
        od=display.Display(dpy); ow=od.create_resource_object('window',xid)
        ow.change_attributes(event_mask=X.StructureNotifyMask); od.sync()
        self.window.destroy(); self.d.sync(); self.window=None
        end=time.monotonic()+2; seen=[]
        while time.monotonic()<end:
            od.sync()
            while od.pending_events():
                e=od.next_event(); wid=getattr(getattr(e,'window',None),'id',None)
                seen.append({'type':e.type,'window':wid})
                if e.type==X.DestroyNotify and wid==xid:
                    od.close(); return xid,seen
            time.sleep(.01)
        od.close(); raise RuntimeError('no exact DestroyNotify')
    def close(self):
        try:
            if self.window is not None: self.window.destroy(); self.d.sync()
        except Exception: pass
        self.d.close()

def start():
    td=pathlib.Path(tempfile.mkdtemp(prefix='i4242-a2-construction-'))
    auth=td/'Xauthority'; auth.write_bytes(b'')
    runtime=td/'runtime'; runtime.mkdir(mode=0o700); home=td/'home'; home.mkdir()
    d=':191'; env=os.environ.copy(); env.update(DISPLAY=d,XAUTHORITY=str(auth),XDG_RUNTIME_DIR=str(runtime),HOME=str(home))
    xp=subprocess.Popen(['Xvfb',d,'-screen','0','800x600x24','-nolisten','tcp','-ac'],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    sock=pathlib.Path('/tmp/.X11-unix/X191')
    for _ in range(150):
        if sock.exists(): break
        if xp.poll() is not None: raise RuntimeError('Xvfb exited')
        time.sleep(.02)
    wm=subprocess.Popen(['openbox','--sm-disable'],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    time.sleep(.25)
    if wm.poll() is not None: raise RuntimeError('Openbox exited')
    return td,d,env,xp,wm,sock

def main():
    out=pathlib.Path(sys.argv[1]).resolve(); out.mkdir(parents=True,exist_ok=False)
    td,d,env,xp,wm,sock=start(); old=os.environ.copy(); os.environ.update(env)
    row={}
    app=None; bridge=None
    try:
        app=App(d); xid1=app.create(); pix1=app.pixels()
        bridge=NativeHandleBridge(d,{'app':xid1},'app',out/'bridge')
        obs1=bridge.observe(); g=bridge.backend.geometry('app')
        point=[g['x']+20,g['y']+70]
        off=bridge.mint('old',obs1['sequence'],point)
        xid_destroyed,events=app.destroy_with_event(d)
        xid2=app.create(reuse=xid1); pix2=app.pixels()
        app.window.set_input_focus(X.RevertToParent,X.CurrentTime); app.d.sync()
        review=bridge.review_window(xid2)
        if review.get('status')!='reviewed': raise RuntimeError(f'review failed: {review}')
        old_diag=bridge.store.resolve_point('old',off,review['observation'],
                    bridge.history[review['observation']['sequence']][1],time.monotonic_ns(),session_scope=bridge.scope)
        fresh_off=bridge.mint('fresh',review['observation']['sequence'],point)
        row={
          'decision':'PASS_CONSTRUCTION_EXACT_BRIDGE_TOPOLOGY',
          'xid1':xid1,'xid2':xid2,'same_xid':xid1==xid2,
          'pixels1':pix1,'pixels2':pix2,'same_pixels':pix1==pix2,
          'destroy_events':events,'destroyed_xid':xid_destroyed,
          'observation1_sequence':obs1['sequence'],'mint_offset':off,
          'review_status':review['status'],'binding_revision':bridge.binding_revision,
          'old_diag':old_diag,'fresh_offset':fresh_off,
          'emissions':bridge.backend.emissions,'recovery_required':bridge.session.recovery_required
        }
        if not row['same_xid'] or not row['same_pixels']: raise RuntimeError('identity discriminator missing')
        if old_diag.get('eligible') is not False or old_diag.get('status')!='MISSING': raise RuntimeError('old alias not revoked')
        if row['emissions']!=0: raise RuntimeError('construction emitted input')
    finally:
        if bridge is not None: bridge.close()
        if app is not None: app.close()
        wm.terminate()
        try: wmrc=wm.wait(timeout=3)
        except subprocess.TimeoutExpired: wm.kill(); wmrc=wm.wait()
        xp.terminate()
        try: xrc=xp.wait(timeout=3)
        except subprocess.TimeoutExpired: xp.kill(); xrc=xp.wait()
        for _ in range(50):
            if not sock.exists(): break
            time.sleep(.02)
        row['openbox_exit']=wmrc; row['xvfb_exit']=xrc; row['socket_absent']=not sock.exists()
        os.environ.clear(); os.environ.update(old)
    (out/'CONSTRUCTION.json').write_text(json.dumps(row,indent=2,sort_keys=True)+'\n')
    print(json.dumps(row,sort_keys=True))
if __name__=='__main__': main()
