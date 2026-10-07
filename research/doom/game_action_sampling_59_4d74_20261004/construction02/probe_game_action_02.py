from pathlib import Path
import subprocess,sys,json,threading,queue,time
out=Path('/out');rows=[];q=queue.Queue()
stderr=(out/'session.stderr.txt').open('wb')
child=subprocess.Popen([sys.executable,'/study/game_action_measurement_entry_01.py','--out','/out/runtime','--seed','40122','--skill','1','--timeout-seconds','60','--load-fixture-manifest','/study/fixture-input/fixture.json'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=stderr,text=True)
def reader():
    with (out/'session.stdout.jsonl').open('w') as raw:
        for line in child.stdout:
            raw.write(line);raw.flush()
            row=json.loads(line);rows.append(row);q.put(row)
t=threading.Thread(target=reader,daemon=True);t.start()
def wait(event,identifier=None,timeout=20):
    until=time.monotonic()+timeout
    while True:
        try: row=q.get(timeout=min(.2,max(.001,until-time.monotonic())))
        except queue.Empty:
            if child.poll() is not None: raise RuntimeError('session exited before '+event)
            if time.monotonic()>until: raise TimeoutError(event)
            continue
        if row.get('event')==event and (identifier is None or row.get('id')==identifier):return row
        if time.monotonic()>until:raise TimeoutError(event)
def send(command):
    child.stdin.write(json.dumps(command)+'\n');child.stdin.flush()
rescue=False
try:
    wait('ready');observation=wait('observation')
    send({'op':'clock','id':'clock-action-probe'})
    clock=wait('clock_probe')
    now=clock.get('now_ns',clock.get('clock_ns',clock.get('emit_ns')))
    send({'op':'submit','id':'left-action-probe','expected_sequence':observation['sequence'],
          'valid_until_ns':now+10_000_000_000,
          'steps':[{'op':'hold','keys':['Left'],'duration_ms':250},{'op':'observe'}]})
    terminal=wait('terminal','left-action-probe')
    assert terminal['status']=='completed',terminal
    send({'op':'coast','duration_ms':500,'sample_ms':50})
    wait('coast_result')
    send({'op':'finish'});wait('post_control_score');code=child.wait(timeout=10);t.join(timeout=3)
    (out/'PROBE_RESULT.json').write_text(json.dumps({'child_exit':code,'reader_alive':t.is_alive(),'terminal':terminal,'external_rescue_used':False},indent=2))
    assert code==0 and not t.is_alive()
finally:
    if child.poll() is None:
        rescue=True;child.kill();child.wait(timeout=3)
    t.join(timeout=3);stderr.close()
    (out/'PROBE_FINAL.json').write_text(json.dumps({'child_exit':child.poll(),'external_rescue_used':rescue,'reader_alive':t.is_alive()}))
