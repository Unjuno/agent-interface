"""Live development probes, not a fixed-model performance benchmark."""
import argparse
import json
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent


def probe(app,seed,out):
    process=subprocess.Popen([sys.executable,str(HERE/'session.py'),'--app',app,'--seed',str(seed),'--out',str(out)],
                             stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
    lines=queue.Queue();events=[]
    def reader():
        for line in process.stdout:lines.put(json.loads(line))
        lines.put(None)
    thread=threading.Thread(target=reader,daemon=True);thread.start()
    def send(obj):process.stdin.write(json.dumps(obj)+'\n');process.stdin.flush()
    def until(predicate):
        end=time.monotonic()+30
        while True:
            row=lines.get(timeout=max(.01,end-time.monotonic()))
            if row is None:raise RuntimeError('session ended early')
            events.append(row)
            if predicate(row):return row
            if time.monotonic()>end:raise TimeoutError('probe deadline')
    def event(name,identifier=None):
        return until(lambda r:r['event']==name and (identifier is None or r.get('id')==identifier))
    try:
        ready=event('ready');event('observation')
        # Entire invalid tail must reject without executing the valid prefix.
        send(dict(op='submit',id='invalid',steps=[dict(op='text',text='bad'),dict(op='text',text='!')]))
        event('rejected')
        send(dict(op='submit',id='hold',steps=[dict(op='hold',keys=['Control_L'],duration_ms=3000),dict(op='text',text='bad')]))
        accepted=event('accepted','hold');held=event('keys_held','hold')
        send(dict(op='submit',id='busy',steps=[dict(op='text',text='bad')]))
        busy=event('rejected')
        send(dict(op='cancel',id='hold'))
        cancel=event('cancel_requested','hold');terminal=event('terminal','hold')
        assert cancel['matched'] and terminal['status']=='cancelled'
        assert terminal['steps_completed']==0 and terminal['release']['verified']
        assert not any(r['event']=='step_started' and r.get('id')=='hold' and r['step']==1 for r in events)
        # A public-condition timeout must stop before its following input.
        send(dict(op='submit',id='timeout',steps=[dict(op='wait_title',contains='MISSING-PROBE-TITLE',timeout_ms=50),dict(op='text',text='bad')]))
        timeout=event('terminal','timeout')
        assert timeout['status']=='failed' and timeout['steps_completed']==0 and timeout['release']['verified']
        goal=ready['goal']
        if app=='xterm':
            steps=[dict(op='text',text=goal['token']),dict(op='key',key='Return'),
                   dict(op='wait_title',contains='AI XTERM SAVED',timeout_ms=2000)]
        else:
            steps=[dict(op='text',text=str(goal['a'])),dict(op='key',key='Return'),
                   dict(op='text',text=str(goal['b'])),dict(op='key',key='Return'),
                   dict(op='chord',modifier='Control_L',key='s'),
                   dict(op='wait_title',contains='Confirm File Format',timeout_ms=2000),dict(op='key',key='Return')]
        send(dict(op='submit',id='task',steps=steps))
        task=event('terminal','task');assert task['status']=='completed' and task['release']['verified']
        send(dict(op='finish'));score=event('independent_evaluation');assert score['success'],score
        process.wait(timeout=15)
        assert process.returncode==0
        # Reopen the actual packet stream and every published image independently.
        sys.path.insert(0,str(HERE.parent/'observation_tiles'))
        from tile_transport import Decoder,Frame
        from PIL import Image
        decoder=Decoder('live-control');frames=0
        for row in events:
            if row['event']!='observation':continue
            frame=decoder.accept((out/f'{row["sequence"]:03d}.ait').read_bytes())
            with Image.open(row['image']) as im:assert Frame(im.width,im.height,im.mode,im.tobytes())==frame
            frames+=1
        report=dict(app=app,seed=seed,success=True,frames_verified=frames,
                    cancel_to_release_ms=(terminal['release']['verified_ns']-cancel['requested_ns'])/1e6,
                    cancel_to_terminal_ms=(terminal['terminal_ns']-cancel['requested_ns'])/1e6,
                    accepted_before_input=accepted['accepted_ns']<=held['input_ack_ns'],
                    release_verified=True,invalid_tail_and_busy_rejected=True,timeout_stopped_tail=True,
                    completed_steps=len(steps),scope='live scripted functional probe; no model or human latency comparison')
        (out/'probe.json').write_text(json.dumps(report,indent=2));return report
    finally:
        if process.poll() is None:
            process.stdin.close()
            try:process.wait(timeout=15)
            except subprocess.TimeoutExpired:process.terminate();process.wait(timeout=10)
        (out/'stderr.txt').write_text(process.stderr.read())


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--seed',type=int,default=820101);ap.add_argument('--pairs',type=int,default=3)
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=False)
    reports=[]
    try:
        for i in range(args.pairs):
            for app in ('xterm','calc'):
                report=probe(app,args.seed+i,args.out/f'{app}-{args.seed+i}')
                reports.append(report);print(json.dumps(report),flush=True)
    finally:(args.out/'summary.json').write_text(json.dumps(reports,indent=2))


if __name__=='__main__':main()
