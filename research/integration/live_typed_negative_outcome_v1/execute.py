from __future__ import annotations
import argparse, json, os, pathlib, signal, subprocess, sys, time

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',required=True); ap.add_argument('--reps',type=int,required=True); ap.add_argument('--timeout',type=float,default=60.0); args=ap.parse_args()
    root=pathlib.Path(args.out); root.parent.mkdir(parents=True,exist_ok=True)
    receipt=pathlib.Path(str(root)+'.EXECUTION.json')
    cmd=[sys.executable,'-B',str(pathlib.Path(__file__).with_name('run.py')),'--out',str(root),'--reps',str(args.reps)]
    started=time.monotonic_ns(); p=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
    timed_out=False
    try:
        out,err=p.communicate(timeout=args.timeout)
    except subprocess.TimeoutExpired:
        timed_out=True; os.killpg(p.pid,signal.SIGTERM)
        try: out,err=p.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid,signal.SIGKILL); out,err=p.communicate()
    ended=time.monotonic_ns()
    rec={'cmd':cmd,'pid':p.pid,'started_ns':started,'ended_ns':ended,'timeout_s':args.timeout,'timed_out':timed_out,'returncode':p.returncode,'stdout':out,'stderr':err}
    receipt.write_text(json.dumps(rec,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'receipt':str(receipt),'timed_out':timed_out,'returncode':p.returncode},sort_keys=True))
    raise SystemExit(0 if (not timed_out and p.returncode==0) else 2)
if __name__=='__main__': main()
