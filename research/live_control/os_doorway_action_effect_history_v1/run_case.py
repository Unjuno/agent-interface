#!/usr/bin/env python3
import argparse, hashlib, json, os, socket, subprocess, sys, tempfile, time
from pathlib import Path
from PIL import Image
from Xlib import X, XK, display
from Xlib.ext import xtest

W,H=320,200
MID_X=130

def cmd(sock_path, text):
    for _ in range(100):
        try:
            s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM); s.connect(str(sock_path)); break
        except OSError: time.sleep(0.02)
    else: raise RuntimeError('socket connect failed')
    with s:
        s.sendall((text+'\n').encode()); out=s.recv(128).decode().strip()
    if out!='OK': raise RuntimeError((text,out))

def capture(dpy):
    root=dpy.screen().root
    raw=root.get_image(0,0,W,H,X.ZPixmap,0xffffffff)
    if raw is None: raise RuntimeError('XGetImage failed')
    # Xvfb 24-bit root is returned as little-endian BGRX.
    im=Image.frombytes('RGB',(W,H),raw.data,'raw','BGRX')
    return im

def rgb_sha(im): return hashlib.sha256(im.tobytes()).hexdigest()

def dark_centroid_x(im):
    pix=im.load(); xs=[]
    # Door interior only; static frame excluded. Panel fill is ~64.
    for y in range(40,160):
        for x in range(70,250):
            r,g,b=pix[x,y]
            if 35 <= r <= 80 and 35 <= g <= 80 and 35 <= b <= 80:
                xs.append(x)
    if not xs: raise RuntimeError('door panel not found')
    return sum(xs)/len(xs)

def choose(policy, pred, cur):
    if policy=='current_only':
        # Current frame contains no trajectory direction; fixed deterministic baseline.
        return 'Right', {'reason':'fixed_on_aliased_current'}
    px=dark_centroid_x(pred); cx=dark_centroid_x(cur)
    if px < cx: action='Right'
    elif px > cx: action='Left'
    else: raise RuntimeError('zero history displacement')
    return action, {'pred_centroid_x':px,'current_centroid_x':cx,'delta_x':cx-px}

def key_down(dpy,keycode):
    km=dpy.query_keymap(); idx=keycode//8; bit=keycode%8
    return bool(km[idx] & (1<<bit))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--trajectory',choices=['opening','closing'],required=True)
    ap.add_argument('--policy',choices=['current_only','history'],required=True)
    ap.add_argument('--case-id',required=True); ap.add_argument('--out',required=True)
    ap.add_argument('--display-num',type=int,required=True); a=ap.parse_args()
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    display_name=f':{a.display_num}'
    xvfb=subprocess.Popen(['Xvfb',display_name,'-screen','0',f'{W}x{H}x24','-nolisten','tcp','-ac'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    env=os.environ.copy(); env['DISPLAY']=display_name
    tmp=Path(tempfile.mkdtemp(prefix='doorway-case-'))
    auth=tmp/'Xauthority'; auth.write_bytes(b'')
    env['XAUTHORITY']=str(auth)
    os.environ['DISPLAY']=display_name; os.environ['XAUTHORITY']=str(auth)
    sock=tmp/'app.sock'; truth=tmp/'truth.json'
    app=None
    try:
        time.sleep(0.12)
        app=subprocess.Popen([sys.executable,str(Path(__file__).with_name('doorway_app.py')),'--trajectory',a.trajectory,'--socket',str(sock),'--truth',str(truth)],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        for _ in range(100):
            if sock.exists(): break
            if app.poll() is not None: raise RuntimeError('app exited early')
            time.sleep(0.02)
        dpy=display.Display(display_name)
        cmd(sock,'PRE'); time.sleep(0.05); pred=capture(dpy)
        cmd(sock,'CURRENT'); time.sleep(0.05); cur=capture(dpy)
        # Current must be canonical mid panel regardless of hidden trajectory.
        cx=dark_centroid_x(cur)
        if abs(cx-(MID_X+29.5)) > 0.6: raise RuntimeError(f'bad current centroid {cx}')
        action,decision=choose(a.policy,pred,cur)
        cmd(sock,'FOCUS'); time.sleep(0.03)
        ks=XK.string_to_keysym(action); kc=dpy.keysym_to_keycode(ks)
        if not kc: raise RuntimeError('keycode missing')
        pre_down=key_down(dpy,kc)
        t0=time.monotonic_ns(); xtest.fake_input(dpy,X.KeyPress,kc); dpy.sync(); t1=time.monotonic_ns()
        xtest.fake_input(dpy,X.KeyRelease,kc); dpy.sync(); t2=time.monotonic_ns()
        for _ in range(100):
            if truth.exists(): break
            time.sleep(0.01)
        if not truth.exists(): raise RuntimeError('no app action receipt')
        effect=json.loads(truth.read_text())
        final=capture(dpy); post_down=key_down(dpy,kc)
        pred.save(out/'predecessor.png'); cur.save(out/'current.png'); final.save(out/'final.png')
        result={
          'case_id':a.case_id,'trajectory':a.trajectory,'policy':a.policy,
          'predecessor_rgb_sha256':rgb_sha(pred),'current_rgb_sha256':rgb_sha(cur),'final_rgb_sha256':rgb_sha(final),
          'predecessor_centroid_x':dark_centroid_x(pred),'current_centroid_x':cx,
          'decision':action,'decision_evidence':decision,'effect':effect,
          'task_correct':bool(effect['correct']),'keycode':kc,'pre_key_down':pre_down,'post_key_down':post_down,
          'press_ns':t0,'press_sync_ns':t1,'release_sync_ns':t2,
          'input_empty':(not post_down),
        }
        (out/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        print(json.dumps(result,sort_keys=True))
        dpy.close()
    finally:
        if app is not None and app.poll() is None:
            try: cmd(sock,'QUIT'); app.wait(timeout=2)
            except Exception: app.kill(); app.wait()
        if xvfb.poll() is None: xvfb.terminate();
        try: xvfb.wait(timeout=2)
        except Exception: xvfb.kill(); xvfb.wait()

if __name__=='__main__': main()
