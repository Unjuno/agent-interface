#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, signal, subprocess, sys, tempfile, time
from pathlib import Path

HERE=Path(__file__).resolve().parent

def wait_display(name: str, timeout_s=3.0) -> None:
    deadline=time.monotonic()+timeout_s
    while time.monotonic()<deadline:
        p=subprocess.run(['xdpyinfo','-display',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        if p.returncode==0: return
        time.sleep(.05)
    raise RuntimeError('Xvfb did not become ready')

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--display',default=':197'); ap.add_argument('--seed',type=int,default=20260915); args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=False)
    auth=args.out/'Xauthority'; auth.write_bytes(b'')
    env=os.environ.copy(); env['XAUTHORITY']=str(auth)
    xvfb=subprocess.Popen(['Xvfb',args.display,'-screen','0','800x600x24','-nolisten','tcp','-ac'],stdout=(args.out/'xvfb.stdout').open('w'),stderr=(args.out/'xvfb.stderr').open('w'),env=env)
    fixture=None
    try:
        wait_display(args.display)
        fixture=subprocess.Popen([sys.executable,str(HERE/'fixture.py'),'--display',args.display,'--events',str(args.out/'fixture-events.jsonl')],stdout=subprocess.PIPE,stderr=(args.out/'fixture.stderr').open('w'),text=True,env=env)
        line=None
        deadline=time.monotonic()+3
        while time.monotonic()<deadline:
            candidate=fixture.stdout.readline()
            if not candidate: time.sleep(.02); continue
            if candidate.lstrip().startswith('{'):
                line=candidate; break
        if line is None: raise RuntimeError('fixture did not publish window id')
        window_id=json.loads(line)['window_id']
        portable=HERE.parent/'runtime_portability_v0'
        if not portable.exists():
            external=os.environ.get('AGENT_INTERFACE_PORTABLE_ORACLE')
            if not external: raise RuntimeError('portable oracle unavailable')
            portable=Path(external)
        child_env=env.copy(); child_env['AGENT_INTERFACE_PORTABLE_ORACLE']=str(portable)
        cmd=[sys.executable,str(HERE/'experiment.py'),'--display',args.display,'--window-id',str(window_id),'--events',str(args.out/'fixture-events.jsonl'),'--out',str(args.out/'result'),'--seed',str(args.seed)]
        run=subprocess.run(cmd,text=True,capture_output=True,env=child_env)
        (args.out/'experiment.stdout').write_text(run.stdout,encoding='utf-8')
        (args.out/'experiment.stderr').write_text(run.stderr,encoding='utf-8')
        (args.out/'experiment.exitcode').write_text(str(run.returncode)+'\n',encoding='utf-8')
        if (args.out/'result'/'report.json').exists(): print((args.out/'result'/'report.json').read_text(encoding='utf-8'))
        return run.returncode
    finally:
        if fixture is not None:
            fixture.terminate()
            try: fixture.wait(timeout=1)
            except subprocess.TimeoutExpired: fixture.kill()
        xvfb.terminate()
        try: xvfb.wait(timeout=1)
        except subprocess.TimeoutExpired: xvfb.kill()

if __name__=='__main__': raise SystemExit(main())
