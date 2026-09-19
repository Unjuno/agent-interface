from pathlib import Path
import json, os, subprocess, sys, time

def run(out: Path, timeout=8):
    out.mkdir(parents=True, exist_ok=True)
    display=':99'; started=time.monotonic()
    xvfb=subprocess.Popen(['Xvfb',display,'-screen','0','640x360x24','-nolisten','tcp','-ac'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    fixture=None; meta=out/'meta.json'
    try:
        socket=Path('/tmp/.X11-unix/X99')
        while not socket.exists() and xvfb.poll() is None and time.monotonic()-started<timeout: time.sleep(.02)
        env=dict(os.environ,DISPLAY=display)
        fixture=subprocess.Popen([sys.executable,'research/integration/golden_v3_second_domain_2246_v1/gtk_fixture_app.py','--mode','useful','--meta',str(meta),'--effect',str(out/'effect.json'),'--events',str(out/'events.jsonl')],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        deadline=time.monotonic()+timeout
        while not meta.exists() and fixture.poll() is None and time.monotonic()<deadline: time.sleep(.02)
        alive=meta.exists() and fixture.poll() is None
        if fixture.poll() is None: fixture.terminate()
        fs,fe=fixture.communicate(timeout=5); xvfb.terminate(); xs,xe=xvfb.communicate(timeout=5)
        result={'decision':'PASS_GTK_FIXTURE_STARTUP_DIAGNOSTIC' if socket.exists() and alive else 'STOP_GTK_FIXTURE_STARTUP','display':display,'x_socket_ready':socket.exists(),'meta_present':meta.exists(),'fixture_alive_at_meta':alive,'fixture_exit_code':fixture.returncode,'xvfb_exit_code':xvfb.returncode,'elapsed_ms':round((time.monotonic()-started)*1000,3),'fixture_stdout':fs,'fixture_stderr':fe,'xvfb_stdout':xs,'xvfb_stderr':xe}
        (out/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        return result
    finally:
        if fixture is not None and fixture.poll() is None: fixture.kill()
        if xvfb.poll() is None: xvfb.kill()

if __name__=='__main__':
    r=run(Path(sys.argv[1])); print(json.dumps(r,indent=2,sort_keys=True)); raise SystemExit(0 if r['decision'].startswith('PASS') else 1)
