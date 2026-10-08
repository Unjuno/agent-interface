"""Fresh private GUI stimuli; model review runs separately after capture."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from Xlib import X, XK, display
from Xlib.ext import xtest
from xwd_png import convert
ROOT=Path(__file__).resolve().parent
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def one(directory,case,token):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    env=dict(os.environ,XDG_CACHE_HOME=str(directory/'cache'))
    (directory/'cache').mkdir()
    argv=[sys.executable,'-B',str(ROOT/'app.py'),str(directory),json.dumps(case),token]
    process=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env)
    d=None
    try:
        deadline=time.monotonic()+5
        while not (directory/'ready.json').exists():
            if process.poll() is not None or time.monotonic()>deadline:raise RuntimeError('STOP_READY')
            time.sleep(.01)
        ready=json.loads((directory/'ready.json').read_bytes())
        if ready['pid']!=process.pid or ready['token']!=token:raise RuntimeError('STOP_IDENTITY')
        d=display.Display(os.environ['DISPLAY']);g=ready[case['recipient']]
        x=g['x']+g['width']//2;y=g['y']+g['height']//2;requests=[]
        click_start=time.monotonic_ns()
        xtest.fake_input(d,X.MotionNotify,x=x,y=y)
        xtest.fake_input(d,X.ButtonPress,1);xtest.fake_input(d,X.ButtonRelease,1);d.sync()
        click_end=time.monotonic_ns();time.sleep(.08)
        for char in case['emitted']:
            key=d.keysym_to_keycode(XK.string_to_keysym(char))
            if not key:raise RuntimeError('STOP_KEYMAP')
            started=time.monotonic_ns()
            xtest.fake_input(d,X.KeyPress,key);xtest.fake_input(d,X.KeyRelease,key);d.sync()
            requests.append(dict(char=char,keycode=key,started_ns=started,completed_ns=time.monotonic_ns()))
            time.sleep(.02)
        time.sleep(.15);screen_start=time.monotonic_ns()
        captured=subprocess.run(['xwd','-silent','-id',str(ready['root']['id'])],capture_output=True,timeout=3)
        screen_end=time.monotonic_ns()
        (directory/'screen.xwd').write_bytes(captured.stdout)
        (directory/'xwd_stderr.bin').write_bytes(captured.stderr)
        if captured.returncode or captured.stderr:raise RuntimeError('STOP_CAPTURE')
        (directory/'screen.png').write_bytes(convert(captured.stdout))
        (directory/'finish.flag').write_bytes(b'captured\n')
        stdout,stderr=process.communicate(timeout=3)
        (directory/'app_stdout.bin').write_bytes(stdout);(directory/'app_stderr.bin').write_bytes(stderr)
        app=json.loads(stdout)
        return dict(case=case,token=token,app_pid=process.pid,app_argv=argv,ready=ready,app=app,app_exit=process.returncode,app_stderr=stderr.decode(),click=dict(x=x,y=y,started_ns=click_start,completed_ns=click_end),key_requests=requests,screen=dict(started_ns=screen_start,completed_ns=screen_end,xwd_sha256=sha(directory/'screen.xwd'),png_sha256=sha(directory/'screen.png'),argv=['xwd','-silent','-id',str(ready['root']['id'])],exit_code=captured.returncode,stderr_sha256=sha(directory/'xwd_stderr.bin')),post_review_input_count=0)
    finally:
        if d is not None:d.close()
        if process.poll() is None:
            process.kill();stdout,stderr=process.communicate()
            (directory/'app_stdout.bin').write_bytes(stdout);(directory/'app_stderr.bin').write_bytes(stderr)
def main(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);fixture=json.loads((ROOT/'fixture.json').read_bytes())
    xlog=(out/'xvfb.log').open('wb');wm_log=(out/'openbox.log').open('wb')
    xvfb=subprocess.Popen(['Xvfb',':97','-screen','0','1024x768x24','-nolisten','tcp','-ac'],stdout=xlog,stderr=xlog)
    wm=None;rows=[];error=None
    try:
        time.sleep(.25);wm=subprocess.Popen(['openbox'],stdout=wm_log,stderr=wm_log);time.sleep(.2)
        for index,case in enumerate(fixture['cases']):
            row=one(out/f'row-{index:03d}',case,fixture['allocation']+f':row-{index:03d}');rows.append(row)
            actual=row['app'][case['recipient']]
            other=row['app']['decoy' if case['recipient']=='target' else 'target']
            if actual!=case['emitted'] or other or row['app_exit'] or row['app_stderr']:raise RuntimeError('STOP_STIMULUS_EFFECT')
    except Exception as exc:error=type(exc).__name__+':'+str(exc)
    finally:
        for process in (wm,xvfb):
            if process is not None and process.poll() is None:process.terminate();process.wait(timeout=3)
        xlog.close();wm_log.close()
    raw=dict(schema='5260-a14-stimulus-v1',fixture=fixture,fixture_sha256=sha(ROOT/'fixture.json'),freeze_sha256=sha(ROOT/'FREEZE.json'),source_sha256={n:sha(ROOT/n) for n in json.loads((ROOT/'FREEZE.json').read_bytes())['sha256']},image_id=os.environ.get('EXPERIMENT_IMAGE_ID'),rows=rows,error=error,model_calls=0)
    (out/'candidate_stdout.json').write_text(json.dumps(raw,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(dict(rows=len(rows),error=error)))
    return 0 if error is None and len(rows)==4 else 1
if __name__=='__main__':raise SystemExit(main(sys.argv[1]))
