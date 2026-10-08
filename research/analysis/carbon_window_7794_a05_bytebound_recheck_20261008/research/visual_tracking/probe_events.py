"""Fresh local functional checks; scripted client is not an LLM benchmark."""
import argparse,hashlib,json,queue,subprocess,sys,threading,time
from pathlib import Path
from PIL import Image
from signals import detect
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'observation_tiles'))
from tile_transport import Decoder,Frame


def probe(out,seed,kind):
    p=subprocess.Popen([sys.executable,str(HERE/'async_events.py'),'--out',str(out),
        '--seed',str(seed),'--seconds','3','--event',kind],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
    q=queue.Queue();events=[]
    def read():
        try:
            for line in p.stdout:q.put(json.loads(line))
        except Exception as exc:q.put(dict(event='reader_error',error=repr(exc)))
        finally:q.put(None)
    threading.Thread(target=read,daemon=True).start()
    def until(name):
        while True:
            e=q.get(timeout=15)
            if e is None:raise RuntimeError('child ended before '+name)
            events.append(e)
            if e['event']==name:return e
            if e['event']=='reader_error':raise RuntimeError(e)
    def send(c):p.stdin.write(json.dumps(c)+'\n');p.stdin.flush()
    try:
        initial=until('observation')
        send(dict(op='submit',id='track',expected_sequence=initial['sequence'],steps=[dict(op='key',key='Return'),dict(op='track_red',duration_ms=3000),dict(op='decide')]))
        terminal=until('terminal')
        assert terminal['status']=='needs_decision' and terminal['release']['verified']
        signals=[e for e in events if e['event']=='critical_signal']
        assert len(signals)==(0 if kind=='none' else 1)
        if signals:
            signal=signals[0]
            assert signal['condition']==('yellow_alert' if kind=='alert' else 'target_lost')
            # Client delay deliberately outlasts the 0.5-second event.
            time.sleep(.7)
            send(dict(op='submit',id='unacked',expected_sequence=terminal['latest_sequence'],steps=[dict(op='key',key='Right')]))
            assert 'pending signals' in until('rejected')['reason']
            send(dict(op='submit',id='refresh',expected_sequence=terminal['latest_sequence'],steps=[dict(op='observe')]))
            fresh=until('observation');assert until('terminal')['status']=='completed'
            send(dict(op='poll'));poll=until('latest_observation')
            assert poll['sequence']==fresh['sequence'] and poll['pending_signals'][0]['signal_id']==signal['signal_id']
            with Image.open(fresh['image']) as im:assert detect(Frame(im.width,im.height,im.mode,im.tobytes())) is None
            send(dict(op='ack_signal',signal_id='incorrect'));assert 'unknown signal' in until('rejected')['reason']
            send(dict(op='ack_signal',signal_id=signal['signal_id']));until('signal_acknowledged')
            send(dict(op='poll'));assert until('latest_observation')['pending_signals']==[]
        send(dict(op='finish'));until('independent_record');p.wait(timeout=10);assert p.returncode==0
        rows=[json.loads(s) for s in (out/'events.jsonl').read_text().splitlines()]
        decoder=Decoder('live-control');frames={}
        for r in rows:
            if r['event']=='observation':
                f=decoder.accept((out/f'{r["sequence"]:03d}.ait').read_bytes())
                with Image.open(out/Path(r['image']).name) as im:assert f==Frame(im.width,im.height,im.mode,im.tobytes())
                frames[r['sequence']]=detect(f)
        for s in signals:assert frames[s['sequence']]==s['condition']
        if signals:
            assert not any(r['event']=='motor_feedback' and r['input_ack_ns']>=signals[0]['detected_ns'] for r in rows)
            assert not any(r['event']=='step_started' and r['id']=='track' and r['step']==2 for r in rows)
        report=dict(seed=seed,kind=kind,passed=True,exact_frames=len(frames),signals=len(signals),
            release_verified=True,signal_to_release_ms=(terminal['release']['verified_ns']-signals[0]['detected_ns'])/1e6 if signals else None,
            scope='scripted private GUI functional probe; no generic event recall or model performance claim')
        (out/'probe.json').write_text(json.dumps(report,indent=2));return report
    finally:
        if p.poll() is None:
            p.stdin.close()
            try:p.wait(timeout=10)
            except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=5)
        if out.exists():(out/'stderr.txt').write_text(p.stderr.read())


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=False)
    names=('probe_events.py','async_events.py','arena_events.py','signals.py')
    (a.out/'freeze.json').write_text(json.dumps({n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in names},indent=2))
    for n in names:(a.out/('source-'+n)).write_bytes((HERE/n).read_bytes())
    rows=[]
    try:
        for seed in (880201,880202):
            for kind in ('alert','target_loss','none'):
                try:r=probe(a.out/f'{seed}-{kind}',seed,kind)
                except Exception as exc:r=dict(seed=seed,kind=kind,passed=False,error=repr(exc))
                rows.append(r);print(json.dumps(r),flush=True)
    finally:(a.out/'summary.json').write_text(json.dumps(rows,indent=2))
