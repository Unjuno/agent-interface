from __future__ import annotations
import argparse, base64, json, math, os, pathlib, statistics, subprocess, tempfile, time
from Xlib import X, display as xdisplay

W,H=320,200
SCAN_Y=100
D=7.3
FORMAL_PHASES=[i/100 for i in range(100)]
CONSTRUCTION_PHASES=[0.005,0.335,0.665,0.995]
TASK="TEMPORAL-X11-CENTROID-LOCALIZATION-A2-20260918-009"

def wait_display(display_name: str, env: dict, timeout_s=4.0):
    sock=pathlib.Path('/tmp/.X11-unix')/('X'+display_name.split(':',1)[1].split('.',1)[0])
    t0=time.monotonic()
    while time.monotonic()-t0<timeout_s:
        if sock.exists():
            r=subprocess.run(['xdpyinfo','-display',display_name],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            if r.returncode==0:
                return sock
        time.sleep(0.02)
    raise RuntimeError(f'display_not_ready:{display_name}')

def decode_scanline(raw: bytes, width=W):
    if len(raw)!=width*4:
        raise RuntimeError(f'bad_scanline_bytes:{len(raw)}')
    xs=[]
    for x in range(width):
        b,g,r,a=raw[4*x:4*x+4]
        if r>=200 and g<=32 and b<=32:
            xs.append(x)
    if not xs:
        return None,0
    return sum(xs)/len(xs),len(xs)

def capture_scanline(dpy):
    root=dpy.screen().root
    t0=time.perf_counter_ns()
    img=root.get_image(0,SCAN_Y,W,1,X.ZPixmap,0xffffffff)
    t1=time.perf_counter_ns()
    raw=bytes(img.data)
    centroid,nred=decode_scanline(raw)
    return raw,centroid,nred,t0,t1

def percentile_nearest(vals,p):
    if not vals:
        return None
    s=sorted(vals)
    k=max(0,min(len(s)-1,math.ceil(p*len(s))-1))
    return s[k]

def run_session(session_id:int,direction:int,phases:list[float],display_num:int):
    display_name=f':{display_num}'
    with tempfile.TemporaryDirectory(prefix=f'x11centroid_{session_id}_') as td:
        xa=pathlib.Path(td)/'Xauthority'
        xa.write_bytes(b'')
        os.chmod(xa,0o600)
        env=os.environ.copy(); env['DISPLAY']=display_name; env['XAUTHORITY']=str(xa)
        xvfb=subprocess.Popen(['Xvfb',display_name,'-screen','0',f'{W}x{H}x24','-nolisten','tcp','-ac'],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=False)
        sock=None; fix=None; dpy=None; rows=[]; cleanup={}
        try:
            sock=wait_display(display_name,env)
            fix=subprocess.Popen([os.environ.get('PYTHON','python'),str(pathlib.Path(__file__).with_name('fixture.py'))],env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
            ready=json.loads(fix.stdout.readline())
            if ready.get('kind')!='ready' or ready.get('w')!=W or ready.get('h')!=H:
                raise RuntimeError(f'bad_fixture_ready:{ready}')
            os.environ['DISPLAY']=display_name
            os.environ['XAUTHORITY']=str(xa)
            dpy=xdisplay.Display(display_name)
            for phase in phases:
                x0=100.0+phase
                x1=x0+direction*D
                pair=[]
                for label,x in [('x0',x0),('x1',x1)]:
                    fix.stdin.write(json.dumps({'cmd':'set','x':x})+'\n'); fix.stdin.flush()
                    ack=json.loads(fix.stdout.readline())
                    if ack.get('kind')!='ack': raise RuntimeError(f'bad_ack:{ack}')
                    raw,centroid,nred,t0,t1=capture_scanline(dpy)
                    authored_root_x=x+float(ack['rootx'])
                    point_error=None if centroid is None else centroid-authored_root_x
                    fr={'session_id':session_id,'display':display_name,'direction':direction,'phase':phase,'label':label,'authored_local_x':x,'fixture_rootx':ack['rootx'],'fixture_rooty':ack['rooty'],'authored_root_x':authored_root_x,'scan_y':SCAN_Y,'scanline_b64':base64.b64encode(raw).decode('ascii'),'scanline_bytes':len(raw),'red_count':nred,'centroid_x':centroid,'point_error_px':point_error,'capture_start_ns':t0,'capture_end_ns':t1,'capture_duration_ns':t1-t0}
                    pair.append(fr)
                r0,r1=pair
                observed_disp=None if r0['centroid_x'] is None or r1['centroid_x'] is None else r1['centroid_x']-r0['centroid_x']
                residual=None if observed_disp is None else observed_disp-direction*D
                rows.append({'session_id':session_id,'display':display_name,'direction':direction,'phase':phase,'authored_displacement_px':direction*D,'observed_displacement_px':observed_disp,'displacement_residual_px':residual,'direction_agreement': observed_disp is not None and ((observed_disp>0)==(direction>0)),'frames':pair})
        finally:
            if dpy is not None:
                try:dpy.close()
                except Exception:pass
            if fix is not None:
                try:
                    if fix.poll() is None:
                        fix.stdin.write(json.dumps({'cmd':'quit'})+'\n'); fix.stdin.flush()
                        fix.communicate(timeout=1.0)
                except Exception:
                    try:fix.kill(); fix.communicate(timeout=1.0)
                    except Exception:pass
                cleanup['fixture_exit']=fix.returncode
            if xvfb.poll() is None:
                xvfb.terminate()
                try:xvfb.communicate(timeout=1.0)
                except subprocess.TimeoutExpired:
                    xvfb.kill(); xvfb.communicate(timeout=1.0)
            cleanup['xvfb_exit']=xvfb.returncode
            if sock is not None:
                for _ in range(50):
                    if not sock.exists(): break
                    time.sleep(0.01)
                cleanup['socket_removed']=not sock.exists()
        return rows,cleanup

def summarize(rows,cleanups,formal):
    frames=[f for p in rows for f in p['frames']]
    point=[abs(f['point_error_px']) for f in frames if f['point_error_px'] is not None]
    resid=[abs(p['displacement_residual_px']) for p in rows if p['displacement_residual_px'] is not None]
    missed=sum(f['centroid_x'] is None for f in frames)
    return {'task':TASK,'formal_invocation':1 if formal else 0,'reruns':0,'pairs':len(rows),'frames':len(frames),'missed_red':missed,'direction_agreement_count':sum(bool(p['direction_agreement']) for p in rows),'max_abs_point_error_px':max(point) if point else None,'p99_abs_point_error_px':percentile_nearest(point,0.99),'max_abs_displacement_residual_px':max(resid) if resid else None,'capture_duration_ns_median':statistics.median([f['capture_duration_ns'] for f in frames]) if frames else None,'cleanup':cleanups}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('mode',choices=['construction','formal']); ap.add_argument('out')
    a=ap.parse_args(); formal=a.mode=='formal'
    specs=[(0,1,FORMAL_PHASES,221),(1,-1,FORMAL_PHASES,222),(2,1,FORMAL_PHASES,223),(3,-1,FORMAL_PHASES,224)] if formal else [(90,1,CONSTRUCTION_PHASES,220)]
    allrows=[]; cleanups=[]; exc=None
    try:
        for sid,d,ph,disp in specs:
            rr,cc=run_session(sid,d,ph,disp); allrows.extend(rr); cleanups.append(cc)
    except Exception as e:
        exc=repr(e)
    payload={'task':TASK,'mode':a.mode,'formal_invocation':1 if formal else 0,'reruns':0,'exception':exc,'pairs_rows':allrows,'summary':summarize(allrows,cleanups,formal)}
    pathlib.Path(a.out).write_text(json.dumps(payload,separators=(',',':'),sort_keys=True),encoding='utf-8')
    print(json.dumps({'exception':exc,'summary':payload['summary']},sort_keys=True))
    if exc: raise SystemExit(2)
if __name__=='__main__':main()
