from __future__ import annotations
import argparse, base64, json, os, pathlib, statistics, subprocess, tempfile, time
from Xlib import X, display as xdisplay

W,H=320,200; SCAN_Y=100; D=7.3
CONTRASTS=(255,192,128,64)
CONSTRUCTION_PHASES=(0.125,0.375,0.625,0.875)
FORMAL_PHASES=tuple(i/100 for i in range(100))
TASK="TEMPORAL-X11-DISPLACEMENT-CONTRAST-R1-20260918-012"

def wait_display(display_name,env,timeout_s=4.0):
    sock=pathlib.Path('/tmp/.X11-unix')/('X'+display_name.split(':',1)[1].split('.',1)[0])
    t0=time.monotonic()
    while time.monotonic()-t0<timeout_s:
        if sock.exists():
            r=subprocess.run(['xdpyinfo','-display',display_name],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            if r.returncode==0:return sock
        time.sleep(.02)
    raise RuntimeError('display_not_ready')

def decode_scanline(raw:bytes):
    if len(raw)!=W*4: raise RuntimeError(f'bad_scanline_bytes:{len(raw)}')
    weighted=[]; total=0
    for x in range(W):
        b,g,r,a=raw[4*x:4*x+4]
        if r>=32 and r>=4*max(g,b):
            weighted.append((x,r)); total+=r
    if not weighted:return None,0,0
    return sum(x*r for x,r in weighted)/total,len(weighted),total

def capture(dpy):
    t0=time.perf_counter_ns(); img=dpy.screen().root.get_image(0,SCAN_Y,W,1,X.ZPixmap,0xffffffff); t1=time.perf_counter_ns()
    data=img.data; raw=data.encode('latin1') if isinstance(data,str) else bytes(data); c,n,w=decode_scanline(raw); return raw,c,n,w,t0,t1

def run_session(phases,out_path,display_num=225,formal=False):
    display_name=f':{display_num}'
    with tempfile.TemporaryDirectory(prefix='x11contrast_') as td:
        xa=pathlib.Path(td)/'Xauthority'; xa.write_bytes(b''); os.chmod(xa,0o600)
        env=os.environ.copy(); env['DISPLAY']=display_name; env['XAUTHORITY']=str(xa)
        xvfb=subprocess.Popen(['Xvfb',display_name,'-screen','0',f'{W}x{H}x24','-nolisten','tcp','-ac'],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        sock=None; fix=None; dpy=None; rows=[]; cleanup={}; exc=None
        try:
            sock=wait_display(display_name,env)
            fix=subprocess.Popen([os.environ.get('PYTHON','python'),str(pathlib.Path(__file__).with_name('fixture.py'))],env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
            ready=json.loads(fix.stdout.readline())
            if ready.get('kind')!='ready' or ready.get('w')!=W or ready.get('h')!=H: raise RuntimeError(f'bad_ready:{ready}')
            os.environ['DISPLAY']=display_name; os.environ['XAUTHORITY']=str(xa); dpy=xdisplay.Display(display_name)
            for red in CONTRASTS:
                for direction in (-1,1):
                    for phase in phases:
                        x0=100.0+phase; x1=x0+direction*D; frames=[]
                        for label,x in (('x0',x0),('x1',x1)):
                            fix.stdin.write(json.dumps({'cmd':'set','x':x,'red':red})+'\n'); fix.stdin.flush(); ack=json.loads(fix.stdout.readline())
                            if ack.get('kind')!='ack':raise RuntimeError(f'bad_ack:{ack}')
                            raw,c,n,w,t0,t1=capture(dpy); authored=x+float(ack['rootx'])
                            frames.append({'label':label,'red':red,'direction':direction,'phase':phase,'authored_root_x':authored,'centroid_x':c,'point_error_px':None if c is None else c-authored,'target_pixel_count':n,'red_weight_total':w,'scanline_b64':base64.b64encode(raw).decode('ascii'),'capture_duration_ns':t1-t0})
                        od=None if any(f['centroid_x'] is None for f in frames) else frames[1]['centroid_x']-frames[0]['centroid_x']
                        rows.append({'red':red,'direction':direction,'phase':phase,'authored_displacement_px':direction*D,'observed_displacement_px':od,'displacement_residual_px':None if od is None else od-direction*D,'direction_agreement':od is not None and ((od>0)==(direction>0)),'frames':frames})
        except Exception as e:
            exc=repr(e)
        finally:
            if dpy is not None:
                try:dpy.close()
                except Exception:pass
            if fix is not None:
                try:
                    if fix.poll() is None:
                        fix.stdin.write(json.dumps({'cmd':'quit'})+'\n'); fix.stdin.flush(); fix.communicate(timeout=1)
                except Exception:
                    try:fix.kill(); fix.communicate(timeout=1)
                    except Exception:pass
                cleanup['fixture_exit']=fix.returncode
            if xvfb.poll() is None:
                xvfb.terminate()
                try:xvfb.communicate(timeout=1)
                except subprocess.TimeoutExpired:xvfb.kill(); xvfb.communicate(timeout=1)
            cleanup['xvfb_exit']=xvfb.returncode
            if sock is not None:
                for _ in range(50):
                    if not sock.exists():break
                    time.sleep(.01)
                cleanup['socket_removed']=not sock.exists()
        metrics={}
        for red in CONTRASTS:
            rr=[r for r in rows if r['red']==red]; res=[abs(r['displacement_residual_px']) for r in rr if r['displacement_residual_px'] is not None]
            metrics[str(red)]={'pairs':len(rr),'missed_frames':sum(f['centroid_x'] is None for r in rr for f in r['frames']),'direction_ok':sum(bool(r['direction_agreement']) for r in rr),'max_abs_residual_px':max(res) if res else None,'median_abs_residual_px':statistics.median(res) if res else None}
        payload={'task':TASK,'mode':'formal' if formal else 'construction','formal_invocation':1 if formal else 0,'reruns':0,'exception':exc,'pairs_rows':rows,'summary':{'pairs':len(rows),'frames':sum(len(r['frames']) for r in rows),'metrics':metrics,'cleanup':[cleanup] if formal else cleanup}}
        pathlib.Path(out_path).write_text(json.dumps(payload,separators=(',',':'),sort_keys=True),encoding='utf-8')
        print(json.dumps({'exception':exc,'summary':payload['summary']},sort_keys=True))
        if exc: raise SystemExit(2)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('mode',choices=['construction','formal']); ap.add_argument('out'); a=ap.parse_args()
    if a.mode=='construction':
        run_session(CONSTRUCTION_PHASES,a.out,225,False)
        return
    allrows=[]; cleanups=[]; exc=None
    for sid in range(4):
        phases=tuple(FORMAL_PHASES[sid*25:(sid+1)*25])
        tmp=pathlib.Path(a.out).with_name(f'.formal_session_{sid}.json')
        try:
            run_session(phases,str(tmp),226+sid,True)
            q=json.loads(tmp.read_text())
            if q.get('exception') is not None: raise RuntimeError(q['exception'])
            allrows.extend(q['pairs_rows']); cleanups.extend(q['summary']['cleanup'])
        except Exception as e:
            exc=repr(e); break
        finally:
            try: tmp.unlink()
            except FileNotFoundError: pass
    metrics={}
    for red in CONTRASTS:
        rr=[r for r in allrows if r['red']==red]; res=[abs(r['displacement_residual_px']) for r in rr if r['displacement_residual_px'] is not None]
        metrics[str(red)]={'pairs':len(rr),'missed_frames':sum(f['centroid_x'] is None for r in rr for f in r['frames']),'direction_ok':sum(bool(r['direction_agreement']) for r in rr),'max_abs_residual_px':max(res) if res else None,'median_abs_residual_px':statistics.median(res) if res else None}
    payload={'task':TASK,'mode':'formal','formal_invocation':1,'reruns':0,'exception':exc,'pairs_rows':allrows,'summary':{'pairs':len(allrows),'frames':sum(len(r['frames']) for r in allrows),'metrics':metrics,'cleanup':cleanups}}
    pathlib.Path(a.out).write_text(json.dumps(payload,separators=(',',':'),sort_keys=True),encoding='utf-8')
    print(json.dumps({'exception':exc,'summary':payload['summary']},sort_keys=True))
    if exc: raise SystemExit(2)
if __name__=='__main__':main()
