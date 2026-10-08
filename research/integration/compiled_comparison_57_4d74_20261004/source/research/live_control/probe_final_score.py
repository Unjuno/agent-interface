"""Subprocess negative episode: invalid reservation, then cancellable final task."""
import json,queue,subprocess,sys,threading,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
out=HERE/'results/final-score-cancel-01'
process=subprocess.Popen([sys.executable,'-u',str(HERE/'interactive_v19.py'),'--app','xterm','--seed','991023','--out',str(out),'--presentation','compact'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
messages=queue.Queue();seen=[]
def read():
    for line in process.stdout:
        try:messages.put(json.loads(line))
        except ValueError:pass
threading.Thread(target=read,daemon=True).start()
def send(command):process.stdin.write(json.dumps(command)+'\n');process.stdin.flush()
def until(kind,timeout=30):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        r=messages.get(timeout=max(.01,deadline-time.monotonic()));seen.append(r)
        if r['event']==kind:return r
    raise TimeoutError(kind)
try:
    obs=until('observation');send(dict(op='clock'));clock=until('clock')
    common=dict(op='submit',finish_after=True,expected_sequence=obs['sequence'],valid_until_ns=clock['runtime_ns']+15_000_000_000,
                decision_evidence=dict(delivery_id=obs['delivery_id'],observation_sequence=obs['sequence'],producer='scripted'))
    send(dict(common,id='invalid',steps=[dict(op='chord',keys=['Control_L','s'])]))
    assert until('rejected')['reason']=='unsupported chord'
    send(dict(common,id='cancel_final',steps=[dict(op='hold',keys=['Shift_L'],duration_ms=3000)]))
    until('step_started');time.sleep(.1);send(dict(op='cancel',id='cancel_final'))
    score=until('independent_evaluation')
    terminal=next(r for r in seen if r['event']=='terminal')
    assert terminal['status']=='cancelled' and terminal['release']['verified']
    assert not score['success'] and score['final_program']=='cancel_final'
    send(dict(op='finish'));process.communicate(timeout=10)
    assert process.returncode==0
    (out/'probe-result.json').write_text(json.dumps(dict(invalid_reservation_rejected=True,cancellation_retained=True,failed_score_retained=True,status=terminal['status']),indent=2)+'\n')
    print('Invalid final reservation rejected; subsequent final task cancelled and independently scored false.')
finally:
    if process.poll() is None:process.kill();process.wait()
