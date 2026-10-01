#!/usr/bin/env python3
import json, os, pathlib, shutil, signal, subprocess, sys, tempfile, time
ROOT=pathlib.Path(__file__).resolve().parent
def main():
    if len(sys.argv)!=2: raise SystemExit('usage: supervisor.py FRESH_OUTPUT')
    out=pathlib.Path(sys.argv[1])
    if out.exists(): raise SystemExit('output exists')
    display=':96'; sock=pathlib.Path('/tmp/.X11-unix/X96')
    if sock.exists(): raise SystemExit('display occupied')
    work=pathlib.Path(tempfile.mkdtemp(prefix='kg-formal-')); xa=work/'Xauthority'; xa.touch()
    cookie=subprocess.check_output(['mcookie'],text=True).strip()
    subprocess.run(['xauth','-f',str(xa),'add',display,'.',cookie],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    xlog=(work/'xvfb.stderr').open('w')
    xvfb=subprocess.Popen(['Xvfb',display,'-screen','0','640x360x24','-nolisten','tcp','-auth',str(xa)],stdout=subprocess.DEVNULL,stderr=xlog,text=True)
    started=time.monotonic_ns(); runner=None
    try:
        for _ in range(100):
            if sock.exists(): break
            if xvfb.poll() is not None: raise RuntimeError('Xvfb exited before ready')
            time.sleep(.02)
        else: raise TimeoutError('Xvfb socket')
        env=os.environ.copy();env['DISPLAY']=display;env['XAUTHORITY']=str(xa);env['PYTHONDONTWRITEBYTECODE']='1'
        runner=subprocess.run([sys.executable,'-B',str(ROOT/'study.py'),'run',str(out),display],env=env,
                              stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=45)
    finally:
        if xvfb.poll() is None:
            xvfb.terminate()
            try:xvfb.wait(timeout=3)
            except subprocess.TimeoutExpired:xvfb.kill();xvfb.wait()
        xlog.close()
    execution={'started_ns':started,'ended_ns':time.monotonic_ns(),'display':display,
       'runner_exit':runner.returncode if runner else None,'runner_stdout':runner.stdout if runner else None,
       'runner_stderr':runner.stderr if runner else None,'xvfb_returncode':xvfb.returncode,
       'xvfb_cleanup':'SIGTERM/reaped','socket_removed':not sock.exists()}
    if out.exists():(out/'EXECUTION.json').write_text(json.dumps(execution,indent=2,sort_keys=True)+'\n')
    shutil.rmtree(work,ignore_errors=True)
    print(json.dumps(execution,sort_keys=True))
    ok=runner is not None and runner.returncode==0 and execution['socket_removed'] and xvfb.returncode in (0,-signal.SIGTERM)
    raise SystemExit(0 if ok else 1)
if __name__=='__main__':main()
