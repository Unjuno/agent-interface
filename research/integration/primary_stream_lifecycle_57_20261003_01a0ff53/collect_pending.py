from pathlib import Path
import datetime,hashlib,json,os,subprocess,time
W=Path(__file__).resolve().parent
NODE='/opt/homebrew/bin/node'
def sha(b):return hashlib.sha256(b).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
out=W/'pending-green';out.mkdir(exist_ok=False);source=W/'candidate'
pins={p.name:sha(p.read_bytes()) for p in source.glob('*.mjs')}
freeze={'created_utc':utc(),'classification':'two additional ordinary actual-owner pending-reply checks, not old consumed allocation','source_commit':json.loads((W/'SOURCE_COMMIT.json').read_bytes())['source_commit'],'source_sha256':pins,'helpers':{n:sha((W/n).read_bytes()) for n in ['pending_fixture.mjs','pending_probe.mjs','collect_pending.py']},'scenarios':['pending_success','pending_persistence_failure'],'parent_timeout_seconds':5,'owned_fixture_observation_seconds':3,'expected_native_requests_each':1,'expected_tool':'interface_clock','no_actual_backend_or_input':True}
(out/'SOURCE_FREEZE.json').write_text(json.dumps(freeze,indent=2)+'\n');rows=[]
for scenario in freeze['scenarios']:
    d=out/scenario;d.mkdir();cmd=[NODE,str(W/'pending_probe.mjs'),scenario,str(source),str(d)];r={'scenario':scenario,'argv':cmd,'started_utc':utc()}
    try:
        p=subprocess.run(cmd,capture_output=True,timeout=5);stdout,stderr=p.stdout,p.stderr;r.update(exit_code=p.returncode,timed_out=False)
    except subprocess.TimeoutExpired as e:
        stdout,stderr=e.stdout or b'',e.stderr or b'';r.update(exit_code=None,timed_out=True)
    r['ended_utc']=utc();(d/'stdout.txt').write_bytes(stdout);(d/'stderr.txt').write_bytes(stderr)
    r.update(stdout_sha256=sha(stdout),stderr_sha256=sha(stderr));deadline=time.monotonic()+3
    while not (d/'fixture.exit.json').exists() and time.monotonic()<deadline:time.sleep(.02)
    for name in ['fixture.started.json','fixture.exit.json','owner.summary.json','host/exit.json']:
        if (d/name).exists():r[name]=json.loads((d/name).read_bytes())
    if 'fixture.started.json' in r:
        pid=r['fixture.started.json']['pid']
        while time.monotonic()<deadline:
            try:os.kill(pid,0)
            except ProcessLookupError:break
            time.sleep(.02)
        try:os.kill(pid,0);r['fixture_pid_absent']=False
        except ProcessLookupError:r['fixture_pid_absent']=True
    (d/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');rows.append(r)
    if r['timed_out']:break
assert {p.name:sha(p.read_bytes()) for p in source.glob('*.mjs')}==pins
(out/'RAW.json').write_text(json.dumps({'classification':freeze['classification'],'rows':rows},indent=2)+'\n')
print(json.dumps({'actual_exits':[r['exit_code'] for r in rows],'fixture_exits':[r.get('fixture.exit.json') for r in rows],'owner_outcomes':[r.get('owner.summary.json',{}).get('rows') for r in rows],'fixture_pid_absent':[r.get('fixture_pid_absent') for r in rows]}))
