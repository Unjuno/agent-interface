from __future__ import annotations
import argparse,json,os,select,signal,subprocess,sys,time,hashlib,traceback
from pathlib import Path
from Xlib import X,XK,display
from Xlib.ext import xtest
from PIL import ImageGrab
HERE=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,x):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
def wait(p,n=8):
    end=time.monotonic()+n
    while not Path(p).exists():
        fail=Path(p).parent/'worker-failure.json'
        if fail.exists():raise RuntimeError(fail.read_text())
        if time.monotonic()>end:raise TimeoutError(str(p))
        time.sleep(.005)
    return json.loads(Path(p).read_text())
def find(root,title):
    try:
        if root.get_wm_name()==title and root.get_attributes().map_state==X.IsViewable:return root
        for c in root.query_tree().children:
            w=find(c,title)
            if w:return w
    except Exception:pass
    return None
def keyrow(dpy):
    a=time.perf_counter_ns();km=list(dpy.query_keymap());b=time.perf_counter_ns();return {'started_ns':a,'finished_ns':b,'keymap':km,'empty':not any(km)}
def snap(p,disp):
    a=time.perf_counter_ns();im=ImageGrab.grab(xdisplay=disp).convert('RGB');b=time.perf_counter_ns();im.save(p);return {'started_ns':a,'finished_ns':b,'rgb_sha256':hashlib.sha256(im.tobytes()).hexdigest(),'file_sha256':sha(p),'size':list(im.size),'file':Path(p).name}
def run(root,plan,spec):
    for p,h in plan['sources'].items():
        if sha(root/p)!=h:raise RuntimeError('source pin '+p)
    for p,h in plan['fixtures'].items():
        if sha(root/p)!=h:raise RuntimeError('fixture pin '+p)
    d=root/'evidence'/spec['id'];d.mkdir(parents=True,exist_ok=False)
    c=dict(spec,source_a=str(root/'fixtures/a.mkv'),source_b=str(root/'fixtures/b.mkv'),expected=str(root/'fixtures/expected.json'));put(d/'case.json',c)
    auth=root/'.xauthority';auth.touch(exist_ok=True);env=dict(os.environ,XAUTHORITY=str(auth));procs=[];dp=obs=None;code=None
    try:
        xv=subprocess.Popen(['Xvfb','-displayfd','1','-screen','0','1024x480x24','-nolisten','tcp','-ac'],stdout=subprocess.PIPE,stderr=(d/'xvfb.stderr').open('xb'),env=env);procs.append(xv)
        if not select.select([xv.stdout],[],[],3)[0]:raise TimeoutError('Xvfb')
        disp=':'+xv.stdout.readline().decode().strip();env['DISPLAY']=disp;os.environ['DISPLAY']=disp;os.environ['XAUTHORITY']=str(auth)
        dp=display.Display(disp);obs=display.Display(disp);title='Quiesce-'+spec['id']
        term=subprocess.Popen(['xterm','-T',title,'-geometry','100x14+10+10','-e',sys.executable,str(HERE/'worker.py'),str(d/'case.json')],env=env,stdout=(d/'xterm.stdout').open('xb'),stderr=(d/'xterm.stderr').open('xb'));procs.append(term);wait(d/'ready.json')
        w=None;end=time.monotonic()+3
        while w is None and time.monotonic()<end:w=find(dp.screen().root,title);time.sleep(.01)
        if w is None:raise RuntimeError('xterm not found')
        w.set_input_focus(X.RevertToParent,X.CurrentTime);dp.sync();time.sleep(.04)
        before=keyrow(obs);snap(d/'before.png',disp)
        if not before['empty']:raise RuntimeError('initial input')
        code=dp.keysym_to_keycode(XK.string_to_keysym('Return'));ps=time.perf_counter_ns();xtest.fake_input(dp,X.KeyPress,code);dp.sync();down=keyrow(obs);time.sleep(.02);xtest.fake_input(dp,X.KeyRelease,code);dp.sync();rel=keyrow(obs);pe=time.perf_counter_ns()
        if not(down['keymap'][code//8]&(1<<(code%8))) or not rel['empty']:raise RuntimeError('Return verification')
        put(d/'input.json',{'keycode':code,'before':before,'down':down,'released':rel,'press_started_ns':ps,'release_finished_ns':pe})
        wait(d/'done.json',10);after=snap(d/'after.png',disp);put(d/'images.json',{'before':json.loads(json.dumps({'file':'before.png'})),'after':after})
        fin=keyrow(obs);put(d/'final-input.json',fin)
        if not fin['empty']:raise RuntimeError('final input')
        (d/'close-worker').touch();term.wait(timeout=3)
        row={'id':spec['id'],'strategy':spec['strategy'],'after_b':json.loads((d/'after-b.json').read_text())['state'],'final':json.loads((d/'final.json').read_text())['state']};print(json.dumps(row),flush=True)
    except BaseException:
        (d/'harness-failure.txt').write_text(traceback.format_exc());raise
    finally:
        if dp is not None and code:
            try:xtest.fake_input(dp,X.KeyRelease,code);dp.sync()
            except Exception:pass
        if obs:obs.close()
        if dp:dp.close()
        for p in reversed(procs):
            if p.poll() is None:
                p.terminate()
                try:p.wait(timeout=2)
                except subprocess.TimeoutExpired:p.kill();p.wait(timeout=2)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('--plan',default='plan.json');ap.add_argument('--block',type=int);a=ap.parse_args();root=a.root.resolve();plan=json.loads((root/a.plan).read_text())
    for c in plan['cases']:
        if a.block is None or c['rep']==a.block:run(root,plan,c)
if __name__=='__main__':main()
